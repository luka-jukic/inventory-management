"""
Tests for the audit fixes: CORS origins, optional API token, input limits and orders pagination.
"""
import main


class TestCors:
    """CORS only allows the frontend dev server."""

    def test_allowed_origin_gets_cors_header(self, client):
        response = client.get("/api/inventory", headers={"Origin": "http://localhost:3000"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_foreign_origin_gets_no_cors_header(self, client):
        response = client.get("/api/inventory", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in response.headers


class TestApiToken:
    """Write endpoints need X-API-Token only when API_TOKEN is set."""

    def test_write_without_token_when_disabled(self, client, monkeypatch):
        monkeypatch.setattr(main, "API_TOKEN", None)
        response = client.post("/api/tasks", json={"title": "t", "dueDate": "2025-01-01"})
        assert response.status_code == 201

    def test_write_rejected_without_token(self, client, monkeypatch):
        monkeypatch.setattr(main, "API_TOKEN", "secret")
        response = client.post("/api/tasks", json={"title": "t", "dueDate": "2025-01-01"})
        assert response.status_code == 401

    def test_write_accepted_with_token(self, client, monkeypatch):
        monkeypatch.setattr(main, "API_TOKEN", "secret")
        response = client.post(
            "/api/tasks",
            json={"title": "t", "dueDate": "2025-01-01"},
            headers={"X-API-Token": "secret"},
        )
        assert response.status_code == 201

    def test_reads_never_need_token(self, client, monkeypatch):
        monkeypatch.setattr(main, "API_TOKEN", "secret")
        assert client.get("/api/tasks").status_code == 200


class TestInputLimits:
    """String fields are length-limited."""

    def test_task_title_too_long(self, client):
        response = client.post("/api/tasks", json={"title": "x" * 201, "dueDate": "2025-01-01"})
        assert response.status_code == 422

    def test_not_found_detail_does_not_echo_input(self, client):
        response = client.delete("/api/tasks/<script>")
        assert response.status_code == 404
        assert "<script>" not in response.json()["detail"]


class TestOrdersPagination:
    """limit/offset on /api/orders; default returns everything."""

    def test_default_returns_all(self, client):
        all_orders = client.get("/api/orders").json()
        assert len(all_orders) == len(main.orders)

    def test_limit_and_offset(self, client):
        all_orders = client.get("/api/orders").json()
        page = client.get("/api/orders?limit=10&offset=5").json()
        assert [o["id"] for o in page] == [o["id"] for o in all_orders[5:15]]

    def test_invalid_limit(self, client):
        assert client.get("/api/orders?limit=0").status_code == 422

    def test_quarter_filter_matches_months(self, client):
        data = client.get("/api/orders?month=Q2-2025").json()
        assert len(data) > 0
        for order in data:
            assert order["order_date"][:7] in {"2025-04", "2025-05", "2025-06"}
