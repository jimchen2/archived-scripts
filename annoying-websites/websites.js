/* Default blocked websites — edit this list to change what new installs block.
 *
 * Each entry is a prefix match pattern: *://<host>/<path>*
 *   "example.com/1"  ->  "*://example.com/1*"
 *   "example.com"    ->  "*://example.com/*"
 * Delete every entry to ship with an empty default list.
 *
 * This file is the single source of truth and is loaded by background.js and
 * the registered content scripts before shared.js.
 *
 * The extension requests access to all URLs, but only entries in the saved
 * website list are blocked (HTTP and HTTPS only).
 */
globalThis.ANNOYING_DEFAULT_WEBSITES = Object.freeze([
  "*://*.1point3acres.com/*",
  "*://*.huaren.us/*",
  "*://www.reddit.com/*",
  "*://arena.ai/c/*",
  "*://www.baidu.com/*",
  "*://aistudio.google.com/*",
  "*://*.zombsroyale.io/*",
]);
