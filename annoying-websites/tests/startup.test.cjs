const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const root = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root, name), 'utf8');

test('toolbar popup and all-URL permission are declared', () => {
  const manifest = JSON.parse(read('manifest.json'));
  assert.equal(manifest.action.default_popup, 'popup.html');
  assert.deepEqual(manifest.host_permissions, ['<all_urls>']);
  assert.equal(manifest.optional_host_permissions, undefined);
  for (const name of ['popup.html', 'popup.js', 'popup.css']) {
    assert.ok(fs.existsSync(path.join(root, name)), `${name} exists`);
  }
});

test('all extension scripts parse successfully', () => {
  for (const name of fs.readdirSync(root).filter(name => name.endsWith('.js'))) {
    assert.doesNotThrow(() => new vm.Script(read(name), { filename: name }), name);
  }
});

test('service worker imports load the bundled website configuration', () => {
  const manifest = JSON.parse(read('manifest.json'));
  const worker = read(manifest.background.service_worker);
  const imports = /importScripts\(([^)]+)\)/.exec(worker);
  assert.ok(imports, 'worker must import its configuration scripts');
  const context = vm.createContext({ console });
  for (const name of JSON.parse(`[${imports[1]}]`)) {
    vm.runInContext(read(name), context, { filename: name });
  }
  assert.ok(context.AnnoyConfig, 'shared configuration is available');
  const websites = context.AnnoyConfig.DEFAULTS.websites;
  assert.ok(websites.length > 0, 'bundled defaults are not empty');
  assert.ok(websites.includes('*://www.reddit.com/*'));
  assert.ok(websites.includes('*://www.baidu.com/*'));
  assert.equal(websites.length, context.ANNOYING_DEFAULT_WEBSITES.length);
});

test('custom website prefixes match only the intended HTTP and HTTPS URLs', () => {
  const context = vm.createContext({ console, URL, TextEncoder });
  vm.runInContext(read('websites.js'), context);
  vm.runInContext(read('shared.js'), context);
  const config = context.AnnoyConfig;
  const pattern = config.normalizePattern('example.org/news');
  assert.equal(pattern, '*://example.org/news*');
  assert.equal(config.matchesUrl(pattern, 'https://example.org/news/latest'), true);
  assert.equal(config.matchesUrl(pattern, 'http://example.org/news'), true);
  assert.equal(config.matchesUrl(pattern, 'https://other.org/news'), false);
  assert.equal(config.matchesUrl(pattern, 'https://example.org/other'), false);
  assert.equal(config.matchesUrl(pattern, 'chrome://settings/'), false);
});
