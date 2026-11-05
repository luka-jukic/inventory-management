"""
Regenerate orders.json and demand_forecasts.json from inventory.json.

Deterministic (fixed seed). The rules the data follows are the same ones
tests/backend/test_data_integrity.py checks:
- an order ships from the warehouse that stocks its items, and all lines
  share one product category (the order's category)
- prices are cost plus a markup; quantities are sized so the cost of goods
  sold fits within procurement spend plus stock
- status follows the dates relative to the 2025-12-31 snapshot; only orders
  with a line larger than the stock on hand are Backordered
- demand forecasts use the real average monthly units of Oct-Dec

Run from server/:  uv run python generate_data.py
"""
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path(__file__).parent / "data"
DATA_AS_OF = datetime(2025, 12, 31, 23, 59)
SEED = 2025
ORDERS_PER_MONTH = (18, 24)
LINE_VALUE = (6_000, 30_000)      # USD revenue per order line
MARKUP = (1.25, 1.6)              # selling price = unit_cost * markup

CUSTOMERS = [
    "Acme Manufacturing Corp", "TechBuild Industries", "Global Parts Ltd", "Precision Tools Inc",
    "Industrial Solutions Inc", "MegaCorp Industries", "BuildTech Co", "FastAssembly Ltd",
    "Quality Parts LLC", "Superior Manufacturing", "PrecisionWorks Inc", "Elite Systems Corp",
    "Advanced Components Inc", "ProManufacturing LLC", "TechSolutions Group", "Innovative Parts Co",
    "Premier Industries", "Dynamic Systems Ltd", "Quantum Manufacturing", "Apex Engineering",
    "Titan Products Inc", "Vanguard Systems", "Omega Manufacturing", "Fusion Industries",
    "Stellar Components Ltd", "Nexus Engineering", "Cascade Manufacturing", "Horizon Technologies",
    "Summit Parts Corp", "Velocity Industries",
]

# Existing forecasts keep their SKU and trend; numbers are recomputed
FORECAST_TRENDS = {
    "PCB-001": "increasing", "PCB-002": "stable", "PCB-003": "increasing",
    "PWM-404": "decreasing", "HMD-202": "increasing", "PRS-203": "stable",
    "PSU-501": "stable", "TMP-201": "stable", "MCU-402": "stable",
}
TREND_FACTOR = {"increasing": (1.15, 1.35), "stable": (0.99, 1.01), "decreasing": (0.75, 0.9)}

FMT = "%Y-%m-%dT%H:%M:%S"


def backorder_probability(month: int) -> float:
    """Most open backorders are recent; a few old ones stay open all year."""
    return 0.015 + 0.009 * month


def make_order(rng, order_id, month, pools):
    order_dt = datetime(2025, month, rng.randint(1, 28), rng.randint(8, 17), rng.randint(0, 59))
    if order_dt > DATA_AS_OF:
        order_dt = DATA_AS_OF - timedelta(hours=1)
    expected = order_dt + timedelta(days=rng.randint(7, 14))

    warehouse, category = rng.choice(sorted(pools))
    pool = pools[(warehouse, category)]
    products = rng.sample(pool, k=min(len(pool), rng.randint(1, 3)))
    backordered = rng.random() < backorder_probability(month)

    items = []
    for i, p in enumerate(products):
        price = round(p["unit_cost"] * rng.uniform(*MARKUP), 2)
        qty = max(1, round(rng.uniform(*LINE_VALUE) / price))
        qty = min(qty, max(1, int(p["quantity_on_hand"] * 0.8)))  # normal orders fit the stock
        if backordered and i == 0:
            qty = p["quantity_on_hand"] + rng.randint(5, max(6, p["quantity_on_hand"] // 2))
        items.append({"sku": p["sku"], "name": p["name"], "quantity": qty, "unit_price": price})

    if backordered:
        status, actual = "Backordered", None
    elif order_dt > DATA_AS_OF - timedelta(days=8):
        status, actual = "Processing", None
    elif expected > DATA_AS_OF - timedelta(days=4):
        status, actual = "Shipped", None
    else:
        status = "Delivered"
        actual = min(max(expected + timedelta(days=rng.randint(-3, 1)), order_dt + timedelta(days=2)), DATA_AS_OF)

    return {
        "id": str(order_id),
        "order_number": f"ORD-2025-{order_id:04d}",
        "customer": rng.choice(CUSTOMERS),
        "items": items,
        "status": status,
        "warehouse": warehouse,
        "category": category,
        "order_date": order_dt.strftime(FMT),
        "expected_delivery": expected.strftime(FMT),
        "total_value": round(sum(i["quantity"] * i["unit_price"] for i in items), 2),
        "actual_delivery": actual.strftime(FMT) if actual else None,
    }


def make_forecasts(rng, orders, inventory):
    names = {i["sku"]: i["name"] for i in inventory}
    units = defaultdict(int)
    for o in orders:
        if o["order_date"][:7] >= "2025-10":
            for line in o["items"]:
                units[line["sku"]] += line["quantity"]
    forecasts = []
    for n, (sku, trend) in enumerate(FORECAST_TRENDS.items(), start=1):
        current = max(1, round(units[sku] / 3))
        forecasts.append({
            "id": str(n),
            "item_sku": sku,
            "item_name": names[sku],
            "current_demand": current,
            "forecasted_demand": max(1, round(current * rng.uniform(*TREND_FACTOR[trend]))),
            "trend": trend,
            "period": "Next 30 days",
        })
    return forecasts


def main():
    rng = random.Random(SEED)
    inventory = json.loads((DATA / "inventory.json").read_text())
    pools = defaultdict(list)
    for item in inventory:
        pools[(item["warehouse"], item["category"])].append(item)

    orders, order_id = [], 1
    for month in range(1, 13):
        for _ in range(rng.randint(*ORDERS_PER_MONTH)):
            orders.append(make_order(rng, order_id, month, pools))
            order_id += 1

    # Fail loudly instead of writing data the integrity tests would reject
    cost = {i["sku"]: i["unit_cost"] for i in inventory}
    cogs = sum(line["quantity"] * cost[line["sku"]] for o in orders for line in o["items"])
    spending = json.loads((DATA / "spending.json").read_text())
    budget = sum(m["procurement"] for m in spending["monthly_spending"]) + \
        sum(i["quantity_on_hand"] * i["unit_cost"] for i in inventory)
    if cogs > budget:
        raise SystemExit(f"Cost of goods {cogs:,.0f} exceeds procurement plus stock {budget:,.0f}; lower LINE_VALUE")

    (DATA / "orders.json").write_text(json.dumps(orders, indent=2, ensure_ascii=False) + "\n")
    (DATA / "demand_forecasts.json").write_text(
        json.dumps(make_forecasts(rng, orders, inventory), indent=2, ensure_ascii=False) + "\n")

    by_status = defaultdict(int)
    for o in orders:
        by_status[o["status"]] += 1
    print(f"{len(orders)} orders, revenue {sum(o['total_value'] for o in orders):,.0f}, {dict(by_status)}")


if __name__ == "__main__":
    main()
