// Run with: node --test tests/test_web_queue.js
// Exercise the actual browser client without starting its UI or a game server.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function client() {
  const elements = new Map();
  const document = {
    querySelector: () => null,
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, {
        textContent: '', classList: { add() {}, remove() {}, toggle() {} },
      });
      return elements.get(id);
    },
  };
  const requests = [];
  let response;
  const context = {
    document,
    performance: { now: () => 0 },
    setTimeout: () => 1,
    clearTimeout() {},
    fetch: async (url, init) => {
      requests.push({ url, body: JSON.parse(init.body) });
      return { ok: true, json: async () => response };
    },
  };
  let source = fs.readFileSync(path.join(__dirname, '../generals_web/static/app.js'), 'utf8');
  source = source.replace('  init();\n})();', '  globalThis.client = { S, tick, queueMove };\n})();');
  vm.runInNewContext(source, context);
  const { S, tick, queueMove } = context.client;
  const snap = {
    id: 'game', h: 2, w: 3, dir_actions: 9, you: 0,
    owner: [0, 0, 0, 0, -1, -2], army: [1, 4, 3, 2, 0, 0],
    generals: { you: [0, 0] }, score: { land: [4, 0], army: [10, 0] },
    turn: 1, done: false,
  };
  Object.assign(S, { id: 'game', snap, settings: { tick_ms: 1000 }, selected: 0 });
  response = snap;
  return { S, tick, queueMove, requests, elements, setResponse: (snap) => { response = snap; } };
}

const move = (src, dir, half = false) => ({ src, dir, half, action: src * 9 + dir + (half ? 4 : 0) });

test('skips ineffective moves and executes only the next playable move', async () => {
  const { S, tick, requests, elements } = client();
  S.queue = [move(0, 4), move(4, 3), move(3, 4), move(1, 4, true)];
  await tick();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].body.action, move(3, 4).action);
  assert.equal(S.queue.length, 1);
  assert.equal(S.queue[0].action, move(1, 4, true).action);
  assert.equal(elements.get('queue').textContent, '1 move queued');
  await tick();
  assert.equal(requests[1].body.action, move(1, 4, true).action);
  assert.equal(elements.get('queue').textContent, 'Queue empty');
});

test('skips lost sources, mountains and off-board moves and passes once when none remain', async () => {
  const { S, tick, requests, elements } = client();
  S.queue = [move(4, 3), move(2, 2), move(3, 3), move(0, 4)];
  await tick();
  assert.equal(requests.length, 1);
  assert.deepEqual(requests[0].body, {});
  assert.equal(S.queue.length, 0);
  assert.equal(elements.get('queue').textContent, 'Queue empty');
});

test('queueing does not reject a source that can grow before its half-turn', async () => {
  const { S, tick, queueMove, requests } = client();
  queueMove(4);
  assert.equal(S.queue.length, 1);
  assert.equal(S.selected, 1);
  S.snap.army[0] = 2;
  await tick();
  assert.equal(requests[0].body.action, move(0, 4).action);
});

test('rechecks remaining moves on the latest snapshot before each half-turn', async () => {
  const { S, tick, requests, setResponse } = client();
  S.queue = [move(1, 4), move(2, 3), move(3, 4)];
  const next = { ...S.snap, owner: [0, 0, 1, 0, -1, -2], army: [1, 1, 3, 2, 0, 0] };
  setResponse(next);
  await tick();
  await tick();
  assert.equal(requests[0].body.action, move(1, 4).action);
  assert.equal(requests[1].body.action, move(3, 4).action);
  assert.equal(S.queue.length, 0);
});

test('a legal split or attack is sent even if it cannot capture the target', async () => {
  const { S, tick, requests } = client();
  S.snap.army[3] = 2;
  S.snap.owner[4] = 1;
  S.snap.army[4] = 10;
  S.queue = [move(3, 4, true)];
  await tick();
  assert.equal(requests[0].body.action, move(3, 4, true).action);
});

test('queues paths beyond the former 24-move limit', () => {
  const { S, queueMove, elements } = client();
  for (let i = 0; i < 200; i++) queueMove(i % 2 === 0 ? 4 : 3);
  assert.equal(S.queue.length, 200);
  assert.equal(S.selected, 0);
  assert.equal(elements.get('queue').textContent, '200 moves queued');
});
