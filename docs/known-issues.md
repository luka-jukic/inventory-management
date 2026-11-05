# Known Issues and Limitations

[Documentation home](README.md) · [User Guide](user-guide.md) · [Technical Reference](technical-reference.md)

Found while writing this documentation (2026-11-05). File references point to the code at that date.

## Fixed

| Issue | Fix |
|---|---|
| `/api/tasks` returned 404, new tasks were lost | GET/POST/PATCH/DELETE `/api/tasks` added (in memory) |
| "Create PO" did nothing; `PurchaseOrderModal` did not exist | Component added; `POST /api/purchase-orders` and `GET /api/purchase-orders/{backlog_item_id}` added |
| Button checked `purchase_order_id`, API sends `has_purchase_order` | Dashboard uses `has_purchase_order`, so "View PO" shows after reload |

## Functional gaps

| # | Issue | Effect | Where |
|---|---|---|---|
| 5 | Logout only shows a browser alert | No real sign-out (there is no login) | `client/src/composables/useAuth.js:94-98` |
| 6 | Four of five Overview KPIs are fixed numbers | Turnover, Orders Fulfilled, Fill Rate and Processing Time do not react to filters | `client/src/views/Dashboard.vue` |
| 7 | `total_backlog_items` in the dashboard summary ignores filters | Count stays the same for every filter | `server/main.py:200` |
| 8 | `Backlog.vue` has no route | Page is unreachable | `client/src/main.js` |
| 9 | Inventory search matches the item name only | Searching by SKU finds nothing | `client/src/views/Inventory.vue:132-150` |

## Translation gaps

These stay in English when Japanese is selected:

- The whole Reports page, which also always shows `$` (`client/src/views/Reports.vue`).
- The four detail dialogs, including "{month} Cost Breakdown".
- Tooltips "Reset all filters" (`FilterBar.vue:62`) and "Delete task".
- The Finance transaction alert and chart tooltips.

## Configuration

- `Reports.vue:156,162` calls `http://localhost:8001` directly with axios instead of going through `api.js`. Changing the API URL in one place is not enough.
- CORS allows all origins with credentials (`server/main.py:50-56`).

## Layout

- At phone width (390px), the Overview, Finance and Reports pages scroll sideways because of fixed-width grids, chart legends and a Reports table without a scroll wrapper. Inventory and Orders fit (`images/12-mobile.png`).
- In Japanese, the smallest bar in "Inventory Value by Category" is too short for its yen label, so the label is cut off (`images/10-japanese.png`).

## Testing

- No frontend tests.
- No backend tests for `/api/orders` or `/api/reports/*`.
- Tasks and purchase orders are kept in memory only; a server restart clears them.
