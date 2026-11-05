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
| Tests | pytest + FastAPI TestClient | `tests/backend/` |

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

`views/Backlog.vue` exists but has no route.

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
| Overview | `/dashboard/summary`, `/orders`, `/inventory`, `/backlog` | all four |
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
| `/api/backlog` | | `BacklogItem[]` |
| `/api/dashboard/summary` | `warehouse`, `category`, `status`, `month` | Summary object |
| `/api/spending/summary` | | Spending totals |
| `/api/spending/monthly` | | 12 monthly cost records |
| `/api/spending/categories` | | Cost per category |
| `/api/spending/transactions` | | Transactions |
| `/api/reports/quarterly` | | Per-quarter metrics |
| `/api/reports/monthly-trends` | | Per-month metrics |

**Write endpoints.** Stored in memory only; a server restart clears them.

| Method | Path | Body | Response |
|---|---|---|---|
| `POST` | `/api/purchase-orders` | `backlog_item_id`, `supplier_name`, `quantity` (>0), `unit_cost` (>0), `expected_delivery_date` (YYYY-MM-DD), `notes?` | 201 `PurchaseOrder`; 404 unknown backlog item; 409 item already has a PO; 422 invalid input |
| `GET` | `/api/purchase-orders/{backlog_item_id}` | | `PurchaseOrder`, 404 if none |
| `GET` | `/api/tasks` | | `Task[]`, newest first |
| `POST` | `/api/tasks` | `title`, `priority` (`high`/`medium`/`low`, default `medium`), `dueDate` (YYYY-MM-DD) | 201 `Task` (`status: pending`) |
| `PATCH` | `/api/tasks/{id}` | | `Task` with `status` toggled between `pending` and `completed`; 404 if unknown |
| `DELETE` | `/api/tasks/{id}` | | 204; 404 if unknown |

**Filter rules.**
- `all` or a missing parameter means no filter.
- `month` accepts `YYYY-MM` (e.g. `2025-03`) or a quarter `Q1-2025` to `Q4-2025`.
- `category` and `status` match case-insensitively; `warehouse` must match exactly (`San Francisco`, `London`, `Tokyo`).

**Example.**

```bash
curl "http://localhost:8001/api/orders?warehouse=Tokyo&status=shipped"
```

## 6. Data model

Files in `server/data/`, loaded by `server/mock_data.py`. `server/generate_data.py` can regenerate them.

| File | Records | Model |
|---|---|---|
| `inventory.json` | 32 | `InventoryItem` |
| `orders.json` | 250 | `Order` |
| `demand_forecasts.json` | 9 | `DemandForecast` |
| `backlog_items.json` | 4 | `BacklogItem` |
| `transactions.json` | 56 | transaction dict |
| `spending.json` | summary, 12 months, 4 categories | dicts |
| `purchase_orders.json` | 0 (new POs are added in memory) | `PurchaseOrder` |

**InventoryItem:** `id`, `sku`, `name`, `category`, `warehouse`, `quantity_on_hand`, `reorder_point`, `unit_cost`, `location`, `last_updated`.

**Order:** `id`, `order_number`, `customer`, `items` (list of dicts), `status`, `order_date`, `expected_delivery`, `total_value`, optional `actual_delivery`, `warehouse`, `category`.

**DemandForecast:** `id`, `item_sku`, `item_name`, `current_demand`, `forecasted_demand`, `trend`, `period`.

**BacklogItem:** `id`, `order_id`, `item_sku`, `item_name`, `quantity_needed`, `quantity_available`, `days_delayed`, `priority`, `has_purchase_order`.

**PurchaseOrder:** `id` (`PO-XXXXXXXX`), `backlog_item_id`, `supplier_name`, `quantity`, `unit_cost`, `expected_delivery_date`, `status` (`pending`), `created_date`, `notes`.

**Task:** `id` (`task-xxxxxxxx`), `title`, `priority`, `dueDate`, `status` (`pending`/`completed`).

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

The frontend has no automated tests. Orders and reports endpoints have no tests. Browser checks are done by hand or with Playwright against `http://localhost:3000`.

## 9. Operations

| Task | How |
|---|---|
| Start / stop | Run or stop the two processes from section 2 |
| Health check | `curl http://localhost:8001/` and open http://localhost:3000 |
| Reset data | Restart the server; data is read-only and reloaded from JSON |
| Change data | Edit `server/data/*.json` or run `server/generate_data.py`, then restart |
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
