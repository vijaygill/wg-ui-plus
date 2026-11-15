# Code review — frontend (Angular) — 15 Nov 2026

Baseline: `develop` @ `82005f4b167940b75905db40bfa4ba39adb753f9`, clean working tree.
Scope: `src/clientapp/src` (~6.4k lines of TS/templates/SCSS, 41 TS files) plus `angular.json`, `tsconfig*.json`, `package.json`, `README.md`. The backend was reviewed separately in [CODE-REVIEW.md](./CODE-REVIEW.md); items there are cited as `REV-n`.
Method: three focused review passes (infrastructure/services, pages, controls/cross-cutting) plus independent re-reading of every cited line by the architect.

**Nothing was executed.** `wg-ui-dev-shell` was not running, and `@angular-devkit/build-angular` is not installed (see FE-06), so `ng build`, `ng serve` and `ng test` could not run. Anything that needs a browser to confirm is labelled `not verified`. `strict: true` and `strictTemplates: true` are already on — the type layer is in good shape.

**Open GitHub issues used as context:** [#315](https://github.com/vijaygill/wg-ui-plus/issues/315) feedback during lengthy backend calls — still open, see FE-24. [#297](https://github.com/vijaygill/wg-ui-plus/issues/297) remove `zone.js` — the signal migration is deliberately in progress; nothing below proposes finishing it.

## Diff style rules applied to every "Minimal fix" below

One commit = one row. ≤ 25 changed lines, most ≤ 10. Same file and same function where possible. No new dependencies, no new modules, no broad renames, no template or CSS reformatting churn, no comment noise, no sweeping `any` out of files you are not otherwise changing. Match the surrounding style — this codebase uses 4-space indent in TS, `@for`/`@switch` control flow in newer templates and `*ngFor` in older ones, and `--mat-sys-*` custom properties for colour.

## Main items — one row, one ticket

| ID | Sev | Where | What is wrong | Minimal fix | ~Diff | Ref |
|----|-----|-------|---------------|-------------|-------|-----|
| FE-01 | High | `pages/server-monitor-peers/server-monitor-peers.component.html:75-76` | The **"Data Tx"** column renders `transfer_rx` and **"Data Rx"** renders `transfer_tx` — the two cells are transposed against their own headers at `:48-49`. The summary tiles (`:22-28`) and the totals in the component are correct, so the table contradicts the tiles on the same screen. Every user reads transfer volume in the wrong direction | Swap the two cell expressions | 2 | — |
| FE-02 | High | `controls/notification/notification.component.html:11` | The dismiss button renders only when `notification.dismissible`, and the two persistent banners built in `app.component.ts:231,237` never set it. So "This will regenerate Server Configuration files and restart WireGuard" and the offline banner cannot be dismissed. Combined with FE-03 the user has no way to get rid of either | Render the dismiss button for persistent notifications too | 1 | pairs FE-03 |
| FE-03 | High | `services/notification.service.ts:97` + 7 call sites | `show()` returns early when a persistent banner is up and the incoming message is not persistent, and only `showEmailDeliveryFailure` passes `replacePersistent`. The "regenerate files" banner appears immediately after any peer/target/group edit, so while it is up these are silently discarded: `"Server configuration saved."`, `"Email settings saved."`, `"MCP configuration saved."`, `"Test e-mail sent successfully."`, `"E-mail sent successfully."` — **and the MCP failure error at `manage-server-configuration.component.ts:563`, where a failed toggle just flips the checkbox back with no explanation** | Add one user-initiated variant that passes the existing `replacePersistent` option (the email path already retains and restores the status banner), and use it at those call sites | ~10 | same bug class already fixed for email |
| FE-04 | High | `pages/manage-server-configuration/manage-server-configuration.component.html:101` + `.ts:516-523`, duplicated at `app.component.ts:246-254` | "Restart" has no `[disabled]`, no confirmation and no `error:` handler, and the nested `subscribe` never inspects `data.status` — so a failed `wg-quick down`/`up` still announces "Wireguard restarted on server." (the backend always returns `ok`, REV-13). It is re-clickable during the multi-second restart and drops every VPN connection with one click. The identical body exists in two components | Add an in-flight flag bound to `[disabled]`, a confirm, an `error:` handler and a `status !== 'ok'` check; keep one copy of the logic | ~8 | REV-13, REV-18 |
| FE-05 | High | `app.config.ts:19-21` | Providers contradict themselves: `provideAnimationsAsync()` at `:19` is overridden by `provideAnimationsAsync('noop')` at `:20`, so all Material animations run in no-op mode; `provideHttpClient` is registered a second time at `:21`; and `provideClientHydration(withNoIncrementalHydration())` is registered although there is no SSR entry, no `ssr` option in `angular.json` and no `main.server.ts` (the `package.json` SSR script is FE-26) | Keep exactly one `provideHttpClient` combining `withXhr()`, `withXsrfConfiguration({...})` and `withInterceptorsFromDi()`, one `provideAnimationsAsync()`, and delete the hydration provider — **confirm first whether the `('noop')` variant was deliberate** | 3 | — |
| FE-06 | High | `angular.json:65,77,83` | `serve`, `extract-i18n` and `test` point at `@angular-devkit/build-angular:*`, which is not a dependency and is **not installed** (`node_modules/@angular-devkit` contains only `architect` and `core`). `build` correctly uses `@angular/build:application`. Consequence: `ng serve` and `ng test` fail with "Builder not found", including the `ng test` AGENTS.md documents and the README advertises | Retarget the three strings to `@angular/build:dev-server`, `:extract-i18n`, `:karma`, and correct AGENTS.md/README if the outcome differs | 3 + 2 docs | — |
| FE-07 | Medium | `pages/server-monitor-peers/server-monitor-peers.component.html:53` | `@for (...; track connectedPeer.peer_name)` — `Peer.name` has no uniqueness constraint (`models.py:107`) and the backend emits one row per peer, so two peers named e.g. "Phone" produce duplicate track keys: NG0501 and a table that stops updating correctly | Track by `public_key`, falling back to `$index` | 1 | — |
| FE-08 | Medium | `http-client-error.interceptor.ts:68`, `app.routes.ts:15-30` | A 401 produces the message "Unauthorised call to server." plus a persistent banner, and nothing else: the interceptor injects only `WebapiService`, and **no route in `app.routes.ts` has a `canActivate` guard**. After a session expires — which happens immediately after a password change, see FE-12 — the user stays on the page and every subsequent save fails with no redirect to login | On `status === 401` inform `LoginService` (or navigate to `/login`) before rethrowing | 4 | REV-22 |
| FE-09 | Medium | `services/login.service.ts:24` | `login()` (and `logout()`, `checkIsUserAuthenticated()`) subscribe with only a next callback. On 500, 404 or a network failure nothing is emitted, so the login form sits on "Logging in. Please wait…" forever with no error and no retry cue — the one screen a locked-out user needs | Add an error callback that emits `{ is_logged_in: false, message: 'Login failed.' }` | 4 | REV-21 |
| FE-10 | Medium | `pages/manage-server-configuration/manage-server-configuration.component.html:165-205` + `.ts:445-451` | Per-field email errors are rendered only inside `<mat-error>`, which Material hides while the `ngModel` control itself is valid. Type port `99999` and press Save: nothing at all happens. A backend 400 on host/user/from-address is hidden the same way | Render these through the `div.editor-message` pattern already used in the same file at `:224-229` | ~6 | — |
| FE-11 | Medium | `pages/manage-server-configuration/manage-server-configuration.component.ts:101-106`, `:188-191` | Any status push carrying a newer `last_db_change_datetime` calls `refreshData()`, which replaces `editItem` and silently throws away unsaved edits. Reproduce alone: edit the Server tab, switch to the Email tab and save (`:490` bumps the same row) — the Server tab's edits are gone with no message | Skip the refresh while `hasChanges`, or warn before discarding | 3 | — |
| FE-12 | Medium | `pages/manage-server-configuration/manage-server-configuration.component.ts:526-535` + `html:288` | Change Password has no `error:` handler and no in-flight disable. The backend returns HTTP 200 for every failure and drops the session because it never calls `update_session_auth_hash` (REV-22), so the user reads "Password changed." and then hits "Unauthorised call to server." on the next page with no redirect and no explanation | On success clear the three fields and route to `/login` with a "sign in again" message; add an `error:` handler | ~6 | REV-22, FE-08 |
| FE-13 | Medium | `pages/server-monitor-peers/…component.ts:95-101`, `server-monitor-iptables/…:50-54`, `server-vpn-layout/…:49-54` | None of the three has an `error:` handler and none is wrapped in `<app-authorized-view>`. A failed poll leaves the previous "Connected" chips and byte counters on screen as if live. Today the routes behind them are anonymous (REV-04/05); once that is fixed these three pages will re-push a 401 banner on every 10-second tick forever | One commit per page: wrap the template in `<app-authorized-view>` + `#childControl`, and add an error handler that marks the data stale | ~4 × 3 | REV-04, REV-05 |
| FE-14 | Medium | `pages/manage-peers-editor/manage-peers-editor.component.ts:62-69` | `serverStatus.subscribe(...)` is registered in the constructor with no teardown. `serverStatus` is a root `ReplaySubject` on the service, so every editor instance ever opened is retained and re-invoked on every status push — memory grows per editor visit for the life of the tab | Guard with `takeUntilDestroyed(inject(DestroyRef))` | 3 | — |
| FE-15 | Medium | `controls/dual-list/dual-list.component.ts:78` + `pages/manage-peers-editor/manage-peers-editor.component.ts:76` | The control has no concept of a protected item. Everyone is filtered out of the Available pane only, so it can still be dragged out of Selected, or moved out by the arrow/`moveAll` buttons: a peer silently loses Everyone membership and `savePeer` persists the loss of internet access, with no confirmation | Add `@Input() lockedIds` to the control and skip locked ids when moving out of the target pane (drop + move-selected + move-all) | ~10 | — |
| FE-16 | Medium | `services/webapi.service.ts:19`, `:174` | `urlGetWireguardConfiguration` is `/api/v1/data/control/wireguard_get_configuration`; the backend route is `/api/v1/control/wireguard_get_configuration` (`api_app/urls.py:34`) — the extra `data/` segment means `getWireguardConfiguration()` can only ever 404. It has no caller today, so the break is latent for the next person who wires it up | Fix the path, or delete the method, the constant and the `WireguardConfiguration` entity together | 8 | — |
| FE-17 | Medium | `http-client-error.interceptor.ts:79` | The exemption list covers `send_peer_email` and `send_test_email` only, so a failed SMTP *connectivity* test also pushes a persistent status error: the toolbar orb flips to red "Offline" and the retained "Server returned HTTP Error 50x" banner reappears after the focused email banner is dismissed | Add `/api/v1/control/email/test_connectivity` to the exempt paths | 1 | — |
| FE-18 | Medium | `webapi.entities.ts:29`, `:80` + `services/webapi.service.ts:157-159` | `Peer.private_key` and `ServerConfiguration.private_key` are declared on the SPA entities, and `saveServerConfiguration` PUTs the whole loaded object — `private_key` and `public_key` included — back to the API on every save. Nothing renders, logs or persists them, so this is exposure in transit and in memory rather than on screen | Once the backend stops sending them (REV-03), drop both fields from the interfaces. Do the backend change first so the SPA is never left without a value it still reads | 2 | REV-03 |

## Smaller items — same format, optional backlog

| ID | Sev | Where | What is wrong | Minimal fix | ~Diff |
|----|-----|-------|---------------|-------------|-------|
| FE-19 | Medium | `controls/org-chart/org-chart.component.html:6`, `:23` | No `trackBy` on the node cells or the connectors while `ngOnChanges` rebuilds both arrays on every 10-second poll, so VPN Layout destroys and recreates every node each tick — open tooltips die and hover state is lost mid-action | Add `trackBy` on both `*ngFor` | ~5 |
| FE-20 | Medium | `controls/app-nav-drawer/app-nav-drawer.component.ts:143-152` | Logged-out users are shown the Server section: Monitor Peers, IP-Tables, VPN Layout. That is tolerable only while those endpoints are anonymous; the moment REV-04/05 land, each link renders an empty table plus an error banner | Drop the Server section from `itemsAnonymous` (or gate on `is_logged_in`) as part of the REV-04/05 change | 3 |
| FE-21 | Medium | `controls/notification/notification.component.html:2` | The banner div has no `role` or `aria-live`, so save results and the "connection to the server was lost" message are never announced — on every page | Add `role="status" aria-live="polite"` | 1 |
| FE-22 | Medium | `controls/dual-list/dual-list.component.html:11` | Items are plain `<div (click)>` with no `tabindex` and no key handler. Keyboard users can focus the arrow buttons but can never select an item, so the control is unusable without a mouse (CDK keyboard drag does not apply: `onDrop` returns for same-pane moves) | `tabindex="0"` plus Enter/Space calling the existing `onItemClick` in both panes | ~4 |
| FE-23 | Medium | `controls/dual-list/dual-list.component.html:26` | All four icon-only buttons are named by `matTooltip` only, and `MatIcon` marks the glyph `aria-hidden`, so they have no accessible name in the peer, target and peer-group picklists | Add `aria-label` to the four buttons | 4 |
| FE-24 | Medium | `manage-server-configuration.component.html:93,101,246,252,288` + the three editors' Ok buttons | **There is no in-flight feedback anywhere in the app.** No `mat-progress-*` and no spinner exists under `src/clientapp/src`; the HTTP interceptor only maps errors to the status banner. GitHub #315 is therefore still unimplemented. The MCP and email tabs are the only controls with `[disabled]` guards; Ok, Restart, Send Test Email, Test Connectivity, Change Password and the editors' Ok buttons are all re-clickable during a long call, which is how a double POST or a double restart happens | Either `[disabled]` plus a label swap on those buttons, or a ~10-line in-flight counter in the interceptor driving one banner. Pick one approach before writing fixes so the two do not collide | 2 per button / ~10 |
| FE-25 | Low | `services/webapi.service.ts:48`, `:153` | `getPeerGroup(id)` and `getServerConfiguration(id)` omit the trailing slash every other item URL carries, so Django's `APPEND_SLASH` costs a 301 round-trip each time an editor opens | Append `/` to both | 2 |
| FE-26 | Low | `package.json:10` | `serve:ssr:wg-ui-plus` runs `dist/wg-ui-plus/server/server.mjs`, which is never produced (no `ssr` option in `angular.json`, no `main.server.ts`) — a dead script a human can trip over | Delete the entry | 1 |
| FE-27 | Low | `pages/server-monitor-peers/server-monitor-peers.component.ts:111-116` | Every column sorts through `String(...).localeCompare`, so clicking "Data Tx" or "Last Handshake" orders `2` above `1000` | Compare numerically when both values are numbers | ~4 |
| FE-28 | Low | `app.routes.ts:28` (and `:17`) | `/test-page` ships a notifications/dialog demo reachable by URL in production with no nav entry — the frontend twin of the backend `/test/` route. `/home` likewise has no nav entry | Remove the route lines; the components can follow separately | 1 |
| FE-29 | Low | `app-shared.module.ts:11`, `:16` | `MatMenuModule` and `MatTableModule` are imported and exported, but `mat-menu` and `mat-table` appear in no template (tables are native `<table class="data-table">` with `matSort`) | Drop both from the modules array | 2 |
| FE-30 | Low | `styles.scss:226`, `:231`, `:249-250` | `.status-chip-disconnected` and `.status-chip-down`, plus their dark overrides, match no template. Meanwhile `.editor-form` is used by 6 templates and defined in no stylesheet, so those forms rely entirely on `form-grid` | Delete the two dead chips; either define `.editor-form` or remove it from the templates | 3 |
| FE-31 | Low | `controls/validation-errors-display/validation-errors-display.component.scss:17` | Hard-coded `#ef5350` error text is roughly 3.1:1 on the light surface, while every other control uses theme tokens | Use `var(--mat-sys-error)` | 1 |
| FE-32 | Low | `controls/validation-errors-display/validation-errors-display.component.html:6` | "Warnings can be ignored." promises a severity split the component cannot make: `component.ts:34` hard-codes `severity: 'error'` and the API sends no severity field at all | Delete the line and the unused field | 2 |
| FE-33 | Low | `src/clientapp/README.md:3`, `:7`, `:19` | Still says "generated with Angular CLI version 17.3.6" (the project is on 22.2), and documents `ng serve` / `ng test` as the workflow, which FE-06 shows cannot run | Correct the version and the commands | 3 |
| FE-34 | Low | `pages/manage-peers-list/…:55`, `manage-targets-list/…:57`, `manage-peer-groups-list`, `server-monitor-peers/…:104` | Four byte-identical `sortData` implementations | One exported `sortByProperty<T>(items, sort)` helper used by all four (touches 5 files, so slightly wider than the usual row) | ~14 |
| FE-35 | Low | `src/index.html:10-12` | Loads Google Fonts. On an offline appliance — the normal deployment — that request fails and the app falls back to whatever the browser has. Whether Roboto is bundled locally was `not verified` | Verify in the dev shell; if it is not bundled, serve the font locally and drop the remote link | ~3 |

## Ticket text

#### FE-01 — Correct the swapped Data Tx and Data Rx columns in Monitor Peers

In `server-monitor-peers.component.html` the headers at `:48-49` read "Data Tx" then "Data Rx", but the cells at `:75-76` emit `{{ connectedPeer.transfer_rx }}` then `{{ connectedPeer.transfer_tx }}`. The summary tiles at `:22-28` and the totals in the component use the correct mapping, so the table contradicts the tiles above it and every user reads send and receive the wrong way round.

Fix: swap the two cell expressions. Acceptance: a peer whose sent counter is larger shows the larger number under "Data Tx".

#### FE-02 — Make persistent banners dismissible

`notification.component.html:11` renders the close button only when `notification.dismissible` is set, and the two persistent banners built in `app.component.ts:231` (offline/error) and `:237` ("This will regenerate Server Configuration files and restart WireGuard") never set it. The user has no way to clear either one.

Fix: render the dismiss button for persistent notifications as well. Acceptance: both banners show an X and clear when it is pressed.

#### FE-03 — Let user-initiated results displace a persistent status banner

`NotificationService.show()` (`services/notification.service.ts:97`) returns without displaying anything whenever a persistent banner is showing and the new message is not persistent. Only `showEmailDeliveryFailure` opts out via `replacePersistent`. Because any edit raises the "regenerate files" persistent banner, every subsequent toast is dropped: "Server configuration saved.", "Email settings saved.", "MCP configuration saved.", "Test e-mail sent successfully.", "E-mail sent successfully." — and at `manage-server-configuration.component.ts:563` so is the *failure* message for an MCP toggle, which just flips the checkbox back with nothing on screen.

Fix: add one user-initiated variant that passes the existing `replacePersistent` option and retains/restores the status banner the way the email path already does, then use it at those seven call sites. Acceptance: saving a peer while the regenerate banner is up shows the confirmation, and the regenerate banner returns after it expires.

#### FE-04 — Make Restart safe and honest about failure

The Restart button (`manage-server-configuration.component.html:101`) has no `[disabled]` and no confirmation, and `applyConfiguration()` (`.ts:516-523`) nests two `subscribe` calls with only next handlers: it never inspects `data.status`, so a backend that failed to bring WireGuard up still announces "Wireguard restarted on server." (the backend always reports ok — REV-13). The same five lines are duplicated verbatim in `app.component.ts:246-254`.

Fix: add an in-flight flag bound to `[disabled]`, a confirmation, an `error:` handler, and a check on the reported status; keep a single copy of the logic. Acceptance: Restart cannot be double-clicked and a backend failure is reported as a failure.

#### FE-05 — Remove the contradictory providers in app.config

`app.config.ts:19-21` calls `provideAnimationsAsync()` and then `provideAnimationsAsync('noop')` (the later registration wins, so Material animations run no-op), calls `provideHttpClient` twice, and calls `provideClientHydration(withNoIncrementalHydration())` with no SSR entry, no `ssr` option in `angular.json` and no `main.server.ts`.

Fix: one `provideHttpClient` that combines `withXhr()`, the existing `withXsrfConfiguration({ cookieName: 'csrftoken', headerName: 'X-CSRFToken' })` and `withInterceptorsFromDi()`; one `provideAnimationsAsync()`; delete the hydration provider. **Check with the maintainer whether `('noop')` was a deliberate choice** — if it was, keep it in the single remaining call instead. Acceptance: POST/PATCH from the SPA still carry the CSRF header (verify in the dev shell), animations behave as intended.

#### FE-06 — Retarget the Angular builders that are not installed

`angular.json:65,77,83` declare `serve`, `extract-i18n` and `test` with `@angular-devkit/build-angular:*` builders. That package is not in `package.json` and is not installed — `node_modules/@angular-devkit` contains only `architect` and `core` — while `build` correctly uses `@angular/build:application`. `ng serve` and `ng test` therefore fail with "Builder not found", including the `ng test` command AGENTS.md tells every developer to run and README advertises.

Fix: point the three at `@angular/build:dev-server`, `@angular/build:extract-i18n` and `@angular/build:karma`, then confirm from the dev shell and correct AGENTS.md/README if the result differs. Acceptance: `ng serve` starts, and `ng test` at least reaches the runner (there are currently no `*.spec.ts` files).

#### FE-07 — Track the connected-peers table by a unique key

`server-monitor-peers.component.html:53` tracks rows by `connectedPeer.peer_name`, but `Peer.name` has no uniqueness constraint (`models.py:107`) and the backend emits one row per peer, so two peers with the same name produce duplicate track keys — NG0501 and a table that stops updating correctly.

Fix: track by `public_key` (falling back to `$index` where it is absent). Acceptance: two peers with the same name both render and update.

#### FE-08 — Send the user to login when the session has expired

The interceptor turns a 401 into the message "Unauthorised call to server." plus a persistent banner and rethrows — it injects only `WebapiService`, so nothing redirects. `app.routes.ts:15-30` defines 13 routes with **no `canActivate` guard on any of them**. After a session expires, and immediately after a password change (FE-12, REV-22), the user keeps working on a dead page: every save fails, and the only clue is the banner.

Fix: on `status === 401`, inform `LoginService` (or navigate to `/login`) before rethrowing. Acceptance: an expired session returns the user to the login screen instead of looping on failures.

#### FE-09 — Report a failed login instead of hanging

`LoginService.login()` (`services/login.service.ts:24`) subscribes with only a next callback, as do `logout()` and `checkIsUserAuthenticated()`. On a 500, a 404 or a network failure nothing is emitted, so the form stays on "Logging in. Please wait…" forever — precisely when a locked-out user needs feedback. The login form also has no in-flight disable (`login.component.html:22`, `.ts:45-49`), so the POST can be fired twice.

Fix: add an error callback emitting `{ is_logged_in: false, message: 'Login failed.' }`, and disable Submit while a request is in flight. Acceptance: a server error clears the wait message and shows a reason.

#### FE-10 — Show email-tab field errors that Material is hiding

On the Email tab (`manage-server-configuration.component.html:165-205`) per-field errors are rendered only inside `<mat-error>`. Material hides `<mat-error>` while the `ngModel` control is valid, so a port of `99999` produces no message at all and Save appears to do nothing; a backend 400 on host, user or from-address is hidden the same way (`.ts:445-451` populates them correctly).

Fix: render those messages through the `div.editor-message` pattern already used a few lines below at `:224-229`. Acceptance: an invalid port shows a visible message without the field needing to be touched again.

#### FE-11 — Do not discard unsaved edits when the status refreshes

`manage-server-configuration.component.ts:101-106` refreshes the page whenever a status push carries a newer `last_db_change_datetime`, and `refreshData()` (`:188-191`) replaces `editItem`. Reproduce: edit the Server tab, switch to the Email tab and save — that save bumps the same row, the push arrives, and the Server tab's unsaved edits vanish with no message.

Fix: skip the refresh while `hasChanges`, or warn before discarding. Acceptance: unsaved edits survive a concurrent status change.

#### FE-12 — Give change-password an honest outcome

`changePassword()` (`.ts:526-535`) has no `error:` handler and no in-flight disable. The backend returns HTTP 200 for every failure path and drops the session because it never calls `update_session_auth_hash` (REV-22), so the user is shown `data.message` — "Password changed." — and then meets "Unauthorised call to server." on the next page with no redirect (FE-08) and no hint to sign in again.

Fix: on success clear the three fields and route to `/login` with a "sign in again" message; add an `error:` handler. Acceptance: after a password change the user is back at login and can sign in with the new password.

#### FE-13 — Handle errors on the three monitor pages

`server-monitor-peers.component.ts:95-101`, `server-monitor-iptables.component.ts:50-54` and `server-vpn-layout.component.ts:49-54` have no `error:` handler and none of the three templates is wrapped in `<app-authorized-view>`. A failed poll leaves stale "Connected" chips and byte counters on screen as if current. Today the endpoints are anonymous (REV-04/05); once that is fixed, all three will re-push a 401 banner every ten seconds with no redirect.

Fix: one small commit per page — wrap in `<app-authorized-view>` with `#childControl`, and add an error handler that flags the data as stale. Acceptance: a failing poll is visibly stale rather than falsely live.

#### FE-14 — Tear down the serverStatus subscription in the peers editor

`manage-peers-editor.component.ts:62-69` subscribes to `webapiService.serverStatus` in the constructor and never unsubscribes. `serverStatus` is a root `ReplaySubject` held by the service, so every editor instance ever created is retained and its callback re-runs on every status push.

Fix: pipe through `takeUntilDestroyed(inject(DestroyRef))`. Acceptance: opening and closing the editor repeatedly does not grow the subscriber list.

#### FE-15 — Let dual-list protect mandatory items so Everyone cannot be removed

`dual-list.component.ts` has no notion of a protected item. `manage-peers-editor.component.ts:76` filters Everyone out of the Available pane only, so it remains draggable out of Selected and can also be moved out with the arrow or move-all buttons. Saving then persists the loss of Everyone membership, which removes the peer's internet access, with no confirmation anywhere.

Fix: add `@Input() lockedIds` to the control and skip locked ids whenever items move out of the target pane (drop, move-selected, move-all). Acceptance: Everyone cannot leave the Selected pane by drag or button.

#### FE-16 — Fix the wireguard_get_configuration URL, or delete the dead method

`webapi.service.ts:19` builds `/api/v1/data/control/wireguard_get_configuration`; the backend route is `/api/v1/control/wireguard_get_configuration` (`api_app/urls.py:34`). `getWireguardConfiguration()` (`:174`) can therefore only 404. Nothing calls it today, so the defect is latent for whoever wires up the configuration view next.

Fix: correct the prefix, or delete the method, the constant and the `WireguardConfiguration` entity together. Acceptance: the call returns 200 when used, or no dead path remains.

#### FE-17 — Exempt the SMTP connectivity test from the persistent status banner

The interceptor's exemption list (`http-client-error.interceptor.ts:79`) covers `send_peer_email` and `send_test_email` but not `test_connectivity`. A failed "Test Connectivity" on the Email tab therefore pushes a persistent status error: the toolbar orb goes red "Offline" and the generic "Server returned HTTP Error 50x" banner reappears once the focused email banner is dismissed.

Fix: add `/api/v1/control/email/test_connectivity` to the exempt paths. Acceptance: a failed connectivity test reports once, in the email panel, without marking the server offline.

#### FE-18 — Drop private keys from the SPA entity types

`webapi.entities.ts:29` and `:80` declare `private_key` on `Peer` and `ServerConfiguration`, and `saveServerConfiguration` (`webapi.service.ts:157-159`) PUTs the entire loaded object — `private_key` and `public_key` included — back on every save. Nothing renders, logs or stores them, so this is exposure in transit and in browser memory.

Fix: after the backend stops sending them (REV-03), remove both fields from the interfaces. Order matters: the backend change first, so the SPA is never left without a value it still reads. Acceptance: no private key in either request or response payload.

### Smaller items — titles and one-paragraph bodies

- **FE-19 — Add trackBy to the VPN Layout org chart.** `org-chart.component.html:6` and the connectors at `:23` have no `trackBy`, while `ngOnChanges` rebuilds both arrays from scratch on every 10-second poll, so every node is destroyed and recreated each tick: tooltips close themselves and hover state is lost mid-interaction. Add `trackBy` keyed on label and type.
- **FE-20 — Hide the Server nav section from logged-out users.** `app-nav-drawer.component.ts:143-152` gives anonymous visitors Monitor Peers, IP-Tables and VPN Layout. That works only while those endpoints are anonymous; once REV-04/05 require authentication each link shows an empty table plus an error banner. Drop the section from `itemsAnonymous`, or gate it on `is_logged_in`, in the same change as REV-04/05.
- **FE-21 — Announce the notification banner.** `notification.component.html:2` has no `role` or `aria-live`, so save confirmations and the "Connection to the server was lost." message are never announced to assistive technology, on any page. Add `role="status" aria-live="polite"`.
- **FE-22 — Make dual-list items keyboard-selectable.** `dual-list.component.html:11` renders items as `<div (click)>` with no `tabindex` and no key handler; CDK keyboard dragging does not apply because `onDrop` returns for same-pane moves. Keyboard users can reach the arrow buttons but can never select an item, so the control is mouse-only. Add `tabindex="0"` and handle Enter/Space through the existing `onItemClick` in both panes.
- **FE-23 — Name the four dual-list buttons.** `dual-list.component.html:26` gives the buttons only `matTooltip`, and `MatIcon` marks the glyph `aria-hidden`, so all four have no accessible name in the peer, target and peer-group picklists. Add `aria-label` to each.
- **FE-24 — Decide how long operations show feedback (#315).** No global in-flight indicator exists: `mat-progress` and `spinner` match nothing under `src/clientapp/src`, and the interceptor only maps errors to the status banner. Only the MCP and email tabs guard their buttons; Ok, Restart, Send Test Email, Test Connectivity, Change Password and the three editors' Ok buttons can all be re-clicked during a long call. Either add `[disabled]` plus a label swap on those buttons, or a ~10-line in-flight counter in `http-client-error.interceptor.ts` driving one banner — pick one first so the two approaches do not collide.
- **FE-25 — Add the missing trailing slash to two item URLs.** `getPeerGroup(id)` (`webapi.service.ts:48`) and `getServerConfiguration(id)` (`:153`) concatenate the id without the trailing slash every other URL carries, so Django's `APPEND_SLASH` adds a 301 round-trip each time an editor opens.
- **FE-26 — Delete the dead SSR npm script.** `package.json:10` runs `dist/wg-ui-plus/server/server.mjs`, which nothing builds: there is no `ssr` option in `angular.json` and no `main.server.ts`. Remove it along with the hydration provider in FE-05.
- **FE-27 — Sort the monitor columns numerically.** `server-monitor-peers.component.ts:111-116` sorts every column with `String(...).localeCompare`, so "Data Tx" and "Last Handshake" order 2 above 1000. Compare numerically when both operands are numbers.
- **FE-28 — Stop shipping the test page route.** `app.routes.ts:28` exposes `/test-page`, a notifications and dialog demo with no nav entry, in production — the frontend twin of the backend `/test/` route. `/home` at `:17` has no nav entry either. Remove the route lines; component deletion can follow separately.
- **FE-29 — Drop two unused Material modules.** `app-shared.module.ts` imports and exports `MatMenuModule` and `MatTableModule`; `mat-menu` and `mat-table` appear in no template (the tables are native `<table class="data-table">` with `matSort`). Remove both entries.
- **FE-30 — Clean up dead and undefined CSS.** `styles.scss:226` `.status-chip-disconnected` and `:231` `.status-chip-down`, with their dark overrides at `:249-250`, match no template. Conversely `.editor-form` is used by six templates and defined in no stylesheet, so those forms are laid out by `form-grid` alone. Delete the dead rules and either define `.editor-form` or drop it from the templates.
- **FE-31 — Use the theme's error colour.** `validation-errors-display.component.scss:17` hard-codes `#ef5350`, about 3.1:1 on the light surface, while every other control uses `--mat-sys-*` tokens. Switch to `var(--mat-sys-error)`.
- **FE-32 — Remove the false "Warnings can be ignored." promise.** `validation-errors-display.component.html:6` tells the user warnings are ignorable, but `component.ts:34` hard-codes `severity: 'error'` and the API sends no severity field at all, so no warning can ever be rendered. Delete the sentence and the unused field.
- **FE-33 — Correct the frontend README.** It still says the project was generated with "Angular CLI version 17.3.6" (the app is on 22.2) and documents `ng serve` and `ng test` as the workflow, which FE-06 shows cannot run.
- **FE-34 — Share one sort helper across the four tables.** `sortData` is byte-identical in `manage-peers-list.component.ts:55`, `manage-targets-list.component.ts:57`, `manage-peer-groups-list` and `server-monitor-peers.component.ts:104`. One exported `sortByProperty<T>(items, sort)` helper (~14 lines) replaces all four; it touches five files, so it is slightly wider than the usual row.
- **FE-35 — Check the Google Fonts dependency.** `src/index.html:10-12` loads fonts from Google, which fails on an offline appliance — the normal deployment — leaving whatever the browser has locally. `not verified` whether Roboto is bundled; if it is not, serve it locally and remove the remote link.

## Not findings — checked and clean

No `bypassSecurityTrust*` and no `[innerHTML]` anywhere in `src/app`, so the iptables log, WireGuard config text and QR data are interpolated as text, not HTML. Every `target="_blank"` carries `rel="noopener"`. Navigation uses `routerLink`, so clicks do not reload the app. No `console.*` outside `main.ts:7`, and nothing logs response bodies. The only `localStorage` use app-wide is the theme key (`theme.service.ts:52,70`) — no token or key material is persisted. The MCP token is masked in the template, fetched on demand, auto-hidden after 60 seconds and clipboard-only (`manage-server-configuration.component.ts:605-660`). The duplicate `provideHttpClient` does **not** drop `withXsrfConfiguration` (they provide separate tokens) — FE-05 is about clarity and the no-op animations, not broken CSRF. Per-field 400 bodies do render in the three editors because the backend uses `drf_standardized_errors`. Deletes are confirmed in all three editors; the Everyone group is protected there via `allow_modify_self` (fields disabled, Delete hidden); `*_ids` are derived from the dual-list selections the serializers declare, so membership is not dropped on save; the lists reload from the server when a dialog closes. `dist/` is git-ignored.

## Known-noted, deliberately excluded (needs a decision, not a diff)

`dual-list.component.ts:91` keeps the caller's array reference and splices/pushes it in place, so Cancel leaves the loaded peer or target already mutated — reopening the editor shows the discarded selection. The correct fix (non-mutating copies plus a `selectedChange` output) is `large`: it touches the control and all three editor pages, so it should be its own change after the smaller ones land. `manage-server-configuration.component.ts` is 777 lines; the three smallest self-contained extractions are the MCP token reveal/copy block (`:605-775`), the email tab (`:296-512` + `html:152-268`), and the `environmentVariableNames`/`environmentVariableLabel` pair (`:66-83`, `:222-233`) which both tabs need — each is a refactor decision, not a defect. `PeriodicRefreshUiService`'s `interval` (`services/periodic-refresh-ui.service.ts:11`) never pauses for hidden tabs, which is a design question rather than a bug. Finishing the `zone.js` removal (#297) is out of scope by design.

## Suggested order if you work down the list

FE-01 and FE-07 (one-line correctness fixes you can verify by eye) → FE-02/FE-03 together (they are one behaviour) → FE-04 and FE-09/FE-12 (the flows that lie about their outcome; FE-12 wants the backend side REV-22 too) → FE-05/FE-06 (config correctness, then re-run a build in the dev shell) → FE-10/FE-11 (config-page usability) → FE-08 with FE-13 and FE-20, ideally coordinated with REV-04/REV-05 on the backend → FE-14/FE-15/FE-16/FE-17 → FE-18 after REV-03 → then the smaller table. Decide FE-24 before touching any button state so the two approaches do not collide.
