"""
Contract tests: filter validation and the shape/consistency of aggregate endpoints.
"""
import pytest

FILTERED_ENDPOINTS = [
    "/api/inventory", "/api/orders", "/api/backlog", "/api/dashboard/summary",
    "/api/reports/quarterly", "/api/reports/monthly-trends",
]


class TestFilterValidation:
    @pytest.mark.parametrize("endpoint", FILTERED_ENDPOINTS)
    @pytest.mark.parametrize("params", [
        {"warehouse": "Paris"},
        {"category": "Widgets"},
        {"month": "2025-13"},
        {"month": "January"},
    ])
    def test_unknown_filter_values_are_rejected(self, client, endpoint, params):
        assert client.get(endpoint, params=params).status_code == 422

    def test_unknown_status_is_rejected(self, client):
        assert client.get("/api/orders", params={"status": "lost"}).status_code == 422

    def test_filters_ignore_case(self, client):
        exact = client.get("/api/orders", params={"warehouse": "Tokyo", "category": "Sensors", "status": "Delivered"}).json()
        lower = client.get("/api/orders", params={"warehouse": "tokyo", "category": "sensors", "status": "delivered"}).json()
        assert exact == lower and len(exact) > 0

    @pytest.mark.parametrize("upper,lower", [("Q2-2025", "q2-2025"), ("all", "ALL")])
    def test_month_ignores_case(self, client, upper, lower):
        assert client.get("/api/orders", params={"month": upper}).json() == \
            client.get("/api/orders", params={"month": lower}).json()

    def test_spending_month_is_validated(self, client):
        assert client.get("/api/spending/summary", params={"month": "2025-13"}).status_code == 422
        assert client.get("/api/spending/transactions", params={"month": "q3-2025"}).status_code == 200

    @pytest.mark.parametrize("endpoint", FILTERED_ENDPOINTS)
    def test_all_means_no_filter(self, client, endpoint):
        params = {"warehouse": "all", "category": "all", "status": "all", "month": "all"}
        assert client.get(endpoint, params=params).json() == client.get(endpoint).json()


class TestDashboardSummaryContract:
    def test_order_metrics_agree_with_orders(self, client):
        params = {"warehouse": "London", "month": "Q2-2025"}
        summary = client.get("/api/dashboard/summary", params=params).json()
        orders = client.get("/api/orders", params=params).json()

        assert summary["total_orders"] == len(orders)
        assert summary["total_orders_value"] == pytest.approx(sum(o["total_value"] for o in orders))
        assert summary["avg_order_value"] == pytest.approx(summary["total_orders_value"] / len(orders), abs=0.01)
        assert sum(summary["status_counts"].values()) == len(orders)
        assert summary["orders_fulfilled"] == summary["status_counts"]["delivered"]
        assert 0 <= summary["on_time_rate"] <= 100

    @pytest.mark.parametrize("month,months", [(None, 12), ("2025-03", 1), ("Q3-2025", 3)])
    def test_revenue_goal_scales_with_period(self, client, month, months):
        params = {"month": month} if month else {}
        assert client.get("/api/dashboard/summary", params=params).json()["revenue_goal"] == 800_000 * months

    def test_category_values_add_up_to_inventory_value(self, client):
        summary = client.get("/api/dashboard/summary").json()
        total = sum(c["value"] for c in summary["inventory_value_by_category"])
        assert total == pytest.approx(summary["total_inventory_value"], abs=0.01)


class TestSpendingContract:
    def test_summary_totals_are_sums_of_monthly_rows(self, client):
        monthly = client.get("/api/spending/monthly").json()
        summary = client.get("/api/spending/summary").json()
        for field, key in [("total_procurement_cost", "procurement"), ("total_operational_cost", "operational"),
                           ("total_labor_cost", "labor"), ("total_overhead", "overhead")]:
            assert summary[field] == sum(m[key] for m in monthly)

    def test_summary_for_one_month(self, client):
        march = next(m for m in client.get("/api/spending/monthly").json() if m["month"] == "Mar")
        summary = client.get("/api/spending/summary", params={"month": "2025-03"}).json()
        assert summary["total_labor_cost"] == march["labor"]

    def test_categories_break_down_procurement(self, client):
        categories = client.get("/api/spending/categories").json()
        summary = client.get("/api/spending/summary").json()
        assert sum(c["amount"] for c in categories) == summary["total_procurement_cost"]

    def test_category_percentages_sum_to_100(self, client):
        categories = client.get("/api/spending/categories").json()
        assert sum(c["percentage"] for c in categories) == pytest.approx(100, abs=0.5)

    def test_transactions_month_filter(self, client):
        sept = client.get("/api/spending/transactions", params={"month": "2025-09"}).json()
        assert sept and all(t["date"].startswith("2025-09") for t in sept)
        assert client.get("/api/spending/transactions", params={"month": "2025-01"}).json() == []


class TestReportsContract:
    def test_quarterly_matches_monthly_trends(self, client):
        quarterly = client.get("/api/reports/quarterly").json()
        monthly = client.get("/api/reports/monthly-trends").json()
        assert sum(q["total_orders"] for q in quarterly) == sum(m["order_count"] for m in monthly)
        assert sum(q["total_revenue"] for q in quarterly) == pytest.approx(sum(m["revenue"] for m in monthly), abs=0.05)
        assert all("fulfillment_rate" in q for q in quarterly)


class TestStockStatusContract:
    def test_one_definition_everywhere(self, client):
        inventory = client.get("/api/inventory").json()
        summary = client.get("/api/dashboard/summary").json()
        assert summary["low_stock_items"] == sum(i["stock_status"] == "low_stock" for i in inventory)
        by_sku = {i["sku"]: i["stock_status"] for i in inventory}
        for p in client.get("/api/dashboard/top-products", params={"limit": 50}).json():
            assert p["stock_status"] == by_sku[p["sku"]]

    @pytest.mark.parametrize("qty,reorder,expected", [(100, 100, "low_stock"), (150, 100, "adequate"), (151, 100, "in_stock")])
    def test_thresholds(self, qty, reorder, expected):
        import main
        assert main.stock_status({"quantity_on_hand": qty, "reorder_point": reorder}) == expected


class TestTopProductsContract:
    def test_matches_order_lines(self, client):
        params = {"warehouse": "Tokyo", "month": "Q3-2025"}
        orders = client.get("/api/orders", params=params).json()
        top = client.get("/api/dashboard/top-products", params={**params, "limit": 50}).json()
        lines = [line for o in orders for line in o["items"]]
        assert {p["sku"] for p in top} == {line["sku"] for line in lines}
        for p in top:
            assert p["warehouse"] == "Tokyo"
            assert p["units_ordered"] == sum(line["quantity"] for line in lines if line["sku"] == p["sku"])

    def test_limit(self, client):
        assert len(client.get("/api/dashboard/top-products", params={"limit": 3}).json()) == 3
        assert client.get("/api/dashboard/top-products", params={"limit": 0}).status_code == 422


class TestBacklogContract:
    def test_backlog_is_the_shortfall_of_backordered_orders(self, client):
        orders = {o["order_number"]: o for o in client.get("/api/orders", params={"status": "backordered"}).json()}
        backlog = client.get("/api/backlog").json()
        assert {b["order_number"] for b in backlog} == set(orders)
        for b in backlog:
            line = next(l for l in orders[b["order_number"]]["items"] if l["sku"] == b["item_sku"])
            assert b["quantity_needed"] == line["quantity"] > b["quantity_available"]

    def test_longest_delayed_first_and_priority_follows_delay(self, client):
        backlog = client.get("/api/backlog").json()
        delays = [b["days_delayed"] for b in backlog]
        assert delays == sorted(delays, reverse=True)
        for b in backlog:
            expected = "high" if b["days_delayed"] > 60 else "medium" if b["days_delayed"] > 14 else "low"
            assert b["priority"] == expected
