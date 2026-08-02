# PrimeNG → Angular Material Migration Plan

> Repository: `wg-ui-plus` (WireGuard UI Plus)
> Scope: `src/clientapp/` (Angular 21 SPA) only. Backend (Django REST API) is untouched.
> Status: **Approved design — pending implementation go-ahead**

---

## 1. Goals

- Replace **every** PrimeNG control, directive, service and type with Angular Material equivalents.
- Fully de-commission `primeng`, `@primeuix/themes`, `primeicons` from `package.json` — no PrimeNG code remains.
- Preserve the current **always-dark** UI, all routes and all CRUD workflows.
- Zero changes to the backend REST API or the webapi entity shapes.

**Design philosophy — Material-native, not a PrimeNG port.** The SPA must behave as if it were written for Angular Material/CDK from day one. We do **not** port, mimic or otherwise carry over PrimeNG visual or behavioural constraints. Where Material conventions differ (colours, severity semantics, toast placement/stacking, table styling, form layout, menu rendering), **Material wins** — such changes are intended outcomes, not regressions. PrimeNG-era scaffolding (e.g. the `.editor-table` form grid, `p-datatable-*` style classes, inert PrimeFlex utility classes) is discarded, not preserved.

## 2. Confirmed design decisions

| Area | Decision |
|---|---|
| Design philosophy | **Native Material throughout** — no PrimeNG parity/mimicry; UX changes that conform to Material conventions are intended |
| Pick-list (`p-pickList` ×4) | New reusable `app-dual-list` built on `@angular/cdk/drag-drop`: drag & drop **+** middle move buttons (`>`, `>>`, `<`, `<<`), ctrl/cmd+click multi-select, **fixed order** (both panes sorted by `name`) |
| Org chart (`p-organizationChart` ×1) | New custom `app-org-chart` component (recursive HTML/CSS/flexbox) |
| Toasts (`p-toast` + `MessageService` ×6) | New `NotificationService` over `MatSnackBar` with a Material-native API (`show()`/`success()`/`error()`/`clear()`), FIFO queue, duration-based dismissal |
| Confirm dialogs (`p-confirmdialog` + `ConfirmationService`) | `ConfirmationDialogService` rewritten on `MatDialog` (standard Material alert dialog: title, message, text buttons) |
| Button colours | Material conventions: affirmative → `color="primary"`; destructive → `color="warn"`; neutral → uncoloured text/stroked button. PrimeNG `severity` semantics dropped |
| Theme | Custom Material dark theme under `.my-app-dark` (always-dark, as today) |
| Tables (`p-table` ×4) | Native `<table>` markup + `matSort` / `mat-sort-header`, styled per Material table density — `p-datatable-*` classes dropped |
| Editor forms | PrimeNG-era `.editor-table` scaffolding replaced with a native Material form layout (full-width `mat-form-field`s, floating labels) |
| Dialogs (`p-dialog` ×1) | **Dead code** — `useDialogForEditor` is hardcoded `false`; branch + `p-dialog` + flag are removed |
| Scope | Full de-commission: remove `primeng`, `@primeuix/themes`, `primeicons` |

## 3. Current PrimeNG inventory (baseline)

### Components (from templates)
| Component | Count | Locations |
|---|---|---|
| `p-button` (+ `pButton` directive) | 23 | all screens |
| `p-card` | 7 | login, about, monitors, crud-container, server-config |
| `p-toast` | 6 | app-root, 3 editors, server-config, testpage |
| `p-checkbox` | 5 | 3 editors, server-config |
| `p-table` | 4 | peers/peer-groups/targets lists, connected-peers monitor |
| `p-pickList` | 4 | peers editor, peer-groups editor (×2), targets editor |
| `p-password` | 4 | login, change-password tab (×3) |
| `p-tabs` (tablist/tab/tabpanels/tabpanel) | 2 groups | about, server-config |
| `p-confirmdialog` | 4 | app-root, 3 editors |
| `p-inputText` directive | ~15 | all editors, login, server-config |
| `p-inputNumber` | 2 | server-config ports |
| `p-message` | 1 (+1 commented) | app-root warning bar |
| `p-panel` | 1 | app-root header |
| `p-organizationChart` | 1 | VPN layout |
| `p-menu` | 1 | sidepanel nav |
| `p-dialog` | 1 | crud-container (dead) |

### Directives
`pInputText`, `pTooltip` (`tooltipPosition="top"`), `pButton`, `[autofocus]` (AutoFocusModule).

### Services / types (`primeng/api`)
`MessageService`, `ConfirmationService`, `MenuItem`, `TreeNode`, `ToastMessageOptions`.

### Icons (primeicons)
`pi-ban`, `pi-check`, `pi-times`, `pi-tag`, `pi-plus-circle`, `pi-file-edit`, `pi-refresh`, `pi-mail`, `pi-ellipsis-v` + sidepanel nav icons (`pi-eye`, `pi-th-large`, `pi-wrench`, `pi-question`, `pi-sign-in`, `pi-sign-out`, `pi-sitemap`, `pi-desktop`, `pi-bullseye`).

### Dead code found during analysis (removal candidates)
- `useDialogForEditor` flag + `p-dialog` branch in `crud-container` — never `true`.
- Unused PrimeNG module imports in `app-shared.module.ts`: `CascadeSelectModule`, `DataViewModule`, `DividerModule`, `DragDropModule`, `ImageModule`, `ListboxModule`.
- `p-message` in `validation-errors-display` template (commented out).
- `MessageService` provided but never used in: `home`, `testpage`, `server-monitor-peers`, `server-monitor-iptables`, `manage-peers`, `manage-peer-groups`, `manage-targets`.
- Inert PrimeFlex utility classes (`flex`, `p-2`, `flex-1`, `gap-3`, `align-items-center`, …) — **no PrimeFlex package is installed**, these are dead today.

---

## 4. Breaking-change & risk analysis

### 4.1 Event & API semantic differences

| # | PrimeNG | Angular Material | Risk / mitigation |
|---|---|---|---|
| 1 | `(onClick)` / `(onShow)` etc. | `(click)` | All 23 `p-button` bindings must rename. Silent break if missed → build-time template check + grep gate. |
| 2 | `severity="success/warn/danger"` | Material color conventions: affirmative → `color="primary"`, destructive → `color="warn"`, neutral → uncoloured text/stroked button | PrimeNG's amber-`warn` / red-`danger` split is **dropped**. One Material `warn` (red) for destructive actions; success is signalled via snackbar/icon, not button colour. Intended change. |
| 3 | `pTooltip` + `tooltipPosition="top"` | `matTooltip` + `matTooltipPosition="above"` | `matTooltip` on a disabled host element does not fire → wrap or use `matTooltipDisabled`. |
| 4 | `[autofocus]` (AutoFocusModule) | native `autofocus` / `cdkFocusInitial` | Native `autofocus` attribute works on `matInput`. |
| 5 | `p-inputNumber` (`min`, `max`, `required`, `allowEmpty=false`) | `matInput type="number"` + Angular `[min]`/`[max]`/`required` validators | PrimeNG blocked empty/invalid values at the input level; native number inputs allow clearing and typing out-of-range. Angular's `min`/`max` validator directives **do** work with template-driven `ngModel`. Server-side validation remains the source of truth, but the UX softens. **Minor behavioural change — accept, note in smoke test.** |
| 6 | `p-password` with `[feedback]="false"` | `matInput type="password"` (optional visibility toggle via `matSuffix`) | No strength meter today, none needed. |

### 4.2 Toast system (p-toast → MatSnackBar)

Target is **native `MatSnackBar` behaviour** — bottom position, single visible message with a FIFO queue, duration-based auto-dismiss. PrimeNG's top-right stacked overlay is intentionally not reproduced.

| # | Concern | Detail / mitigation |
|---|---|---|
| 1 | **Position** | `MatSnackBar` shows at the bottom (default). Intended change. |
| 2 | **Stacking** | Snackbar shows one message at a time. `NotificationService` keeps a small **FIFO queue** so multi-message flows (e.g. "config generated" → "restarted") play sequentially. |
| 3 | **10-second polling** | `app.component` refreshes server status every `PeriodicRefreshUiService` tick (**every 10 s**). `NotificationService.clear()` + `show()` must be "replace current" semantics (no queue buildup) to avoid flicker. |
| 4 | **Per-component scoping** | Today each editor has its own `MessageService` + own `<p-toast>`. After migration one root-provided `NotificationService` + global snackbar serves all; component-level `MessageService` providers are removed. |
| 5 | **Dismissal** | Snackbar auto-dismisses (~3–4 s); an optional dismiss/action button per message. `closable: false` is not reproduced. |

### 4.3 Confirmation dialogs (p-confirmdialog → MatDialog)

Standard Material alert dialog (title, message, text action buttons in a right-aligned action row).

| # | Concern | Detail / mitigation |
|---|---|---|
| 1 | API | `ConfirmationDialogService.confirm()` / `showMessage()` keep the app-owned `(title, message): Observable<boolean>` shape (this is our abstraction, not a PrimeNG constraint) — call sites (3 editors, app.component) stay unchanged. |
| 2 | Modal & dismiss | `MatDialog` is modal; Esc / backdrop click resolve `false` (reject) via `afterClosed()` — standard Material behaviour. |
| 3 | Latent bug fixed | Current implementation reuses one shared `Subject` across all confirm calls (old subscriptions never complete). Rewriting on `MatDialog` gives each call its own `afterClosed()` — strictly better. |
| 4 | New component | `ConfirmDialogComponent` (title, message, Cancel/OK text buttons) — new file. |

### 4.4 Navigation menu (p-menu → mat-nav-list / mat-menu)

| # | Concern | Detail / mitigation |
|---|---|---|
| 1 | Desktop sidebar | PrimeNG static menu panel → `mat-nav-list` (+ `mat-list-item` with `routerLink`). **Visual change by design**; groups (`expanded: true`) → subheaders, `separator` → `mat-divider`. |
| 2 | Mobile popup | `p-menu [popup]` + `menu.toggle($event)` → `mat-menu` + `menuTrigger.openMenu()`. Popup **flattens** group headers/separators (mat-menu has no subheaders) → flatter item list with dividers. |
| 3 | `replaceUrl: true` | Log in/Log out items use `routerLink`; `[replaceUrl]="true"` on the `routerLink` input (or `navigate()` in `command`). |
| 4 | `MenuItem` type | Replace `primeng/api` `MenuItem` with a local `NavMenuItem` interface (`label`, `route?`, `url?`, `icon`, `tooltip`, `command?`, `separator?`, `items?`). |

### 4.5 Tables (p-table → native + matSort)

| # | Concern | Detail / mitigation |
|---|---|---|
| 1 | Default sort | `sortField="name"` / `sortField="peer_name"` → `matSortActive` + `matSortDirection` on `<table matSort>` to preserve initial ordering. |
| 2 | Row identity | `dataKey="id"` → `trackBy` on `ngFor`. |
| 3 | PrimeNG styleClass | `p-datatable-striped p-datatable-gridlines p-datatable-sm` are **dropped**. Use Material table conventions: default/compact density, subtle striping optional. Must render correctly on the dark theme. |
| 4 | Header templates | Current `<ng-template pTemplate="header">` with `<th colspan>` + New-button row → plain `<thead>`; keep exact columns/cells. |
| 5 | Mobile overflow | 7-column monitor table will overflow on small screens → wrap tables in `overflow-x: auto` (same as today's outer scroll behaviour). |
| 6 | Number pipe | `transfer_rx \| number` — Angular built-in, unchanged. |

### 4.6 Forms layout (Material-native; PrimeNG-era editor scaffolding discarded)

| # | Concern | Detail / mitigation |
|---|---|---|
| 1 | **Editor scaffolding** | The `.editor-table` grid (external `<label>` cell + input cell) is **replaced** with a native Material form layout: one full-width `mat-form-field` per field with floating `mat-label`, checkboxes on their own rows, action buttons in a right-aligned row. Same for the peer-editor side column (QR / download / email). |
| 2 | **Width CSS conflict** | `styles.scss` rule `td:nth-child(2) input { width: 100% }` and the `.editor-table` rules are **removed**; `mat-form-field { width: 100% }` applies globally. |
| 3 | Checkbox layout | `p-checkbox [binary]="true"` → `mat-checkbox` with `[(ngModel)]` (boolean); `variant="filled"` is dropped (Material checkbox styling). |
| 4 | Password fields | `p-password` → `mat-form-field` + `matInput type="password"` (optional visibility toggle via `matSuffix`). |
| 5 | Server validation errors | `app-validation-errors-display` restyled Material-native (warn-coloured text, error icon). Field-level `mat-error` is not used because server errors don't map to Angular control validity; the existing display component is kept and restyled. |

### 4.7 Dependency / build risks

| # | Concern | Detail / mitigation |
|---|---|---|
| 1 | **Version alignment** | Add `@angular/material@^21.2.13` to match installed `@angular/cdk@^21.2.13`. npm will warn on mismatch — pin to the same `21.2.x`. |
| 2 | **DragDropModule name collision** | Currently `DragDropModule` comes from `primeng/dragdrop` (unused). New import from `@angular/cdk/drag-drop`. After de-commission there is no collision. |
| 3 | **Material Icons font = external Google Fonts link** | `index.html` loads `fonts.googleapis.com/icon?family=Material+Icons`. This app is **self-hosted in Docker** — an offline/air-gapped deployment loses all icons (tofu glyphs). **Mitigation: self-host the icons** by adding the `material-icons` npm package and importing `material-icons/iconfont/material-icons.css` in `styles.scss`, then remove the Google Fonts `<link>`. |
| 4 | **Bundle budgets** | `angular.json`: `initial` 2 MB warn / 4 MB error; `anyComponentStyle` 2 KB warn / 4 KB error. Material tree-shakes well, but the new `dual-list`/`org-chart` component styles must stay small. Watch the initial-bundle warning. |
| 5 | `package-lock.json` | Regenerated by `npm install`; Docker `builder` stage re-runs install. Commit the lockfile together with `package.json` changes. |
| 6 | Leftover PrimeNG refs | Any missed `primeng`/`pi-`/`p-`/`p-*` reference fails the build. Add a **grep gate** (`primeng`, `primeicons`, `@primeuix`, `pi pi-`, `<p-`) after migration. |

### 4.8 TypeScript / strict-mode risks (`strict`, `strictTemplates`)

| # | Item | Detail |
|---|---|---|
| 1 | `TreeNode` (primeng/api) | → local `OrgChartNode` interface (fields: `label`, `type`, `expanded`, `data {disabled, ip_address, details}`, `children`). `webapi.service.getTargetHeirarchy()` retyped; mapping code unchanged. |
| 2 | `MenuItem` (primeng/api) | → local `NavMenuItem` (see 4.4). |
| 3 | `ToastMessageOptions` (primeng/api) | → local message type in `notification.service.ts` (Material-native API: `show()`, `success()`, `error()`, `clear()`, queue). |
| 4 | Provider/DI churn | Remove `MessageService` / `ConfirmationService` providers from **~10 components**; inject `NotificationService` in `app.component`, `manage-server-configuration`, `manage-peers-editor` (email success). Missing providers = runtime DI error → compiler (`strictInjectionParameters`) catches most. |
| 5 | Generic `app-dual-list` | Must be strict-safe: `@ContentChild(TemplateRef)` typing, `transferArrayItem<T>`, `CdkDragDrop<T[]>`. |
| 6 | MatDialog results | `afterClosed().subscribe(result => …)` — result typed `any`/`boolean`; cast explicitly. |

### 4.9 Material-native behaviours to confirm in smoke test (intended changes, not regressions)

- **Button colours**: primary actions `color="primary"`, destructive `color="warn"`, neutral uncoloured — confirm the resulting hierarchy reads well on the dark theme.
- **Snackbar**: bottom position, single-at-a-time queue, server-status replace semantics (no flicker over the 10 s poll).
- **Dark theme**: tables, form fields, snackbar, dialog, checkbox render correctly on the custom dark theme.
- **Sidebar nav**: `mat-nav-list` look; grouping (subheaders/dividers) still reads well; active route indicated via `routerLinkActive`.
- **Editor forms**: new `mat-form-field` layout — labels float, fields full width, error display warn-coloured.
- **Org chart**: root `VPN` node must still show; disabled-node `mat-icon block` + tooltips per node type.
- **Peer editor side column**: QR image, "Download .conf", "Send Config By Email" — layout must survive the restructure.
- **Fixed-order pick-lists**: saved `peer_ids` / `target_ids` / `peer_group_ids` arrays become name-sorted. These are M2M relations (sets) so backend semantics are unaffected — **confirm** that saving + reload round-trips correctly.
- **Small screens**: popup menu, table overflow, dual-list stacking (CSS media query replaces `breakpoint="900px"`).
- **About page**: acknowledgements text updated from PrimeNG → Angular Material.
- **Icons**: mapping in §4.10 checked on-screen.

### 4.10 Icon mapping (`pi-*` → Material icon names)

| PrimeIcons | `mat-icon` |
|---|---|
| `pi-ban` | `block` |
| `pi-check` | `check` |
| `pi-times` | `close` |
| `pi-tag` | `sell` |
| `pi-plus-circle` | `add_circle` |
| `pi-file-edit` | `edit` |
| `pi-refresh` | `refresh` |
| `pi-mail` | `mail` |
| `pi-ellipsis-v` | `more_vert` |
| `pi-eye` | `visibility` |
| `pi-th-large` | `grid_view` |
| `pi-wrench` | `build` |
| `pi-question` | `help` |
| `pi-sign-in` | `login` |
| `pi-sign-out` | `logout` |
| `pi-sitemap` | `account_tree` |
| `pi-desktop` | `desktop_windows` |
| `pi-bullseye` | `track_changes` |

### 4.11 Mitigation summary

1. Keep `app-shared.module.ts` as the single import hub (PrimeNG → Material modules) → minimal churn in component `.ts` files.
2. `NotificationService` (Material-native API) + rewritten `ConfirmationDialogService` keep call-site churn small while the app is written Material-first.
3. Self-host Material Icons (npm package) instead of the Google Fonts link.
4. Remove dead code (dialog branch, unused modules/providers, inert flex classes, `.editor-table` scaffolding) as part of the migration.
5. Grep gates + full-route smoke test in the dev container.

---

## 5. Implementation plan (phases)

### Phase 1 — Dependencies & theme
1. `package.json`: add `@angular/material@^21.2.13` (exact match to `@angular/cdk`); remove `primeng`, `@primeuix/themes`, `primeicons`. Add `material-icons` for self-hosted icon fonts.
2. `src/styles.scss`: remove `@import "primeicons/primeicons.css"`; add `@use '@angular/material' as mat;` + `mat.core()` + dark `mat.theme(...)` under `.my-app-dark`; import the self-hosted icon font. **Remove** the `.editor-table` scaffolding and the `td:nth-child(2) input { width: 100% }` rule; add `mat-form-field { width: 100% }` and Material table density/striping styles.
3. `src/app/app.config.ts`: remove `providePrimeNG` + Aura import.
4. `src/index.html`: remove the Google Fonts Material Icons `<link>` (icons self-hosted via npm); keep Roboto + `mat-typography` + `my-app-dark`.

### Phase 2 — Infrastructure & shared components (new files)
1. `src/app/notification.service.ts` — Material-native snackbar service (`show()`, `success()`, `error()`, `clear()`, FIFO queue, replace-current semantics).
2. `src/app/confirm-dialog/confirm-dialog.component.ts|html|scss` — standard Material alert dialog.
3. `src/app/confirmation-dialog-service.ts` — rewrite on `MatDialog` (keeps `Observable<boolean>` API for existing call sites).
4. `src/app/dual-list/dual-list.component.ts|html|scss` — `app-dual-list` (CDK drag-drop + move buttons + fixed order).
5. `src/app/org-chart/org-chart.component.ts|html|scss` — `app-org-chart` (recursive tree).
6. `src/app/app-shared.module.ts` — swap `primeng/*` → Material modules (+ `CdkDragDrop`); drop `ConfirmationService`/`MessageService` providers; remove dead imports.
7. Types: add `OrgChartNode` (+ `NavMenuItem`) interfaces; retype `webapi.service.ts`.

### Phase 3 — Component migration (templates + TS)
Per the mapping table in §4.1–4.6:
1. `app.component.html|ts`
2. `app-sidepanel/app-sidepanel.component.html|ts`
3. `login/login.component.html`
4. `crud-container/crud-container.component.html|ts` (remove dead dialog)
5. `manage-peers-list`, `manage-peer-groups-list`, `manage-targets-list` (`*.html`)
6. `manage-peers-editor`, `manage-peer-groups-editor`, `manage-targets-editor` (`*.html|ts`)
7. `server-monitor-peers`, `server-monitor-iptables` (`*.html|ts`)
8. `server-vpn-layout/server-vpn-layout.component.html|ts`
9. `manage-server-configuration/manage-server-configuration.component.html|ts`
10. `app-about/app-about.component.html` (+ acknowledgements text)
11. `validation-errors-display/validation-errors-display.component.html|ts`
12. `testpage/testpage.component.html|ts`
13. Wrappers `manage-peers` / `manage-peer-groups` / `manage-targets` (`*.ts` — drop unused providers).

### Phase 4 — CSS & polish
- Discard inert PrimeFlex utility classes (they never had any effect — no PrimeFlex is installed); write real Material-native component styles (dual-list, org-chart, nav, editors). Dark-theme table/form/snackbar/dialog styling; icon pass (§4.10); Material error/warning colours throughout.

### Phase 5 — Verification
1. Grep gates: `rg -n "primeng|primeicons|@primeuix|pi pi-|<p-|pInputText|pButton|pTooltip" src/clientapp/src` → expect **zero** hits.
2. Production build in dev container:
   `cd src/clientapp && npm install && ng build --configuration production --prerender=false --deploy-url="/" --base-href="/"`
3. Full-route smoke test in the running app (docker-compose dev stack): login → monitor peers → IP-tables → VPN layout → server configuration (both tabs) → peers/peer-groups/targets CRUD (list, add, edit, delete, dual-list drag **and** buttons, confirm dialogs, toasts) → download .conf / QR / email.
4. Optional backend sanity: `pytest` (unchanged code, but confirms no unintended coupling).
5. Budget check: confirm no `initial` budget error; keep new component styles under `anyComponentStyle` limit.

---

## 6. File inventory

**New files**
- `src/app/notification.service.ts`
- `src/app/confirm-dialog/confirm-dialog.component.{ts,html,scss}`
- `src/app/dual-list/dual-list.component.{ts,html,scss}`
- `src/app/org-chart/org-chart.component.{ts,html,scss}`

**Modified files**
- `package.json` / `package-lock.json`
- `src/styles.scss`, `src/index.html`
- `src/app/app.config.ts`
- `src/app/app-shared.module.ts`
- `src/app/confirmation-dialog-service.ts`
- `src/app/webapi.service.ts`, `src/app/webapi.entities.ts`
- `src/app/app.component.{html,ts}`
- `src/app/app-sidepanel/app-sidepanel.component.{html,ts}`
- `src/app/login/login.component.html`
- `src/app/crud-container/crud-container.component.{html,ts}`
- `src/app/manage-peers-list/manage-peers-list.component.html`
- `src/app/manage-peer-groups-list/manage-peer-groups-list.component.html`
- `src/app/manage-targets-list/manage-targets-list.component.html`
- `src/app/manage-peers-editor/manage-peers-editor.component.{html,ts}`
- `src/app/manage-peer-groups-editor/manage-peer-groups-editor.component.{html,ts}`
- `src/app/manage-targets-editor/manage-targets-editor.component.{html,ts}`
- `src/app/manage-peers/manage-peers.component.ts`
- `src/app/manage-peer-groups/manage-peer-groups.component.ts`
- `src/app/manage-targets/manage-targets.component.ts`
- `src/app/server-monitor-peers/server-monitor-peers.component.{html,ts}`
- `src/app/server-monitor-iptables/server-monitor-iptables.component.{html,ts}`
- `src/app/server-vpn-layout/server-vpn-layout.component.{html,ts}`
- `src/app/manage-server-configuration/manage-server-configuration.component.{html,ts}`
- `src/app/app-about/app-about.component.html`
- `src/app/validation-errors-display/validation-errors-display.component.{html,ts}`
- `src/app/testpage/testpage.component.{html,ts}`

**Unchanged**: backend, all `webapi.entities.ts` entity shapes, `app.routes.ts`, `authorized-view`, `home` (template already empty).
