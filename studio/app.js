/* AI x Ahmad Studio — application (source; generate_studio.py inlines it).
   One Post record flows: candidate (Ideas) -> draft (Compose) -> scheduled
   (Schedule) -> published (Published). The agents (run_pipeline.py) fill the
   store; this page is where you decide, edit and post. Nothing posts itself. */
"use strict";

/* ================================================================ helpers */
const D = window.STUDIO_DATA;
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nowIso = () => new Date().toISOString();
function jload(k, fb) { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? fb : v; } catch (e) { return fb; } }
function jsave(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
function toast(msg, ms = 2600) { const t = $("#toast"); t.textContent = msg; t.classList.add("on"); clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("on"), ms); }
async function sha(algo, t) { const b = await crypto.subtle.digest(algo, new TextEncoder().encode(t)); return Array.from(new Uint8Array(b)).map(x => x.toString(16).padStart(2, "0")).join(""); }
const sha256 = t => sha("SHA-256", t);
function ago(d) {
  if (!d) return ""; const ms = Date.now() - new Date(d).getTime(); if (isNaN(ms)) return "";
  const h = ms / 36e5; if (h < 1) return Math.max(1, Math.round(ms / 6e4)) + "m"; if (h < 48) return Math.round(h) + "h"; return Math.round(h / 24) + "d";
}
function fmtDT(d) { if (!d) return ""; const x = new Date(d); if (isNaN(x)) return String(d); return x.toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }); }
function fmtD(d) { if (!d) return ""; const x = new Date(d); if (isNaN(x)) return String(d); return x.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }); }
function fmtT(d) { return new Date(d).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }); }
function toLocalInput(d) { const x = d ? new Date(d) : new Date(); const p = n => String(n).padStart(2, "0"); return `${x.getFullYear()}-${p(x.getMonth() + 1)}-${p(x.getDate())}T${p(x.getHours())}:${p(x.getMinutes())}`; }
function copy(text, msg) { navigator.clipboard.writeText(text).then(() => toast(msg || "Copied"), () => toast("Copy failed — select and copy manually")); }
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
const TOPIC_OF_PILLAR = { 1: "models", 2: "coding", 3: "society", 4: "society", 5: "politics_policy", 6: "science", 7: "science", 8: "health", 9: "science", 10: "other" };
const TOPIC_LABEL = { models: "Models", tools: "Tools", coding: "Coding", agents: "Agents", business: "Business", health: "Health", science: "Science", politics_policy: "Policy", security: "Security", education: "Education", society: "Society", other: "Other" };
const VERDICT_CHIP = { pass: "good", warn: "warn", fail: "bad", none: "plain" };
const STATUS_LABEL = { draft: "Draft", approved: "Approved", scheduled: "Scheduled", published: "Posted", rejected: "Rejected" };

/* Inline icon set (stroke, 24 viewBox). Kept tiny and consistent on purpose. */
const ICONS = {
  home: '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
  radar: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v4M12 17v4M3 12h4M17 12h4"/>',
  bulb: '<path d="M9 18h6"/><path d="M10 21h4"/><path d="M8.5 14.5A6 6 0 1 1 15.5 14.5c-.6.6-1 1.4-1 2.3H9.5c0-.9-.4-1.7-1-2.3Z"/>',
  pen: '<path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3Z"/><path d="m13.5 6.5 3 3"/>',
  calendar: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 4.5-5"/>',
  book: '<path d="M5 4h6a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H5Z"/><path d="M19 4h-6a3 3 0 0 0-3 3v13a2 2 0 0 1 2-2h7Z"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4"/>',
  star: '<path d="m12 3 2.7 5.6 6.1.8-4.5 4.3 1.1 6.1L12 17l-5.4 2.8 1.1-6.1L3.2 9.4l6.1-.8Z"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
  external: '<path d="M14 4h6v6"/><path d="M20 4 11 13"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>',
  disk: '<path d="M5 4h11l3 3v13H5Z"/><path d="M8 4v5h7V4"/><rect x="8" y="14" width="8" height="6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/>',
  warn: '<path d="M12 3 2 21h20Z"/><path d="M12 10v5M12 18h.01"/>',
  play: '<path d="M7 4v16l13-8Z"/>',
  message: '<path d="M4 5h16v11H9l-5 4Z"/>',
  search: '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',
};
const ic = (name, cls = "") => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;
const LI = '<span style="font:600 12px/1 Arial,sans-serif;letter-spacing:-.02em">in</span>';

/* ================================================================ lock + theme */
const LOCKHASH = D.lockHash || "";
const FBURL = (D.fbUrl || "").replace(/\/+$/, "");
let KEY = localStorage.getItem("boardkey") || "";
async function tryUnlock() {
  const code = $("#lockcode").value.trim();
  if (await sha256(code) === LOCKHASH) {
    localStorage.setItem("unlock", LOCKHASH);
    KEY = (await sha256("aixboard:" + code)).slice(0, 40);
    localStorage.setItem("boardkey", KEY);
    $("#lock").hidden = true;
    boot();
  } else { $("#lockerr").textContent = "That code is not right. Try again."; }
}
function applyTheme(dark) {
  document.body.classList.toggle("dark", dark);
  $("#themebtn").innerHTML = ic(dark ? "sun" : "moon");
  const m = $('meta[name="theme-color"]'); if (m) m.content = dark ? "#0e1018" : "#f3f4f9";
}
applyTheme(localStorage.getItem("theme") === "dark");
$("#themebtn").onclick = () => { const d = !document.body.classList.contains("dark"); localStorage.setItem("theme", d ? "dark" : "light"); applyTheme(d); };
$("#lockbtn").onclick = tryUnlock;
$("#lockcode").addEventListener("keydown", e => { if (e.key === "Enter") tryUnlock(); });
$$(".navitem[data-icon]").forEach(a => a.insertAdjacentHTML("afterbegin", ic(a.dataset.icon)));

/* ================================================================ state */
const S = { candidates: {}, sources: {}, drafts: {}, settings: {}, runs: {} };
let MODE = "file";                 // "firebase" when the baked-in URL + your key are present
let OVR = jload("studio_overrides", {});   // edits made on this device (also the offline queue)
let stream = null, loadedAt = null;
const fbRoot = () => `${FBURL}/studio/${KEY}`;
function setCloud(ok) {
  const b = $("#cloudbtn"); b.classList.toggle("off", !ok);
  b.title = MODE === "firebase" ? (ok ? "Live sync on" : "Sync problem: edits are kept on this device") : "Local mode: edits stay on this device";
  b.innerHTML = ic(MODE === "firebase" ? (ok ? "bolt" : "warn") : "disk");
}
function applyOverrides() {
  for (const coll of Object.keys(OVR)) for (const [id, fields] of Object.entries(OVR[coll] || {})) {
    const cur = S[coll][id] || { id };
    if (!cur.updated || String(fields.updated || "") >= String(cur.updated)) S[coll][id] = Object.assign({}, cur, fields);
  }
}
async function loadState() {
  let raw = null;
  if (FBURL && KEY) {
    MODE = "firebase";
    try { const r = await fetch(fbRoot() + ".json", { cache: "no-store" }); raw = r.ok ? await r.json() : null; setCloud(r.ok); } catch (e) { setCloud(false); }
    if (raw == null) { try { const r = await fetch("pipeline.json?v=" + D.cache, { cache: "no-store" }); if (r.ok) raw = await r.json(); } catch (e) {} }
  } else {
    MODE = "file"; setCloud(true);
    try { const r = await fetch("pipeline.json?v=" + D.cache, { cache: "no-store" }); if (r.ok) raw = await r.json(); } catch (e) {}
  }
  raw = raw || {};
  for (const c of Object.keys(S)) S[c] = (raw[c] && typeof raw[c] === "object") ? Object.assign({}, raw[c]) : {};
  applyOverrides();
  loadedAt = new Date();
  if (MODE === "firebase") { flushOverrides(); startStream(); }
}
async function flushOverrides() {          /* push edits made while offline */
  for (const coll of Object.keys(OVR)) for (const [id, fields] of Object.entries(OVR[coll] || {})) {
    try { const r = await fetch(`${fbRoot()}/${coll}/${id}.json`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(fields) }); if (r.ok) { delete OVR[coll][id]; } } catch (e) { return; }
  }
  jsave("studio_overrides", OVR);
}
function startStream() {
  if (stream || !FBURL) return;
  try {
    stream = new EventSource(fbRoot() + ".json");
    const refresh = debounce(async () => { const before = JSON.stringify(S); await loadStateQuiet(); if (JSON.stringify(S) !== before) rerender(); }, 800);
    stream.addEventListener("put", e => { if (!e.data || e.data === "null") return; refresh(); });
    stream.addEventListener("patch", refresh);
    stream.onerror = () => setCloud(false);
  } catch (e) { stream = null; }
}
async function loadStateQuiet() {
  try { const r = await fetch(fbRoot() + ".json", { cache: "no-store" }); if (!r.ok) return; const raw = await r.json() || {}; for (const c of Object.keys(S)) S[c] = (raw[c] && typeof raw[c] === "object") ? Object.assign({}, raw[c]) : {}; applyOverrides(); setCloud(true); } catch (e) { setCloud(false); }
}
async function patchDoc(coll, id, fields, quiet) {
  fields = Object.assign({}, fields, { updated: nowIso() });
  S[coll][id] = Object.assign({}, S[coll][id] || { id }, fields);
  OVR[coll] = OVR[coll] || {}; OVR[coll][id] = Object.assign({}, OVR[coll][id] || {}, fields); jsave("studio_overrides", OVR);
  if (MODE === "firebase") {
    try {
      const r = await fetch(`${fbRoot()}/${coll}/${id}.json`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(fields) });
      setCloud(r.ok); if (r.ok) { delete OVR[coll][id]; jsave("studio_overrides", OVR); }
    } catch (e) { setCloud(false); }
  }
  if (!quiet) rerender();
}
const settings = () => S.settings.profile || {};
const slots = () => (settings().slots && settings().slots.length) ? settings().slots : ["Tue 09:00", "Wed 09:00", "Thu 09:00", "Sat 11:00"];
const target = () => Number(settings().postsPerWeek) || 4;
const drafts = f => Object.values(S.drafts).filter(f || (() => true));
const cands = f => Object.values(S.candidates).filter(f || (() => true));
const postOf = d => (d.edited_post != null ? d.edited_post : d.post) || "";
const commentOf = d => (d.edited_comment != null ? d.edited_comment : d.first_comment) || "";
const byScore = (a, b) => (b.score || 0) - (a.score || 0) || String(b.published || "").localeCompare(String(a.published || ""));
const byCreated = (a, b) => String(b.created || "").localeCompare(String(a.created || ""));
function weekStart() { const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d; }
const postedThisWeek = () => drafts(d => d.status === "published" && new Date(d.published_at || d.updated) >= weekStart()).length;
function lastRun() { const r = Object.values(S.runs).sort((a, b) => String(b.ts).localeCompare(String(a.ts))); return r[0]; }
const verdictOf = d => (d.verify || {}).verdict || "none";
const candUrl = c => c.resolved_url || c.url;

/* ================================================================ client-side checks (mirror of agents/verify.py) */
const BANNED = ["game changer", "game-changer", "gamechanger", "revolutionise", "revolutionize", "unlock the power", "unlock value", "next big thing", "cutting-edge", "cutting edge", "seamless", "transformative", "in today's world", "the future is here", "ai is changing everything", "disrupt every industry", "paradigm shift", "landscape", "delve", "dive in", "deep dive", "supercharge", "elevate", "testament", "underscore", "leverage", "harness", "robust", "buckle up", "let that sink in", "mind-blowing", "follow me for more", "comment yes", "tag someone", "agree?"];
const PATTERNS = [[/\bit'?s not (just|only) [^.\n]{2,60}, it'?s\b/i, "'It's not just X, it's Y' pattern", "warn"], [/\bthe real [^.\n]{2,40} isn'?t [^.\n]{2,60}, it'?s\b/i, "'The real X isn't Y, it's Z' pattern", "warn"], [/\bhere'?s the thing\b/i, "'Here's the thing' opener", "warn"], [/\bat the end of the day\b/i, "'At the end of the day' closer", "warn"], [/\blink in (the )?(comments|bio)\b/i, "'link in comments' bait", "fail"], [/\bin a (major|significant|big) (development|move|step)\b/i, "press-release opener", "warn"]];
const NUM_RE = /(?<![\w.])(\$?\d[\d,]*(?:\.\d+)?)\s?(%|percent|million|billion|trillion|k\b|x\b|bn\b|m\b|b\b)?/gi;
function numbersIn(text) {
  const out = new Set(); let m; NUM_RE.lastIndex = 0;
  while ((m = NUM_RE.exec(text || ""))) { const num = m[1].replace(/,/g, "").replace(/^\$/, ""); let u = (m[2] || "").toLowerCase().replace(/\.$/, ""); u = { percent: "%", bn: "billion", m: "million", b: "billion" }[u] || u; out.add(num + u); out.add(num); }
  return out;
}
function checkPost(post, pack, allowedText, hashtags) {
  const issues = []; post = post || ""; const hook = post.trim().split("\n")[0].trim();
  const add = (level, code, msg) => issues.push({ level, code, msg });
  const src = [pack.title, pack.feed_summary, pack.excerpt, (pack.quotes || []).join(" "), allowedText || ""].join(" ");
  const allowed = numbersIn(src);
  for (const tok of Array.from(numbersIn(post)).sort()) { const base = tok.replace(/[^\d.]/g, ""); if (allowed.has(tok) || allowed.has(base) || /^(19|20)\d\d$/.test(base) || ["1", "2", "3"].includes(base)) continue; add("fail", "number", `'${tok}' is not in the source material`); }
  const low = post.toLowerCase(); for (const ph of BANNED) if (low.includes(ph)) add("fail", "banned", `banned phrase: '${ph}'`);
  for (const [re, label, lv] of PATTERNS) if (re.test(post)) add(lv, "pattern", label);
  if (hook.length > 210) add("fail", "hook", `hook is ${hook.length} chars; cut at ~210 on desktop`); else if (hook.length > 140) add("warn", "hook", `hook is ${hook.length} chars; mobile preview cuts at ~140`);
  if (post.length > 3000) add("fail", "length", `${post.length} chars exceeds LinkedIn's 3000 limit`); else if (post.length && post.length < 400) add("warn", "length", `only ${post.length} chars — short for LinkedIn`);
  const tags = hashtags != null ? hashtags : (post.match(/#\w+/g) || []); if (tags.length > 3) add("fail", "hashtags", `${tags.length} hashtags (max 3)`);
  if (/https?:\/\/\S+|www\.\S+/i.test(post)) add("warn", "link", "a link in the body reduces reach — keep it in the first comment");
  if (/(\*\*|__|^#{1,6}\s)/m.test(post)) add("fail", "markdown", "markdown does not render on LinkedIn");
  const verdict = issues.some(i => i.level === "fail") ? "fail" : issues.length ? "warn" : "pass";
  return { issues, verdict, hook, hookLen: hook.length, chars: post.length };
}

/* ================================================================ router */
const SCREENS = { today: ["Today", "Your desk at a glance"], discover: ["Discover", "Everything the radar collected. Save what deserves a post."], ideas: ["Ideas", "Triage picks and your own saves. Shortlist what to write next."], compose: ["Compose", "Write and edit in your voice, check it, approve."], schedule: ["Schedule", "Approved posts on your slots. You post them; the studio reminds you."], published: ["Published", "What went out, how it did, what to reuse."], library: ["Library", "Hooks, rules, voice and examples the writer uses."], settings: ["Settings", "Personal note, slots, channels, sync."] };
let CUR = "today";
function go(name) { if (!SCREENS[name]) name = "today"; CUR = name; if (location.hash !== "#" + name) history.replaceState(null, "", "#" + name); rerender(); window.scrollTo(0, 0); }
window.addEventListener("hashchange", () => go(location.hash.slice(1) || "today"));
function rerender() {
  $$(".screen").forEach(s => s.hidden = s.id !== "s-" + CUR);
  $$(".navitem").forEach(n => n.classList.toggle("active", n.dataset.screen === CUR));
  $("#pageTitle").textContent = SCREENS[CUR][0]; $("#pageSub").textContent = SCREENS[CUR][1];
  navCounts();
  ({ today: renderToday, discover: renderDiscover, ideas: renderIdeas, compose: renderCompose, schedule: renderSchedule, published: renderPublished, library: renderLibrary, settings: renderSettings })[CUR]();
}
function navCounts() {
  $("#nc-ideas").textContent = cands(c => c.status === "new").length || "";
  $("#nc-compose").textContent = drafts(d => d.status === "draft").length || "";
  $("#nc-schedule").textContent = drafts(d => d.status === "scheduled").length || "";
}
window.go = go;

/* ================================================================ shared renderers */
const panel = (title, body, sub = "", extra = "") => `<div class="panel"><div class="ph"><h3>${title}</h3><span class="sp">${sub}${extra}</span></div>${body}</div>`;
const emptyBox = (t, s = "") => `<div class="empty"><b>${esc(t)}</b>${esc(s)}</div>`;
function draftRow(d, opts = {}) {
  const v = verdictOf(d); const p = postOf(d);
  const due = d.status === "scheduled" && new Date(d.scheduled_for) <= new Date();
  return `<div class="item ${v} ${due ? "due" : ""}">
    <div class="lead"><span class="chip ${VERDICT_CHIP[v]}">${v === "none" ? "manual" : v}</span></div>
    <div class="body">
      <div class="t"><a href="#compose" onclick="openDraft('${d.id}');return false">${esc(d.title)}</a></div>
      <div class="meta"><span>${esc(TOPIC_LABEL[d.topic] || d.topic || "")}</span><span>·</span><span>${esc(d.source || "")}</span>${d.thin_source ? '<span>·</span><span class="chip warn plain">thin source</span>' : ""}${d.scheduled_for ? `<span>·</span><span class="mono">${esc(fmtDT(d.scheduled_for))}</span>` : ""}</div>
      ${p ? `<div class="why">${esc(p.split("\n")[0].slice(0, 150))}</div>` : ""}
    </div>
    <div class="acts">${opts.extra || ""}<button class="btn sm" onclick="openDraft('${d.id}')">Open</button></div></div>`;
}
function candActions(c) {
  const st = c.status; const a = [];
  if (st === "new" || st === "shortlisted") a.push(`<button class="btn sm primary" onclick="manualDraft('${c.id}')">${ic("pen")}Write</button>`);
  if (st !== "shortlisted") a.push(`<button class="btn sm icon" title="Shortlist" aria-label="Shortlist" onclick="setCand('${c.id}','shortlisted')">${ic("star")}</button>`);
  if (st === "shortlisted") { if (D.mode === "api") a.push(`<button class="btn sm" title="Copy the command that drafts this with the Claude API" onclick="draftCmd('${c.id}')">Draft with API</button>`); a.push(`<button class="btn sm icon" title="Back to new" aria-label="Back to new" onclick="setCand('${c.id}','new')">${ic("undo")}</button>`); }
  if (st !== "dismissed") a.push(`<button class="btn sm icon" title="Dismiss" aria-label="Dismiss" onclick="setCand('${c.id}','dismissed')">${ic("x")}</button>`); else a.push(`<button class="btn sm icon" title="Restore" aria-label="Restore" onclick="setCand('${c.id}','new')">${ic("undo")}</button>`);
  return a.join("");
}
function candRow(c) {
  return `<div class="item">
    <div class="lead"><span class="score ${c.score >= 8 ? "hi" : ""}">${c.score || "–"}</span></div>
    <div class="body">
      <div class="t"><a href="${esc(candUrl(c))}" target="_blank" rel="noopener">${esc(c.title)}</a></div>
      <div class="meta"><span>${esc(TOPIC_LABEL[c.topic] || c.topic || "")}</span><span>·</span><span>${esc(c.source || "")}</span><span>·</span><span class="mono">${esc(ago(c.published))}</span>${c.urgency === "today" ? '<span class="chip accent plain">today</span>' : ""}${c.manual ? '<span class="chip purple plain">saved by you</span>' : ""}${c.source_ok ? '<span class="chip good plain">article fetched</span>' : ""}</div>
      ${c.reason ? `<div class="why">${esc(c.reason)}${c.angle_hint ? ` — ${esc(c.angle_hint)}` : ""}</div>` : ""}
    </div>
    <div class="acts">${candActions(c)}</div></div>`;
}
function candCard(c) {
  return `<div class="kcard">
    <div class="top"><span class="score ${c.score >= 8 ? "hi" : ""}">${c.score || "–"}</span><span class="src">${esc(c.source || "")}</span><span class="age">${esc(ago(c.published))}</span></div>
    <div class="t"><a href="${esc(candUrl(c))}" target="_blank" rel="noopener">${esc(c.title)}</a></div>
    <div class="row" style="gap:4px"><span class="chip plain">${esc(TOPIC_LABEL[c.topic] || c.topic || "")}</span>${c.urgency === "today" ? '<span class="chip accent plain">today</span>' : ""}${c.manual ? '<span class="chip purple plain">saved by you</span>' : ""}${c.source_ok ? '<span class="chip good plain">article</span>' : ""}${c.duplicate_of ? '<span class="chip plain">duplicate</span>' : ""}</div>
    ${c.reason ? `<div class="why" style="margin-top:6px">${esc(c.reason)}</div>` : ""}
    <div class="acts">${candActions(c)}</div></div>`;
}
window.setCand = (id, status) => { patchDoc("candidates", id, { status }); toast(status === "shortlisted" ? "Shortlisted" : status === "dismissed" ? "Dismissed" : "Moved back to New"); };
window.draftCmd = id => { const ids = cands(c => c.status === "shortlisted").map(c => c.id); copy(`python run_pipeline.py --mode api --draft --ids ${ids.includes(id) ? ids.join(",") : id}`, "Command copied. Run it in the project folder; drafts appear here."); };
window.manualDraft = async id => {
  const c = S.candidates[id]; if (!c) return;
  if (S.drafts[id]) { openDraft(id); return; }
  const url = (S.sources[id] || {}).url || candUrl(c);
  await patchDoc("drafts", id, { candidate_id: id, title: c.title, url, source: c.source, topic: c.topic, score: c.score, post: "", first_comment: `Source: ${c.source} — ${url}`, hashtags: [], claims: [], review_notes: "", verify: { verdict: "none", issues: [] }, status: "draft", manual: true, channel: "linkedin", format: "text", created: nowIso() }, true);
  await patchDoc("candidates", id, { status: "drafted" }, true);
  openDraft(id);
};
window.openDraft = id => { composeId = id; go("compose"); };

/* ================================================================ Today */
function renderToday() {
  const review = drafts(d => d.status === "draft").sort(byCreated);
  const approved = drafts(d => d.status === "approved");
  const sched = drafts(d => d.status === "scheduled").sort((a, b) => String(a.scheduled_for).localeCompare(String(b.scheduled_for)));
  const picks = cands(c => c.status === "new").sort(byScore).slice(0, 6);
  const run = lastRun(); const posted = postedThisWeek();
  const due = sched.filter(d => new Date(d.scheduled_for) <= new Date());
  const today = new Date().toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" });
  $("#s-today").innerHTML = `
    <div class="row" style="justify-content:space-between;margin-bottom:14px"><span class="eyebrow">${esc(today)}</span>${run ? `<span class="faint mono">last pipeline run ${esc(fmtDT(run.ts))} · $${Number((run.cost || {}).usd || 0).toFixed(3)}</span>` : ""}</div>
    <div class="stats">
      <div class="stat ${review.length ? "warn" : ""}"><span class="l">drafts to review</span><span class="n">${review.length}</span></div>
      <div class="stat"><span class="l">approved, not scheduled</span><span class="n">${approved.length}</span></div>
      <div class="stat ${due.length ? "due" : ""}"><span class="l">scheduled${due.length ? ` · ${due.length} due now` : ""}</span><span class="n">${sched.length}</span></div>
      <div class="stat ${posted >= target() ? "good" : ""}"><span class="l">posted this week</span><span class="n">${posted}<small>/${target()}</small></span></div>
      <div class="stat"><span class="l">new ideas from triage</span><span class="n">${cands(c => c.status === "new").length}</span></div>
    </div>
    ${due.length ? panel("Due now", `<div class="pb flush">${due.map(d => draftRow(d, { extra: `<button class="btn sm li" onclick="postNow('${d.id}')">${LI}&nbsp;Post now</button>` })).join("")}</div>`, "copy, paste on LinkedIn, mark as posted") : ""}
    <div class="grid2">
      <div>
        ${panel("Review now", `<div class="pb flush">${review.length ? review.slice(0, 6).map(d => draftRow(d)).join("") : emptyBox("No drafts waiting", "Pick an idea and write, or run the pipeline in API mode.")}</div>`, review.length ? `${review.length} open` : "")}
        ${panel("Up next", `<div class="pb flush">${sched.length ? sched.slice(0, 4).map(d => draftRow(d)).join("") : emptyBox("Nothing scheduled", "Approve a draft, then place it on a slot.")}</div>`, sched.length ? `${sched.length} in queue` : "")}
      </div>
      <div>
        ${panel("Top picks", `<div class="pb flush">${picks.length ? picks.map(c => candRow(c)).join("") : emptyBox("Triage has not run yet", "The hourly cloud job fills this in.")}</div>`, "highest-scored new ideas", `<a class="btn sm" href="#ideas" onclick="go('ideas');return false">All ideas</a>`)}
        ${panel("Pipeline", `<div class="pb"><p class="muted" style="margin-bottom:10px">${D.mode === "api" ? "API mode: the Claude agents draft and verify." : "Free mode: ideas arrive from the hourly cloud job with their articles fetched; you write in Compose with your Claude or ChatGPT subscription."}</p>
          <code class="cmd">python run_pipeline.py</code>
          <div class="row" style="margin-top:10px"><button class="btn sm" onclick="copy('python run_pipeline.py','Copied')">${ic("copy")}Copy command</button>
          <a class="btn sm" href="digests/latest.html" target="_blank">${ic("external")}Weekly digest</a>
          <a class="btn sm" href="studio-legacy.html" target="_blank">${ic("external")}Old studio</a></div></div>`)}
      </div>
    </div>`;
}
window.postNow = id => { composeId = id; go("compose"); setTimeout(() => { copyPost(id); }, 50); };

/* ================================================================ Discover */
let disc = { sub: "news", q: "", pillar: 0, tab: "", shown: 60, hideSaved: true, sort: "latest" };
$$("#disc-tabs .subtab").forEach(b => b.onclick = () => { disc.sub = b.dataset.sub; disc.shown = 60; renderDiscover(); });
function renderDiscover() {
  $$("#disc-tabs .subtab").forEach(b => b.classList.toggle("active", b.dataset.sub === disc.sub));
  const body = $("#disc-body");
  if (disc.sub === "pulse") return renderPulse(body);
  const items = disc.sub === "news" ? D.news : D.agents;
  const q = disc.q.toLowerCase();
  let list = items.filter(it => (!q || (it.t + " " + it.s).toLowerCase().includes(q)) && (disc.sub !== "news" || !disc.pillar || it.p === disc.pillar) && (disc.sub !== "agents" || !disc.tab || (it.tabs || []).includes(disc.tab)) && (!disc.hideSaved || !S.candidates[it.k]));
  if (disc.sort === "score") list = list.slice().sort((a, b) => (b.sc || 0) - (a.sc || 0));
  const chips = disc.sub === "news"
    ? [`<button class="fchip ${!disc.pillar ? "active" : ""}" onclick="discSet('pillar',0)">All</button>`].concat(Object.entries(D.pillars).map(([k, v]) => `<button class="fchip ${disc.pillar == k ? "active" : ""}" onclick="discSet('pillar',${k})">${esc(v)}</button>`))
    : [`<button class="fchip ${!disc.tab ? "active" : ""}" onclick="discSet('tab','')">All</button>`].concat(D.agentTabs.map(([k, v]) => `<button class="fchip ${disc.tab === k ? "active" : ""}" onclick="discSet('tab','${k}')">${esc(v)}</button>`));
  body.innerHTML = `
    <div class="row"><div style="position:relative;flex:1;max-width:380px"><input type="search" id="disc-q" placeholder="Search ${list.length} stories" value="${esc(disc.q)}" aria-label="Search" style="padding-left:32px"><span style="position:absolute;left:10px;top:9px;color:var(--ink-3)">${ic("search")}</span></div>
      <button class="btn sm ${disc.sort === "latest" ? "active" : ""}" onclick="discSet('sort','latest')">Latest</button>
      <button class="btn sm ${disc.sort === "score" ? "active" : ""}" onclick="discSet('sort','score')">Best for audience</button>
      <label class="faint" style="display:flex;gap:6px;align-items:center;margin-left:4px"><input type="checkbox" ${disc.hideSaved ? "checked" : ""} onchange="discSet('hideSaved',this.checked)"> hide saved</label>
      ${D.trends.length ? `<span class="faint" style="margin-left:auto">Rising: ${D.trends.slice(0, 6).map(t => esc(t.term || t.name || "")).join(", ")}</span>` : ""}</div>
    <div class="chips">${chips.join("")}</div>
    <div class="panel"><div class="pb flush">${list.slice(0, disc.shown).map(it => `<div class="item">
      <div class="lead"><span class="score ${it.sc >= 8 ? "hi" : ""}">${it.sc || "–"}</span></div>
      <div class="body"><div class="t"><a href="${esc(it.u)}" target="_blank" rel="noopener">${esc(it.t)}</a></div>
      <div class="meta"><span>${esc(D.pillars[it.p] || (it.primary || ""))}</span><span>·</span><span>${esc(it.s)}</span><span>·</span><span class="mono">${esc(ago(it.d || it.pub))}</span>${(it.l || it.links || []).length ? `<span>·</span><span>+${(it.l || it.links).length} more sources</span>` : ""}</div>
      ${it.sm ? `<div class="why">${esc(it.sm.slice(0, 200))}</div>` : ""}</div>
      <div class="acts">${S.candidates[it.k] ? '<span class="chip purple plain">saved</span>' : `<button class="btn sm" onclick="saveIdea('${it.k}','${disc.sub}')">${ic("bulb")}Save as idea</button>`}</div></div>`).join("") || emptyBox("Nothing matches", "Try another word or clear the filter.")}</div></div>
    ${list.length > disc.shown ? `<button class="btn" onclick="disc.shown+=60;renderDiscover()">Show more (${list.length - disc.shown} left)</button>` : ""}`;
  const qi = $("#disc-q"); qi.oninput = debounce(() => { disc.q = qi.value; disc.shown = 60; renderDiscover(); $("#disc-q").focus(); const v = $("#disc-q").value; $("#disc-q").setSelectionRange(v.length, v.length); }, 250);
}
window.discSet = (k, v) => { disc[k] = v; disc.shown = 60; renderDiscover(); };
window.saveIdea = async (k, sub) => {
  const it = (sub === "news" ? D.news : D.agents).find(x => x.k === k); if (!it) return;
  await patchDoc("candidates", k, { title: it.t, url: it.u, source: it.s, category: D.pillars[it.p] || "", published: it.d || it.pub || "", summary: it.sm || "", score: Math.max(5, Math.min(10, Math.round(it.sc || 6))), topic: TOPIC_OF_PILLAR[it.p] || "other", urgency: "this_week", reason: "saved from Discover", angle_hint: "", status: "shortlisted", manual: true, created: nowIso() });
  toast("Saved to Ideas as shortlisted");
};
async function renderPulse(body) {
  body.innerHTML = emptyBox("Loading Pulse");
  let p = null; try { const r = await fetch("pulse.json?v=" + D.cache, { cache: "no-store" }); if (r.ok) p = await r.json(); } catch (e) {}
  if (!p) { body.innerHTML = emptyBox("Pulse is not available", "pulse.json could not be loaded."); return; }
  const trends = p.trends || []; const pains = p.pain_points || [];
  body.innerHTML = `<p class="faint" style="margin-bottom:12px">Generated ${esc(fmtDT(p.generated_at))} · sources: ${esc(((p.meta || {}).sources_used || []).join(", "))} · mode ${esc((p.meta || {}).mode || "")}</p>
    <div class="grid2">${panel("Trending across platforms", `<div class="pb flush">${trends.map(t => `<div class="item"><div class="lead"><span class="chip ${t.momentum === "hot" || t.momentum === "rising" ? "accent" : "plain"}">${esc(t.momentum || "")}</span></div>
      <div class="body"><div class="t">${esc(t.name)}</div><div class="meta"><span>${esc(t.category || "")}</span>${(t.platforms || []).map(x => `<span>·</span><span>${esc(x.replace("_inferred", "*"))}</span>`).join("")}</div>${t.linkedin_angle ? `<div class="why">${esc(t.linkedin_angle)}</div>` : ""}</div>
      <div class="acts">${(t.sources || [])[0] ? `<a class="btn sm icon" title="Open signal" target="_blank" rel="noopener" href="${esc(t.sources[0].url)}">${ic("external")}</a>` : ""}</div></div>`).join("") || emptyBox("No trends")}</div>`)}
    ${panel("Pain points people talk about", `<div class="pb flush">${pains.map(x => `<div class="item"><div class="lead">${ic("message")}</div><div class="body"><div class="why" style="margin:0">${esc(x.text || x.problem || x.summary || JSON.stringify(x).slice(0, 200))}</div></div><div class="acts">${x.url ? `<a class="btn sm icon" title="Source" target="_blank" rel="noopener" href="${esc(x.url)}">${ic("external")}</a>` : ""}</div></div>`).join("") || emptyBox("None detected")}</div>`)}</div>`;
}

/* ================================================================ Ideas */
let ideasShowLater = false;
function renderIdeas() {
  const short = cands(c => c.status === "shortlisted").sort(byScore);
  const fresh = cands(c => c.status === "new").sort(byScore);
  const later = cands(c => ["low", "duplicate", "dismissed", "skipped"].includes(c.status)).sort(byScore);
  $("#s-ideas").innerHTML = `
    <div class="row" style="margin-bottom:14px"><span class="muted">Shortlisted ideas are written first. Everything scores 1–10 for your audience.</span>
      <span style="flex:1"></span>
      ${short.length && D.mode === "api" ? `<button class="btn sm" onclick="draftCmd('${short[0].id}')">${ic("copy")}Draft all shortlisted with API</button>` : ""}
      <button class="btn sm" onclick="go('discover')">${ic("radar")}Find more in Discover</button></div>
    <div class="kanban">
      <div class="kcol"><h3>${ic("star")}Shortlisted <span class="cnt">${short.length}</span></h3>${short.map(c => candCard(c)).join("") || emptyBox("Nothing shortlisted", "Star an idea here or save one from Discover.")}</div>
      <div class="kcol"><h3>${ic("bulb")}New from triage <span class="cnt">${fresh.length}</span></h3>${fresh.slice(0, 40).map(c => candCard(c)).join("") || emptyBox("No new ideas yet", "The hourly cloud job fills this in.")}${fresh.length > 40 ? `<p class="faint" style="padding:4px 6px">${fresh.length - 40} more, lower scored.</p>` : ""}</div>
      <div class="kcol"><h3>${ic("clock")}Later / dismissed <span class="cnt">${later.length}</span><button class="btn sm" onclick="ideasShowLater=!ideasShowLater;renderIdeas()">${ideasShowLater ? "Hide" : "Show"}</button></h3>${ideasShowLater ? later.slice(0, 60).map(c => candCard(c)).join("") : ""}</div>
    </div>`;
}

/* ================================================================ Compose */
let composeId = null, composeFilter = "review";
function renderCompose() {
  const filt = { review: d => d.status === "draft", approved: d => ["approved", "scheduled"].includes(d.status), all: d => d.status !== "published" }[composeFilter];
  const list = drafts(filt).sort(byCreated);
  if (!composeId || !S.drafts[composeId]) composeId = (list[0] || {}).id || null;
  $("#compose-list").innerHTML = `<div class="row">${[["review", "To review"], ["approved", "Approved"], ["all", "All open"]].map(([k, v]) => `<button class="btn sm ${composeFilter === k ? "active" : ""}" onclick="composeFilter='${k}';renderCompose()">${v}</button>`).join("")}</div>
    ${list.map(d => `<button class="citem ${verdictOf(d)} ${d.id === composeId ? "active" : ""}" onclick="composeId='${d.id}';renderCompose()"><div class="t">${esc(d.title)}</div><div class="meta"><span>${esc(STATUS_LABEL[d.status] || d.status)}</span><span>·</span><span>${esc(TOPIC_LABEL[d.topic] || d.topic || "")}</span>${d.manual ? "<span>·</span><span>manual</span>" : ""}</div></button>`).join("") || emptyBox("Nothing here", "Pick an idea and press Write.")}`;
  renderEditor(composeId);
}
function stepper(st) {
  const order = ["draft", "approved", "scheduled", "published"]; const i = order.indexOf(st);
  return `<div class="stepper">${order.map((s, k) => `<span class="step ${k < i ? "done" : k === i ? "now" : ""}">${STATUS_LABEL[s]}</span>`).join("")}${st === "rejected" ? '<span class="step now">Rejected</span>' : ""}</div>`;
}
function renderEditor(id) {
  const ed = $("#compose-editor"); const d = id && S.drafts[id];
  if (!d) { ed.innerHTML = `<div class="panel">${emptyBox("Pick a draft on the left", "Or go to Ideas and press Write on a story.")}</div>`; return; }
  const pack = S.sources[d.candidate_id || d.id] || {};
  const st = d.status;
  ed.innerHTML = `
    <div class="panel"><div class="pb">
      <div class="chead"><div style="min-width:0;flex:1"><h2>${esc(d.title)}</h2>
        <div class="meta"><span>${esc(d.source || "")}</span><span>·</span><a href="${esc(d.url)}" target="_blank" rel="noopener">source</a><span>·</span><span>${esc(TOPIC_LABEL[d.topic] || d.topic || "")}</span>${d.format ? `<span>·</span><span>${esc(d.format)}</span>` : ""}${d.scheduled_for ? `<span>·</span><span class="mono">${esc(fmtDT(d.scheduled_for))}</span>` : ""}</div>
        ${d.angle && d.angle.angle ? `<p class="muted" style="margin:8px 0 0"><span class="eyebrow">Angle</span>&nbsp; ${esc(d.angle.angle)}</p>` : ""}</div>
        <div class="row">
          ${st === "draft" ? `<button class="btn primary" onclick="setDraft('${d.id}',{status:'approved'},'Approved')">${ic("check")}Approve</button>` : ""}
          ${["approved", "scheduled"].includes(st) ? `<button class="btn" onclick="setDraft('${d.id}',{status:'draft'},'Back to review')">${ic("undo")}Back to review</button>` : ""}
          ${st === "approved" ? `<button class="btn primary" onclick="scheduleNext('${d.id}')">${ic("calendar")}Next free slot</button>` : ""}
          ${st !== "published" ? `<button class="btn danger" data-confirm="Reject this draft?" onclick="confirmThen(this,()=>setDraft('${d.id}',{status:'rejected'},'Rejected'))">Reject</button>` : ""}
        </div></div>
      ${stepper(st)}
    </div></div>
    <div class="editor-grid">
      <div>
        <div class="panel"><div class="pb">
          <label class="f" for="ed-post">Post</label>
          <textarea id="ed-post" class="post-ta" placeholder="Write the post here. Line 1 is the hook.">${esc(postOf(d))}</textarea>
          <div class="counter" id="ed-counter"></div>
          <label class="f" for="ed-comment">First comment (the source link lives here)</label>
          <textarea id="ed-comment" style="min-height:58px">${esc(commentOf(d))}</textarea>
          <label class="f" for="ed-tags">Hashtags (max 3)</label>
          <input type="text" id="ed-tags" value="${esc((d.hashtags || []).join(" "))}" placeholder="#ai #healthcare">
        </div>
        <div class="actionbar">
          <button class="btn" onclick="copyPost('${d.id}')">${ic("copy")}Copy post</button>
          <button class="btn" onclick="copy(commentOf(S.drafts['${d.id}']),'First comment copied')">${ic("message")}Copy first comment</button>
          <button class="btn li" onclick="window.open('https://www.linkedin.com/feed/?shareActive=true','_blank','noopener')">${LI}&nbsp;Open LinkedIn</button>
          <span class="spacer"></span>
          ${st !== "published" ? `<button class="btn dark" data-confirm="Posted on LinkedIn?" onclick="confirmThen(this,()=>markPosted('${d.id}'))">${ic("check")}Mark as posted</button>` : `<span class="chip good">posted ${esc(fmtDT(d.published_at))}</span>`}
        </div></div>
        <p class="faint" style="margin:-6px 0 14px 2px">Copying or opening LinkedIn changes nothing. Only “Mark as posted” moves this to Published.</p>
        ${panel("Write with Claude or ChatGPT", `<div class="pb">
          <ol class="steps"><li>Copy the writer prompt and paste it into Claude.ai or ChatGPT.</li><li>Paste its answer below and press Parse. Post, first comment, claims and checks fill in.</li><li>Edit in your voice. Optionally run the fact-check the same way.</li></ol>
          ${pack.excerpt ? `<p class="faint">Source text loaded (${pack.chars} chars${pack.thin ? ", thin" : ""}). The prompt uses the real article, not just the headline.</p>` : `<div class="row" style="margin-bottom:6px"><button class="btn sm" id="ed-fetch" onclick="fetchArticle('${d.id}')">${ic("radar")}Fetch article text</button><span class="faint">No article text yet. Fetch it, or paste facts from the article below; the prompt is never built from the link alone.</span></div>
          <textarea id="ed-facts" placeholder="A few lines of real facts, numbers, quotes copied from the article">${esc(d.facts || "")}</textarea>`}
          <div class="row" style="margin-top:10px"><button class="btn primary" onclick="copyPrompt('${d.id}')">${ic("copy")}Copy writer prompt</button>
            <button class="btn" onclick="copyJudgePrompt('${d.id}')" ${postOf(d).trim() ? "" : "disabled"}>${ic("search")}Copy fact-check prompt</button></div>
          <label class="f" for="ed-paste">Paste the answer here</label>
          <textarea id="ed-paste" style="min-height:64px;font-family:var(--mono);font-size:12px" placeholder='{"angles": [...], "post": "...", ...}'></textarea>
          <div class="row" style="margin-top:8px"><button class="btn" onclick="parseAnswer('${d.id}')">${ic("play")}Parse answer</button><span class="faint" id="ed-parse-msg"></span></div></div>`, "your subscription, no API cost")}
        ${(d.claims || []).length ? `<div class="panel"><div class="pb"><details><summary>Claims and where they come from (${d.claims.length})</summary><table class="claims" style="margin-top:8px">${d.claims.map(c => `<tr><td>${esc(c.claim)}</td><td><span class="chip ${c.kind === "reported_fact" ? "good" : c.kind === "unsupported" ? "bad" : c.kind === "my_interpretation" ? "purple" : "info"} plain">${esc(String(c.kind || "").replace(/_/g, " "))}</span> ${esc(c.support)}</td></tr>`).join("")}</table></details></div></div>` : ""}
        ${d.review_notes ? `<div class="panel"><div class="pb"><details open><summary>Writer's private notes</summary><p class="muted" style="white-space:pre-wrap;margin:8px 0 0">${esc(d.review_notes)}</p></details></div></div>` : ""}
        ${pack.excerpt || pack.feed_summary ? `<div class="panel"><div class="pb"><details><summary>Source pack (${pack.chars || 0} chars${pack.thin ? ", thin" : ""})</summary><div class="excerpt">${esc(pack.excerpt || pack.feed_summary)}</div>${pack.note ? `<p class="faint" style="margin-top:6px">${esc(pack.note)}</p>` : ""}</details></div></div>` : ""}
      </div>
      <div>
        ${panel("LinkedIn preview", `<div class="pb"><div class="preview" id="ed-preview"></div></div>`, "mobile cut at 140")}
        ${panel("Checks", `<div class="pb" id="ed-issues"></div>${(d.verify || {}).judge ? `<div class="pb" style="border-top:1px solid var(--line)"><details><summary>Fact-checker's verdict</summary><p class="muted" style="margin:8px 0 4px">${esc(d.verify.judge.summary || "")}</p><p class="faint">AI-smell ${esc(d.verify.judge.ai_smell)}/5 · specificity ${esc(d.verify.judge.specificity)}/5</p>${(d.verify.judge.fixes || []).length ? `<ul class="muted" style="margin:6px 0 0;padding-left:18px">${d.verify.judge.fixes.map(f => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}</details></div>` : ""}`, `<span id="ed-verdict"></span>`)}
        ${st === "approved" || st === "scheduled" ? panel("Schedule", `<div class="pb"><input type="datetime-local" id="ed-when" value="${esc(toLocalInput(d.scheduled_for || nextFreeSlot()))}"><div class="row" style="margin-top:8px"><button class="btn sm primary" onclick="setDraft('${d.id}',{status:'scheduled',scheduled_for:new Date($('#ed-when').value).toISOString()},'Scheduled')">Save slot</button>${st === "scheduled" ? `<button class="btn sm" onclick="setDraft('${d.id}',{status:'approved',scheduled_for:null},'Unscheduled')">Unschedule</button>` : ""}</div></div>`) : ""}
      </div>
    </div>`;
  const refresh = () => refreshEditorPanels(d.id);
  const persist = debounce(() => { const dd = S.drafts[d.id]; if (!dd) return; patchDoc("drafts", d.id, { edited_post: $("#ed-post").value, edited_comment: $("#ed-comment").value, hashtags: ($("#ed-tags").value.match(/#\w+/g) || []), facts: $("#ed-facts") ? $("#ed-facts").value : (dd.facts || "") }, true); }, 700);
  ["ed-post", "ed-comment", "ed-tags", "ed-facts"].forEach(i => { const el = $("#" + i); if (el) el.addEventListener("input", () => { refresh(); persist(); }); });
  refresh();
}
function refreshEditorPanels(id) {
  const d = S.drafts[id]; if (!d) return;
  const post = $("#ed-post") ? $("#ed-post").value : postOf(d);
  const tags = $("#ed-tags") ? ($("#ed-tags").value.match(/#\w+/g) || []) : (d.hashtags || []);
  const pack = S.sources[d.candidate_id || d.id] || {};
  const r = checkPost(post, pack, [(d.angle || {}).angle, (d.angle || {}).hook, d.facts].join(" "), tags);
  const pipe = ((d.verify || {}).issues || []).filter(i => ["unsupported", "attribution", "ai_smell", "vague"].includes(i.code));
  const all = r.issues.concat(pipe);
  $("#ed-counter").innerHTML = `<span class="${r.chars > 3000 ? "bad" : r.chars < 400 ? "mid" : "ok"}">${r.chars}/3000 chars</span><span class="${r.hookLen > 210 ? "bad" : r.hookLen > 140 ? "mid" : "ok"}">hook ${r.hookLen}/140</span><span>${post.split(/\s+/).filter(Boolean).length} words</span>`;
  const verdict = all.some(i => i.level === "fail") ? "fail" : all.length ? "warn" : "pass";
  $("#ed-verdict").innerHTML = `<span class="chip ${VERDICT_CHIP[verdict]}">${verdict}</span>`;
  $("#ed-issues").innerHTML = all.map(i => `<div class="issue"><span class="lv ${i.level}"></span><span>${esc(i.msg)}</span></div>`).join("") || '<p class="faint" style="margin:0">No issues found. Read it once more as your audience would.</p>';
  const hook = post.split("\n")[0]; const rest = post.slice(hook.length);
  $("#ed-preview").innerHTML = `<div class="ph"><span class="av">A</span><div><b>Ahmad</b><small>AI x Ahmad · The World of AI, made simple</small><small>Now · Anyone</small></div></div>
    <div class="body">${esc(hook.slice(0, 140))}${hook.length > 140 || rest.trim() ? `<span class="more" onclick="this.parentNode.innerHTML=this.parentNode.dataset.full">${hook.length > 140 ? "" : " "}…more</span>` : ""}</div>
    <div class="bar"><span>Like</span><span>Comment</span><span>Repost</span><span>Send</span></div>`;
  $("#ed-preview .body").dataset.full = esc(post) + (tags.length ? "\n\n" + esc(tags.join(" ")) : "");
}
window.setDraft = (id, fields, msg) => { if ($("#ed-post") && S.drafts[id]) Object.assign(fields, { edited_post: $("#ed-post").value, edited_comment: $("#ed-comment").value }); patchDoc("drafts", id, fields); if (msg) toast(msg); };
window.copyPost = id => { const d = S.drafts[id]; if (!d) return; const tags = ($("#ed-tags") && composeId === id) ? ($("#ed-tags").value.match(/#\w+/g) || []) : (d.hashtags || []); const post = ($("#ed-post") && composeId === id) ? $("#ed-post").value : postOf(d); copy(post.trim() + (tags.length ? "\n\n" + tags.join(" ") : ""), "Post copied. Paste it into LinkedIn, then add the first comment."); };
window.markPosted = async id => {
  const d = S.drafts[id]; if (!d) return;
  await patchDoc("drafts", id, { status: "published", published_at: nowIso(), edited_post: $("#ed-post") ? $("#ed-post").value : postOf(d) }, true);
  if (d.candidate_id) await patchDoc("candidates", d.candidate_id, { status: "published" }, true);
  toast("Marked as posted. Rate it in Published when the numbers come in."); go("published");
};
window.confirmThen = (btn, fn) => { if (btn.dataset.armed) { delete btn.dataset.armed; fn(); return; } const orig = btn.innerHTML; btn.dataset.armed = "1"; btn.textContent = btn.dataset.confirm + " Click again"; setTimeout(() => { if (btn.dataset.armed) { delete btn.dataset.armed; btn.innerHTML = orig; } }, 4000); };

/* Fetch the article from inside the Studio. A page cannot read other sites
   directly, so this goes through the free r.jina.ai reader (plain text back).
   User-triggered only; the result is saved as the story's source pack. */
window.fetchArticle = async id => {
  const d = S.drafts[id]; if (!d) return;
  const btn = $("#ed-fetch"); if (btn) { btn.disabled = true; btn.textContent = "Fetching…"; }
  try {
    const r = await fetch("https://r.jina.ai/" + d.url, { headers: { "Accept": "text/plain", "X-Return-Format": "text" } });
    if (!r.ok) throw new Error("reader returned " + r.status);
    let text = await r.text();
    const i = text.indexOf("Markdown Content:"); if (i >= 0) text = text.slice(i + 17);
    text = text.replace(/!\[[^\]]*\]\([^)]*\)/g, "").replace(/\[([^\]]*)\]\([^)]*\)/g, "$1").replace(/[ \t]+/g, " ");
    const paras = text.split(/\n+/).map(x => x.trim()).filter(x => x.length >= 40 && !/^(cookie|subscribe|sign in|share|advertisement)/i.test(x));
    const excerpt = paras.join("\n\n").slice(0, 7000);
    if (excerpt.length < 200) throw new Error("the page gave almost no text (paywall or video?)");
    const quotes = (excerpt.match(/["“]([^"”]{25,320})["”]/g) || []).slice(0, 8).map(q => q.slice(1, -1));
    await patchDoc("sources", d.candidate_id || d.id, { url: d.url, title: d.title, source: d.source, excerpt, chars: excerpt.length, quotes, thin: excerpt.length < 600, ok: excerpt.length >= 600, note: "fetched in the Studio via r.jina.ai", fetched_at: nowIso() }, true);
    if (d.candidate_id && S.candidates[d.candidate_id]) await patchDoc("candidates", d.candidate_id, { source_ok: excerpt.length >= 600, source_chars: excerpt.length }, true);
    renderEditor(id); toast(`Article fetched: ${excerpt.length} characters of source text`);
  } catch (e) {
    toast("Could not fetch the article (" + e.message + "). Paste a few facts instead.", 4000);
    if (btn) { btn.disabled = false; btn.innerHTML = ic("radar") + "Fetch article text"; }
  }
};

/* Manual mode: the same agent prompts, answered by your Claude / ChatGPT
   subscription. The answer is one JSON object; parseAnswer() fills the draft. */
function sourceBlock(d) {
  const pack = S.sources[d.candidate_id || d.id] || {};
  const facts = $("#ed-facts") ? $("#ed-facts").value.trim() : (d.facts || "");
  const text = pack.excerpt || facts;
  if (!text) return null;
  return ["STORY: " + d.title, `SOURCE: ${d.source} (${d.url})` + (pack.published ? "  published " + String(pack.published).slice(0, 10) : ""),
    pack.thin ? "SOURCE WARNING: the article could not be fully fetched — work only with what is here and keep it short and honest." : "",
    "SOURCE TEXT:\n" + text, (pack.quotes || []).length ? "QUOTES:\n" + pack.quotes.slice(0, 8).map(q => "- " + q).join("\n") : ""].filter(Boolean).join("\n\n");
}
window.copyPrompt = id => {
  const d = S.drafts[id]; const src = sourceBlock(d);
  if (!src) { toast("Paste some facts first. A headline alone produces invented details."); return; }
  const recent = drafts(x => x.status === "published").sort((a, b) => String(b.published_at || "").localeCompare(String(a.published_at || ""))).slice(0, 12);
  const p = [D.prompts.writer, "", "CREATOR & VOICE:\n" + D.content.voice, "", "LINKEDIN RULES:\n" + D.content.rules,
    "", "HOOK PATTERNS (draw on, never copy):\n" + (D.content.hooks || []).map(h => "- " + (h.text || h)).join("\n"),
    "", "EXAMPLES OF THE CREATOR'S BEST POSTS (match the voice, never reuse the content):\n" + D.content.examples,
    "", "STEP 1 — ANGLES. Before writing, follow these angle rules and propose 2-3 angles:\n" + D.prompts.angle,
    "", "STEP 2 — WRITE the post for the best angle, following everything above.", "", src,
    "", settings().audience ? "AUDIENCE OVERRIDE: " + settings().audience : "",
    settings().personal_note ? "PERSONAL NOTE (owner-supplied, real — first person allowed only for this): " + settings().personal_note : "PERSONAL NOTE: none — do not write any firsthand experience claim.",
    recent.length ? "\nRECENTLY POSTED (do not repeat these angles or openings):\n" + recent.map(r => "- " + r.title + " | " + postOf(r).split("\n")[0].slice(0, 120)).join("\n") : "",
    "", "OUTPUT: return ONE JSON object only, inside a ```json fence, nothing else. Keys:",
    '{"angles":[{"angle":"","hook":"","format":"text|carousel|image","mode":"insight|practical|story|question","why":""}],',
    ' "chosen":0, "post":"", "first_comment":"", "hashtags":[], "claims":[{"claim":"","support":"","kind":"reported_fact|attributed_claim|my_interpretation|unsupported"}],',
    ' "review_notes":"", "status":"draft|skip"}'].filter(x => x !== "").join("\n");
  copy(p, "Writer prompt copied. Paste it into Claude.ai or ChatGPT, then paste the JSON answer back here.");
};
window.copyJudgePrompt = id => {
  const d = S.drafts[id]; const post = $("#ed-post") ? $("#ed-post").value : postOf(d); const src = sourceBlock(d);
  if (!post.trim()) { toast("Nothing to check yet"); return; }
  const p = [D.prompts.judge, "", "POST:\n" + post, "", src || ("STORY: " + d.title + "\nSOURCE TEXT: (none supplied)"),
    "", "OUTPUT: return ONE JSON object only, inside a ```json fence:", '{"unsupported_claims":[], "misattributed":[], "ai_smell":1, "specificity":1, "fixes":[], "summary":""}'].join("\n");
  copy(p, "Fact-check prompt copied. Paste the JSON answer back here.");
};
function extractJson(text) {
  text = String(text || "").trim();
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i); if (fence) text = fence[1];
  const a = text.indexOf("{"), b = text.lastIndexOf("}"); if (a < 0 || b <= a) throw new Error("no JSON object found");
  return JSON.parse(text.slice(a, b + 1));
}
window.parseAnswer = async id => {
  const d = S.drafts[id]; const raw = $("#ed-paste").value; const msg = $("#ed-parse-msg");
  let j; try { j = extractJson(raw); } catch (e) { msg.textContent = "Could not read that: " + e.message + ". Paste the whole JSON answer."; return; }
  const pack = S.sources[d.candidate_id || d.id] || {};
  if (typeof j.post === "string") {
    if (j.status === "skip" && !j.post.trim()) { msg.textContent = "The writer says skip: " + (j.review_notes || "no useful angle"); await patchDoc("drafts", id, { review_notes: j.review_notes || "writer suggested skip" }, true); return; }
    const angles = Array.isArray(j.angles) ? j.angles : []; const chosen = angles[Math.min(Number(j.chosen) || 0, Math.max(angles.length - 1, 0))] || null;
    const hashtags = (Array.isArray(j.hashtags) ? j.hashtags : String(j.hashtags || "").split(/\s+/)).map(h => String(h).trim()).filter(Boolean).map(h => h.startsWith("#") ? h : "#" + h).slice(0, 3);
    const r = checkPost(j.post, pack, [(chosen || {}).angle, (chosen || {}).hook, d.facts].join(" "), hashtags);
    await patchDoc("drafts", id, { post: j.post, edited_post: null, first_comment: String(j.first_comment || commentOf(d)), edited_comment: null, hashtags, claims: Array.isArray(j.claims) ? j.claims : [], review_notes: String(j.review_notes || ""), angle: chosen, format: (chosen || {}).format || d.format || "text", angles, verify: { verdict: r.verdict, issues: r.issues, hook_len: r.hookLen, chars: r.chars, engine: "manual" }, status: d.status === "rejected" ? "draft" : d.status }, true);
    renderEditor(id); toast("Draft filled in. Now edit it in your voice.");
    return;
  }
  if (Array.isArray(j.unsupported_claims) || j.ai_smell != null) {
    const v = Object.assign({}, d.verify || { issues: [] });
    v.issues = (v.issues || []).filter(i => !["unsupported", "attribution", "ai_smell", "vague"].includes(i.code));
    (j.unsupported_claims || []).forEach(c => v.issues.push({ level: "fail", code: "unsupported", msg: String(c) }));
    (j.misattributed || []).forEach(c => v.issues.push({ level: "warn", code: "attribution", msg: String(c) }));
    if (Number(j.ai_smell) >= 4) v.issues.push({ level: "warn", code: "ai_smell", msg: `reads generic (ai_smell ${j.ai_smell}/5)` });
    if (j.specificity != null && Number(j.specificity) <= 2) v.issues.push({ level: "warn", code: "vague", msg: `low specificity (${j.specificity}/5)` });
    v.judge = { summary: String(j.summary || ""), ai_smell: Number(j.ai_smell) || 0, specificity: Number(j.specificity) || 0, fixes: Array.isArray(j.fixes) ? j.fixes : [], unsupported_claims: j.unsupported_claims || [], misattributed: j.misattributed || [] };
    v.verdict = v.issues.some(i => i.level === "fail") ? "fail" : v.issues.length ? "warn" : "pass";
    await patchDoc("drafts", id, { verify: v }, true);
    renderEditor(id); toast("Fact-check applied: " + v.verdict);
    return;
  }
  msg.textContent = "That JSON has neither a post nor a fact-check. Paste the writer's or the checker's answer.";
};

/* ================================================================ Schedule */
function parseSlot(s) { const m = String(s).trim().match(/^(mon|tue|wed|thu|fri|sat|sun)\w*\s+(\d{1,2}):(\d{2})$/i); if (!m) return null; return { dow: ["sun", "mon", "tue", "wed", "thu", "fri", "sat"].indexOf(m[1].toLowerCase().slice(0, 3)), h: +m[2], m: +m[3] }; }
function nextFreeSlot() {
  const taken = drafts(d => d.status === "scheduled" && d.scheduled_for).map(d => new Date(d.scheduled_for).getTime());
  const sl = slots().map(parseSlot).filter(Boolean); if (!sl.length) return new Date(Date.now() + 864e5).toISOString();
  for (let i = 0; i < 28; i++) {
    const day = new Date(); day.setHours(0, 0, 0, 0); day.setDate(day.getDate() + i);
    for (const s of sl) { if (s.dow !== day.getDay()) continue; const t = new Date(day); t.setHours(s.h, s.m, 0, 0); if (t.getTime() < Date.now()) continue; if (taken.some(x => Math.abs(x - t.getTime()) < 36e5)) continue; return t.toISOString(); }
  }
  return new Date(Date.now() + 864e5).toISOString();
}
window.scheduleNext = id => { const when = nextFreeSlot(); patchDoc("drafts", id, { status: "scheduled", scheduled_for: when }); toast("Scheduled for " + fmtDT(when)); };
function renderSchedule() {
  const sched = drafts(d => d.status === "scheduled").sort((a, b) => String(a.scheduled_for).localeCompare(String(b.scheduled_for)));
  const approved = drafts(d => d.status === "approved");
  const sl = slots().map(parseSlot).filter(Boolean);
  const days = []; const start = new Date(); start.setHours(0, 0, 0, 0);
  for (let i = 0; i < 14; i++) { const day = new Date(start); day.setDate(start.getDate() + i); days.push(day); }
  const dayCell = day => {
    const end = new Date(day); end.setDate(day.getDate() + 1);
    const items = sched.filter(d => { const t = new Date(d.scheduled_for); return t >= day && t < end; });
    const free = sl.filter(s => s.dow === day.getDay() && !items.some(d => Math.abs(new Date(d.scheduled_for).getHours() - s.h) < 1) && new Date(day).setHours(s.h, s.m) > Date.now());
    return `<div class="day ${day.toDateString() === new Date().toDateString() ? "today" : ""}"><div class="dh"><b>${day.getDate()}</b>${esc(day.toLocaleDateString(undefined, { weekday: "short" }))}</div>
      ${items.map(d => `<div class="slot ${new Date(d.scheduled_for) <= new Date() ? "due" : ""}" onclick="openDraft('${d.id}')"><b>${esc(fmtT(d.scheduled_for))}</b>${esc(d.title.slice(0, 54))}</div>`).join("")}
      ${free.map(s => `<div class="slot free">${String(s.h).padStart(2, "0")}:${String(s.m).padStart(2, "0")} free</div>`).join("")}</div>`;
  };
  $("#s-schedule").innerHTML = `
    ${panel("Next two weeks", `<div class="pb"><div class="week">${days.slice(0, 7).map(dayCell).join("")}</div><div class="week">${days.slice(7).map(dayCell).join("")}</div></div>`, `slots ${esc(slots().join(" · "))} · target ${target()}/week · ${postedThisWeek()} posted this week`)}
    <div class="grid2">
      ${panel("Approved, waiting for a slot", `<div class="pb flush">${approved.map(d => draftRow(d, { extra: `<button class="btn sm" onclick="scheduleNext('${d.id}')">${ic("calendar")}Next free slot</button>` })).join("") || emptyBox("Nothing approved yet", "Approve drafts in Compose first.")}</div>`, `${approved.length}`)}
      ${panel("Queue", `<div class="pb flush">${sched.map(d => draftRow(d, { extra: `<button class="btn sm li" onclick="postNow('${d.id}')">${LI}&nbsp;Post now</button><button class="btn sm icon" title="Unschedule" aria-label="Unschedule" onclick="setDraft('${d.id}',{status:'approved',scheduled_for:null},'Unscheduled')">${ic("x")}</button>` })).join("") || emptyBox("Queue is empty")}</div>`, `${sched.length}`)}
    </div>`;
}

/* ================================================================ Published */
function renderPublished() {
  const list = drafts(d => d.status === "published").sort((a, b) => String(b.published_at || "").localeCompare(String(a.published_at || "")));
  const rated = list.filter(d => d.rating); const avg = rated.length ? (rated.reduce((s, d) => s + Number(d.rating), 0) / rated.length).toFixed(1) : "–";
  const month = list.filter(d => new Date(d.published_at).getMonth() === new Date().getMonth() && new Date(d.published_at).getFullYear() === new Date().getFullYear()).length;
  const byTopic = {}; rated.forEach(d => { const k = d.topic || "other"; byTopic[k] = byTopic[k] || []; byTopic[k].push(Number(d.rating)); });
  const best = Object.entries(byTopic).map(([k, v]) => [k, v.reduce((a, b) => a + b, 0) / v.length]).sort((a, b) => b[1] - a[1])[0];
  $("#s-published").innerHTML = `
    <div class="stats"><div class="stat"><span class="l">posts published</span><span class="n">${list.length}</span></div><div class="stat"><span class="l">this month</span><span class="n">${month}</span></div><div class="stat"><span class="l">average rating</span><span class="n">${avg}</span></div><div class="stat"><span class="l">best-rated topic</span><span class="n" style="font-family:var(--sans);font-size:18px">${best ? esc(TOPIC_LABEL[best[0]] || best[0]) : "–"}</span></div></div>
    ${panel("Log", `<div class="pb flush" style="overflow-x:auto"><table class="list"><tr><th>Date</th><th>Post</th><th>Topic</th><th>Rating</th><th>Impressions</th><th>Reactions</th><th>Comments</th><th>Notes</th><th></th></tr>
      ${list.map(d => `<tr><td class="num" style="white-space:nowrap">${esc(fmtD(d.published_at))}</td><td><b style="font-weight:500">${esc(d.title)}</b><div class="faint">${esc(postOf(d).split("\n")[0].slice(0, 100))}</div></td><td><span class="chip plain">${esc(TOPIC_LABEL[d.topic] || d.topic || "")}</span></td>
        <td><select onchange="patchDoc('drafts','${d.id}',{rating:+this.value||null},true)"><option value="">–</option>${[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => `<option ${d.rating == n ? "selected" : ""}>${n}</option>`).join("")}</select></td>
        <td><input class="num" type="number" style="width:96px" value="${esc((d.stats || {}).impressions || "")}" onchange="statSet('${d.id}','impressions',this.value)"></td>
        <td><input class="num" type="number" style="width:76px" value="${esc((d.stats || {}).reactions || "")}" onchange="statSet('${d.id}','reactions',this.value)"></td>
        <td><input class="num" type="number" style="width:76px" value="${esc((d.stats || {}).comments || "")}" onchange="statSet('${d.id}','comments',this.value)"></td>
        <td><input type="text" style="min-width:150px" value="${esc(d.notes || "")}" onchange="patchDoc('drafts','${d.id}',{notes:this.value},true)"></td>
        <td><div class="row" style="flex-wrap:nowrap;gap:4px"><button class="btn sm icon" title="Copy post" aria-label="Copy post" onclick="copyPost('${d.id}')">${ic("copy")}</button><button class="btn sm" onclick="openDraft('${d.id}')">Open</button></div></td></tr>`).join("") || `<tr><td colspan="9">${emptyBox("Nothing published yet", "Posts land here when you press Mark as posted.")}</td></tr>`}</table></div>`,
      "rate 1–10 and note the numbers a day later; top-rated posts become the writer's examples", `<button class="btn sm" onclick="exportPublished()">${ic("copy")}Export markdown</button>`)}
    ${panel("Other channels", `<div class="pb"><p class="muted" style="margin:0">X, Reddit, Facebook, WhatsApp Channel and YouTube adaptations come later as separate agents that take an approved LinkedIn post as input. They appear in Settings when they exist.</p></div>`)}`;
}
window.statSet = (id, k, v) => { const d = S.drafts[id]; patchDoc("drafts", id, { stats: Object.assign({}, d.stats || {}, { [k]: v === "" ? null : +v }) }, true); };
window.exportPublished = () => { const list = drafts(d => d.status === "published").sort((a, b) => String(b.published_at || "").localeCompare(String(a.published_at || ""))); copy(list.map(d => `## ${fmtD(d.published_at)} — ${d.title}\nrating: ${d.rating || "-"} | impressions: ${(d.stats || {}).impressions || "-"} | topic: ${d.topic || ""}\n\n${postOf(d)}\n\n${commentOf(d)}\n`).join("\n---\n\n"), "Markdown copied. Paste the best ones into content/examples.md."); };

/* ================================================================ Library */
function renderLibrary() {
  $("#s-library").innerHTML = `
    <p class="muted" style="margin-bottom:14px">These come from the <span class="mono">content/</span> folder in the repo and are baked in at build time. Edit the files there; every agent and prompt reads them on the next run.</p>
    <div class="grid2">
      ${panel("Hook library", `<div class="pb flush">${(D.content.hooks || []).map(h => `<div class="hook"><span class="chip plain">${esc(h.type || "hook")}</span><span class="tx">${esc(h.text || h)}</span><button class="btn sm icon" title="Copy" aria-label="Copy hook" onclick="copy(${JSON.stringify(h.text || h)},'Hook copied')">${ic("copy")}</button></div>`).join("")}</div>`, "content/hooks.json")}
      <div>
        ${panel("Voice profile", `<div class="pb"><pre class="excerpt" style="max-height:420px;margin:0">${esc(D.content.voice)}</pre></div>`, "content/voice.md")}
        ${panel("LinkedIn rules", `<div class="pb"><pre class="excerpt" style="max-height:420px;margin:0">${esc(D.content.rules)}</pre></div>`, "content/linkedin_rules.md")}
        ${panel("Example posts", `<div class="pb"><pre class="excerpt" style="max-height:420px;margin:0">${esc(D.content.examples)}</pre></div>`, "content/examples.md")}
      </div></div>`;
}

/* ================================================================ Settings */
function renderSettings() {
  const p = settings();
  $("#s-settings").innerHTML = `
    <div class="grid2">
      <div>
        ${panel("You", `<div class="pb">
          <label class="f" for="st-note">Personal note for the writer (real experience it may use in first person; leave empty for none)</label>
          <textarea id="st-note">${esc(p.personal_note || "")}</textarea>
          <label class="f" for="st-aud">Audience override (optional; voice.md is the default)</label>
          <input type="text" id="st-aud" value="${esc(p.audience || "")}" placeholder="e.g. freelancers and small business owners in Pakistan">
          <label class="f" for="st-target">Posts per week target</label>
          <input type="number" id="st-target" min="1" max="14" value="${esc(p.postsPerWeek || 4)}" style="width:100px">
          <label class="f" for="st-slots">Posting slots (one per line, e.g. <span class="mono">Tue 09:00</span>)</label>
          <textarea id="st-slots" style="min-height:100px;font-family:var(--mono);font-size:12.5px">${esc(slots().join("\n"))}</textarea>
          <div class="row" style="margin-top:12px"><button class="btn primary" onclick="saveSettings()">Save</button></div></div>`)}
        ${panel("Channels", `<div class="pb">
          ${[["linkedin", "LinkedIn", true], ["x", "X", false], ["reddit", "Reddit", false], ["facebook", "Facebook", false], ["whatsapp", "WhatsApp Channel", false], ["youtube", "YouTube", false]].map(([k, v, on]) => `<div class="chan"><b>${v}</b>${on ? '<span class="chip good">active · manual posting</span>' : '<span class="chip plain">coming later</span>'}</div>`).join("")}
          <p class="faint" style="margin:10px 0 0">Nothing is ever posted automatically. Each future channel is its own agent that adapts an approved LinkedIn post.</p></div>`)}
      </div>
      <div>
        ${panel("Sync", `<div class="pb">
          <p class="muted">Mode: <b>${MODE === "firebase" ? "Firebase live sync" : "local file (pipeline.json) + this device"}</b>${KEY ? ` · key ${esc(KEY.slice(0, 8))}…` : ""}<br>Loaded ${esc(loadedAt ? loadedAt.toLocaleTimeString() : "")} · page built ${esc(D.updated)}</p>
          ${MODE !== "firebase" ? '<p class="faint">Set FIREBASE_URL (secret in the cloud, firebase_url.txt locally) so the agents and every device share one state. Without it, your edits stay in this browser and the agents cannot see them.</p>' : ""}
          <div class="row"><button class="btn sm" onclick="location.reload()">Reload</button><button class="btn sm danger" data-confirm="Forget access on this device?" onclick="confirmThen(this,()=>{localStorage.removeItem('unlock');localStorage.removeItem('boardkey');location.reload()})">Log out of this device</button></div></div>`)}
        ${panel("Running the agents", `<div class="pb">
          <p class="muted">Mode: <b>${D.mode === "api" ? "API (Claude agents draft, ~$0.30/run)" : "free (rules triage + article fetch; you write with your subscription)"}</b>. Set <span class="mono">PIPELINE_MODE</span> in config.py.</p>
          <code class="cmd">python run_pipeline.py            # free: triage + fetch articles (no key)
python run_pipeline.py --mode api # Claude agents draft top ${esc(D.draftsPerRun)} (needs key)
python run_pipeline.py --triage   # only score new stories
python run_pipeline.py --dry-run  # shows what would run
python run_pipeline.py --status</code>
          <p class="faint" style="margin:10px 0 0">In the cloud: free triage runs inside the hourly news job; the “Content pipeline” workflow (API mode) runs only when you start it from the Actions tab.</p></div>`)}
        ${panel("Appearance", `<div class="pb"><div class="row"><button class="btn sm" onclick="$('#themebtn').click()">Toggle dark / light</button></div></div>`)}
      </div></div>`;
}
window.saveSettings = () => { patchDoc("settings", "profile", { personal_note: $("#st-note").value.trim(), audience: $("#st-aud").value.trim(), postsPerWeek: +$("#st-target").value || 4, slots: $("#st-slots").value.split("\n").map(s => s.trim()).filter(Boolean) }); toast("Settings saved" + (MODE === "firebase" ? ". The agents use the note on their next run." : " on this device.")); };

/* ================================================================ boot */
$("#updated").textContent = "news " + D.updated;
$$(".navitem").forEach(a => a.onclick = e => { e.preventDefault(); go(a.dataset.screen); });
async function boot() {
  await loadState();
  go(location.hash.slice(1) || "today");
}
if (LOCKHASH && localStorage.getItem("unlock") !== LOCKHASH) { $("#lock").hidden = false; setTimeout(() => $("#lockcode").focus(), 0); }
else boot();
window.__S = S; window.__D = D; window.checkPost = checkPost; window.patchDoc = patchDoc; window.rerender = rerender;
