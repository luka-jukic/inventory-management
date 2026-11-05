---
name: frontend-design
description: Redesign a Vue 3 app's UI into a modern light SaaS-style interface - left vertical sidebar nav (icons, collapsible to icons-only, mobile drawer), CSS design tokens, consistent spacing, polished cards/tables/badges. Use when asked to redesign, modernize, or give a SaaS look to the Vue frontend, move top nav to a sidebar, or add a collapsible sidebar.
---

# Frontend Design: SaaS Redesign for Vue 3

Turns a top-nav Vue 3 app into a light, professional SaaS layout. Changes the **shell, design tokens and global styles**. Views inherit the look through the global classes.

## Rules

- Follow the repo's delegation rules. In this repo, every `.vue` create or edit goes through the **vue-expert** subagent. Hand it this file's path plus the concrete spec. Tell it to keep the existing component style (for example `export default { setup() }`, do not convert to `<script setup>`) and leave unrelated logic untouched.
- No new dependencies. No icon library, no UI kit, no CSS framework. Inline SVG icons, plain CSS.
- No emojis in UI. If the app has i18n (`t()`), every new string, including aria-labels and tooltips, gets a key in every locale file. Reuse existing keys.
- Keep all existing routes, filters, modals and component behavior. Visual change only.
- Views: delete scoped rules that only restate the look of a global class (`.card`, `.stat-card`, `.badge`, `.page-header`, ...) so the global polish reaches every view. Keep scoped rules that do layout work for that view. No other view rewrites.
- Public repos: do not touch `.npmrc` or lockfiles, and do not commit credentials or registry URLs.

## Step 1: Read before changing

The paths below are this repo's defaults. In another app, find the root component, router, locales and global stylesheet first.

1. `client/src/App.vue`: shell markup and global (unscoped) styles: `.card`, `.stat-card`, `table`, `.badge`, `.page-header`, `.main-content`.
2. `client/src/main.js`: the route list, so every route gets a nav item. Note whether routes have a `name`; often they do not.
3. Components that move into the shell (here: `FilterBar.vue`, `ProfileMenu.vue`, `LanguageSwitcher.vue`): note their z-index, their sticky offsets, and labels that are too wide for mobile.
4. Grep the views and components for:
   - `position: sticky`, `top:`, `max-width`, `100vw`, `z-index`: anything tied to the old top nav or the stacking order.
   - **Scoped redefinitions of global classes**, for example `grep -nE '^\s*\.(card|card-header|card-title|stats-grid|stat-card|stat-label|stat-value|badge|page-header)\b' views/*.vue`. List them in the plan with "delete" or "keep (layout)".
   - Status colour usage, so the tokens can map to the existing values.

## Step 2: Design tokens

Define them on `:root` in the global style. Replace the hardcoded values in the global styles with tokens. **Map the status tokens to the colours the app already uses.** Do not change their meaning. Text on a tint needs a contrast of at least 4.5:1.

```css
:root {
  /* surface */
  --bg: #f8fafc;
  --surface: #ffffff;
  --border: #e2e8f0;
  /* text */
  --text: #0f172a;
  --text-muted: #64748b;
  /* accent */
  --accent: #2563eb;
  --accent-soft: #eff6ff;
  /* status: use the app's existing values, these are examples */
  --success: #059669; --warning: #ea580c; --danger: #dc2626; --info: #2563eb;
  /* spacing scale: use only these */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px;
  /* shape */
  --radius-sm: 6px; --radius: 10px; --radius-lg: 14px;
  --shadow-sm: 0 1px 2px rgb(15 23 42 / 0.05);
  --shadow: 0 1px 3px rgb(15 23 42 / 0.08), 0 1px 2px rgb(15 23 42 / 0.04);
  /* layout */
  --sidebar-w: 240px;
  --sidebar-w-collapsed: 68px;
  --topbar-h: 60px;
  --content-max: 1440px;
}
```

Font: keep the existing stack (or the system stack). `font-size: 14px` goes on `body`, **not `html`**, because views use rem. Headings use weight 600. Stat values use `font-variant-numeric: tabular-nums`.

## Step 3: Shell layout

```
+-----------+--------------------------------------+
| Logo      | Topbar: [hamburger]    Lang | Profile|
|-----------+--------------------------------------+
| Nav items | FilterBar                            |
| (icon +   |--------------------------------------|
|  label)   | main content (max --content-max)     |
|           |                                      |
| collapse  |                                      |
+-----------+--------------------------------------+
```

- Root: CSS Grid `grid-template-columns: var(--sidebar-w) minmax(0, 1fr)`. Use `minmax(0, 1fr)`, not `1fr`, or wide tables widen the page and `overflow-x: auto` containers never scroll. Collapsed: `var(--sidebar-w-collapsed) minmax(0, 1fr)`, with `transition: grid-template-columns 0.2s`. No `overflow: hidden` on the content column, because it breaks sticky.
- Sidebar: `position: sticky; top: 0; height: 100vh`, white surface, right border. Logo at the top, then the nav list, then the collapse toggle pinned at the bottom.
- Nav item: icon (20px) + label, `padding: var(--space-2) var(--space-3)`, `border-radius: var(--radius-sm)`. Hover uses `--bg`. Active: style `.router-link-active` with an `--accent-soft` background, `--accent` text and a 3px left accent bar. Vue Router 4 has **no `exact` prop**. With flat (non-nested) routes, `/` is only active on `/`. With nested routes, use `.router-link-exact-active` for the root link.
- Topbar: `position: sticky; top: 0; height: var(--topbar-h); z-index: 100`. Hamburger on the left (mobile only), language and profile on the right. **No page title if the views already render their own heading.** If you add one, take it from the nav item that matches `route.path`, because routes may have no `name`.
- The filter bar (if any) sits under the topbar in the content column, `top: var(--topbar-h)`, `max-width: var(--content-max)`.
- `.main-content`: `max-width: var(--content-max)`, padding `var(--space-6)`.

### z-index stack (write it down, do not guess)

| Layer | z-index |
|---|---|
| Filter bar (sticky) | 90 |
| Topbar (sticky; its dropdowns at 1000 live inside its stacking context) | 100 |
| Mobile backdrop | 140 |
| Mobile drawer | 150 |
| Modals | unchanged (above 1000) |

The topbar must be above the filter bar. Otherwise its dropdowns open behind the filters.

## Step 4: Icons

Inline SVG, 20x20, `viewBox="0 0 24 24"`, `stroke="currentColor"`, `fill="none"`, `stroke-width="1.75"`, round caps and joins. Keep the paths in one `navItems` array (`{ to, labelKey, icon }`) in the root component, `v-for` keyed by `to`. Suggested shapes: overview = grid of 4 squares, inventory = box, orders = clipboard, finance = dollar, demand = trending-up line, reports = bar chart, collapse = chevron.

Icons get `aria-hidden="true"`. The label text stays in the DOM.

## Step 5: Collapsible (icons-only, desktop only)

- `collapsed` ref. localStorage key `sidebarCollapsed`, with every access in try/catch.
- Read order: stored value if set, else `matchMedia('(min-width: 768px) and (max-width: 1024px)').matches`. Write the value **only in the toggle handler**, never on init, or the default never applies again.
- **Every collapsed style sits inside `@media (min-width: 768px)`**, so a stored `true` never shrinks the mobile drawer.
- Collapsed: labels are visually hidden (a clip-based visually-hidden class, not `display: none`), the logo text is hidden while a logo mark stays, icons are centered, and each link gets `:title` set to the translated label.
- Toggle button: translated `aria-label` (collapse or expand) and `aria-expanded`.
- Nav links and the toggle get a visible `:focus-visible` ring.

## Step 6: Mobile drawer (< 768px)

- The grid becomes a single column. The sidebar is `position: fixed`, off-canvas with `transform: translateX(-100%)`, and slides in when `mobileOpen` is true.
- A closed drawer is removed from the tab order with `:inert="isMobile && !mobileOpen"` (or `visibility: hidden` transitioned with the transform).
- The hamburger is visible only below 768px. It gets a translated `aria-label`, `:aria-expanded="mobileOpen"` and `aria-controls="sidebar"`.
- The backdrop (`aria-hidden="true"`) closes the drawer on click.
- On a route change, close the drawer with `const route = useRoute(); watch(() => route.path, () => { mobileOpen.value = false })`. Note: `watch(route.path)` is a bug, because it passes a string and never fires.
- Escape closes the drawer. Add the keydown listener in `onMounted` and remove it in `onUnmounted`.
- `isMobile` comes from `matchMedia('(max-width: 767px)')` with a change listener. When it turns false, set `mobileOpen = false`. Remove the listener on unmount.
- The collapse toggle is hidden on mobile, where the drawer is always full width with labels.
- Topbar fit at 375px: hide wide labels (profile name, language label) below 768px. The filter row wraps (`flex-wrap: wrap`). The page has no horizontal scroll.
- Optional: move focus into the drawer on open and back to the hamburger on close, and lock body scroll while it is open.

## Step 7: Component polish (global styles)

- `.card`: `--surface`, `1px solid var(--border)`, `--radius`, `--shadow-sm`, padding `--space-5`. No heavy hover lift; only a subtle shadow change.
- `.stat-card`: same base as `.card`. Label in `--text-muted`, 12px, uppercase, letter-spaced. Value 28px, weight 600, tabular-nums. Keep the status colour variants (`.warning`, `.success`, `.danger`, `.info`).
- `table`: no outer border inside cards. `th` 12px uppercase `--text-muted` on `--bg`. Rows separated by `--border`, row hover `--bg`, cell padding `--space-3 --space-4`.
- `.badge`: pill shape (`border-radius: 999px`), 12px, weight 500. **Keep the existing text and background pair of every variant**. List them all (in this repo: success, warning, danger, info, increasing, decreasing, stable, high, medium, low).
- Buttons and inputs (if styled globally): height 36px, `--radius-sm`, focus ring `0 0 0 3px var(--accent-soft)` plus an `--accent` border.
- `.page-header`: title 24px weight 600, subtitle `--text-muted`, margin-bottom `--space-5`.

## Step 8: Verify

1. `npm run build` in the client must pass. It is only a compile check.
2. Browser: use the browser tool the project prescribes (here, Playwright MCP at `http://localhost:3000`). If it is down, retry it. If it is still down, do not switch tools without asking. Give the user the checklist below and report the result as "not browser-verified".
3. Checklist:
   - 1440px: active nav correct on every route; topbar dropdowns open over the filter bar.
   - 900px, after clearing `sidebarCollapsed`: starts collapsed, tooltips work, the toggle works and the state survives reload.
   - 375px: drawer is full width with labels. Backdrop, Escape and a nav click each close it. With the drawer closed, Tab skips the sidebar. Filters are usable and there is no horizontal scroll.
   - A wide table scrolls inside its card.
   - Every view's cards and headers look the same.
   - Filters still change data, modals open above the sidebar and drawer, and a language switch updates every label, including aria labels.
   - No new console errors.
4. Run frontend tests only if the project has them.
