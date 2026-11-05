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
| Ten orders shared IDs and order numbers with other orders (201-210) | Renumbered to the missing 116-125; integrity test checks uniqueness |
| 8 of 9 demand forecasts and all backlog items used SKUs not in inventory | Forecasts point at real inventory SKUs; integrity test checks every reference |
| 8 Delivered orders had no delivery date; 2 were delivered after the end of the data | Dates added; the two late ones are Shipped. The generator no longer skips Nov/Dec delivery dates |
| Spending totals did not match the monthly rows (labor off by 879K); category percentages summed to 123.6% | Totals and percentages are computed by the API |
| Transactions used warehouses A/B/C | Use the same warehouse names as the rest of the data |
| An unknown filter value returned an empty list; warehouse matching was case-sensitive | 422 with the allowed values; all filters ignore case |
| Order lines, spending, summary and report responses were untyped | Pydantic response models for every endpoint; `OrderLine` model |
| Two purchase orders for the same backlog item could be created at the same moment | Check and insert run under a lock |
| Spending categories summed to 8.7M while procurement was 7.4M | Categories are a breakdown of procurement and sum to it; label says "of procurement" |
| Finance filtered months in the browser with `toISOString()`, so in UTC+ time zones the 1st of a month fell into the previous month | The API filters by month |
| Inventory, Orders, Finance and three dialogs showed ¥ in front of unconverted USD amounts | All amounts go through `utils/currency.js` |
| Backlog dialog showed an "Expected Date" the API never sends | Row removed |
| 210 of 250 orders shipped items from a warehouse that does not stock them; 38 orders listed the same SKU twice | Orders are generated from the inventory: one warehouse and one category per order, distinct lines |
| Most Shipped/Processing orders were months overdue; 18 of 22 Backordered orders had no backlog item and 7 had all items in stock | Statuses follow the dates; Backordered means a line exceeds stock; the backlog is computed from those orders (25 items) |
| Backlog `days_delayed` (1-5) and quantities were stored copies that had drifted (real delay up to 354 days) | Computed at request time; priority follows the delay |
| Cost of goods was $26.9M against $7.4M procurement; 41% of lines sold below cost | Prices are cost plus 25-60%; quantities fit procurement plus stock (stock tripled so turnover is about 3.5) |
| Springs and a pulley were filed under Sensors | Moved to Actuators |
| Stock status had three definitions (server, Inventory, Overview) | One `stock_status` from the API |
| Overview computed top products from every order in the browser | `/api/dashboard/top-products` |
| Task due dates showed a day early west of UTC | Parsed as local dates |
| Concurrent task changes could fail with 500 | Task changes run under a lock |

## Functional gaps

| # | Issue | Effect | Where |
|---|---|---|---|
| 5 | Logout only shows a browser alert | No real sign-out (there is no login) | `client/src/composables/useAuth.js:94-98` |

## Configuration

- The API token is a single shared value, not per-user authentication. Do not deploy without real auth.

## Testing

- Frontend tests cover the API client, `BaseModal`, the Backlog view, filters and locales; the other views have none.
- Tasks and purchase orders are kept in memory only; a server restart clears them.
- Spending categories (Raw Materials, Components, ...) are cost types, not the product categories, so the category filter does not apply to Finance.
- Transactions only cover September 2025.
- Money is stored as floating point; fine for a demo, use integer cents or `Decimal` for real accounting.
- Customers and suppliers are free-text names, not entities.
