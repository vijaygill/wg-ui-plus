/**
 * Navigation menu item used by the app side panel.
 * Replaces the old navigation menu item type used previously.
 *
 * `route` is optional: items such as "Log out" perform an action via a
 * component-level `command` instead of navigating.
 */
export interface NavMenuItem {
    label: string;
    icon: string;
    route?: string;
}
