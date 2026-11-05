"""
Tests for the tasks and purchase order API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_state():
    """Both stores are in-memory module lists; restore them around each test."""
    saved_pos, saved_tasks = list(main.purchase_orders), list(main.tasks)
    main.purchase_orders.clear()
    main.tasks.clear()
    yield
    main.purchase_orders[:] = saved_pos
    main.tasks[:] = saved_tasks


def po_payload(**overrides):
    payload = {
        "backlog_item_id": "1",
        "supplier_name": "Acme Filters",
        "quantity": 350,
        "unit_cost": 12.5,
        "expected_delivery_date": "2026-12-01",
        "notes": "Rush",
    }
    payload.update(overrides)
    return payload


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_create_purchase_order(self, client):
        """Test creating a purchase order for a backlog item."""
        response = client.post("/api/purchase-orders", json=po_payload())
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == "1"
        assert po["status"] == "pending"
        assert po["expected_delivery_date"] == "2026-12-01"
        assert len(po["created_date"]) == 10

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching the purchase order that was created."""
        created = client.post("/api/purchase-orders", json=po_payload()).json()

        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_backlog_reports_purchase_order(self, client):
        """Test that /api/backlog flags the item after a PO is created."""
        client.post("/api/purchase-orders", json=po_payload())

        backlog = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert backlog["1"]["has_purchase_order"] is True
        assert backlog["2"]["has_purchase_order"] is False

    def test_create_duplicate_purchase_order(self, client):
        """Test that a second PO for the same backlog item is rejected."""
        client.post("/api/purchase-orders", json=po_payload())

        response = client.post("/api/purchase-orders", json=po_payload())
        assert response.status_code == 409
        assert "already has" in response.json()["detail"]

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test creating a PO for a backlog item that doesn't exist."""
        response = client.post("/api/purchase-orders", json=po_payload(backlog_item_id="999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize("field,value", [
        ("quantity", 0),
        ("unit_cost", -1),
        ("supplier_name", ""),
        ("expected_delivery_date", "not-a-date"),
    ])
    def test_create_purchase_order_invalid_input(self, client, field, value):
        """Test that invalid input is rejected with 422."""
        response = client.post("/api/purchase-orders", json=po_payload(**{field: value}))
        assert response.status_code == 422

    def test_get_nonexistent_purchase_order(self, client):
        """Test getting a PO for an item without one."""
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestTaskEndpoints:
    """Test suite for task endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that the task list starts empty."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task."""
        response = client.post("/api/tasks", json={"title": "Count stock", "priority": "high", "dueDate": "2026-11-10"})
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Count stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-11-10"
        assert task["status"] == "pending"
        assert client.get("/api/tasks").json() == [task]

    def test_new_tasks_come_first(self, client):
        """Test that the newest task is first in the list."""
        client.post("/api/tasks", json={"title": "First", "dueDate": "2026-11-10"})
        client.post("/api/tasks", json={"title": "Second", "dueDate": "2026-11-10"})

        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["Second", "First"]

    def test_toggle_task(self, client):
        """Test toggling a task to completed and back."""
        task = client.post("/api/tasks", json={"title": "Toggle me", "dueDate": "2026-11-10"}).json()

        assert client.patch(f"/api/tasks/{task['id']}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task['id']}").json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task."""
        task = client.post("/api/tasks", json={"title": "Delete me", "dueDate": "2026-11-10"}).json()

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 204
        assert client.get("/api/tasks").json() == []

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_nonexistent_task(self, client, method):
        """Test toggling or deleting a task that doesn't exist."""
        response = getattr(client, method)("/api/tasks/task-missing")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize("body", [
        {"title": "", "dueDate": "2026-11-10"},
        {"title": "x", "priority": "urgent", "dueDate": "2026-11-10"},
        {"title": "x"},
    ])
    def test_create_task_invalid_input(self, client, body):
        """Test that invalid task input is rejected with 422."""
        response = client.post("/api/tasks", json=body)
        assert response.status_code == 422
