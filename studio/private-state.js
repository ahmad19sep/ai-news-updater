/* Same-origin private Studio transport. The server owns revisions and approval. */
(function () {
  "use strict";
  const clone = value => JSON.parse(JSON.stringify(value));
  const collections = ["candidates", "sources", "drafts", "settings", "runs"];
  const editable = collections.filter(coll => coll !== "runs");
  const unsafeKeys = ["__proto__", "constructor", "prototype"];
  const object = value => !!value && typeof value === "object" && !Array.isArray(value);
  const validId = id => typeof id === "string" && /^[A-Za-z0-9_-]{1,100}$/.test(id) && !unsafeKeys.includes(id);
  const revision = value => Number.isSafeInteger(value) && value >= 0;
  function safe(value, depth = 0) {
    if (depth > 64) throw new Error("Saved state is too deeply nested");
    if (value === null || typeof value === "string" || typeof value === "boolean") return;
    if (typeof value === "number" && Number.isFinite(value)) return;
    if (!value || typeof value !== "object") throw new Error("Invalid JSON value");
    for (const key of Object.keys(value)) {
      if (unsafeKeys.includes(key)) throw new Error("Unsafe saved state");
      safe(value[key], depth + 1);
    }
  }
  function canonical(value) {
    if (Array.isArray(value)) return value.map(canonical);
    if (object(value)) return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
    return value;
  }
  // Mirrors creator.contracts.content_fingerprint for display only. The server
  // remains the authority for the approval hash and the content revision.
  function material(record) {
    const pick = (name, fallback, defaultValue) => record[name] !== undefined ? record[name] : record[fallback] !== undefined ? record[fallback] : defaultValue;
    const result = {
      body: record.edited_post != null ? record.edited_post : pick("body", "post", ""),
      comment: record.edited_comment != null ? record.edited_comment : pick("source_comment", "first_comment", ""),
      hashtags: pick("hashtags", "hashtags", []), platform: pick("platform", "channel", "linkedin"),
      content_type: pick("content_type", "format", "text"), language: pick("language", "language", "en"),
    };
    for (const key of ["title", "url", "source", "candidate_id", "facts", "angle", "claims", "claim_refs", "creator_note_refs",
      "story_id", "story_revision", "evidence", "evidence_revision", "evidence_pack_id", "evidence_pack_revision", "evidence_refs",
      "source_pack", "source_revision", "source_hash", "asset_refs", "asset_ids", "assets", "visual", "image_prompt"]) result[key] = record[key] === undefined ? null : record[key];
    return JSON.stringify(canonical(result));
  }
  function validateRecord(id, record) {
    if (!object(record) || record.id !== id || !revision(record._revision)) throw new Error("Invalid private record revision");
  }

  window.createPrivateStudio = function (options) {
    let csrf = "", confirmed = {}, pending = {}, sequence = 0, epoch = 0, loadSequence = 0;
    let recovery = [], preserveOriginal = false, storageMessage = "";
    const queues = new Map(), conflicts = new Map();
    const key = "studio_private_overrides", recoveryKey = key + "_recovery";
    let original = null;
    try {
      const savedRecovery = localStorage.getItem(recoveryKey);
      if (savedRecovery) {
        try {
          const parsed = JSON.parse(savedRecovery);
          if (!Array.isArray(parsed) || parsed.some(row => !object(row) || typeof row.raw !== "string" || typeof row.reason !== "string")) throw new Error("Invalid recovery backup");
          recovery = parsed;
        } catch (error) { recovery = [{ raw: savedRecovery, reason: "Previous recovery backup needs review" }]; }
      }
      original = localStorage.getItem(key);
      pending = JSON.parse(original || "{}"); safe(pending);
      if (!object(pending)) throw new Error("Invalid pending state");
      for (const [coll, records] of Object.entries(pending)) {
        if (!editable.includes(coll) || !object(records)) throw new Error("Invalid pending collection");
        for (const [id, row] of Object.entries(records)) {
          if (!validId(id) || !object(row) || !object(row.fields) || !object(row.versions) || !revision(row.expected_revision) || !Object.keys(row.fields).length) throw new Error("Invalid pending record");
          if (Object.keys(row.versions).length !== Object.keys(row.fields).length) throw new Error("Invalid pending field versions");
          for (const field of Object.keys(row.fields)) {
            const version = row.versions[field];
            if (!revision(version) || version >= Number.MAX_SAFE_INTEGER) throw new Error("Invalid pending field version");
            sequence = Math.max(sequence, version);
          }
          if (row.conflict !== undefined && typeof row.conflict !== "boolean") throw new Error("Invalid pending conflict");
        }
      }
    } catch (error) {
      pending = {};
      if (original !== null) {
        if (!recovery.some(row => row.raw === original)) recovery.push({ raw: original, reason: error.message });
        try { localStorage.setItem(recoveryKey, JSON.stringify(recovery)); }
        catch (backupError) { preserveOriginal = true; }
        options.onStatus("blocked", "The saved recovery data needs review. Export its preserved original value before replacing it.");
      } else {
        // Reading failed before we could inspect the old value. Do not replace
        // unknown recovery data if writes happen to be permitted later.
        preserveOriginal = true;
        storageMessage = "Browser storage is unavailable. Keep this page open and export unsaved edits.";
        options.onStatus("blocked", storageMessage);
      }
    }
    const hasPending = () => Object.values(pending).some(records => Object.keys(records).length);
    const persist = () => {
      if (preserveOriginal) { if (original !== null) storageMessage = "Recovery backup could not be stored. The original browser value is preserved; export recovery and pending edits."; return; }
      try { localStorage.setItem(key, JSON.stringify(pending)); storageMessage = ""; }
      catch (error) { storageMessage = "Browser storage is unavailable. Keep this page open and export unsaved edits."; }
    };
    const rowFor = (coll, id) => (pending[coll] || {})[id];
    function displayed(coll, id) {
      const saved = (confirmed[coll] || {})[id] || { id, _revision: 0 };
      const row = rowFor(coll, id), result = Object.assign({}, saved, row ? row.fields : {});
      if (coll === "drafts" && row) {
        if (["approved", "scheduled", "published"].includes(row.fields.status)) result.status = saved.status || "draft";
        if (material(saved) !== material(result) || row.fields.status === "draft") {
          result.approval = null;
          if (["approved", "scheduled"].includes(result.status)) result.status = "draft";
        }
        if (saved.status === "published") result.status = "published";
      }
      return result;
    }
    function emitRecord(coll, id) { if (csrf) options.onRecord(coll, id, clone(displayed(coll, id))); }
    function emitState() {
      if (!csrf) return;
      const state = clone(confirmed);
      for (const coll of collections) {
        state[coll] = state[coll] || {};
        for (const id of Object.keys(pending[coll] || {})) state[coll][id] = clone(displayed(coll, id));
      }
      options.onState(state);
    }
    function status() {
      if (conflicts.size) options.onStatus("conflict", "A newer saved version exists. Your edits are kept here for review.");
      else if (storageMessage) options.onStatus("blocked", storageMessage);
      else if (recovery.length) options.onStatus("blocked", "Original recovery data is preserved separately. Export it for review.");
      else options.onStatus(hasPending() ? "pending" : "saved", hasPending() ? "Pending edits on this device" : "Saved in your private workspace");
    }
    function adoptRecord(coll, id, record) {
      validateRecord(id, record);
      const current = (confirmed[coll] || {})[id];
      if (current && current._revision > record._revision) return false;
      confirmed[coll] = confirmed[coll] || {};
      confirmed[coll][id] = clone(record);
      const conflict = conflicts.get(coll + "/" + id);
      if (conflict) { conflict.current = clone(record); notifyConflicts(); }
      return true;
    }
    function notifyConflicts() { options.onConflict(clone(Array.from(conflicts.values()))); }
    async function jsonRequest(path, init = {}) {
      const response = await fetch("/api" + path, Object.assign({ credentials: "same-origin", cache: "no-store" }, init));
      const body = await response.json(); safe(body);
      if (!object(body)) throw new Error("Invalid private server response");
      return { response, body };
    }
    function locked(message) {
      epoch++; loadSequence++; csrf = ""; confirmed = {}; conflicts.clear();
      notifyConflicts(); options.onLock(); options.onStatus("locked", message || "Sign in to load your private workspace");
    }
    async function load() {
      const started = epoch, requestId = ++loadSequence;
      const stale = () => started !== epoch || requestId !== loadSequence;
      try {
        const login = await jsonRequest("/session");
        if (stale()) return false;
        if (!login.response.ok || !login.body.authenticated || typeof login.body.csrf_token !== "string" || !login.body.csrf_token) { locked(); return false; }
        csrf = login.body.csrf_token;
        const result = await jsonRequest("/state");
        if (stale()) return false;
        if (result.response.status === 401) { locked(); return false; }
        if (!result.response.ok) throw new Error(result.body.error || "Private state could not be loaded");
        if (result.body.schema_version !== 1) throw new Error("This state version needs a newer Studio");
        for (const coll of collections) {
          if (!object(result.body[coll])) throw new Error("Invalid private state collection");
          for (const [id, record] of Object.entries(result.body[coll])) {
            if (!validId(id)) throw new Error("Invalid private record ID");
            validateRecord(id, record);
          }
        }
        const previous = confirmed;
        confirmed = clone(result.body);
        for (const coll of collections) for (const [id, record] of Object.entries(confirmed[coll])) {
          const newer = (previous[coll] || {})[id];
          if (newer && newer._revision > record._revision) confirmed[coll][id] = newer;
        }
        for (const [coll, records] of Object.entries(pending)) for (const [id, row] of Object.entries(records)) {
          if (row.conflict) conflicts.set(coll + "/" + id, { collection: coll, id, current: clone((confirmed[coll] || {})[id] || { id, _revision: 0 }), error: "Review the newer saved version" });
        }
        emitState(); notifyConflicts(); status(); return true;
      } catch (error) { if (!stale()) options.onStatus("offline", error.message || "Private server unavailable; edits remain on this device"); return false; }
    }
    async function login(passcode) {
      const result = await jsonRequest("/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ passcode }) });
      if (!result.response.ok) throw new Error(result.body.error || "Sign in failed");
      return load();
    }
    async function save(coll, id, fields, baseRevision) {
      safe(fields);
      if (!editable.includes(coll) || !validId(id) || !object(fields) || !Object.keys(fields).length || sequence >= Number.MAX_SAFE_INTEGER || baseRevision !== undefined && !revision(baseRevision)) throw new Error("Invalid private edit");
      const previous = rowFor(coll, id), version = ++sequence;
      const captured = clone(fields);
      pending[coll] = pending[coll] || {};
      const row = pending[coll][id] = previous || { fields: {}, versions: {}, expected_revision: baseRevision === undefined ? ((confirmed[coll] || {})[id] || {})._revision || (((confirmed._deleted_revisions || {})[coll] || {})[id] || 0) : baseRevision };
      Object.assign(row.fields, captured);
      for (const field of Object.keys(captured)) row.versions[field] = version;
      persist(); emitRecord(coll, id);
      const recordKey = coll + "/" + id;
      const write = async () => {
        if (!csrf) { options.onStatus("locked", "Sign in before saving your private edits"); return false; }
        if (conflicts.has(recordKey)) { status(); return false; }
        const current = rowFor(coll, id);
        if (!current) return true;
        const started = epoch;
        options.onStatus("saving", "Saving privately…");
        try {
          const result = await jsonRequest("/records/" + coll + "/" + id, {
            method: "PATCH", headers: { "Content-Type": "application/json", "X-Studio-CSRF": csrf },
            body: JSON.stringify({ expected_revision: current.expected_revision, fields: captured }),
          });
          if (started !== epoch) return false;
          if (result.response.status === 401) { locked(); return false; }
          if (result.response.status === 409) {
            const incoming = object(result.body.current) && Object.keys(result.body.current).length ? result.body.current : { id, _revision: revision(result.body.deleted_revision) ? result.body.deleted_revision : 0, _deleted: true };
            adoptRecord(coll, id, incoming);
            conflicts.set(recordKey, { collection: coll, id, current: clone(confirmed[coll][id]), error: result.body.error });
            current.conflict = true; persist(); emitRecord(coll, id); status(); notifyConflicts(); return false;
          }
          if (!result.response.ok) {
            for (const field of Object.keys(captured)) {
              const saved = ((confirmed[coll] || {})[id] || {})[field];
              if (current.versions[field] === version && (["status", "scheduled_for", "published_at"].includes(field) || JSON.stringify(saved) === JSON.stringify(captured[field]))) { delete current.fields[field]; delete current.versions[field]; }
            }
            if (!Object.keys(current.fields).length) delete pending[coll][id];
            persist(); emitRecord(coll, id); options.onStatus("blocked", result.body.error || "This save was rejected"); return false;
          }
          validateRecord(id, result.body.record);
          const related = result.body.related_drafts || {};
          if (!object(related)) throw new Error("Invalid related drafts");
          for (const [draftId, draft] of Object.entries(related)) { if (!validId(draftId)) throw new Error("Invalid related draft ID"); validateRecord(draftId, draft); }
          adoptRecord(coll, id, result.body.record);
          for (const [draftId, draft] of Object.entries(related)) { adoptRecord("drafts", draftId, draft); emitRecord("drafts", draftId); }
          for (const field of Object.keys(captured)) if (current.versions[field] === version) { delete current.fields[field]; delete current.versions[field]; }
          if (!Object.keys(current.fields).length) delete pending[coll][id];
          else current.expected_revision = result.body.record._revision;
          persist(); emitRecord(coll, id); status(); return true;
        } catch (error) { if (started === epoch) options.onStatus("offline", "Private save could not be confirmed. Your edits remain available for export on this device."); return false; }
      };
      const task = (queues.get(recordKey) || Promise.resolve()).then(write, write);
      queues.set(recordKey, task);
      return task;
    }
    async function retryPending() {
      for (const [coll, records] of Object.entries(clone(pending))) for (const [id, row] of Object.entries(records)) {
        if (!conflicts.has(coll + "/" + id)) await save(coll, id, row.fields);
      }
    }
    async function resolve(coll, id, choice) {
      if (choice !== "saved" && choice !== "local") throw new Error("Choose a saved or local version");
      const recordKey = coll + "/" + id, conflict = conflicts.get(recordKey);
      if (!conflict) return;
      if (!csrf) return false;
      adoptRecord(coll, id, conflict.current);
      conflicts.delete(recordKey);
      if (choice === "saved") { delete pending[coll][id]; persist(); emitRecord(coll, id); }
      else {
        const row = rowFor(coll, id);
        row.expected_revision = confirmed[coll][id]._revision; delete row.conflict;
        await save(coll, id, clone(row.fields));
      }
      notifyConflicts(); status();
    }
    async function logout() {
      if (hasPending()) { options.onStatus("blocked", "Finish saving or export and review pending edits before signing out."); return false; }
      if (!csrf) { locked(); return true; }
      try {
        const result = await jsonRequest("/session", { method: "DELETE", headers: { "X-Studio-CSRF": csrf } });
        if (!result.response.ok && result.response.status !== 401) { options.onStatus("blocked", "Sign out failed; your session is still open."); return false; }
        pending = {};
        let cleanupFailed = false;
        try { if (!preserveOriginal) localStorage.removeItem(key); } catch (error) { cleanupFailed = true; }
        locked(cleanupFailed ? "Signed out. Browser recovery storage could not be cleared." : undefined); return true;
      } catch (error) { options.onStatus("offline", "Sign out could not be confirmed. Retry when the private server is available."); return false; }
    }
    return { load, login, save, retryPending, resolve, logout, hasPending, pending: () => clone(pending), pendingRecovery: () => clone(recovery) };
  };
})();
