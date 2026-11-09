Annoying Websites

https://chromewebstore.google.com/detail/annoying-websites/lkaiabamlhfejfbnfinfocnpaanehpag

Files

- `websites.js` — the default blocked website list. Edit this to change what new installs block.
- `manifest.json` — extension settings. The extension requests access to all URLs so users can block custom HTTP and HTTPS websites. Chrome may ask existing users to approve the broader access.
- `popup.html`, `popup.js`, `popup.css` — toolbar interface to add and remove website prefixes.
- `shared.js` — settings helpers and URL prefix matching.
- `background.js` — service worker: settings sync, permissions, content script registration.
- `content.js` — the block overlay (ЭТОТ САЙТ ЗАБЛОКИРОВАН) and the browsing timer.

Validation

Run `node --test tests/*.test.cjs` (Node.js 18+) before loading the extension to check
JavaScript syntax and the service worker's configuration imports. A syntax error in
`websites.js` also prevents the background worker from registering (Chrome status 15).

Click the extension icon to manage the blocked list. Enter a domain or URL prefix, such as `example.com` or `example.com/path`. Only websites in the list are blocked; browser-internal and other Chrome-restricted pages cannot be blocked. Chrome site-access settings can also restrict the extension.
