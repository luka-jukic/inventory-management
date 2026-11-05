# Technical Reference

[Documentation home](README.md) · [User Guide](user-guide.md) · [Known Issues](known-issues.md)

## Contents

1. [Architecture](#1-architecture)
2. [Requirements and setup](#2-requirements-and-setup)
3. [Configuration](#3-configuration)
4. [Frontend](#4-frontend)
5. [REST API](#5-rest-api)
6. [Data model](#6-data-model)
7. [Internationalisation](#7-internationalisation)
8. [Testing](#8-testing)
9. [Operations](#9-operations)
10. [Security notes](#10-security-notes)

---

## 1. Architecture

```
Browser (Vue 3 SPA, :3000)
   │  FilterBar state (useFilters, module singleton)
   │  api.js (axios)  ── query params: warehouse, category, status, month
   ▼
FastAPI (:8001)  server/main.py
   │  in-memory filtering, Pydantic validation
   ▼
server/mock_data.py  ── loads server/data/*.json once at start
```

| Layer | Technology | Location |
|---|---|---|
| UI | Vue 3 (Composition API), vue-router 4, plain CSS, custom SVG charts | `client/src/` |
| Build / dev server | Vite 8 | `client/vite.config.js` |
| HTTP client | axios | `client/src/api.js` |
| API | FastAPI, Pydantic 2, uvicorn | `server/main.py` |
| Data | JSON files, in memory | `server/data/` |
| Tests | pytest + FastAPI TestClient; Vitest + Vue Test Utils + jsdom | `tests/backend/`, `client/tests/` |

**Data flow.** A filter change updates the shared filter state. Each page watches it, calls `api.js`, and the server filters the in-memory lists and returns JSON. Pages keep raw data in `ref`s and derive totals in `computed` properties.

There is no database and no authentication. Tasks and purchase orders can be created, but they live in memory; restarting the server resets everything.

## 2. Requirements and setup

| Tool | Version |
|---|---|
| Python | 3.11 or later |
| uv | current |
| Node.js | 20.19+ or 22.12+ (`client/package.json` `engines`) |

```bash
# Backend
cd server
uv run python main.py          # http://localhost:8001, docs at /docs

# Frontend
cd client
npm install
npm run dev                    # http://localhost:3000
npm run build                  # production build into client/dist
```

`client/.npmrc` pins the public npm registry and `client/package-lock.json` is not tracked. Keep both as they are; the repository is public.

## 3. Configuration

| Setting | Value | Where |
|---|---|---|
| API base URL | `http://localhost:8001/api` | `client/src/api.js:3` |
| API port | 8001 | `server/main.py` (uvicorn run) |
| Dev server port | 3000 | `client/vite.config.js` |
| CORS | all origins, credentials allowed | `server/main.py:50-56` |

The API base URL is hardcoded. To deploy elsewhere, change `api.js` (and the direct URLs in `Reports.vue`, see [Known Issues](known-issues.md)).

**Browser storage.**

| Key | Values | Purpose |
|---|---|---|
| `app-locale` | `en`, `ja` | Chosen language |
| `sidebarCollapsed` | `true`, `false` | Sidebar state; written only when the user clicks the toggle |

## 4. Frontend

### Routes (`client/src/main.js`)

| Path | View | Nav key |
|---|---|---|
| `/` | `views/Dashboard.vue` | `nav.overview` |
| `/inventory` | `views/Inventory.vue` | `nav.inventory` |
| `/orders` | `views/Orders.vue` | `nav.orders` |
| `/spending` | `views/Spending.vue` | `nav.finance` |
| `/demand` | `views/Demand.vue` | `nav.demandForecast` |
| `/reports` | `views/Reports.vue` | `nav.reports` |

`views/Backlog.vue` is routed at `/backlog`.

### Shell (`client/src/App.vue`)

- CSS grid: `var(--sidebar-w) minmax(0, 1fr)`. `minmax(0, …)` lets wide tables scroll inside their card.
- Sidebar: 240px, or 68px when collapsed. Collapsed styles only apply from 768px up.
- Below 768px the sidebar is an off-canvas drawer (`position: fixed`, `inert` while closed). It closes on backdrop click, Escape and route change.
- Nav items come from one `navItems` array (`{ to, labelKey, icon }`) with inline SVG icons.
- Global styles and design tokens live on `:root` in `App.vue`: `--bg`, `--surface`, `--border`, `--text`, `--text-muted`, `--accent`, status colours, `--space-1` to `--space-7`, radii, shadows, `--topbar-h: 60px`, `--content-max: 1440px`.

**Stacking order.**

| Layer | z-index |
|---|---|
| Filter bar (sticky) | 90 |
| Top bar (sticky) | 100 |
| Phone backdrop | 140 |
| Phone drawer | 150 |
| Modals | 1000 / 2000 |

### Components

| Component | Role |
|---|---|
| `FilterBar.vue` | Four selects + reset; sticky under the top bar |
| `LanguageSwitcher.vue` | en / ja dropdown |
| `ProfileMenu.vue` | Profile dropdown, task count badge |
| `ProfileDetailsModal.vue` | Mock user profile |
| `TasksModal.vue` | Add, toggle, delete tasks |
| `PurchaseOrderModal.vue` | Create a purchase order for a shortage, or view the existing one |
| `InventoryDetailModal.vue`, `ProductDetailModal.vue`, `BacklogDetailModal.vue`, `CostDetailModal.vue` | Read-only detail dialogs |

### Composables

| File | Purpose |
|---|---|
| `useFilters.js` | Shared filter state; converts it to API query params (`month` for the period) |
| `useI18n.js` | `t()`, locale switch, currency formatting, name translation |
| `useAuth.js` | Mock current user and mock tasks |

### Page data sources

| Page | API calls | Filters used |
|---|---|---|
| Overview | `/dashboard/summary`, `/dashboard/top-products`, `/backlog` | all four |
| Inventory | `/inventory` | warehouse, category |
| Orders | `/orders` | all four |
| Finance | `/spending/summary`, `/spending/monthly`, `/spending/categories`, `/spending/transactions`, `/orders` | period (client-side) |
| Demand Forecast | `/demand`, `/inventory` | warehouse, category |
| Reports | `/reports/quarterly`, `/reports/monthly-trends` | none |

## 5. REST API

Base URL `http://localhost:8001`. Interactive docs: `http://localhost:8001/docs` (FastAPI default). All endpoints return JSON. Errors return `{"detail": "..."}`.

| Path | Query params | Response |
|---|---|---|
| `/` | | `{"message": "Factory Inventory Management System API", "version": "1.0.0"}` |
| `/api/inventory` | `warehouse`, `category` | `InventoryItem[]` |
| `/api/inventory/{item_id}` | | `InventoryItem`, 404 if unknown |
| `/api/orders` | `warehouse`, `category`, `status`, `month` | `Order[]` |
| `/api/orders/{order_id}` | | `Order`, 404 if unknown |
| `/api/demand` | | `DemandForecast[]` |
| `/api/backlog` | `warehouse`, `category`, `status`, `month` (matched on the linked order) | `BacklogItem[]`, computed from Backordered orders whose line needs more than the stock on hand; longest delayed first |
| `/api/dashboard/top-products` | `warehouse`, `category`, `status`, `month`, `limit` (1-50, default 12) | `TopProduct[]`: products in the filtered orders, earliest first order first, then by revenue |
| `/api/dashboard/summary` | `warehouse`, `category`, `status`, `month` | `DashboardSummary`: inventory value, low stock, pending orders, backlog count, KPIs (`orders_fulfilled`, `order_fill_rate`, `avg_processing_days`, `inventory_turnover`, `on_time_rate`), order totals (`total_orders`, `total_orders_value`, `avg_order_value`), `revenue_goal` (800K per month in the period), `status_counts`, `inventory_value_by_category` |
| `/api/spending/summary` | `month` | `SpendingSummary`: totals summed from the monthly rows of the period, plus year-over-year change percentages |
| `/api/spending/monthly` | | `MonthlySpending[]`, 12 monthly cost records |
| `/api/spending/categories` | | `CategorySpending[]`; `percentage` is computed from the amounts and sums to 100 |
| `/api/spending/transactions` | `month` | `Transaction[]` |
| `/api/reports/quarterly` | `warehouse`, `category`, `status`, `month` | `QuarterlyReport[]` |
| `/api/reports/monthly-trends` | `warehouse`, `category`, `status`, `month` | `MonthlyTrend[]` (months with orders only) |

**Write endpoints.** Stored in memory only; a server restart clears them.

| Method | Path | Body | Response |
|---|---|---|---|
| `POST` | `/api/purchase-orders` | `backlog_item_id`, `supplier_name`, `quantity` (>0), `unit_cost` (>0), `expected_delivery_date` (YYYY-MM-DD), `notes?` | 201 `PurchaseOrder`; 404 unknown backlog item; 409 item already has a PO; 422 invalid input |
| `GET` | `/api/purchase-orders/{backlog_item_id}` | | `PurchaseOrder`, 404 if none |
| `GET` | `/api/tasks` | | `Task[]`, newest first |
| `POST` | `/api/tasks` | `title`, `priority` (`high`/`medium`/`low`, default `medium`), `due_date` (YYYY-MM-DD) | 201 `Task` (`status: pending`) |
| `PATCH` | `/api/tasks/{id}` | | `Task` with `status` toggled between `pending` and `completed`; 404 if unknown |
| `DELETE` | `/api/tasks/{id}` | | 204; 404 if unknown |

**Filter rules.**
- `all` or a missing parameter means no filter.
- `month` accepts `YYYY-MM` (e.g. `2025-03`) or a quarter `Q1-2025` to `Q4-2025`.
- All filters match case-insensitively. Allowed values: warehouse `San Francisco`, `London`, `Tokyo`; category `Circuit Boards`, `Sensors`, `Actuators`, `Controllers`, `Power Supplies`; status `Delivered`, `Shipped`, `Processing`, `Backordered`.
- An unknown value returns 422 with the allowed values in `detail`, instead of an empty result.

**Example.**

```bash
curl "http://localhost:8001/api/orders?warehouse=Tokyo&status=shipped"
```

## 6. Data model

Files in `server/data/`, loaded by `server/mock_data.py`. The data is a snapshot as of 2025-12-31.

- `orders.json` and `demand_forecasts.json` are generated from `inventory.json` by `server/generate_data.py` (fixed seed, so the output is reproducible). Orders ship from the warehouse that stocks their items, all lines share the order's category, prices are cost plus 25-60%, statuses follow the dates, and only orders with a line larger than the stock on hand are Backordered.
- The backlog is not stored: the API computes it from Backordered orders and stock.
- Stock status (`low_stock` at or below the reorder point, `adequate` up to 1.5x, `in_stock` above) is defined once in the API.
- `tests/backend/test_data_integrity.py` checks all these rules, so hand edits that break them fail the tests.

Warehouse, category and order status are fixed lists (`Literal` types in `server/main.py`), shared by the data models and the filters.

| File | Records | Model |
|---|---|---|
| `inventory.json` | 32 | `InventoryItem` |
| `orders.json` | 250 | `Order` |
| `demand_forecasts.json` | 9 | `DemandForecast` |
| `transactions.json` | 56 | `Transaction` |
| `spending.json` | change percentages, 12 months, 4 categories | `MonthlySpending`, `CategorySpending` (totals and percentages are computed, not stored) |
| `purchase_orders.json` | 0 (new POs are added in memory) | `PurchaseOrder` |

**InventoryItem:** `id`, `sku`, `name`, `category`, `warehouse`, `quantity_on_hand`, `reorder_point`, `unit_cost`, `location`, `last_updated`; the API adds `stock_status`.

**Order:** `id`, `order_number`, `customer`, `items` (`OrderLine[]`: `sku`, `name`, `quantity`, `unit_price`), `status`, `order_date`, `expected_delivery`, `total_value`, `actual_delivery` (set exactly when `status` is `Delivered`), `warehouse`, `category`.

**DemandForecast:** `id`, `item_sku`, `item_name`, `current_demand`, `forecasted_demand`, `trend`, `period`.

**BacklogItem** (computed): `id` (`BL-<order number>-<sku>`), `order_number`, `item_sku`, `item_name`, `quantity_needed` (the order line), `quantity_available` (stock on hand), `days_delayed` (since expected delivery, at the snapshot date), `priority` (`high` > 60 days, `medium` > 14, else `low`), `has_purchase_order`.

**PurchaseOrder:** `id` (`PO-XXXXXXXX`), `backlog_item_id`, `supplier_name`, `quantity`, `unit_cost`, `expected_delivery_date`, `status` (`pending`), `created_date`, `notes`.

**Task:** `id` (`task-xxxxxxxx`), `title`, `priority`, `due_date`, `status` (`pending`/`completed`).

When you change the JSON structure, update the Pydantic model in `server/main.py` too, or responses fail validation.

## 7. Internationalisation

- Locales: `client/src/locales/en.js`, `client/src/locales/ja.js`.
- Use `const { t } = useI18n()` and `t('section.key')` in components. Every new string needs a key in both files.
- Missing keys fall back to English, then to the key itself.
- Currency follows the locale: `en` shows USD, `ja` shows JPY.
- Product, customer and warehouse names have their own translation helpers in `useI18n.js`.

## 8. Testing

```bash
cd server
uv run --dev pytest ../tests/backend -c ../tests/pytest.ini -v                    # 60 tests
uv run --dev pytest ../tests/backend -c ../tests/pytest.ini --cov=.               # with coverage
```

The test dependencies live in `server/pyproject.toml`, so run pytest from `server/`. `cd tests && uv run pytest` fails with "Failed to spawn: pytest".

| File | Covers |
|---|---|
| `tests/backend/test_inventory.py` | Inventory list, filters, single item |
| `tests/backend/test_dashboard.py` | Dashboard summary and filters |
| `tests/backend/test_misc_endpoints.py` | Demand, backlog, spending, root |
| `tests/backend/test_tasks_and_purchase_orders.py` | Tasks and purchase orders: create, read, toggle, delete, 404/409/422 |
| `tests/backend/test_data_integrity.py` | Every JSON row validates; unique IDs; references resolve; totals equal line sums; orders ship from the warehouse holding the stock and have one category; prices above cost; statuses fit the dates; Backordered exactly when stock is short; cost of goods fits procurement plus stock; forecasts match recent orders |
| `tests/backend/test_api_contract.py` | 422 on unknown filter values, case-insensitive filters, summary/spending/report numbers agree, one stock status definition, top products and backlog match the orders |
| `tests/backend/test_openapi_snapshot.py` | The published OpenAPI schema equals `openapi.snapshot.json`; regenerate with `UPDATE_OPENAPI_SNAPSHOT=1` when a change is intended |

Frontend tests run with Vitest in jsdom (config in `client/vite.config.js`):

```bash
cd client
npm test              # run once
npm run test:watch    # re-run on change
```

| File | Covers |
|---|---|
| `client/tests/api.test.js` | Filter params skip `all`, inventory sends only warehouse/category, abort signal, `X-API-Token`, `isCanceled` |
| `client/tests/BaseModal.test.js` | Dialog role and label, focus in, Escape, overlay click, Tab trap, focus return |
| `client/tests/Backlog.test.js` | Loads with filters, reloads on all four filters, aborts stale and unmounted requests, error display |
| `client/tests/useFilters.test.js` | Period to `month` mapping, shared state, reset |
| `client/tests/locales.test.js` | English and Japanese have the same keys and no empty strings |

Visual checks and full flows are done by hand or with Playwright against `http://localhost:3000`.

## 9. Operations

| Task | How |
|---|---|
| Start / stop | Run or stop the two processes from section 2 |
| Health check | `curl http://localhost:8001/` and open http://localhost:3000 |
| Reset data | Restart the server; data is read-only and reloaded from JSON |
| Change data | Edit `inventory.json`/`spending.json`/`transactions.json`, or change and run `server/generate_data.py` for orders and forecasts; run the tests, then restart |
| Logs | uvicorn writes to the console; there is no log file |
| Backups | Nothing to back up except the JSON files in git |

**Troubleshooting.**

| Symptom | Cause | Fix |
|---|---|---|
| Pages show no data | API not running on 8001 | Start the backend |
| `npm install` pulls from a private registry | Local npm config overrides | Keep `client/.npmrc` |
| Response validation error | JSON changed without the Pydantic model | Update the model in `server/main.py` |
| `.getMonth()` errors | Invalid date in data | Check dates before use |

## 10. Security notes

- No authentication or authorization. Anyone who reaches the ports sees all data. The API binds to `0.0.0.0` (`server/main.py:309`), so it is reachable from the local network. Do not expose it outside a trusted network.
- CORS allows every origin with credentials. Restrict `allow_origins` before any real deployment.
- The repository is public. Never commit credentials, internal hostnames or private registry URLs.
