# Known Issues and Limitations

[Documentation home](README.md) · [User Guide](user-guide.md) · [Technical Reference](technical-reference.md)

Found while writing this documentation (2026-11-05). File references point to the code at that date.

## Fixed

| Issue | Fix |
|---|---|
| `/api/tasks` returned 404, new tasks were lost | GET/POST/PATCH/DELETE `/api/tasks` added (in memory) |
| "Create PO" did nothing; `PurchaseOrderModal` did not exist | Component added; `POST /api/purchase-orders` and `GET /api/purchase-orders/{backlog_item_id}` added |
| Button checked `purchase_order_id`, API sends `has_purchase_order` | Dashboard uses `has_purchase_order`, so "View PO" shows after reload |
| CORS allowed all origins with credentials; API listened on all interfaces | CORS limited to `CORS_ORIGINS` (default `localhost:3000`), server binds `127.0.0.1` |
| Write endpoints had no protection | Optional shared `API_TOKEN` / `X-API-Token` header |
| Dialogs had no dialog role, no Escape (6 of 7), no focus handling | Shared `BaseModal.vue` used by all dialogs |
| Clickable table rows could not be reached by keyboard | Rows are focusable and open with Enter or Space |
| Fast filter changes could show data from an older request | Views cancel the previous request |
| Detail dialogs, filter and task tooltips were English only | Translated |
| Finance transaction details used a browser alert | Shown in a dialog |
| Overview and Finance scrolled sideways at phone width | Grids collapse to one column below 768px |
| Four of five Overview KPIs were fixed numbers | Turnover, Orders Fulfilled, Fill Rate and Processing Time come from the filtered data (`/api/dashboard/summary`). Goals are unchanged, so turnover and processing time now show far off goal with the mock data |
| Backlog items pointed to orders and SKUs that did not exist, so the backlog count ignored filters | `backlog_items.json` links each item to a real Backordered order; `/api/backlog` and the summary count follow all filters |
| `Backlog.vue` had no route | Route `/backlog` and a sidebar entry |
| Inventory search matched the item name only | Search matches name, SKU and location |
| Reports page was English only and called `localhost:8001` directly | Translated, goes through `api.js` and follows the filters |
| Reports scrolled sideways at phone width | Chart scrolls inside its card |
| In Japanese, the smallest "Inventory Value by Category" bar cut off its label | Bars are at least as wide as their label |

## Functional gaps

| # | Issue | Effect | Where |
|---|---|---|---|
| 5 | Logout only shows a browser alert | No real sign-out (there is no login) | `client/src/composables/useAuth.js:94-98` |

## Configuration

- The API token is a single shared value, not per-user authentication. Do not deploy without real auth.

## Testing

- No frontend tests.
- `/api/reports/*` has one filter test; `/api/orders` only has pagination and quarter filter tests.
- Tasks and purchase orders are kept in memory only; a server restart clears them.
