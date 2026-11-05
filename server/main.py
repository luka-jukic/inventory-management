import os
import re
from datetime import date, datetime
from uuid import uuid4
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import threading
from typing import List, Literal, Optional, get_args
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Fixed vocabularies shared by data, filters and response models
Warehouse = Literal["San Francisco", "London", "Tokyo"]
Category = Literal["Circuit Boards", "Sensors", "Actuators", "Controllers", "Power Supplies"]
OrderStatus = Literal["Delivered", "Shipped", "Processing", "Backordered"]
WAREHOUSES, CATEGORIES, ORDER_STATUSES = get_args(Warehouse), get_args(Category), get_args(OrderStatus)

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}
MONTH_PATTERN = r"^(2025-(0[1-9]|1[0-2])|Q[1-4]-2025)$"
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
REVENUE_GOAL_PER_MONTH = 800_000
DATA_AS_OF = datetime(2025, 12, 31, 23, 59, 59)  # snapshot date of the mock data


class Filters(BaseModel):
    """Validated global filters; None means 'all'. Values are canonical (data spelling)."""
    warehouse: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    month: Optional[str] = None


def canonical(value: Optional[str], allowed: tuple, name: str) -> Optional[str]:
    """Map a case-insensitive filter value to its canonical spelling; 422 if unknown."""
    if value is None or value.lower() == 'all':
        return None
    match = next((a for a in allowed if a.lower() == value.lower()), None)
    if match is None:
        raise HTTPException(status_code=422, detail=f"Invalid {name} '{value}'. Allowed: all, {', '.join(allowed)}")
    return match


def canonical_month(month: Optional[str] = None) -> Optional[str]:
    """Validate a month (YYYY-MM) or quarter (Q1-2025) filter, any case; None = all."""
    if month is None or month.lower() == 'all':
        return None
    if not re.fullmatch(MONTH_PATTERN, month.upper()):
        raise HTTPException(status_code=422, detail=f"Invalid month '{month}'. Use YYYY-MM (2025) or Q1-2025 to Q4-2025")
    return month.upper()


def get_filters(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = Depends(canonical_month),
) -> Filters:
    return Filters(
        warehouse=canonical(warehouse, WAREHOUSES, "warehouse"),
        category=canonical(category, CATEGORIES, "category"),
        status=canonical(status, ORDER_STATUSES, "status"),
        month=month,
    )


def months_of(month: Optional[str]) -> Optional[set]:
    """YYYY-MM months covered by a validated month filter; None = all."""
    if not month:
        return None
    return set(QUARTER_MAP[month]) if month.startswith('Q') else {month}


def filter_by_month(items: list, month: Optional[str], date_field: str = 'order_date') -> list:
    """Filter items by month or quarter on a date field"""
    months = months_of(month)
    if months is None:
        return items
    return [item for item in items if item.get(date_field, '')[:7] in months]


def apply_filters(items: list, f: Filters, with_status: bool = True) -> list:
    """Apply validated warehouse/category(/status) filters (values are already canonical)"""
    return [
        item for item in items
        if (not f.warehouse or item.get('warehouse') == f.warehouse)
        and (not f.category or item.get('category') == f.category)
        and (not with_status or not f.status or item.get('status') == f.status)
    ]


def filtered_orders(f: Filters) -> list:
    return filter_by_month(apply_filters(orders, f), f.month)


def round_or_none(value: Optional[float], digits: int = 1) -> Optional[float]:
    return None if value is None else round(value, digits)

# CORS: only the Vite dev server by default. Override with a comma-separated CORS_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-API-Token"],
)

# ponytail: single shared token, off unless API_TOKEN is set; real per-user auth before any deployment
API_TOKEN = os.getenv("API_TOKEN")

def require_token(x_api_token: Optional[str] = Header(default=None)):
    if API_TOKEN and x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")

MAX_TASKS = 1000

# Data models
StockStatus = Literal["low_stock", "adequate", "in_stock"]


def stock_status(item: dict) -> str:
    """One definition of stock status for every view: at/below reorder point, up to 1.5x, above"""
    if item["quantity_on_hand"] <= item["reorder_point"]:
        return "low_stock"
    if item["quantity_on_hand"] <= item["reorder_point"] * 1.5:
        return "adequate"
    return "in_stock"


def with_stock_status(item: dict) -> dict:
    return {**item, "stock_status": stock_status(item)}


class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: Category
    warehouse: Warehouse
    quantity_on_hand: int = Field(ge=0)
    reorder_point: int = Field(ge=0)
    unit_cost: float = Field(gt=0)
    location: str
    last_updated: datetime
    stock_status: StockStatus

class OrderLine(BaseModel):
    sku: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[OrderLine] = Field(min_length=1)
    status: OrderStatus
    order_date: datetime
    expected_delivery: datetime
    total_value: float = Field(ge=0)
    actual_delivery: Optional[datetime] = None
    warehouse: Warehouse
    category: Category

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int = Field(ge=0)
    forecasted_demand: int = Field(ge=0)
    trend: Literal["increasing", "stable", "decreasing"]
    period: str

class BacklogItem(BaseModel):
    id: str
    order_number: str
    item_sku: str
    item_name: str
    quantity_needed: int = Field(gt=0)
    quantity_available: int = Field(ge=0)
    unit_cost: float = Field(gt=0)
    days_delayed: int = Field(ge=0)
    priority: Literal["high", "medium", "low"]
    has_purchase_order: bool = False

class CategoryValue(BaseModel):
    category: Category
    value: float
    count: int

class StatusCounts(BaseModel):
    delivered: int
    shipped: int
    processing: int
    backordered: int

class DashboardSummary(BaseModel):
    total_inventory_value: float
    low_stock_items: int
    pending_orders: int
    total_backlog_items: int
    orders_fulfilled: int
    order_fill_rate: Optional[float]
    avg_processing_days: Optional[float]
    inventory_turnover: Optional[float]
    total_orders: int
    total_orders_value: float
    avg_order_value: float
    on_time_rate: Optional[float]
    revenue_goal: float
    status_counts: StatusCounts
    inventory_value_by_category: List[CategoryValue]

class SpendingSummary(BaseModel):
    total_procurement_cost: float
    total_operational_cost: float
    total_labor_cost: float
    total_overhead: float
    procurement_change: float
    operational_change: float
    labor_change: float
    overhead_change: float

class MonthlySpending(BaseModel):
    month: Literal['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    procurement: float = Field(ge=0)
    operational: float = Field(ge=0)
    labor: float = Field(ge=0)
    overhead: float = Field(ge=0)

class CategorySpending(BaseModel):
    category: str
    amount: float = Field(ge=0)
    percentage: float
    change: float

class Transaction(BaseModel):
    id: str
    date: date
    description: str
    category: str
    warehouse: Warehouse
    amount: float = Field(gt=0)
    vendor: str
    type: Literal["Purchase", "Operational", "Overhead"]

class QuarterlyReport(BaseModel):
    quarter: str
    total_orders: int
    total_revenue: float
    delivered_orders: int
    avg_order_value: float
    fulfillment_rate: float

class MonthlyTrend(BaseModel):
    month: str
    order_count: int
    revenue: float
    delivered_count: int

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: date
    status: Literal["pending"]
    created_date: date
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0)
    expected_delivery_date: date
    notes: Optional[str] = Field(default=None, max_length=1000)

class Task(BaseModel):
    id: str
    title: str
    priority: Literal["high", "medium", "low"]
    due_date: date
    status: Literal["pending", "completed"]

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: Literal["high", "medium", "low"] = "medium"
    due_date: date

# ponytail: in-memory store like the rest of the mock data; lost on restart
tasks: List[dict] = []
# ponytail: one global lock; per-item locks only if write volume ever matters
purchase_order_lock = threading.Lock()
task_lock = threading.Lock()

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(f: Filters = Depends(get_filters)):
    """Get all inventory items, filtered by warehouse and category (no time dimension)"""
    return [with_stock_status(i) for i in apply_filters(inventory_items, f, with_status=False)]

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return with_stock_status(item)

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    f: Filters = Depends(get_filters),
    limit: Optional[int] = Query(default=None, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """Get orders with optional filtering; limit/offset paginate (default: all)"""
    return filtered_orders(f)[offset:offset + limit if limit else None]

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

def backlog_priority(days_delayed: int) -> str:
    if days_delayed > 60:
        return "high"
    if days_delayed > 14:
        return "medium"
    return "low"


def compute_backlog(order_list: list) -> list:
    """Backlog = lines of Backordered orders that need more than the stock on hand.

    Computed, not stored, so it always matches the orders and the inventory.
    ponytail: each order is compared with the full stock on hand (no allocation
    across orders), so two backlog rows for one SKU both show all stock as
    available; allocate in order_date order if that ever matters.
    """
    stock = {item["sku"]: item for item in inventory_items}
    po_items = {po["backlog_item_id"] for po in purchase_orders}
    backlog = []
    for order in order_list:
        if order["status"] != "Backordered":
            continue
        days_delayed = max(0, (DATA_AS_OF - datetime.fromisoformat(order["expected_delivery"])).days)
        for line in order["items"]:
            available = stock[line["sku"]]["quantity_on_hand"]
            if line["quantity"] <= available:
                continue
            item_id = f"BL-{order['order_number'][4:]}-{line['sku']}"
            backlog.append({
                "id": item_id,
                "order_number": order["order_number"],
                "item_sku": line["sku"],
                "item_name": stock[line["sku"]]["name"],
                "quantity_needed": line["quantity"],
                "quantity_available": available,
                "unit_cost": stock[line["sku"]]["unit_cost"],
                "days_delayed": days_delayed,
                "priority": backlog_priority(days_delayed),
                "has_purchase_order": item_id in po_items,
            })
    return sorted(backlog, key=lambda b: (-b["days_delayed"], b["id"]))


def filter_backlog(f: Filters) -> list:
    """Backlog items whose order matches the filters"""
    return compute_backlog(filtered_orders(f))

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog(f: Filters = Depends(get_filters)):
    """Backlog items (longest delayed first) with purchase order status, filtered by their order"""
    return filter_backlog(f)

@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(f: Filters = Depends(get_filters)):
    """Get summary statistics for dashboard with optional filtering"""
    inventory = apply_filters(inventory_items, f, with_status=False)
    order_list = filtered_orders(f)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in inventory)
    delivered = [o for o in order_list if o["status"] == "Delivered"]
    status_counts = {s.lower(): sum(1 for o in order_list if o["status"] == s) for s in ORDER_STATUSES}
    total_orders_value = sum(o["total_value"] for o in order_list)

    processing_days = [
        round((datetime.fromisoformat(o["actual_delivery"]) - datetime.fromisoformat(o["order_date"])).total_seconds() / 86400)
        for o in delivered
    ]
    on_time = sum(1 for o in delivered if o["actual_delivery"] <= o["expected_delivery"])

    # Turnover = cost of delivered goods / current inventory value
    unit_cost = {item["sku"]: item["unit_cost"] for item in inventory_items}
    cost_of_goods_sold = sum(i["quantity"] * unit_cost.get(i["sku"], 0) for o in delivered for i in o["items"])

    # Inventory value per category; with a period selected, only SKUs ordered in that period
    ordered_skus = {i["sku"] for o in order_list for i in o["items"]} if f.month else None
    by_category = {}
    for item in inventory:
        if ordered_skus is not None and item["sku"] not in ordered_skus:
            continue
        entry = by_category.setdefault(item["category"], {"category": item["category"], "value": 0.0, "count": 0})
        entry["value"] += item["quantity_on_hand"] * item["unit_cost"]
        entry["count"] += 1

    months = months_of(f.month)
    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": sum(1 for item in inventory if stock_status(item) == "low_stock"),
        "pending_orders": status_counts["processing"] + status_counts["backordered"],
        "total_backlog_items": len(filter_backlog(f)),
        "orders_fulfilled": len(delivered),
        "order_fill_rate": round_or_none(100 * (1 - status_counts["backordered"] / len(order_list)) if order_list else None),
        "avg_processing_days": round_or_none(sum(processing_days) / len(processing_days) if processing_days else None),
        "inventory_turnover": round_or_none(cost_of_goods_sold / total_inventory_value if total_inventory_value else None),
        "total_orders": len(order_list),
        "total_orders_value": round(total_orders_value, 2),
        "avg_order_value": round(total_orders_value / len(order_list), 2) if order_list else 0.0,
        "on_time_rate": round_or_none(100 * on_time / len(delivered) if delivered else None),
        "revenue_goal": REVENUE_GOAL_PER_MONTH * (len(months) if months else 12),
        "status_counts": status_counts,
        "inventory_value_by_category": sorted(by_category.values(), key=lambda c: -c["value"]),
    }

class TopProduct(BaseModel):
    sku: str
    name: str
    category: Category
    warehouse: Warehouse
    units_ordered: int
    revenue: float
    quantity_on_hand: int
    reorder_point: int
    stock_status: StockStatus
    first_order_date: datetime

@app.get("/api/dashboard/top-products", response_model=List[TopProduct])
def get_top_products(f: Filters = Depends(get_filters), limit: int = Query(default=12, ge=1, le=50)):
    """Products ordered in the filtered orders: earliest first order first, then by revenue"""
    stock = {item["sku"]: item for item in inventory_items}
    products = {}
    for order in filtered_orders(f):
        for line in order["items"]:
            item = stock[line["sku"]]
            p = products.setdefault(line["sku"], {
                "sku": item["sku"], "name": item["name"], "category": item["category"],
                "warehouse": item["warehouse"], "units_ordered": 0, "revenue": 0.0,
                "quantity_on_hand": item["quantity_on_hand"], "reorder_point": item["reorder_point"],
                "stock_status": stock_status(item), "first_order_date": order["order_date"],
            })
            p["units_ordered"] += line["quantity"]
            p["revenue"] += line["quantity"] * line["unit_price"]
            p["first_order_date"] = min(p["first_order_date"], order["order_date"])
    ranked = sorted(products.values(), key=lambda p: (p["first_order_date"], -p["revenue"]))
    return [{**p, "revenue": round(p["revenue"], 2)} for p in ranked[:limit]]

def spending_months(month: Optional[str]) -> list:
    """Monthly spending rows covered by the month filter"""
    months = months_of(month)
    if months is None:
        return monthly_spending
    names = {MONTH_NAMES[int(m[5:7]) - 1] for m in months}
    return [row for row in monthly_spending if row["month"] in names]

@app.get("/api/spending/summary", response_model=SpendingSummary)
def get_spending_summary(month: Optional[str] = Depends(canonical_month)):
    """Spending totals derived from the monthly rows (optionally one month or quarter)"""
    rows = spending_months(month)
    return {
        "total_procurement_cost": sum(r["procurement"] for r in rows),
        "total_operational_cost": sum(r["operational"] for r in rows),
        "total_labor_cost": sum(r["labor"] for r in rows),
        "total_overhead": sum(r["overhead"] for r in rows),
        **spending_summary,  # year-over-year change percentages
    }

@app.get("/api/spending/monthly", response_model=List[MonthlySpending])
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories", response_model=List[CategorySpending])
def get_category_spending():
    """Procurement spend by category; percentage = share of procurement, derived from the amounts"""
    total = sum(c["amount"] for c in category_spending)
    return [{**c, "percentage": round(100 * c["amount"] / total, 1) if total else 0.0} for c in category_spending]

@app.get("/api/spending/transactions", response_model=List[Transaction])
def get_recent_transactions(month: Optional[str] = Depends(canonical_month)):
    """Get recent transactions, optionally for one month or quarter"""
    return filter_by_month(recent_transactions, month, date_field='date')

@app.get("/api/reports/quarterly", response_model=List[QuarterlyReport])
def get_quarterly_reports(f: Filters = Depends(get_filters)):
    """Get quarterly performance reports, honoring the global filters"""
    month_to_quarter = {m: q for q, ms in QUARTER_MAP.items() for m in ms}
    quarters = {}
    for order in filtered_orders(f):
        quarter = month_to_quarter.get(order["order_date"][:7])
        if quarter is None:  # outside the 2025 quarters
            continue
        q = quarters.setdefault(quarter, {"quarter": quarter, "total_orders": 0, "total_revenue": 0.0, "delivered_orders": 0})
        q["total_orders"] += 1
        q["total_revenue"] += order["total_value"]
        q["delivered_orders"] += order["status"] == "Delivered"

    return [
        {
            **q,
            "total_revenue": round(q["total_revenue"], 2),
            "avg_order_value": round(q["total_revenue"] / q["total_orders"], 2),
            "fulfillment_rate": round(100 * q["delivered_orders"] / q["total_orders"], 1),
        }
        for q in sorted(quarters.values(), key=lambda q: q["quarter"])
    ]

@app.get("/api/reports/monthly-trends", response_model=List[MonthlyTrend])
def get_monthly_trends(f: Filters = Depends(get_filters)):
    """Get month-over-month trends, honoring the global filters"""
    months = {}
    for order in filtered_orders(f):
        key = order["order_date"][:7]
        m = months.setdefault(key, {"month": key, "order_count": 0, "revenue": 0.0, "delivered_count": 0})
        m["order_count"] += 1
        m["revenue"] += order["total_value"]
        m["delivered_count"] += order["status"] == "Delivered"
    return [{**m, "revenue": round(m["revenue"], 2)} for m in sorted(months.values(), key=lambda m: m["month"])]

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201, dependencies=[Depends(require_token)])
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (one per item)"""
    if not any(item["id"] == request.backlog_item_id for item in compute_backlog(orders)):
        raise HTTPException(status_code=404, detail="Backlog item not found")
    po = request.model_dump()
    po.update(
        id=f"PO-{uuid4().hex[:8].upper()}",
        expected_delivery_date=request.expected_delivery_date.isoformat(),
        status="pending",
        created_date=date.today().isoformat(),
    )
    # Sync endpoints run in a threadpool: check and append atomically
    with purchase_order_lock:
        if any(existing["backlog_item_id"] == request.backlog_item_id for existing in purchase_orders):
            raise HTTPException(status_code=409, detail="Backlog item already has a purchase order")
        purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order of a backlog item"""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

def find_task(task_id: str) -> dict:
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all tasks, newest first"""
    with task_lock:
        return [dict(t) for t in tasks]

@app.post("/api/tasks", response_model=Task, status_code=201, dependencies=[Depends(require_token)])
def create_task(request: CreateTaskRequest):
    """Create a task"""
    task = {
        "id": f"task-{uuid4().hex[:8]}",
        "title": request.title,
        "priority": request.priority,
        "due_date": request.due_date.isoformat(),
        "status": "pending",
    }
    with task_lock:
        if len(tasks) >= MAX_TASKS:
            raise HTTPException(status_code=409, detail="Task limit reached")
        tasks.insert(0, task)
    return task

@app.delete("/api/tasks/{task_id}", status_code=204, dependencies=[Depends(require_token)])
def delete_task(task_id: str):
    """Delete a task"""
    with task_lock:
        tasks.remove(find_task(task_id))

@app.patch("/api/tasks/{task_id}", response_model=Task, dependencies=[Depends(require_token)])
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    with task_lock:
        task = find_task(task_id)
        task["status"] = "completed" if task["status"] == "pending" else "pending"
        return dict(task)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=8001)
