"""
Integrity checks for the mock data in server/data/.

orders.json and demand_forecasts.json come from server/generate_data.py;
the other files are hand-edited. These tests keep them consistent and
believable: unique IDs, references that resolve, totals that add up,
orders that ship from the warehouse holding the stock, statuses that fit
the dates, and money flows that fit together. They read the loaded module
data, not the API (except where the API computes the data).
"""
from collections import Counter

import pytest

import main
from main import DemandForecast, MonthlySpending, Order, Transaction, WAREHOUSES

DATA_AS_OF = "2025-12-31T23:59:59"
STOCK = {i["sku"]: i for i in main.inventory_items}


def duplicates(values):
    return [v for v, n in Counter(values).items() if n > 1]


@pytest.mark.parametrize("model,rows", [
    (Order, main.orders),
    (DemandForecast, main.demand_forecasts),
    (MonthlySpending, main.monthly_spending),
    (Transaction, main.recent_transactions),
], ids=lambda x: getattr(x, "__name__", ""))
def test_every_row_matches_its_model(model, rows):
    for row in rows:
        model.model_validate(row)


def test_ids_are_unique():
    assert duplicates(i["id"] for i in main.inventory_items) == []
    assert duplicates(i["sku"] for i in main.inventory_items) == []
    assert duplicates(o["id"] for o in main.orders) == []
    assert duplicates(o["order_number"] for o in main.orders) == []
    assert duplicates(f["id"] for f in main.demand_forecasts) == []
    assert duplicates(b["id"] for b in main.compute_backlog(main.orders)) == []
    assert duplicates(t["id"] for t in main.recent_transactions) == []


def test_order_lines_reference_inventory_with_matching_names():
    names = {i["sku"]: i["name"] for i in main.inventory_items}
    for order in main.orders:
        for line in order["items"]:
            assert line["sku"] in names, f"{order['order_number']}: unknown SKU {line['sku']}"
            assert line["name"] == names[line["sku"]], f"{order['order_number']}: name mismatch for {line['sku']}"


def test_order_total_equals_sum_of_lines():
    for order in main.orders:
        lines = sum(line["quantity"] * line["unit_price"] for line in order["items"])
        assert order["total_value"] == pytest.approx(lines, abs=0.01), order["order_number"]


def test_delivery_dates_match_status():
    for order in main.orders:
        delivered = order["status"] == "Delivered"
        assert bool(order.get("actual_delivery")) == delivered, order["order_number"]
        if delivered:
            assert order["order_date"] <= order["actual_delivery"] <= DATA_AS_OF, order["order_number"]
        assert order["order_date"] <= order["expected_delivery"], order["order_number"]


def test_nothing_is_dated_after_the_snapshot():
    assert max(o["order_date"] for o in main.orders) <= DATA_AS_OF
    assert max(i["last_updated"] for i in main.inventory_items) <= DATA_AS_OF


def test_inventory_rows_validate_with_stock_status():
    for item in main.inventory_items:
        main.InventoryItem.model_validate(main.with_stock_status(item))


def test_orders_ship_from_the_warehouse_that_stocks_them():
    for order in main.orders:
        for line in order["items"]:
            assert STOCK[line["sku"]]["warehouse"] == order["warehouse"], f"{order['order_number']} {line['sku']}"


def test_order_category_is_the_category_of_its_lines():
    for order in main.orders:
        assert {STOCK[line["sku"]]["category"] for line in order["items"]} == {order["category"]}, order["order_number"]


def test_order_lines_have_distinct_skus():
    for order in main.orders:
        assert duplicates(line["sku"] for line in order["items"]) == [], order["order_number"]


def test_lines_sell_above_cost():
    for order in main.orders:
        for line in order["items"]:
            assert line["unit_price"] > STOCK[line["sku"]]["unit_cost"], f"{order['order_number']} {line['sku']}"


def test_open_orders_fit_the_snapshot():
    """Old orders are delivered or backordered; Shipped/Processing are recent."""
    for order in main.orders:
        if order["status"] == "Processing":
            assert order["order_date"] >= "2025-12-20", order["order_number"]
        if order["status"] == "Shipped":
            assert order["expected_delivery"] >= "2025-12-20", order["order_number"]


def test_backordered_means_short_on_stock():
    backlog_orders = {b["order_number"] for b in main.compute_backlog(main.orders)}
    for order in main.orders:
        short = any(line["quantity"] > STOCK[line["sku"]]["quantity_on_hand"] for line in order["items"])
        assert short == (order["status"] == "Backordered"), order["order_number"]
        assert (order["order_number"] in backlog_orders) == (order["status"] == "Backordered"), order["order_number"]


def test_cost_of_goods_fits_procurement_and_stock():
    cogs = sum(line["quantity"] * STOCK[line["sku"]]["unit_cost"] for o in main.orders for line in o["items"])
    procurement = sum(m["procurement"] for m in main.monthly_spending)
    stock_value = sum(i["quantity_on_hand"] * i["unit_cost"] for i in main.inventory_items)
    assert cogs <= procurement + stock_value


def test_forecast_demand_matches_recent_orders():
    """current_demand = average monthly units ordered in Oct-Dec"""
    for f in main.demand_forecasts:
        units = sum(line["quantity"] for o in main.orders if o["order_date"][:7] >= "2025-10"
                    for line in o["items"] if line["sku"] == f["item_sku"])
        assert f["current_demand"] == max(1, round(units / 3)), f["item_sku"]


def test_forecasts_reference_inventory():
    names = {i["sku"]: i["name"] for i in main.inventory_items}
    for f in main.demand_forecasts:
        assert names.get(f["item_sku"]) == f["item_name"], f["item_sku"]


def test_transactions_use_known_warehouses():
    assert {t["warehouse"] for t in main.recent_transactions} <= set(WAREHOUSES)


def test_spending_months_are_complete_and_unique():
    months = [m["month"] for m in main.monthly_spending]
    assert sorted(months, key=main.MONTH_NAMES.index) == main.MONTH_NAMES
