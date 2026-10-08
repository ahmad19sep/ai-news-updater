/* Offline transport regressions; node private_studio_test.js. No dependencies. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { test } = require("node:test");
const vm = require("node:vm");

const code = fs.readFileSync(path.join(__dirname, "studio", "private-state.js"), "utf8");
const KEY = "studio_private_overrides", BACKUP = KEY + "_recovery";
const copy = value => JSON.parse(JSON.stringify(value));
const turn = () => new Promise(resolve => setImmediate(resolve));
const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => copy(body) });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
const initialState = () => ({ schema_version: 1, candidates: {}, sources: {}, drafts: {
  a: { id: "a", _revision: 1, revision: 1, post: "Original post", first_comment: "Original source", hashtags: ["#ai"], status: "draft" },
}, settings: {}, runs: {} });

function harness({ seed = {}, storageFailures = {}, authenticated = true } = {}) {
  const memory = new Map(Object.entries(seed));
  const calls = [], records = [], states = [], statuses = [], conflicts = [];
  const app = { state: initialState(), authenticated, offline: false, patches: null, stateRequest: null, lockCount: 0 };
  const context = {
    window: {}, localStorage: {
      getItem(key) { if (storageFailures.get) throw new Error("Unavailable"); return memory.get(key) || null; },
      setItem(key, value) { if (storageFailures.set || (storageFailures.backup && key === BACKUP)) throw new Error("Quota"); memory.set(key, value); },
      removeItem(key) { if (storageFailures.remove) throw new Error("Unavailable"); memory.delete(key); },
    },
    fetch: async (url, options = {}) => {
      const call = { url, options: copy(options) }; calls.push(call);
      if (app.offline) throw new Error("Offline");
      if (url === "/api/session") {
        if (options.method === "POST") {
          if (JSON.parse(options.body).passcode !== "test-owner-code") return response({ error: "Bad code" }, 401);
          app.authenticated = true;
        } else if (options.method === "DELETE") {
          assert.equal(options.headers["X-Studio-CSRF"], "csrf-owner-token"); app.authenticated = false;
        }
        return response({ authenticated: app.authenticated, csrf_token: app.authenticated ? "csrf-owner-token" : null });
      }
      if (url === "/api/state") return app.stateRequest ? app.stateRequest(call) : response(app.state, app.authenticated ? 200 : 401);
      if (url.startsWith("/api/records/")) {
        assert.equal(options.method, "PATCH");
        assert.equal(options.headers["X-Studio-CSRF"], "csrf-owner-token");
        if (!app.authenticated) return response({ error: "Sign in" }, 401);
        if (app.patches) return app.patches(call);
        const [, , , coll, id] = url.split("/");
        const data = JSON.parse(options.body), before = app.state[coll][id] || { id, _revision: 0 };
        if (before._revision !== data.expected_revision) return response({ error: "Changed elsewhere", current: before }, 409);
        const record = { ...before, ...data.fields, _revision: before._revision + 1 };
        app.state[coll][id] = record;
        return response({ record, related_drafts: {} });
      }
      throw new Error("Unexpected request: " + url);
    },
  };
  vm.runInNewContext(code, context, { filename: "private-state.js" });
  const client = context.window.createPrivateStudio({
    onStatus: (state, message) => statuses.push({ state, message }),
    onState: state => states.push(copy(state)), onRecord: (coll, id, record) => records.push({ coll, id, record: copy(record) }),
    onLock: () => { app.lockCount++; }, onConflict: rows => conflicts.push(copy(rows)),
  });
  return { client, app, memory, calls, records, states, statuses, conflicts, storageFailures,
    lastRecord: (coll = "drafts", id = "a") => records.filter(row => row.coll === coll && row.id === id).at(-1)?.record };
}

test("private login and writes use same-origin cookies and session CSRF", async () => {
  const h = harness({ authenticated: false });
  assert.equal(await h.client.load(), false);
  assert.equal(h.states.length, 0);
  assert.equal(h.app.lockCount, 1);
  assert.equal(await h.client.save("drafts", "a", { edited_post: "Kept while locked" }), false);
  assert.equal(h.records.length, 0);
  assert.equal(h.calls.some(call => call.options.method === "PATCH"), false);
  await assert.rejects(h.client.login("incorrect"), /Bad code/);
  assert.equal(await h.client.login("test-owner-code"), true);
  await h.client.retryPending();
  // Work created while locked had no authoritative base revision. It must be
  // explicitly reconciled rather than silently overwriting the existing draft.
  await h.client.resolve("drafts", "a", "local");
  assert.equal(h.client.hasPending(), false);
  const patch = h.calls.find(call => call.options.method === "PATCH");
  assert.equal(patch.options.headers["X-Studio-CSRF"], "csrf-owner-token");
  assert.equal(patch.options.credentials, "same-origin");
  assert.equal(patch.options.cache, "no-store");
});

test("offline edits remain in browser storage and retry against their original revision", async () => {
  const h = harness(); await h.client.load(); h.app.offline = true;
  assert.equal(await h.client.save("drafts", "a", { edited_post: "Offline owner text" }), false);
  assert.equal(h.client.pending().drafts.a.fields.edited_post, "Offline owner text");
  assert.equal(JSON.parse(h.memory.get(KEY)).drafts.a.expected_revision, 1);
  h.app.offline = false;
  await h.client.retryPending();
  assert.equal(h.app.state.drafts.a.edited_post, "Offline owner text");
  assert.equal(h.client.hasPending(), false);
});

test("conflict resolution requires an explicit local or saved choice", async () => {
  const h = harness(); await h.client.load();
  h.app.state.drafts.a = { ...h.app.state.drafts.a, _revision: 2, post: "Other device text" };
  assert.equal(await h.client.save("drafts", "a", { edited_post: "My text" }), false);
  assert.equal(h.conflicts.at(-1)[0].current.post, "Other device text");
  const patchCount = h.calls.filter(call => call.options.method === "PATCH").length;
  await h.client.retryPending();
  assert.equal(h.calls.filter(call => call.options.method === "PATCH").length, patchCount);
  await assert.rejects(h.client.resolve("drafts", "a", "unknown"), /Choose/);
  await h.client.resolve("drafts", "a", "local");
  assert.equal(h.app.state.drafts.a._revision, 3);
  assert.equal(h.app.state.drafts.a.edited_post, "My text");
  h.app.state.drafts.a = { ...h.app.state.drafts.a, _revision: 4, edited_post: "New saved text" };
  await h.client.save("drafts", "a", { edited_post: "Discarded after explicit choice" });
  await h.client.resolve("drafts", "a", "saved");
  assert.equal(h.client.hasPending(), false);
  assert.equal(h.lastRecord().edited_post, "New saved text");
});

test("restored conflict data stays blocked until reviewed instead of retrying automatically", async () => {
  const pending = { drafts: { a: { fields: { edited_post: "Unsaved local" }, versions: { edited_post: 7 }, expected_revision: 1, conflict: true } } };
  const h = harness({ seed: { [KEY]: JSON.stringify(pending) } });
  h.app.state.drafts.a._revision = 2;
  await h.client.load(); await h.client.retryPending();
  assert.equal(h.calls.some(call => call.options.method === "PATCH"), false);
  assert.equal(h.conflicts.at(-1)[0].current._revision, 2);
  await h.client.resolve("drafts", "a", "local");
  assert.equal(h.client.hasPending(), false);
});

test("an older save acknowledgement cannot replace a newer loaded record", async () => {
  const h = harness(); await h.client.load(); const ack = deferred();
  h.app.patches = () => ack.promise;
  const saving = h.client.save("drafts", "a", { edited_post: "Own accepted revision" }); await turn();
  h.app.state.drafts.a = { ...h.app.state.drafts.a, _revision: 3, revision: 3, edited_post: "Newer other-device revision" };
  await h.client.load();
  ack.resolve(response({ record: { ...initialState().drafts.a, _revision: 2, revision: 2, edited_post: "Own accepted revision" } }));
  assert.equal(await saving, true);
  assert.equal(h.lastRecord()._revision, 3);
  assert.equal(h.lastRecord().edited_post, "Newer other-device revision");
  assert.equal(h.client.hasPending(), false);
});

test("an early acknowledgement preserves later typing and serializes the next conditional write", async () => {
  const h = harness(); await h.client.load(); const first = deferred(), second = deferred(); let count = 0;
  h.app.patches = () => (++count === 1 ? first.promise : second.promise);
  const older = h.client.save("drafts", "a", { edited_post: "Earlier typing" }); await turn();
  const newer = h.client.save("drafts", "a", { edited_post: "Later typing" });
  first.resolve(response({ record: { ...initialState().drafts.a, _revision: 2, edited_post: "Earlier typing" } }));
  assert.equal(await older, true); await turn();
  assert.equal(h.client.pending().drafts.a.fields.edited_post, "Later typing");
  assert.equal(h.lastRecord().edited_post, "Later typing");
  const request = h.calls.filter(call => call.options.method === "PATCH").at(-1);
  assert.equal(JSON.parse(request.options.body).expected_revision, 2);
  second.resolve(response({ record: { ...initialState().drafts.a, _revision: 3, edited_post: "Later typing" } }));
  assert.equal(await newer, true);
  assert.equal(h.client.hasPending(), false);
});

test("source-related acknowledgement cannot regress a newer draft revision", async () => {
  const h = harness(); h.app.state.sources.s = { id: "s", _revision: 1, excerpt: "Original evidence" };
  await h.client.load(); const ack = deferred(); h.app.patches = () => ack.promise;
  const saving = h.client.save("sources", "s", { excerpt: "Updated evidence" }); await turn();
  h.app.state.drafts.a = { ...h.app.state.drafts.a, _revision: 5, edited_post: "Newer owner draft" };
  await h.client.load();
  ack.resolve(response({ record: { id: "s", _revision: 2, excerpt: "Updated evidence" }, related_drafts: {
    a: { ...initialState().drafts.a, _revision: 4, evidence_revision: 2 },
  } }));
  await saving;
  assert.equal(h.lastRecord()._revision, 5);
  assert.equal(h.lastRecord().edited_post, "Newer owner draft");
});

test("pending material changes remove approval while published history stays published", async () => {
  const h = harness(); const approval = { revision: 1, content_hash: "manual-marker" };
  h.app.state.drafts.a = { ...h.app.state.drafts.a, status: "scheduled", approval };
  await h.client.load(); h.app.offline = true;
  await h.client.save("drafts", "a", { edited_post: "Unreviewed new words" });
  assert.equal(h.lastRecord().status, "draft");
  assert.equal(h.lastRecord().approval, null);
  h.app.offline = false; h.app.state.drafts.a.status = "published"; h.app.state.drafts.a.published_at = "2026-10-08T10:00:00+05:00";
  await h.client.load();
  assert.equal(h.states.at(-1).drafts.a.status, "published");
  assert.equal(h.states.at(-1).drafts.a.published_at, "2026-10-08T10:00:00+05:00");
  assert.equal(h.states.at(-1).drafts.a.approval, null);
});

test("approval and publication state actions wait for server acknowledgement and reject cleanly", async () => {
  const h = harness(); await h.client.load(); const ack = deferred(); h.app.patches = () => ack.promise;
  const saving = h.client.save("drafts", "a", { status: "approved" }); await turn();
  assert.equal(h.lastRecord().status, "draft");
  ack.resolve(response({ error: "Blocking checks remain" }, 422));
  assert.equal(await saving, false);
  assert.equal(h.lastRecord().status, "draft");
  assert.equal(h.client.hasPending(), false);
  h.app.patches = async () => response({ error: "Invalid fields" }, 422);
  await h.client.save("drafts", "a", { edited_post: "Owner work worth preserving", status: "published" });
  assert.equal(h.client.pending().drafts.a.fields.edited_post, "Owner work worth preserving");
  assert.equal(h.client.pending().drafts.a.fields.status, undefined);
  assert.equal(h.lastRecord().status, "draft");
});

test("invalid saved recovery bytes survive a new save and are exportable", async () => {
  const original = '{"drafts":{"a":{"fields":{"post":"Owner work"}}}}';
  const h = harness({ seed: { [KEY]: original } });
  assert.equal(h.client.pendingRecovery()[0].raw, original);
  assert.equal(JSON.parse(h.memory.get(BACKUP))[0].raw, original);
  await h.client.load(); await h.client.save("drafts", "a", { edited_post: "New safe work" });
  assert.equal(JSON.parse(h.memory.get(BACKUP))[0].raw, original);
  const restarted = harness({ seed: Object.fromEntries(h.memory) });
  assert.equal(restarted.client.pendingRecovery()[0].raw, original);
});

test("failed recovery backup cannot cause the original invalid cache to be overwritten", async () => {
  const original = 'unfinished owner work {"post":"text"';
  const h = harness({ seed: { [KEY]: original }, storageFailures: { backup: true } });
  await h.client.load(); h.app.offline = true;
  await h.client.save("drafts", "a", { edited_post: "New work in memory" });
  assert.equal(h.memory.get(KEY), original);
  assert.equal(h.client.pendingRecovery()[0].raw, original);
  assert.equal(h.client.pending().drafts.a.fields.edited_post, "New work in memory");
});

test("unreadable browser recovery storage is never blindly replaced by new edits", async () => {
  const original = "Old inaccessible owner recovery value";
  const h = harness({ seed: { [KEY]: original }, storageFailures: { get: true } });
  await h.client.load(); h.app.offline = true;
  await h.client.save("drafts", "a", { edited_post: "New owner work" });
  assert.equal(h.memory.get(KEY), original);
  assert.equal(h.client.pending().drafts.a.fields.edited_post, "New owner work");
});

test("logout clears private callbacks even when browser cleanup fails", async () => {
  const h = harness({ storageFailures: { remove: true } }); await h.client.load();
  assert.equal(await h.client.logout(), true);
  assert.equal(h.app.authenticated, false);
  assert.equal(h.app.lockCount, 1);
  assert.equal(h.statuses.at(-1).state, "locked");
  assert.match(h.statuses.at(-1).message, /could not be cleared/);
  assert.equal(await h.client.save("drafts", "a", { edited_post: "Locked local work" }), false);
  assert.equal(h.records.length, 0);
});

test("session expiration and late write responses cannot restore locked private data", async () => {
  const h = harness(); await h.client.load(); const ack = deferred(); h.app.patches = () => ack.promise;
  const saving = h.client.save("drafts", "a", { edited_post: "Queued owner text" }); await turn();
  h.app.authenticated = false; assert.equal(await h.client.load(), false);
  const emitted = h.records.length;
  ack.resolve(response({ record: { ...initialState().drafts.a, _revision: 2, edited_post: "Queued owner text" } }));
  assert.equal(await saving, false);
  assert.equal(h.records.length, emitted);
  assert.equal(h.app.lockCount, 1);
  assert.equal(h.client.hasPending(), true);
  assert.equal(await h.client.logout(), false);
});

test("locked debounce capture preserves the original server revision without rebasing existing pending work", async () => {
  const h = harness(); await h.client.load();
  const originalRevision = h.states.at(-1).drafts.a._revision;
  h.app.authenticated = false; await h.client.load();
  assert.equal(await h.client.save("drafts", "a", { edited_post: "Last keystrokes before expiry" }, originalRevision), false);
  assert.equal(h.client.pending().drafts.a.expected_revision, 1);
  assert.equal(h.records.length, 0);
  await h.client.save("drafts", "a", { edited_comment: "Newer buffered source comment" }, 99);
  assert.equal(h.client.pending().drafts.a.expected_revision, 1);
  for (const invalid of [true, -1, 1.5, Number.MAX_SAFE_INTEGER + 1]) await assert.rejects(h.client.save("drafts", "a", { post: "Unsafe base" }, invalid));
  assert.equal(await h.client.login("test-owner-code"), true);
  await h.client.retryPending();
  assert.equal(h.client.hasPending(), false);
  assert.equal(h.app.state.drafts.a.edited_post, "Last keystrokes before expiry");
  assert.equal(h.app.state.drafts.a.edited_comment, "Newer buffered source comment");
});

test("a late state response cannot restore a workspace after logout", async () => {
  const h = harness(); await h.client.load(); const state = deferred(); h.app.stateRequest = () => state.promise;
  const loading = h.client.load(); await turn();
  assert.equal(await h.client.logout(), true);
  const emissions = h.states.length;
  state.resolve(response(initialState()));
  assert.equal(await loading, false);
  assert.equal(h.states.length, emissions);
});

test("a deleted record can be explicitly reconciled using its deletion revision", async () => {
  const h = harness(); await h.client.load();
  h.app.patches = () => response({error:"Deleted elsewhere", current:{}, deleted_revision:2}, 409);
  assert.equal(await h.client.save("drafts", "a", {edited_post:"Recovered owner text"}), false);
  assert.equal(h.conflicts.at(-1)[0].current._revision, 2);
  assert.equal(h.conflicts.at(-1)[0].current._deleted, true);
  h.app.patches = call => {
    const data = JSON.parse(call.options.body);
    assert.equal(data.expected_revision, 2);
    return response({record:{id:"a", _revision:3, post:"", edited_post:data.fields.edited_post, status:"draft"}});
  };
  await h.client.resolve("drafts", "a", "local");
  assert.equal(h.client.hasPending(), false);
  assert.equal(h.lastRecord().edited_post, "Recovered owner text");
  assert.equal(h.lastRecord()._deleted, undefined);
});

test("a new save after loading a deletion uses the preserved generation", async () => {
  const h = harness();
  h.app.state.drafts = {};
  h.app.state._deleted_revisions = {drafts:{a:4}};
  await h.client.load();
  h.app.patches = call => {
    const data = JSON.parse(call.options.body);
    assert.equal(data.expected_revision, 4);
    return response({record:{id:"a", _revision:5, post:data.fields.post, status:"draft"}});
  };
  assert.equal(await h.client.save("drafts", "a", {post:"New owner draft"}), true);
  assert.equal(h.lastRecord()._revision, 5);
});

test("prototype keys, unsupported state schemas and unsafe revisions never enter the view", async () => {
  const h = harness(); await h.client.load();
  for (const fields of [JSON.parse('{"__proto__":{"polluted":true}}'), { post: NaN }, [], {}, { post: undefined }]) {
    await assert.rejects(h.client.save("drafts", "a", fields));
  }
  await assert.rejects(h.client.save("runs", "a", { post: "No run writes" }));
  await assert.rejects(h.client.save("drafts", "__proto__", { post: "Bad ID" }));
  assert.equal(h.client.hasPending(), false);
  for (const state of [{ ...initialState(), schema_version: 2 }, { ...initialState(), drafts: [] },
    { ...initialState(), drafts: { a: { id: "a", _revision: true } } }]) {
    h.app.state = state;
    assert.equal(await h.client.load(), false);
  }
  assert.equal(h.states.length, 1);
});
