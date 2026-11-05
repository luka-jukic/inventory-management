"""
Integrity checks for the mock data in server/data/.

The JSON files are hand-edited, so these tests keep them consistent:
unique IDs, references that resolve, totals that add up, statuses that
match their dates. They read the loaded module data, not the API.
"""
from collections import Counter

import pytest

import main
from main import (BacklogItem, DemandForecast, InventoryItem, MonthlySpending, Order,
                  Transaction, WAREHOUSES)

DATA_AS_OF = "2025-12-31T23:59:59"


def duplicates(values):
    return [v for v, n in Counter(values).items() if n > 1]


@pytest.mark.parametrize("model,rows", [
    (InventoryItem, main.inventory_items),
    (Order, main.orders),
    (DemandForecast, main.demand_forecasts),
    (BacklogItem, main.backlog_items),
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
    assert duplicates(b["id"] for b in main.backlog_items) == []
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


def test_forecasts_reference_inventory():
    names = {i["sku"]: i["name"] for i in main.inventory_items}
    for f in main.demand_forecasts:
        assert names.get(f["item_sku"]) == f["item_name"], f["item_sku"]


def test_backlog_references_backordered_orders_and_inventory():
    orders = {o["order_number"]: o for o in main.orders}
    skus = {i["sku"] for i in main.inventory_items}
    for item in main.backlog_items:
        assert item["order_id"] in orders, item["id"]
        assert orders[item["order_id"]]["status"] == "Backordered", item["id"]
        assert item["item_sku"] in skus, item["id"]
        assert item["quantity_available"] < item["quantity_needed"], item["id"]


def test_purchase_orders_reference_backlog():
    backlog_ids = {b["id"] for b in main.backlog_items}
    for po in main.purchase_orders:
        assert po["backlog_item_id"] in backlog_ids


def test_transactions_use_known_warehouses():
    assert {t["warehouse"] for t in main.recent_transactions} <= set(WAREHOUSES)


def test_spending_months_are_complete_and_unique():
    months = [m["month"] for m in main.monthly_spending]
    assert sorted(months, key=main.MONTH_NAMES.index) == main.MONTH_NAMES
