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
  if (ms < 0) return "Upcoming";
  const h = ms / 36e5; if (h < 1) return Math.max(1, Math.round(ms / 6e4)) + "m"; if (h < 48) return Math.round(h) + "h"; return Math.round(h / 24) + "d";
}
function collectionHealth() {
  const date = D.collectedAt;
  const stamp = date ? new Date(date).getTime() : NaN;
  const known = Number.isFinite(stamp) && stamp <= Date.now();
  return { date, known, delayed: known && Date.now() - stamp > 6 * 36e5 };
}
function collectionNotice() {
  const health = collectionHealth();
  if (!health.known) return `<div class="collection-notice"><span class="collection-dot unknown" aria-hidden="true"></span><div><b>Collection time unavailable</b><span>Story dates are shown on each card.</span></div></div>`;
  return `<div class="collection-notice ${health.delayed ? "delayed" : ""}" role="status"><span class="collection-dot" aria-hidden="true"></span><div><b>${health.delayed ? "Showing saved coverage" : "Collection updated recently"}</b><span>Last collected ${esc(fmtDT(health.date))}${health.delayed ? ". Recent stories may be missing." : "."}</span></div><span class="collection-age mono">${esc(ago(health.date))} ago</span></div>`;
}
function fmtDT(d) { if (!d) return ""; const x = new Date(d); if (isNaN(x)) return String(d); return x.toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }); }
function fmtD(d) { if (!d) return ""; const x = new Date(d); if (isNaN(x)) return String(d); return x.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }); }
function fmtT(d) { return new Date(d).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }); }
function toLocalInput(d) { const x = d ? new Date(d) : new Date(); const p = n => String(n).padStart(2, "0"); return `${x.getFullYear()}-${p(x.getMonth() + 1)}-${p(x.getDate())}T${p(x.getHours())}:${p(x.getMinutes())}`; }
function copy(text, msg) { navigator.clipboard.writeText(text).then(() => toast(msg || "Copied"), () => toast("Copy failed. Select the text and copy it manually.")); }
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
const TOPIC_OF_PILLAR = { 1: "models", 2: "coding", 3: "society", 4: "society", 5: "politics_policy", 6: "science", 7: "science", 8: "health", 9: "science", 10: "other" };
const TOPIC_LABEL = { models: "Models", tools: "Tools", coding: "Coding", agents: "Agents", business: "Business", health: "Health", science: "Science", politics_policy: "Policy", security: "Security", education: "Education", society: "Society", other: "Other" };
const STATUS_LABEL = { draft: "Draft", approved: "Approved", scheduled: "Scheduled", published: "Posted", rejected: "Rejected" };

/* Inline icon set (16px stroke). */
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
  panel: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
  download: '<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M4 20h16"/>',
  image: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="m21 16-5-5-7 7"/>',
  inbox: '<path d="M4 4h16v16H4Z"/><path d="M4 14h5l1.5 2h3L15 14h5"/>',
};
const ic = (name, cls = "") => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;
const LI = '<span style="font:700 12px/1 Arial,sans-serif;letter-spacing:-.02em">in</span>';
const isMac = /Mac|iPhone|iPad/.test(navigator.platform || "");
const MOD = isMac ? "⌘" : "Ctrl";

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
    syncOverlayAccess();
    boot();
  } else { $("#lockerr").textContent = "That code is not right. Try again."; }
}
function applyTheme(dark) {
  document.body.classList.toggle("dark", dark);
  $("#themebtn").innerHTML = ic(dark ? "sun" : "moon");
  $("#themebtn").setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
  $("#themebtn").title = dark ? "Switch to light theme" : "Switch to dark theme";
  const m = $('meta[name="theme-color"]'); if (m) m.content = dark ? "#171621" : "#f8f6fb";
  $$(".appearance-option").forEach(button => { const active = button.dataset.theme === (dark ? "dark" : "light"); button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active)); });
}
applyTheme(localStorage.getItem("theme") === "dark");
$("#themebtn").onclick = () => { const d = !document.body.classList.contains("dark"); localStorage.setItem("theme", d ? "dark" : "light"); applyTheme(d); };
$("#lockbtn").onclick = tryUnlock;
$("#lockcode").addEventListener("keydown", e => { if (e.key === "Enter") tryUnlock(); });
$$(".navitem[data-icon]").forEach(a => a.insertAdjacentHTML("afterbegin", ic(a.dataset.icon)));
$("#sidebtn").innerHTML = ic("panel");
const mobileSidebar = () => window.innerWidth <= 760;
function syncOverlayAccess() {
  const blocked = !$("#lock").hidden || !$("#palette").hidden;
  $(".app").inert = blocked;
  const skip = $(".skip-link"); if (skip) skip.inert = blocked || (mobileSidebar() && document.body.classList.contains("sb-open"));
}
function trapFocus(e, container) {
  if (e.key !== "Tab") return;
  const controls = $$("a[href], input, textarea, select, button, [tabindex]", container).filter(el => !el.disabled && !el.hidden && el.tabIndex >= 0 && !el.closest("[hidden]"));
  const first = controls[0], last = controls[controls.length - 1]; if (!first) return;
  if (e.shiftKey && (document.activeElement === first || !container.contains(document.activeElement))) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && (document.activeElement === last || !container.contains(document.activeElement))) { e.preventDefault(); first.focus(); }
}
function syncSidebar() {
  const mobile = mobileSidebar(), visible = mobile ? document.body.classList.contains("sb-open") : !document.body.classList.contains("nosb");
  $("#sidebar").inert = !visible; $("#sidebar").setAttribute("aria-hidden", String(!visible));
  const main = $("#workspace") || $(".main"); if (main) main.inert = mobile && visible;
  $("#sidebtn").setAttribute("aria-expanded", String(visible));
  if ($("#sidebar-backdrop")) $("#sidebar-backdrop").setAttribute("aria-hidden", String(!(mobile && visible)));
  syncOverlayAccess();
}
function closeSidebar() {
  const restoreFocus = document.body.classList.contains("sb-open") || $("#sidebar").contains(document.activeElement);
  document.body.classList.remove("sb-open"); syncSidebar();
  if (restoreFocus && !$("#lock").hidden) return;
  if (restoreFocus && $("#sidebar").inert) $("#sidebtn").focus();
}
$("#sidebtn").onclick = () => {
  if (mobileSidebar()) {
    if (document.body.classList.contains("sb-open")) { closeSidebar(); return; }
    document.body.classList.add("sb-open"); syncSidebar();
    const first = $("#sidebar .navitem.active") || $("#sidebar .navitem"); if (first) first.focus();
  } else { document.body.classList.toggle("nosb"); jsave("nosb", document.body.classList.contains("nosb")); syncSidebar(); }
};
if (jload("nosb", false)) document.body.classList.add("nosb");
closeSidebar();
if ($("#sidebar-backdrop")) $("#sidebar-backdrop").onclick = closeSidebar;
window.addEventListener("resize", closeSidebar);
$("#lock").addEventListener("keydown", e => trapFocus(e, $("#lock")));
$("#sidebar").addEventListener("keydown", e => { if (mobileSidebar() && document.body.classList.contains("sb-open")) trapFocus(e, $("#sidebar")); });
$(".search kbd").textContent = MOD + "K";

/* ================================================================ state */
const S = { candidates: {}, sources: {}, drafts: {}, settings: {}, runs: {} };
let MODE = "file";
let OVR = jload("studio_overrides", {});
let stream = null, loadedAt = null;
const fbRoot = () => `${FBURL}/studio/${KEY}`;
function setCloud(ok) {
  const b = $("#cloudbtn"); b.classList.toggle("off", !ok);
  b.title = MODE === "firebase" ? (ok ? "Live sync on" : "Sync problem: edits are kept on this device") : "Local mode: edits stay on this device";
  b.innerHTML = ic(MODE === "firebase" ? (ok ? "bolt" : "warn") : "disk");
  b.setAttribute("aria-label", b.title);
  const label = $("#syncLabel"); if (label) label.textContent = MODE === "firebase" ? (ok ? "Live sync" : "Saved on this device") : "Local workspace";
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
async function flushOverrides() {
  for (const coll of Object.keys(OVR)) for (const [id, fields] of Object.entries(OVR[coll] || {})) {
    try { const r = await fetch(`${fbRoot()}/${coll}/${id}.json`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(fields) }); if (r.ok) { delete OVR[coll][id]; } } catch (e) { return; }
  }
  jsave("studio_overrides", OVR);
}
function startStream() {
  if (stream || !FBURL) return;
  try {
    stream = new EventSource(fbRoot() + ".json");
    const refresh = debounce(async () => {
      const before = JSON.stringify(canon(S)); await loadStateQuiet(); if (JSON.stringify(canon(S)) === before) return;
      const a = document.activeElement;
      if (a && /^(TEXTAREA|INPUT)$/.test(a.tagName) && a.closest("#compose-editor")) {
        const ed = a.closest("#compose-editor");
        if (!ed.syncPending) {
          ed.syncPending = true;
          const leaveEditor = e => {
            if (e.relatedTarget && ed.contains(e.relatedTarget)) return;
            ed.removeEventListener("focusout", leaveEditor); ed.syncPending = false;
            if (ed.flushEdits) ed.flushEdits();
            setTimeout(() => rerender(), 0);
          };
          ed.addEventListener("focusout", leaveEditor);
        }
        return;
      }
      rerender();
    }, 800);
    stream.addEventListener("put", e => { if (!e.data || e.data === "null") return; refresh(); });
    stream.addEventListener("patch", refresh);
    stream.onerror = () => setCloud(false);
  } catch (e) { stream = null; }
}
/* Firebase returns keys sorted and drops null / empty arrays / empty objects; compare on that shape so a round-trip never counts as a change. */
function canon(v) {
  if (Array.isArray(v)) { const a = v.map(canon).filter(x => x !== undefined); return a.length ? a : undefined; }
  if (v && typeof v === "object") { const o = {}; for (const k of Object.keys(v).sort()) { const c = canon(v[k]); if (c !== undefined) o[k] = c; } return Object.keys(o).length ? o : undefined; }
  return v == null ? undefined : v;
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
const isDue = d => d.status === "scheduled" && d.scheduled_for && new Date(d.scheduled_for) <= new Date();

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
const SCREENS = { today: ["Today", "Your desk"], discover: ["Discover", "Everything the radar collected"], ideas: ["Ideas", "Triage picks and your saves"], compose: ["Compose", "Write, check, approve"], schedule: ["Schedule", "Your posting slots"], published: ["Published", "What went out and how it did"], library: ["Library", "What the writer reads"], settings: ["Settings", ""] };
const ORDER = ["today", "discover", "ideas", "compose", "schedule", "published", "library", "settings"];
let CUR = "today";
function go(name) { if (!$("#lock").hidden) return; if (!SCREENS[name]) name = "today"; const ed = $("#compose-editor"); if (CUR === "compose" && ed && ed.flushEdits) ed.flushEdits(); CUR = name; closeSidebar(); if (location.hash !== "#" + name) history.replaceState(null, "", "#" + name); rerender(); window.scrollTo(0, 0); }
window.addEventListener("hashchange", () => go(location.hash.slice(1) || "today"));
function rerender() {
  $$(".screen").forEach(s => s.hidden = s.id !== "s-" + CUR);
  $$(".navitem").forEach(n => { const active = n.dataset.screen === CUR; n.classList.toggle("active", active); if (active) n.setAttribute("aria-current", "page"); else n.removeAttribute("aria-current"); });
  $("#pageTitle").textContent = SCREENS[CUR][0]; $("#pageSub").textContent = SCREENS[CUR][1];
  $("#topActions").innerHTML = "";
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
const sec = (title, body, sub = "", extra = "") => `<section class="sec"><div class="sh"><h2>${title}</h2><span class="sp">${sub}${extra}</span></div>${body}</section>`;
const emptyBox = (t, s = "", icon = "inbox", action = "") => `<div class="empty"><div class="ei">${ic(icon)}</div><b>${esc(t)}</b>${s ? `<p>${esc(s)}</p>` : ""}${action}</div>`;
const pageIntro = (eyebrow, title, description, actions = "") => `<div class="page-intro"><div><span class="eyebrow intro-kicker">${ic("star")}${esc(eyebrow)}</span><h2>${esc(title)}</h2><p>${esc(description)}</p></div>${actions ? `<div class="welcome-actions">${actions}</div>` : ""}</div>`;
const quickCard = (icon, value, label, action, note = "") => `<button class="quick-card" onclick="${action}"><span class="quick-icon">${ic(icon)}</span><span class="quick-value">${esc(value)}</span><span class="quick-label">${esc(label)}</span>${note ? `<span class="cap">${esc(note)}</span>` : ""}<span class="quick-arrow" aria-hidden="true">↗</span></button>`;
const glyphFor = d => isDue(d) ? "due" : d.status === "draft" ? "draft" : d.status;
const storyScore = it => `<span class="score ${it.scoreKind !== "engagement" && it.sc >= 8 ? "hi" : ""}" title="${it.scoreKind === "engagement" ? "Community " + esc(it.scoreLabel || "votes") : "Audience score"}">${it.sc || "–"}<small>${it.scoreKind === "engagement" ? esc(it.scoreLabel || "votes") : "/10"}</small></span>`;
function draftRow(d, opts = {}) {
  const v = verdictOf(d); const p = postOf(d);
  return `<div class="item ${isDue(d) ? "attn" : ""}" data-id="${d.id}">
    <div class="g" title="${esc(STATUS_LABEL[d.status] || d.status)}"><span class="glyph ${glyphFor(d)}"></span></div>
    <div class="b"><div class="t"><a href="#compose" onclick="openDraft('${d.id}');return false">${esc(d.title)}</a></div>
      <div class="m"><span>${esc(STATUS_LABEL[d.status] || d.status)}</span>${v !== "none" ? `<span><span class="dot ${v === "pass" ? "ok" : v}"></span>checks ${v}</span>` : "<span>manual</span>"}<span>${esc(TOPIC_LABEL[d.topic] || d.topic || "")}</span><span>${esc(d.source || "")}</span>${d.scheduled_for ? `<span>${esc(fmtDT(d.scheduled_for))}</span>` : ""}${d.thin_source ? "<span>thin source</span>" : ""}</div></div>
    <div class="r">${opts.extra || ""}<button class="btn sm ghost keep" onclick="openDraft('${d.id}')">Open</button></div></div>`;
}
function candActions(c) {
  const st = c.status; const a = [];
  if (st === "new" || st === "shortlisted") a.push(`<button class="btn sm keep" onclick="manualDraft('${c.id}')">Write</button>`);
  if (st !== "shortlisted") a.push(`<button class="btn sm icon ghost" title="Shortlist" aria-label="Shortlist" onclick="setCand('${c.id}','shortlisted')">${ic("star")}</button>`);
  if (st === "shortlisted") { if (D.mode === "api") a.push(`<button class="btn sm ghost" title="Copy the command that drafts this with the Claude API" onclick="draftCmd('${c.id}')">Draft with API</button>`); a.push(`<button class="btn sm icon ghost" title="Back to new" aria-label="Back to new" onclick="setCand('${c.id}','new')">${ic("undo")}</button>`); }
  if (st !== "dismissed") a.push(`<button class="btn sm icon ghost" title="Dismiss" aria-label="Dismiss" onclick="setCand('${c.id}','dismissed')">${ic("x")}</button>`); else a.push(`<button class="btn sm icon ghost" title="Restore" aria-label="Restore" onclick="setCand('${c.id}','new')">${ic("undo")}</button>`);
  return a.join("");
}
function candRow(c) {
  return `<div class="item ${c.status === "new" ? "new" : ""}" data-id="${c.id}">
    <div class="g"><span class="score ${c.score >= 8 ? "hi" : ""}" title="score for your audience">${c.score || "–"}</span></div>
    <div class="b"><div class="t"><a href="${esc(candUrl(c))}" target="_blank" rel="noopener">${esc(c.title)}</a></div>
      <div class="m"><span class="chip">${esc(TOPIC_LABEL[c.topic] || c.topic || "")}</span><span>${esc(c.source || "")}</span>${c.urgency === "today" ? '<span class="chip accent">Timely today</span>' : ""}${c.manual ? "<span>Saved by you</span>" : ""}${c.source_ok ? "<span>Source ready</span>" : ""}</div>${c.reason ? `<p class="idea-reason">${esc(c.reason)}</p>` : ""}</div>
    <div class="r"><span class="mono">${esc(ago(c.published))}</span>${candActions(c)}</div></div>`;
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
  const fresh = cands(c => c.status === "new").sort(byScore);
  const picks = fresh.slice(0, 4);
  const run = lastRun(), posted = postedThisWeek(), due = sched.filter(isDue);
  const progress = Math.min(100, Math.round(posted / target() * 100));
  const today = new Date().toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" });
  const nextStory = due[0] || review[0] || approved[0] || picks[0];
  const nextLabel = due.length ? "Share your due post" : review.length ? "Review your next draft" : approved.length ? "Schedule an approved post" : "Find your next idea";
  const nextAction = due.length ? `postNow('${due[0].id}')` : review.length ? `openDraft('${review[0].id}')` : approved.length ? "go('schedule')" : "go('discover')";
  const nextIcon = due.length ? "external" : review.length ? "pen" : approved.length ? "calendar" : "radar";
  const nextState = due.length ? "Ready to share" : review.length ? "Ready for your review" : approved.length ? "Approved by you" : "An idea to explore";
  $("#pageSub").textContent = "Your creative workspace";
  if ($("#workspaceDate")) $("#workspaceDate").textContent = today;
  $("#topActions").innerHTML = `<button class="btn sm" onclick="go('discover')">${ic("radar")}Explore stories</button>`;
  $("#s-today").innerHTML = `
    ${collectionNotice()}
    <div class="today-hero">
      <div class="hero-copy"><div class="hero-eyebrow"><span class="eyebrow">${ic("star")}YOUR CREATIVE WORKSPACE</span><span class="hero-date">${esc(today)}</span></div><h2>Make something<br><em>worth sharing.</em></h2>
        <p>Welcome back, Ahmad. ${review.length ? `You have ${review.length} draft${review.length === 1 ? "" : "s"} ready for your attention.` : fresh.length ? `${fresh.length} new ideas are waiting for your perspective.` : "Your next great post starts with a small spark."} Let's turn a good idea into something worth sharing.</p>
        <div class="welcome-actions"><button class="btn primary" onclick="${nextAction}">${ic(nextIcon)}${nextLabel} <span aria-hidden="true">↗</span></button><button class="btn ghost" onclick="go('${review.length || due.length || approved.length ? "discover" : "ideas"}')">${ic("bulb")}${review.length || due.length || approved.length ? "Explore new stories" : "Your saved ideas"}</button></div>
        <span class="hero-note">Your voice. Your pace. Your final say.</span>
      </div>
      <div class="hero-art" aria-hidden="true"><span class="hero-orbit"></span><div class="hero-sheet sheet-back"></div><div class="hero-sheet sheet-front ${nextStory ? "has-story" : ""}"><div class="sheet-heading">${ic(nextIcon)}<span>${nextStory ? "UP NEXT ON YOUR DESK" : "YOUR NEXT IDEA"}</span></div>${nextStory ? `<p class="sheet-story">${esc(nextStory.title)}</p><span class="sheet-source">${esc(nextStory.source || TOPIC_LABEL[nextStory.topic] || "Your workspace")}</span>` : '<span class="sheet-line line-title"></span><span class="sheet-line"></span><span class="sheet-line"></span><span class="sheet-line line-short"></span>'}<span class="sheet-tag">${nextStory ? nextState : "Made by you"}</span></div><span class="hero-spark">${ic("star")}</span></div>
    </div>
    <div class="quick-grid">
      ${quickCard("bulb", fresh.length, "Fresh ideas", "go('ideas')", "Ready to explore")}
      ${quickCard("pen", review.length, "Drafts to review", "composeFilter='review';go('compose')", "Add your finishing touch")}
      ${quickCard("calendar", sched.length, "In the schedule", "go('schedule')", due.length ? `${due.length} ready to post` : "A little planning goes a long way")}
      ${quickCard("check", `${posted}/${target()}`, "Posts this week", "go('published')", progress >= 100 ? "Weekly goal reached" : `${Math.max(0, target() - posted)} to your weekly goal`)}
    </div>
    ${due.length ? sec("Ready to share", `<div class="list">${due.map(d => draftRow(d, { extra: `<button class="btn sm primary keep" onclick="postNow('${d.id}')">${LI}&nbsp;Post now</button>` })).join("")}</div>`, `<span class="chip accent">${due.length} due</span>`) : ""}
    <div class="dashboard-grid"><div class="dashboard-main">
      ${sec("A fresh perspective", `<div class="list">${picks.length ? picks.map(c => candRow(c)).join("") : emptyBox("Make room for inspiration", "Explore the latest stories and save the ones that interest you.", "bulb", `<button class="btn sm" onclick="go('discover')">Discover stories</button>`)}</div>`, "Your highest-scored new ideas", `<button class="btn sm ghost" onclick="go('ideas')">View all ${ic("external")}</button>`)}
      ${sec("On your writing desk", `<div class="list">${review.length ? review.slice(0, 4).map(d => draftRow(d)).join("") : emptyBox("A clear writing desk", "Choose a story in Ideas and press Write to begin.", "pen", `<button class="btn sm" onclick="go('ideas')">Choose an idea</button>`)}</div>`, `<span class="cnt">${review.length}</span>`, `<button class="btn sm ghost" onclick="go('compose')">Open Compose</button>`)}
      ${sec("From spark to shared", `<div class="flow-steps">${[["radar", "Discover", D.news.length + D.agents.length, "Stories collected", "discover"], ["bulb", "Ideas", cands(c => c.status === "shortlisted").length, "Shortlisted", "ideas"], ["pen", "Compose", review.length + approved.length, "Drafts in progress", "compose"], ["calendar", "Schedule", sched.length, "Posts in the queue", "schedule"]].map(([icon, title, value, label, screen], i) => `<button class="flow-step" onclick="go('${screen}')"><span class="flow-number">0${i + 1}</span>${ic(icon)}<b>${title}</b><span class="cap">${value.toLocaleString()} ${label.toLowerCase()}</span></button>`).join("")}</div>`, "One idea, one thoughtful post")}
    </div><aside class="dashboard-aside">
      <section class="sec insight-card"><div class="sh"><h2>A steady rhythm</h2>${ic("check")}</div><div class="weekly-count"><strong>${posted}<span>/${target()}</span></strong><span>posts this week</span></div><div class="progress-track" role="progressbar" aria-label="Weekly publishing goal" aria-valuemin="0" aria-valuemax="${target()}" aria-valuenow="${Math.min(posted, target())}"><span class="progress-fill" style="width:${progress}%"></span></div><p class="t3">${progress >= 100 ? "You reached your weekly goal. Nice work making space for your ideas." : `${Math.max(0, target() - posted)} more post${target() - posted === 1 ? "" : "s"} to reach your goal. Keep it thoughtful, keep it yours.`}</p><button class="btn sm ghost" onclick="go('settings')">Adjust your rhythm ${ic("external")}</button></section>
      ${sec("Coming up next", `<div class="list">${sched.length ? sched.slice(0, 3).map(d => draftRow(d)).join("") : emptyBox("Your next opening", fmtDT(nextFreeSlot()), "calendar", `<button class="btn sm" onclick="go('schedule')">Plan a post</button>`)}</div>`, "", `<button class="btn sm icon ghost" onclick="go('schedule')" aria-label="Open schedule">${ic("external")}</button>`)}
      <section class="sec insight-card"><span class="eyebrow">WORKSPACE PULSE</span><h3>Your sources, at a glance.</h3><div class="radar-summary"><strong>${new Set(D.news.map(it => it.s).filter(Boolean)).size}<span>feed sources</span></strong><strong>${D.news.length.toLocaleString()}<span>collected stories</span></strong></div><p class="t3">${run ? `Last pipeline run ${esc(fmtDT(run.ts))}.` : "Save a useful story to start your next draft."} ${D.mode === "api" ? "Your agents also draft and check selected ideas." : "Bring your perspective, then write in Compose."}</p><div class="row"><a class="btn sm ghost" href="digests/latest.html" target="_blank" rel="noopener">${ic("book")}Weekly digest</a><button class="btn sm ghost" onclick="go('discover')">${ic("radar")}Explore</button></div></section>
    </aside></div>`;
}
window.postNow = id => { composeId = id; go("compose"); setTimeout(() => { copyPost(id); }, 50); };

/* ================================================================ Discover */
let disc = { sub: "news", q: "", pillar: 0, tab: "", shown: 60, hideSaved: true, sort: "latest", days: 0, view: jload("studio_discovery_view", "cards") === "list" ? "list" : "cards" };
$$("#disc-tabs .subtab").forEach(b => b.onclick = () => { disc.sub = b.dataset.sub; disc.shown = 60; renderDiscover(); });
$("#disc-tabs").addEventListener("keydown", e => {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
  const tabs = $$("#disc-tabs .subtab"), current = tabs.indexOf(e.target); if (current < 0) return;
  const next = e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 : (current + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
  e.preventDefault(); tabs[next].click(); tabs[next].focus();
});
function renderDiscover() {
  if (!$("#disc-intro")) $("#disc-tabs").insertAdjacentHTML("beforebegin", '<div id="disc-intro"></div>');
  $("#disc-intro").innerHTML = pageIntro("A LITTLE CURIOSITY GOES A LONG WAY", "Find the story worth telling.", "Explore what is happening in AI. Save a promising story, then make it your own.", `<button class="btn" onclick="go('ideas')">${ic("bulb")}Your saved ideas</button>`);
  $$("#disc-tabs .subtab").forEach(b => { const active = b.dataset.sub === disc.sub; b.classList.toggle("active", active); b.setAttribute("aria-selected", String(active)); b.tabIndex = active ? 0 : -1; b.setAttribute("aria-controls", "disc-body"); });
  const body = $("#disc-body"); body.setAttribute("role", "tabpanel"); body.setAttribute("aria-labelledby", "tab-" + disc.sub);
  if (disc.sub === "pulse") return renderPulse(body);
  const items = disc.sub === "news" ? D.news : D.agents;
  const q = disc.q.toLowerCase().trim();
  const cutoff = Date.now() - disc.days * 864e5;
  let list = items.filter(it => (!q || (it.t + " " + it.s + " " + (it.sm || "")).toLowerCase().includes(q)) && (!disc.days || (new Date(it.d || it.pub).getTime() >= cutoff && new Date(it.d || it.pub).getTime() <= Date.now())) && (disc.sub !== "news" || !disc.pillar || it.p === disc.pillar) && (disc.sub !== "agents" || !disc.tab || (it.tabs || []).includes(disc.tab)) && (!disc.hideSaved || !S.candidates[it.k]));
  list = list.slice().sort(disc.sort === "score" ? (a, b) => (b.sc || 0) - (a.sc || 0) : (a, b) => String(b.d || b.pub || "").localeCompare(String(a.d || a.pub || "")));
  const chips = disc.sub === "news"
    ? [`<button class="fchip ${!disc.pillar ? "active" : ""}" aria-pressed="${!disc.pillar}" onclick="discSet('pillar',0)">All topics</button>`].concat(Object.entries(D.pillars).map(([k, v]) => `<button class="fchip ${disc.pillar == k ? "active" : ""}" aria-pressed="${disc.pillar == k}" onclick="discSet('pillar',${k})">${esc(v)}</button>`))
    : [`<button class="fchip ${!disc.tab ? "active" : ""}" aria-pressed="${!disc.tab}" onclick="discSet('tab','')">All categories</button>`].concat(D.agentTabs.map(([k, v]) => `<button class="fchip ${disc.tab === k ? "active" : ""}" aria-pressed="${disc.tab === k}" onclick="discSet('tab','${k}')">${esc(v)}</button>`));
  body.innerHTML = `
    ${collectionNotice()}
    <div class="screen-toolbar"><div class="search-field">${ic("search")}<input type="search" id="disc-q" placeholder="Search stories, sources, or ideas…" value="${esc(disc.q)}" aria-label="Search stories"></div>
      <div class="seg" aria-label="Sort stories"><button class="${disc.sort === "latest" ? "active" : ""}" aria-pressed="${disc.sort === "latest"}" onclick="discSet('sort','latest')">Latest</button><button class="${disc.sort === "score" ? "active" : ""}" aria-pressed="${disc.sort === "score"}" onclick="discSet('sort','score')">${disc.sub === "agents" ? "Top signals" : "For your audience"}</button></div>
      <select id="disc-days" class="discovery-period" aria-label="Filter by story date" onchange="discSet('days',Number(this.value))">${[[0, "Any time"], [1, "Past 24 hours"], [7, "Past 7 days"], [30, "Past 30 days"]].map(([days, label]) => `<option value="${days}" ${disc.days === days ? "selected" : ""}>${label}</option>`).join("")}</select>
      <label class="check-label"><input id="disc-hide-saved" type="checkbox" ${disc.hideSaved ? "checked" : ""} onchange="discSet('hideSaved',this.checked)">Hide saved stories</label></div>
    <div class="fchips" aria-label="Filter stories">${chips.join("")}</div>
    ${D.trends.length ? `<div class="trend-shortcuts"><span>${ic("radar")}In this collection</span>${D.trends.slice(0, 5).map(t => { const term = t.term || t.name || ""; return term ? `<button type="button" class="trend-chip" data-trend="${esc(term)}">${esc(term)} <span aria-hidden="true">↗</span></button>` : ""; }).join("")}</div>` : ""}
    <div class="result-meta"><span id="discovery-result-count" role="status"><b>${list.length.toLocaleString()}</b> ${disc.sub === "news" ? "stories" : "agent stories"}${q ? ` matching “${esc(disc.q)}”` : " to explore"}</span><div class="result-controls">${q || disc.pillar || disc.tab || disc.days || disc.hideSaved ? `<button class="btn sm ghost" onclick="resetDiscover()">Reset filters</button>` : ""}<div class="seg view-switch" aria-label="Story layout"><button class="${disc.view === "cards" ? "active" : ""}" aria-pressed="${disc.view === "cards"}" onclick="discSet('view','cards')">Cards</button><button class="${disc.view === "list" ? "active" : ""}" aria-pressed="${disc.view === "list"}" onclick="discSet('view','list')">List</button></div></div></div>
    <div class="story-grid list ${disc.view === "list" ? "story-list-view" : ""}">${list.slice(0, disc.shown).map(it => `<article class="item story-card" data-id="${esc(it.k)}">
      <div class="story-top"><span class="chip">${esc(D.pillars[it.p] || it.primary || "AI")}</span>${storyScore(it)}</div>
      <div class="b"><div class="t"><a href="${esc(it.u)}" target="_blank" rel="noopener">${esc(it.t)}</a></div>${it.sm ? `<p class="story-summary">${esc(it.sm.slice(0, 190))}${it.sm.length > 190 ? "…" : ""}</p>` : ""}<div class="m"><span class="story-source"><span class="source-monogram" aria-hidden="true">${esc((it.s || "AI").charAt(0).toUpperCase())}</span>${esc(it.s)}</span><time datetime="${esc(it.d || it.pub || "")}" title="${esc(fmtDT(it.d || it.pub))}">${esc(ago(it.d || it.pub)) || "Date unavailable"}</time>${(it.l || it.links || []).length ? `<span>+${(it.l || it.links).length} sources</span>` : ""}</div></div>
      <div class="story-actions"><a class="btn sm icon ghost" href="${esc(it.u)}" target="_blank" rel="noopener" aria-label="Read ${esc(it.t)}">${ic("external")}</a>${S.candidates[it.k] ? '<span class="chip ok">Saved to Ideas</span>' : `<button class="btn sm" onclick="saveIdea('${it.k}','${disc.sub}')">${ic("bulb")}Save idea</button>`}</div></article>`).join("") || emptyBox("A fresh search might help", "Try a different topic, clear your filters, or include saved stories.", "search", `<button class="btn sm" onclick="resetDiscover()">Reset filters</button>`)}</div>
    ${list.length > disc.shown ? `<div class="load-more"><button class="btn" onclick="disc.shown+=60;renderDiscover()">Show more stories <span class="cnt">${list.length - disc.shown}</span></button></div>` : ""}`;
  $$(".trend-chip", body).forEach(button => { button.onclick = () => { discSet("q", button.dataset.trend); $("#disc-q").focus(); }; });
  const qi = $("#disc-q"); qi.oninput = debounce(() => { disc.q = qi.value; disc.shown = 60; renderDiscover(); const input = $("#disc-q"); input.focus(); input.setSelectionRange(input.value.length, input.value.length); }, 250);
}
window.resetDiscover = () => { disc.q = ""; disc.pillar = 0; disc.tab = ""; disc.days = 0; disc.hideSaved = false; disc.shown = 60; renderDiscover(); const search = $("#disc-q"); if (search) search.focus(); };
window.discSet = (k, v) => {
  const active = document.activeElement, id = active && active.id, action = active && active.getAttribute("onclick");
  disc[k] = v; if (k === "view") jsave("studio_discovery_view", v); disc.shown = 60; renderDiscover();
  const control = id ? document.getElementById(id) : action ? $$("#disc-body button[onclick]").find(button => button.getAttribute("onclick") === action) : null;
  if (control) control.focus();
};
window.saveIdea = async (k, sub) => {
  const it = (sub === "news" ? D.news : D.agents).find(x => x.k === k); if (!it) return;
  await patchDoc("candidates", k, { title: it.t, url: it.u, source: it.s, category: D.pillars[it.p] || "", published: it.d || it.pub || "", summary: it.sm || "", score: it.scoreKind === "engagement" ? 6 : Math.max(5, Math.min(10, Math.round(it.sc || 6))), topic: TOPIC_OF_PILLAR[it.p] || "other", urgency: "this_week", reason: "saved from Discover", angle_hint: "", status: "shortlisted", manual: true, created: nowIso() });
  toast("Saved to Ideas as shortlisted");
};
let pulseRequest = 0;
async function renderPulse(body) {
  const request = ++pulseRequest;
  body.innerHTML = emptyBox("Gathering the signals…", "Trends and conversations from across platforms.", "radar");
  let p = null; try { const r = await fetch("pulse.json?v=" + D.cache, { cache: "no-store" }); if (r.ok) p = await r.json(); } catch (e) {}
  if (request !== pulseRequest || disc.sub !== "pulse" || CUR !== "discover") return;
  if (!p) { body.innerHTML = emptyBox("The signals are taking a moment", "Pulse could not be loaded. Try refreshing the signals.", "warn", `<button class="btn sm" onclick="renderDiscover()">Try again</button>`); return; }
  const trends = p.trends || [], pains = p.pain_points || [];
  body.innerHTML = `<div class="result-meta"><span>${trends.length} trends · ${pains.length} audience conversations</span><span>Updated ${esc(fmtDT(p.generated_at))}</span><button class="btn sm ghost" onclick="renderDiscover()">Refresh signals</button></div>
    <div class="pulse-grid"><section class="sec"><div class="sh"><h2>What is picking up momentum</h2><span class="chip purple">Across platforms</span></div><div class="pulse-cards">${trends.map(t => `<article class="pulse-card"><div class="row"><span class="chip ${["hot", "rising"].includes(t.momentum) ? "accent" : ""}">${esc(t.momentum || "Signal")}</span><span class="cap">${esc(t.category || "")}</span></div><h3>${esc(t.name)}</h3>${t.linkedin_angle ? `<p>${esc(t.linkedin_angle)}</p>` : ""}<div class="m">${(t.platforms || []).map(x => `<span>${esc(x.replace("_inferred", " (inferred)"))}</span>`).join("")}</div>${(t.sources || [])[0] ? `<a class="btn sm ghost" target="_blank" rel="noopener" href="${esc(t.sources[0].url)}">Explore the signal ${ic("external")}</a>` : ""}</article>`).join("") || emptyBox("No trends in this snapshot", "Check back after the next Pulse run.", "radar")}</div></section>
    <section class="sec"><div class="sh"><h2>Listen to your audience</h2>${ic("message")}</div><div class="pulse-cards">${pains.map(x => `<article class="pulse-card"><span class="eyebrow">A QUESTION WORTH EXPLORING</span><h3>${esc(x.text || x.problem || x.summary || JSON.stringify(x).slice(0, 200))}</h3>${x.url ? `<a class="btn sm ghost" target="_blank" rel="noopener" href="${esc(x.url)}">Read the conversation ${ic("external")}</a>` : ""}</article>`).join("") || emptyBox("A quiet moment", "No audience pain points were detected in this snapshot.", "message")}</div></section></div>
    <p class="cap">Collected from ${esc(((p.meta || {}).sources_used || []).join(", ") || "available platform signals")}. ${esc((p.meta || {}).mode || "")} signals can help you choose a useful angle.</p>`;
}
/* ================================================================ Ideas */
let ideasView = "all";
function renderIdeas() {
  const short = cands(c => c.status === "shortlisted").sort(byScore);
  const fresh = cands(c => c.status === "new").sort(byScore);
  const later = cands(c => ["low", "duplicate", "dismissed", "skipped"].includes(c.status)).sort(byScore);
  $("#topActions").innerHTML = `<button class="btn sm" onclick="go('discover')">${ic("radar")}Discover more</button>`;
  const show = k => ideasView === "all" || ideasView === k;
  const lane = (key, title, subtitle, list, icon, limit = 60) => `<section class="pipeline-lane"><div class="lane-head"><div>${ic(icon)}<h3>${title}</h3><span class="cnt">${list.length}</span></div><p>${subtitle}</p></div><div class="list">${list.slice(0, limit).map(c => candRow(c)).join("") || emptyBox(key === "shortlisted" ? "Keep your favourites here" : key === "new" ? "Waiting for a spark" : "A place for another day", key === "shortlisted" ? "Star a promising idea, or save a story from Discover." : key === "new" ? "New stories arrive after the next triage run." : "Dismissed and lower-scored ideas stay here. You can restore them anytime.", icon)}${list.length > limit ? `<p class="cap lane-more">Showing the top ${limit} of ${list.length} ideas by score.</p>` : ""}</div>${key === "shortlisted" && D.mode === "api" && list.length ? `<button class="btn sm lane-action" onclick="draftCmd('${list[0].id}')">Draft shortlist with API</button>` : ""}</section>`;
  $("#s-ideas").innerHTML = `${pageIntro("MAKE SPACE FOR THE GOOD ONES", "Small sparks. Strong ideas.", "Choose the stories that fit your audience. Star a favourite, start a draft, or leave it for another day.")}
    <div class="screen-toolbar"><div class="seg" aria-label="Idea view">${[["all", "Your pipeline"], ["shortlisted", `Shortlisted ${short.length}`], ["new", `New ${fresh.length}`], ["later", `Later ${later.length}`]].map(([k, v]) => `<button class="${ideasView === k ? "active" : ""}" aria-pressed="${ideasView === k}" onclick="ideasView='${k}';renderIdeas()">${v}</button>`).join("")}</div><span class="cap">Audience scores help you decide. Your perspective does the rest.</span></div>
    <div class="pipeline-grid ${ideasView === "all" ? "" : "single-lane"}">${show("new") ? lane("new", "Fresh discoveries", "New stories, scored for your audience.", fresh, "radar") : ""}${show("shortlisted") ? lane("shortlisted", "The shortlist", "Your favourites, ready for a first draft.", short, "star") : ""}${show("later") ? lane("later", "For another day", "Keep the door open to a different angle.", later, "clock", 80) : ""}</div>`;
}
/* ================================================================ Compose */
let composeId = null, composeFilter = "review", previewMode = jload("previewMode", "mobile");
const pasteBuf = {}; window.pasteBuf = pasteBuf;
function renderCompose() {
  const previous = $("#compose-editor"); if (previous && previous.flushEdits) previous.flushEdits();
  if (!$("#compose-intro")) $("#s-compose .compose").insertAdjacentHTML("beforebegin", '<div id="compose-intro"></div>');
  $("#compose-intro").innerHTML = pageIntro("YOUR WRITING DESK", "Make it yours.", "Your source, your words, your final say.");
  const filt = { review: d => d.status === "draft", approved: d => ["approved", "scheduled"].includes(d.status), all: d => d.status !== "published" }[composeFilter];
  const list = drafts(filt).sort(byCreated);
  if (!composeId || !S.drafts[composeId]) composeId = (list[0] || {}).id || null;
  $("#compose-list").innerHTML = `<div class="clist-heading"><span class="eyebrow">ON YOUR DESK</span><span class="cnt">${list.length}</span></div><div class="seg" aria-label="Filter drafts">${[["review", "To review"], ["approved", "Approved"], ["all", "All open"]].map(([k, v]) => `<button class="${composeFilter === k ? "active" : ""}" aria-pressed="${composeFilter === k}" onclick="composeFilter='${k}';renderCompose()">${v}</button>`).join("")}</div>
    ${list.map(d => `<button class="citem ${d.id === composeId ? "active" : ""}" onclick="composeId='${d.id}';renderCompose()"><div class="t">${esc(d.title)}</div><div class="m"><span class="glyph ${glyphFor(d)}" style="width:10px;height:10px"></span>${esc(STATUS_LABEL[d.status] || d.status)} · ${esc(TOPIC_LABEL[d.topic] || d.topic || "")}${d.manual ? " · manual" : ""}</div></button>`).join("") || emptyBox("Nothing here", "Pick an idea and press Write.", "pen")}`;
  renderEditor(composeId);
}
function stepper(st) {
  const order = ["draft", "approved", "scheduled", "published"]; const i = order.indexOf(st);
  return `<div class="steps">${order.map((s, k) => `<span class="${k < i ? "done" : k === i ? "now" : ""}"><span class="glyph ${k < i ? "published" : k === i ? s : "draft"}" style="width:10px;height:10px;${k < i ? "" : k === i ? "" : "opacity:.5"}"></span>${STATUS_LABEL[s]}</span>`).join("")}${st === "rejected" ? '<span class="now">Rejected</span>' : ""}</div>`;
}
function renderEditor(id) {
  const ed = $("#compose-editor"); if (ed.flushEdits) ed.flushEdits(); ed.flushEdits = null;
  const d = id && S.drafts[id];
  if (!d) { ed.innerHTML = emptyBox("Pick a draft on the left", "Or go to Ideas and press Write on a story.", "pen", `<button class="btn sm" onclick="go('ideas')">Go to Ideas <kbd>3</kbd></button>`); return; }
  const pack = S.sources[d.candidate_id || d.id] || {};
  const st = d.status;
  ed.innerHTML = `
    <div class="toolbar">
      <div class="tt"><h2>${esc(d.title)}</h2><div class="m"><span>${esc(d.source || "")}</span><span><a href="${esc(d.url)}" target="_blank" rel="noopener">source</a></span><span>${esc(TOPIC_LABEL[d.topic] || d.topic || "")}</span>${d.scheduled_for ? `<span>${esc(fmtDT(d.scheduled_for))}</span>` : ""}<span id="ed-saved">saved</span></div></div>
      ${st === "draft" ? `<button class="btn primary" onclick="setDraft('${d.id}',{status:'approved'},'Approved')">Approve <kbd>${MOD}↵</kbd></button>` : ""}
      ${st === "approved" ? `<button class="btn primary" onclick="scheduleNext('${d.id}')">Next free slot <kbd>${MOD}↵</kbd></button>` : ""}
      ${["approved", "scheduled"].includes(st) ? `<button class="btn ghost" onclick="setDraft('${d.id}',{status:'draft'},'Back to review')">Back to review</button>` : ""}
      ${st !== "published" ? `<button class="btn ghost danger" data-confirm="Reject this draft?" onclick="confirmThen(this,()=>setDraft('${d.id}',{status:'rejected'},'Rejected'))">Reject</button>` : ""}
    </div>
    ${stepper(st)}
    ${d.angle && d.angle.angle ? `<p class="t3" style="margin:-6px 0 14px"><span class="label">Angle</span>&nbsp; ${esc(d.angle.angle)}</p>` : ""}
    <div class="epanes">
      <div class="composer">
        <div class="writing-heading"><div><span class="eyebrow writing-kicker">${ic("pen")}THE WRITING SPACE</span><label for="ed-post">Your post</label></div><span class="chip purple">LinkedIn · text</span></div>
        <textarea id="ed-post" class="post-ta" placeholder="Start with a line that makes someone pause. Then tell them something useful, in your own words." spellcheck="true">${esc(postOf(d))}</textarea>
        <div class="metabar" id="ed-counter"></div>
        <div class="field"><label for="ed-comment">First comment (the source link lives here)</label><textarea id="ed-comment" style="min-height:56px">${esc(commentOf(d))}</textarea></div>
        <div class="field"><label for="ed-tags">Hashtags (max 3)</label><input type="text" id="ed-tags" value="${esc((d.hashtags || []).join(" "))}" placeholder="#ai #healthcare"></div>
        <div class="row" style="margin:4px 0 24px">
          <button class="btn" onclick="copyPost('${d.id}')">${ic("copy")}Copy post <kbd>${MOD}⇧C</kbd></button>
          <button class="btn" onclick="copy($('#ed-comment').value,'First comment copied')">${ic("message")}Copy first comment</button>
          <button class="btn li" onclick="window.open('https://www.linkedin.com/feed/?shareActive=true','_blank','noopener')">${LI}&nbsp;Open LinkedIn</button>
          ${st !== "published" ? `<button class="btn" data-confirm="Posted on LinkedIn?" onclick="confirmThen(this,()=>markPosted('${d.id}'))">${ic("check")}Mark as posted</button>` : `<span class="chip ok">posted ${esc(fmtDT(d.published_at))}</span>`}
        </div>
        ${sec("Write with Claude or ChatGPT", `
          <ol class="howto"><li>Copy the writer prompt and paste it into Claude.ai or ChatGPT.</li><li>Paste its answer below and press Parse. Post, first comment, claims and checks fill in.</li><li>Edit in your voice. Optionally run the fact-check the same way.</li></ol>
          ${pack.excerpt ? `<p class="cap" style="margin-bottom:8px"><span class="dot ok"></span>Source text loaded (${pack.chars} chars${pack.thin ? ", thin" : ""}). The prompt uses the real article, not just the headline.</p>` : `<label class="f" for="ed-url">Article address</label><div class="row" style="margin-bottom:6px"><input type="text" id="ed-url" value="${esc(fetchUrlFor(d))}" placeholder="https://publisher.com/the-article" spellcheck="false" style="flex:1;min-width:220px;font-family:var(--mono);font-size:12px"><button class="btn sm" id="ed-fetch" onclick="fetchArticle('${d.id}')">${ic("download")}Fetch article text</button></div>
          <p class="cap" id="ed-fetch-msg" style="margin-bottom:8px">${isGoogleNews(fetchUrlFor(d)) ? "This is a Google News redirect link, which the reader cannot open. Open the story, copy the publisher's address from the browser bar, paste it above and fetch." : "Optional. The prompt works from the headline and feed summary; fetching the article, or pasting a few facts below, gives the writer real numbers and quotes to use."}</p>
          <label class="f" for="ed-facts">Facts to ground your writing</label><textarea id="ed-facts" placeholder="Optional: a few lines of real facts, numbers, quotes copied from the article">${esc(d.facts || "")}</textarea>`}
          <div class="row" style="margin:8px 0"><button class="btn" onclick="copyPrompt('${d.id}')">${ic("copy")}Copy writer prompt</button>
            <button class="btn ghost" id="ed-judge-prompt" onclick="copyJudgePrompt('${d.id}')" ${postOf(d).trim() ? "" : "disabled"}>${ic("search")}Copy fact-check prompt</button>
            <button class="btn ghost" id="ed-image-prompt" onclick="copyImagePrompt('${d.id}')" ${postOf(d).trim() ? "" : "disabled"} title="A LinkedIn-tuned brief: 4:5, one message, readable on a phone, only facts from the post">${ic("image")}Copy image prompt</button></div>
          <div class="field"><label for="ed-paste">Paste the answer</label><textarea id="ed-paste" style="min-height:56px;font-family:var(--mono);font-size:12px" placeholder='{"angles": [...], "post": "...", ...}' oninput="pasteBuf['${d.id}']=this.value">${esc(pasteBuf[d.id] || "")}</textarea></div>
          <div class="row"><button class="btn sm" onclick="parseAnswer('${d.id}')">${ic("play")}Parse answer</button><span class="cap" id="ed-parse-msg"></span></div>`, "your subscription, no API cost")}
        ${(d.claims || []).length ? `<details style="margin-bottom:12px"><summary>Claims and where they come from (${d.claims.length})</summary><table class="claims">${d.claims.map(c => `<tr><td>${esc(c.claim)}</td><td><span class="chip ${c.kind === "reported_fact" ? "ok" : c.kind === "unsupported" ? "bad" : c.kind === "my_interpretation" ? "purple" : "accent"}">${esc(String(c.kind || "").replace(/_/g, " "))}</span> ${esc(c.support)}</td></tr>`).join("")}</table></details>` : ""}
        ${d.visual ? `<details style="margin-bottom:12px"><summary>Writer's image idea</summary><p class="t3" style="white-space:pre-wrap;padding:4px 0 0 17px">${esc(d.visual)}</p><p class="cap" style="padding:6px 0 0 17px">Press Copy image prompt: the brief carries this idea and reshapes it for LinkedIn.</p></details>` : ""}
        ${d.review_notes ? `<details open style="margin-bottom:12px"><summary>Writer's private notes</summary><p class="t3" style="white-space:pre-wrap;padding:4px 0 0 17px">${esc(d.review_notes)}</p></details>` : ""}
        ${pack.excerpt || pack.feed_summary ? `<details style="margin-bottom:12px"><summary>Source pack (${pack.chars || 0} chars${pack.thin ? ", thin" : ""})</summary><div class="excerpt">${esc(pack.excerpt || pack.feed_summary)}</div>${pack.note ? `<p class="cap" style="margin-top:6px">${esc(pack.note)}</p>` : ""}</details>` : ""}
      </div>
      <div class="prevpane">
        <div class="ph"><span class="label">Audience preview</span><div class="seg" aria-label="Preview device"><button data-preview="mobile" class="${previewMode === "mobile" ? "active" : ""}" aria-pressed="${previewMode === "mobile"}" onclick="setPreviewMode('mobile','${d.id}')">Mobile</button><button data-preview="desktop" class="${previewMode === "desktop" ? "active" : ""}" aria-pressed="${previewMode === "desktop"}" onclick="setPreviewMode('desktop','${d.id}')">Desktop</button></div></div>
        <div class="preview ${previewMode}" id="ed-preview"></div>
        <div class="checks"><div class="ph"><span class="label">A final look</span><span id="ed-verdict" aria-live="polite"></span></div><div id="ed-issues"></div>
          ${(d.verify || {}).judge ? `<details style="margin-top:6px"><summary>Fact-checker's verdict</summary><p class="t3" style="padding:4px 0 0 17px">${esc(d.verify.judge.summary || "")}</p><p class="cap" style="padding-left:17px">AI-smell ${esc(d.verify.judge.ai_smell)}/5 · specificity ${esc(d.verify.judge.specificity)}/5</p>${(d.verify.judge.fixes || []).length ? `<ul class="t3" style="margin:6px 0 0;padding-left:34px">${d.verify.judge.fixes.map(f => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}</details>` : ""}</div>
        ${st === "approved" || st === "scheduled" ? `<div class="checks"><div class="ph"><span class="label">Slot</span></div><input type="datetime-local" id="ed-when" aria-label="Posting date and time" value="${esc(toLocalInput(d.scheduled_for || nextFreeSlot()))}"><div class="row" style="margin-top:8px"><button class="btn sm" onclick="saveDraftSlot('${d.id}')">Save slot</button>${st === "scheduled" ? `<button class="btn sm ghost" onclick="setDraft('${d.id}',{status:'approved',scheduled_for:null},'Unscheduled')">Unschedule</button>` : ""}</div></div>` : ""}
      </div>
    </div>`;
  const refresh = () => refreshEditorPanels(d.id);
  let persistTimer = null;
  const saveEdits = () => { clearTimeout(persistTimer); persistTimer = null; const dd = S.drafts[d.id]; if (!dd) return; patchDoc("drafts", d.id, { edited_post: $("#ed-post").value, edited_comment: $("#ed-comment").value, hashtags: ($("#ed-tags").value.match(/#\w+/g) || []), facts: $("#ed-facts") ? $("#ed-facts").value : (dd.facts || "") }, true); const sv = $("#ed-saved"); if (sv) sv.textContent = "saved " + fmtT(new Date()); };
  const persist = () => { clearTimeout(persistTimer); persistTimer = setTimeout(saveEdits, 700); };
  ed.flushEdits = () => { if (persistTimer !== null) saveEdits(); };
  const grow = el => { el.style.height = "auto"; el.style.height = Math.max(320, el.scrollHeight + 4) + "px"; };
  ["ed-post", "ed-comment", "ed-tags", "ed-facts"].forEach(i => { const el = $("#" + i); if (el) el.addEventListener("input", () => { const sv = $("#ed-saved"); if (sv) sv.textContent = "saving…"; if (i === "ed-post") grow(el); refresh(); persist(); }); });
  grow($("#ed-post"));
  refresh();
}
function refreshEditorPanels(id) {
  const d = S.drafts[id]; if (!d) return;
  const post = $("#ed-post") ? $("#ed-post").value : postOf(d);
  ["ed-judge-prompt", "ed-image-prompt"].forEach(id => { const button = $("#" + id); if (button) button.disabled = !post.trim(); });
  const tags = $("#ed-tags") ? ($("#ed-tags").value.match(/#\w+/g) || []) : (d.hashtags || []);
  const pack = S.sources[d.candidate_id || d.id] || {};
  const r = checkPost(post, pack, [(d.angle || {}).angle, (d.angle || {}).hook, d.facts, summaryOf(d)].join(" "), tags);
  const pipe = ((d.verify || {}).issues || []).filter(i => ["unsupported", "attribution", "ai_smell", "vague"].includes(i.code));
  const all = r.issues.concat(pipe);
  const words = post.split(/\s+/).filter(Boolean).length;
  $("#ed-counter").innerHTML = `<span class="${r.chars > 3000 ? "bad" : ""}">${r.chars.toLocaleString()} / 3,000</span><span class="${r.hookLen > 210 ? "bad" : r.hookLen > 140 ? "mid" : r.hookLen ? "ok" : ""}">hook ${r.hookLen} / 140</span><span>${words} words</span><span>${tags.length} tag${tags.length === 1 ? "" : "s"}</span><span class="sp"></span><span>${esc(STATUS_LABEL[d.status] || d.status)}</span>`;
  const verdict = all.some(i => i.level === "fail") ? "fail" : all.length ? "warn" : "pass";
  $("#ed-verdict").innerHTML = `<span class="chip ${verdict === "pass" ? "ok" : verdict}">${verdict}</span>`;
  $("#ed-issues").innerHTML = all.map(i => `<div class="issue"><span class="dot ${i.level === "fail" ? "bad" : "warn"}"></span><span>${esc(i.msg)}</span></div>`).join("") || '<p class="cap">No issues found. Read it once more as your audience would.</p>';
  const cut = previewMode === "desktop" ? 210 : 140;
  const pv = $("#ed-preview"); pv.className = "preview " + previewMode;
  const hook = post.split("\n")[0]; const rest = post.slice(hook.length);
  pv.innerHTML = `<div class="pp"><span class="av">A</span><div><b>Ahmad</b><small>AI x Ahmad · The World of AI, made simple</small><small>Preview · Anyone</small></div></div>
    <div class="body">${esc(hook.slice(0, cut))}${hook.length > cut || rest.trim() ? `<button class="more" type="button" onclick="this.parentNode.innerHTML=this.parentNode.dataset.full">${hook.length > cut ? "" : " "}…more</button>` : ""}</div>
    <div class="bar"><span>Like</span><span>Comment</span><span>Repost</span><span>Send</span></div>`;
  $("#ed-preview .body").dataset.full = esc(post) + (tags.length ? "\n\n" + esc(tags.join(" ")) : "");
}
window.refreshEditorPanels = refreshEditorPanels;
window.setPreviewMode = (mode, id) => { previewMode = mode; jsave("previewMode", mode); $$("[data-preview]").forEach(button => { const active = button.dataset.preview === mode; button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active)); }); refreshEditorPanels(id); };
window.setDraft = (id, fields, msg) => { if (CUR === "compose" && composeId === id && $("#ed-post") && S.drafts[id]) Object.assign(fields, { edited_post: $("#ed-post").value, edited_comment: $("#ed-comment").value }); patchDoc("drafts", id, fields); if (msg) toast(msg); };
window.copyPost = id => { const d = S.drafts[id]; if (!d) return; const tags = ($("#ed-tags") && composeId === id) ? ($("#ed-tags").value.match(/#\w+/g) || []) : (d.hashtags || []); const post = ($("#ed-post") && composeId === id) ? $("#ed-post").value : postOf(d); copy(post.trim() + (tags.length ? "\n\n" + tags.join(" ") : ""), "Post copied. Paste it into LinkedIn, then add the first comment."); };
window.markPosted = async id => {
  const d = S.drafts[id]; if (!d) return;
  await patchDoc("drafts", id, { status: "published", published_at: nowIso(), edited_post: $("#ed-post") ? $("#ed-post").value : postOf(d) }, true);
  if (d.candidate_id) await patchDoc("candidates", d.candidate_id, { status: "published" }, true);
  toast("Marked as posted. Rate it in Published when the numbers come in."); go("published");
};
window.confirmThen = (btn, fn) => { if (btn.dataset.armed) { delete btn.dataset.armed; fn(); return; } const orig = btn.innerHTML; btn.dataset.armed = "1"; btn.textContent = btn.dataset.confirm + " Click again"; setTimeout(() => { if (btn.dataset.armed) { delete btn.dataset.armed; btn.innerHTML = orig; } }, 4000); };

/* Fetch the article from inside the Studio through the r.jina.ai reader. */
const isGoogleNews = u => /^https?:\/\/news\.google\.com\//i.test(String(u || ""));
/* Best address to read: a pack or candidate the pipeline already resolved beats the feed link. */
function fetchUrlFor(d) {
  const cid = d.candidate_id || d.id; const pack = S.sources[cid] || {}; const c = S.candidates[cid] || {};
  return [pack.url, c.resolved_url, d.url].find(u => u && !isGoogleNews(u)) || d.url || "";
}
window.fetchArticle = async id => {
  const d = S.drafts[id]; if (!d) return;
  const box = $("#ed-url"); const url = ((box && box.value) || fetchUrlFor(d) || "").trim();
  const msg = $("#ed-fetch-msg"); const say = (t, bad) => { if (msg) { msg.textContent = t; msg.style.color = bad ? "var(--bad)" : ""; } if (bad) toast(t, 5000); };
  if (!/^https?:\/\/\S+$/i.test(url)) { say("Paste the article's address in the box first.", true); return; }
  if (isGoogleNews(url)) { say("That is a Google News redirect link and the reader is blocked on that domain. The story is opening in a new tab: copy the publisher's address from the browser bar, paste it in the box and fetch again.", true); window.open(url, "_blank", "noopener"); return; }
  const btn = $("#ed-fetch"); if (btn) { btn.disabled = true; btn.textContent = "Fetching…"; }
  try {
    let r; try { r = await fetch("https://r.jina.ai/" + url, { headers: { "Accept": "text/plain", "X-Return-Format": "text" } }); } catch (e) { throw new Error("the reader could not be reached: offline, or an ad-blocker stops r.jina.ai"); }
    if (!r.ok) throw new Error(r.status === 429 ? "the reader is rate-limited, try again in a minute" : (r.status === 403 || r.status === 451) ? "the reader refuses this site (" + r.status + ")" : "reader returned " + r.status);
    let text = await r.text();
    const i = text.indexOf("Markdown Content:"); if (i >= 0) text = text.slice(i + 17);
    text = text.replace(/!\[[^\]]*\]\([^)]*\)/g, "").replace(/\[([^\]]*)\]\([^)]*\)/g, "$1").replace(/[ \t]+/g, " ");
    const paras = text.split(/\n+/).map(x => x.trim()).filter(x => x.length >= 40 && !/^(cookie|subscribe|sign in|share|advertisement)/i.test(x));
    const excerpt = paras.join("\n\n").slice(0, 7000);
    if (excerpt.length < 200) throw new Error("the page gave almost no text (paywall or video?)");
    const quotes = (excerpt.match(/["“]([^"”]{25,320})["”]/g) || []).slice(0, 8).map(q => q.slice(1, -1));
    const cid = d.candidate_id || d.id;
    const flushCurrent = () => { const editor = $("#compose-editor"); if (CUR === "compose" && composeId === id && editor.flushEdits) editor.flushEdits(); };
    flushCurrent();
    await patchDoc("sources", cid, { url, title: d.title, source: d.source, excerpt, chars: excerpt.length, quotes, thin: excerpt.length < 600, ok: excerpt.length >= 600, note: "fetched in the Studio via r.jina.ai", fetched_at: nowIso() }, true);
    flushCurrent();
    const current = S.drafts[id] || d;
    if (url !== current.url) {
      const fields = { url };
      for (const k of ["first_comment", "edited_comment"]) if (current.url && String(current[k] || "").includes(current.url)) fields[k] = String(current[k]).split(current.url).join(url);
      const comment = CUR === "compose" && composeId === id && $("#ed-comment");
      if (comment && current.url) comment.value = comment.value.split(current.url).join(url);
      await patchDoc("drafts", id, fields, true);
    }
    if (S.candidates[cid]) await patchDoc("candidates", cid, { resolved_url: url, source_ok: excerpt.length >= 600, source_chars: excerpt.length }, true);
    if (CUR === "compose" && composeId === id) renderEditor(id);
    toast(`Article fetched: ${excerpt.length} characters of source text`);
  } catch (e) {
    say("Could not fetch the article (" + e.message + "). Paste a few facts from it below instead.", true);
    if (btn) { btn.disabled = false; btn.innerHTML = ic("download") + "Fetch article text"; }
  }
};

/* Manual mode: the same agent prompts, answered by your Claude / ChatGPT
   subscription. The answer is one JSON object; parseAnswer() fills the draft. */
/* The feed summary that came with the headline (pipeline candidates and ideas saved from Discover both carry one). */
const summaryOf = d => { const cid = d.candidate_id || d.id; return String((S.candidates[cid] || {}).summary || (S.sources[cid] || {}).feed_summary || d.summary || "").trim(); };
/* Article text when fetched, else typed facts, else the headline + feed summary with a
   warning. The prompt is never refused: a thin source just gets a stricter brief. */
function sourceBlock(d) {
  const pack = S.sources[d.candidate_id || d.id] || {};
  const facts = $("#ed-facts") ? $("#ed-facts").value.trim() : (d.facts || "");
  const summary = summaryOf(d);
  const text = pack.excerpt || facts || summary;
  const warn = pack.excerpt ? (pack.thin ? "SOURCE WARNING: the article could not be fully fetched — work only with what is here and keep it short and honest." : "")
    : facts ? "SOURCE WARNING: these are facts the creator copied by hand, not the full article — use nothing beyond them."
    : "SOURCE WARNING: only the headline and the feed summary are available. Use no number, name, quote or detail that is not in them; keep the post short and honest, and say what is known rather than guessing.";
  return ["STORY: " + d.title, `SOURCE: ${d.source} (${d.url})` + (pack.published ? "  published " + String(pack.published).slice(0, 10) : ""), warn,
    text ? "SOURCE TEXT:\n" + text : "SOURCE TEXT: (none beyond the headline)", (pack.quotes || []).length ? "QUOTES:\n" + pack.quotes.slice(0, 8).map(q => "- " + q).join("\n") : ""].filter(Boolean).join("\n\n");
}
const sourceKind = d => { const pack = S.sources[d.candidate_id || d.id] || {}; const facts = $("#ed-facts") ? $("#ed-facts").value.trim() : (d.facts || ""); return pack.excerpt ? "article" : facts ? "facts" : "headline"; };
window.copyPrompt = id => {
  const d = S.drafts[id]; const src = sourceBlock(d); const kind = sourceKind(d);
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
    ' "visual":"one sentence: the single image that would belong with this post, built only from facts in it, or empty if a picture would only decorate",',
    ' "review_notes":"", "status":"draft|skip"}'].filter(x => x !== "").join("\n");
  copy(p, kind === "headline" ? "Writer prompt copied from the headline and feed summary. Paste it into Claude.ai or ChatGPT, then paste the JSON answer back here. Fetch the article for a richer post."
    : "Writer prompt copied. Paste it into Claude.ai or ChatGPT, then paste the JSON answer back here.");
};
window.copyImagePrompt = id => {
  const d = S.drafts[id]; if (!d) return;
  const post = ($("#ed-post") && composeId === id) ? $("#ed-post").value.trim() : postOf(d).trim();
  if (!post) { toast("Write or parse the post first. The image is built from it, never from the headline alone."); return; }
  const p = [D.content.image_prompt || "", "", "POST (the image may only say what this says):\n" + post, "", "STORY: " + d.title + "\nSOURCE: " + (d.source || ""),
    d.visual ? "\nTHE WRITER'S IDEA (a starting point; keep only what fits the rules above):\n" + d.visual : ""].filter(Boolean).join("\n");
  copy(p, "Image brief copied. Paste it into ChatGPT or Gemini: it answers with the prompt and alt text, or makes the image directly.");
};
window.copyJudgePrompt = id => {
  const d = S.drafts[id]; const post = $("#ed-post") ? $("#ed-post").value : postOf(d); const src = sourceBlock(d);
  if (!post.trim()) { toast("Nothing to check yet"); return; }
  const p = [D.prompts.judge, "", "POST:\n" + post, "", src || ("STORY: " + d.title + "\nSOURCE TEXT: (none supplied)"),
    "", "OUTPUT: return ONE JSON object only, inside a ```json fence:", '{"unsupported_claims":[], "misattributed":[], "ai_smell":1, "specificity":1, "fixes":[], "summary":""}'].join("\n");
  copy(p, "Fact-check prompt copied. Paste the JSON answer back here.");
};
/* Chat answers are rarely clean JSON: raw line breaks inside strings, trailing commas,
   curly quotes. Try strict first, then progressively repaired copies. */
function repairJson(text) {
  text = text.replace(/,\s*([}\]])/g, "$1");
  let out = "", inStr = false, escd = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (!inStr) { if (ch === '"') inStr = true; out += ch; continue; }
    if (escd) { escd = false; out += ch; }
    else if (ch === "\\") { escd = true; out += ch; }
    else if (ch === '"') {
      // a quote inside a value (He said "yes") is not followed by , } ] or : -- escape it instead of closing the string
      const rest = text.slice(i + 1).match(/^\s*([,}\]:]|$)/); if (rest) { inStr = false; out += ch; } else out += '\\"';
    }
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "";
    else if (ch === "\t") out += "\\t";
    else out += ch;
  }
  return out;
}
function extractJson(text) {
  text = String(text || "").trim();
  if (!text) throw new Error("the box is empty");
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i); if (fence) text = fence[1];
  const a = text.indexOf("{"), b = text.lastIndexOf("}"); if (a < 0 || b <= a) throw new Error("no JSON object found");
  const body = text.slice(a, b + 1); let err = null;
  for (const t of [body, repairJson(body), repairJson(body.replace(/[\u201c\u201d]/g, '"').replace(/[\u2018\u2019]/g, "'"))]) {
    try { return JSON.parse(t); } catch (e) { err = err || e; }
  }
  throw err;
}
window.parseAnswer = async id => {
  const editor = $("#compose-editor"); if (composeId === id && editor.flushEdits) editor.flushEdits();
  const d = S.drafts[id]; const box = $("#ed-paste"); const raw = box ? box.value : (pasteBuf[id] || ""); const msg = $("#ed-parse-msg");
  const say = (text, bad) => { if (msg) { msg.textContent = text; msg.style.color = bad ? "var(--bad)" : ""; } if (bad) toast(text, 4000); };
  if (!d) { say("This draft is no longer loaded. Reload the page.", true); return; }
  if (!raw.trim()) { say("The box is empty. Paste the writer's or the checker's JSON answer first.", true); return; }
  let j; try { j = extractJson(raw); } catch (e) {
    const m = /position (\d+)/.exec(e.message || ""); const at = m ? Number(m[1]) : -1;
    const near = at >= 0 ? " Near: \u201c\u2026" + raw.slice(Math.max(0, at - 60), at + 20).replace(/\s+/g, " ") + "\u2026\u201d" : "";
    say("Could not read that: " + e.message + "." + near + " Fix that spot in the box, or paste the text straight into the post box.", true); return;
  }
  try {
    const pack = S.sources[d.candidate_id || d.id] || {};
    if (typeof j.post === "string") {
      if (j.status === "skip" && !j.post.trim()) { say("The writer says skip: " + (j.review_notes || "no useful angle")); await patchDoc("drafts", id, { review_notes: j.review_notes || "writer suggested skip" }, true); return; }
      const angles = Array.isArray(j.angles) ? j.angles : []; const chosen = angles[Math.min(Number(j.chosen) || 0, Math.max(angles.length - 1, 0))] || null;
      const hashtags = (Array.isArray(j.hashtags) ? j.hashtags : String(j.hashtags || "").split(/\s+/)).map(h => String(h).trim()).filter(Boolean).map(h => h.startsWith("#") ? h : "#" + h).slice(0, 3);
      const r = checkPost(j.post, pack, [(chosen || {}).angle, (chosen || {}).hook, d.facts, summaryOf(d)].join(" "), hashtags);
      await patchDoc("drafts", id, { post: j.post, edited_post: null, first_comment: String(j.first_comment || commentOf(d)), edited_comment: null, hashtags, claims: Array.isArray(j.claims) ? j.claims : [], review_notes: String(j.review_notes || ""), visual: String(j.visual || ""), angle: chosen, format: (chosen || {}).format || d.format || "text", angles, verify: { verdict: r.verdict, issues: r.issues, hook_len: r.hookLen, chars: r.chars, engine: "manual" }, status: d.status === "rejected" ? "draft" : d.status }, true);
      delete pasteBuf[id]; if (CUR === "compose" && composeId === id) renderEditor(id); toast("Draft filled in. Now edit it in your voice.");
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
      delete pasteBuf[id]; if (CUR === "compose" && composeId === id) renderEditor(id); toast("Fact-check applied: " + v.verdict);
      return;
    }
    say("That JSON has neither a post nor a fact-check. Paste the writer's or the checker's answer.", true);
  } catch (e) { console.error(e); say("Parse failed: " + e.message, true); }
};

/* ================================================================ Schedule */
function parseSlot(s) { const m = String(s).trim().match(/^(mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\s+(\d{1,2}):(\d{2})$/i); if (!m || +m[2] > 23 || +m[3] > 59) return null; return { dow: ["sun", "mon", "tue", "wed", "thu", "fri", "sat"].indexOf(m[1].toLowerCase().slice(0, 3)), h: +m[2], m: +m[3] }; }
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
function slotAvailable(when, id) {
  const time = new Date(when).getTime();
  return Number.isFinite(time) && time > Date.now() && !drafts(d => d.id !== id && d.status === "scheduled").some(d => Math.abs(new Date(d.scheduled_for).getTime() - time) < 36e5);
}
window.saveDraftSlot = id => {
  const input = $("#ed-when"), draft = S.drafts[id];
  if (CUR !== "compose" || composeId !== id || !input || !draft || !["approved", "scheduled"].includes(draft.status)) return;
  const time = new Date(input.value).getTime();
  if (!Number.isFinite(time) || time <= Date.now()) { toast("Choose a valid posting date and time in the future."); input.focus(); return; }
  const when = new Date(time).toISOString();
  if (!slotAvailable(when, id)) { toast("That opening is no longer available. Choose another slot."); input.focus(); return; }
  setDraft(id, { status: "scheduled", scheduled_for: when }, "Scheduled for " + fmtDT(when));
};
let scheduleOffset = 0, selectedSlot = null;
window.shiftSchedule = offset => { scheduleOffset = offset === 0 ? 0 : scheduleOffset + offset; selectedSlot = null; renderSchedule(); };
window.selectSlot = when => { selectedSlot = when; renderSchedule(); const picker = $("#slot-picker"); if (picker) picker.focus(); };
window.placeInSlot = id => { if (!id || !selectedSlot) return; const when = selectedSlot, draft = S.drafts[id]; if (!draft || draft.status !== "approved") { toast("Choose a draft that is still approved."); renderSchedule(); return; } if (!slotAvailable(when, id)) { selectedSlot = null; toast("That opening is no longer available. Choose another slot."); renderSchedule(); return; } selectedSlot = null; patchDoc("drafts", id, { status: "scheduled", scheduled_for: when }); toast("Scheduled for " + fmtDT(when)); };
function renderSchedule() {
  const sched = drafts(d => d.status === "scheduled").sort((a, b) => String(a.scheduled_for).localeCompare(String(b.scheduled_for)));
  const approved = drafts(d => d.status === "approved").sort(byCreated);
  const sl = slots().map(parseSlot).filter(Boolean);
  const days = [], start = new Date(); start.setHours(0, 0, 0, 0); start.setDate(start.getDate() + scheduleOffset);
  for (let i = 0; i < 14; i++) { const day = new Date(start); day.setDate(start.getDate() + i); days.push(day); }
  const dayCell = day => {
    const end = new Date(day); end.setDate(day.getDate() + 1);
    const items = sched.filter(d => { const t = new Date(d.scheduled_for); return t >= day && t < end; });
    const free = sl.map(slot => { const t = new Date(day); t.setHours(slot.h, slot.m, 0, 0); return { slot, when: t }; }).filter(({ slot, when }) => slot.dow === day.getDay() && when > new Date() && !sched.some(d => Math.abs(new Date(d.scheduled_for).getTime() - when.getTime()) < 36e5));
    return `<div class="day ${day.toDateString() === new Date().toDateString() ? "today" : ""}"><div class="dh"><span>${esc(day.toLocaleDateString(undefined, { weekday: "short" }))}</span><b>${day.getDate()}</b>${day.toDateString() === new Date().toDateString() ? '<span class="day-today">Today</span>' : ""}</div>
      ${items.map(d => `<button class="slot ${isDue(d) ? "due" : ""}" onclick="openDraft('${d.id}')" aria-label="Open ${esc(d.title)} scheduled for ${esc(fmtDT(d.scheduled_for))}"><b>${esc(fmtT(d.scheduled_for))}</b><span>${esc(String(d.title || "Untitled post").slice(0, 54))}</span>${isDue(d) ? '<small>Ready to post</small>' : ""}</button>`).join("")}
      ${free.map(({ when }) => `<button class="slot free ${selectedSlot === when.toISOString() ? "selected" : ""}" onclick="selectSlot('${when.toISOString()}')" aria-label="Choose free slot ${esc(fmtDT(when))}"><b>${esc(fmtT(when))}</b><span>+ Add a post</span></button>`).join("")}</div>`;
  };
  $("#pageSub").textContent = "A rhythm that works for you";
  $("#topActions").innerHTML = `<button class="btn sm" onclick="go('settings')">${ic("settings")}Posting rhythm</button>`;
  $("#s-schedule").innerHTML = `${pageIntro("GIVE YOUR IDEAS A LITTLE ROOM", "Good timing. Your timing.", "Build a steady publishing rhythm. Choose an open slot or let Studio find the next one for you.")}
    <div class="schedule-heading"><div class="row"><h3>${esc(start.toLocaleDateString(undefined, { month: "long", year: "numeric" }))}${days[13].getMonth() !== start.getMonth() ? ` – ${esc(days[13].toLocaleDateString(undefined, { month: "long" }))}` : ""}</h3><span class="chip purple">${sched.length} queued</span><span class="chip">${approved.length} ready</span></div><div class="row"><span class="cap">${esc(Intl.DateTimeFormat().resolvedOptions().timeZone || "Local time")}</span><button class="btn sm icon ghost" onclick="shiftSchedule(-14)" aria-label="Previous two weeks">‹</button><button class="btn sm" onclick="shiftSchedule(0)">Today</button><button class="btn sm icon ghost" onclick="shiftSchedule(14)" aria-label="Next two weeks">›</button></div></div>
    <section class="sec calendar-panel"><div class="calendar-scroll"><div class="week">${days.slice(0, 7).map(dayCell).join("")}</div><div class="week">${days.slice(7).map(dayCell).join("")}</div></div><div class="calendar-legend"><span><i class="dot accent"></i>Scheduled post</span><span><i class="dot warn"></i>Ready to publish</span><span>+ An opening in your rhythm</span></div></section>
    ${selectedSlot ? `<section class="sec slot-picker" id="slot-picker" tabindex="-1"><div class="sh"><h2>A home for your next post</h2><button class="btn sm icon ghost" onclick="selectedSlot=null;renderSchedule()" aria-label="Close slot selection">${ic("x")}</button></div><p class="t3">Selected: <b>${esc(fmtDT(selectedSlot))}</b></p>${approved.length ? `<div class="row"><select id="slot-draft" aria-label="Approved post to schedule">${approved.map(d => `<option value="${esc(d.id)}">${esc(d.title)}</option>`).join("")}</select><button class="btn primary" onclick="placeInSlot($('#slot-draft').value)">Place on this slot</button></div>` : emptyBox("A little writing first", "Approve a draft in Compose, then place it in this opening.", "pen", `<button class="btn sm" onclick="go('compose')">Open Compose</button>`)}</section>` : ""}
    <div class="cols">${sec("Ready when you are", `<div class="list">${approved.map(d => draftRow(d, { extra: `<button class="btn sm keep" onclick="scheduleNext('${d.id}')">${ic("calendar")}Next free slot</button>` })).join("") || emptyBox("Make something worth sharing", "Approved drafts appear here, ready for a spot on your calendar.", "check", `<button class="btn sm" onclick="go('compose')">Review your drafts</button>`)}</div>`, `<span class="cnt">${approved.length}</span>`)}
      ${sec("Your publishing queue", `<div class="list">${sched.map(d => draftRow(d, { extra: `<button class="btn sm li keep" onclick="postNow('${d.id}')">${LI}&nbsp;Post now</button><button class="btn sm icon ghost" aria-label="Unschedule ${esc(d.title)}" onclick="setDraft('${d.id}',{status:'approved',scheduled_for:null},'Unscheduled')">${ic("x")}</button>` })).join("") || emptyBox("A little space ahead", "Choose an approved draft and give it a time to shine.", "calendar")}</div>`, `<span class="cnt">${sched.length}</span>`)}</div>`;
}
/* ================================================================ Published */
let publishedQuery = "", publishedTopic = "";
function renderPublished() {
  const all = drafts(d => d.status === "published").sort((a, b) => String(b.published_at || "").localeCompare(String(a.published_at || "")));
  const list = all.filter(d => (!publishedQuery || (d.title + " " + postOf(d)).toLowerCase().includes(publishedQuery.toLowerCase())) && (!publishedTopic || d.topic === publishedTopic));
  const rated = all.filter(d => d.rating), avg = rated.length ? (rated.reduce((sum, d) => sum + Number(d.rating), 0) / rated.length).toFixed(1) : "—";
  const month = all.filter(d => new Date(d.published_at).getMonth() === new Date().getMonth() && new Date(d.published_at).getFullYear() === new Date().getFullYear()).length;
  const metric = key => { const recorded = all.filter(d => (d.stats || {})[key] != null); return recorded.length ? recorded.reduce((sum, d) => sum + Number(d.stats[key] || 0), 0).toLocaleString() : "—"; };
  const topics = Array.from(new Set(all.map(d => d.topic).filter(Boolean))).sort();
  $("#topActions").innerHTML = `<button class="btn sm" onclick="exportPublished()">${ic("download")}Export posts</button>`;
  $("#s-published").innerHTML = `${pageIntro("LOOK BACK. LEARN. MAKE THE NEXT ONE BETTER.", "Your words, out in the world.", "Keep a record of what you shared. Add the real numbers and a few notes when the response comes in.")}
    <div class="quick-grid published-metrics">${quickCard("check", all.length, "Posts published", "$('#published-search').focus()", `${month} this month`)}${quickCard("star", avg, "Average rating", "$('#published-log').scrollIntoView({behavior:'smooth'})", `${rated.length} rated posts`)}${quickCard("radar", metric("impressions"), "Recorded impressions", "$('#published-log').scrollIntoView({behavior:'smooth'})", "From the numbers you enter")}${quickCard("message", metric("reactions"), "Recorded reactions", "$('#published-log').scrollIntoView({behavior:'smooth'})", `${metric("comments")} recorded comments`)}</div>
    <div class="screen-toolbar"><div class="search-field">${ic("search")}<input type="search" id="published-search" value="${esc(publishedQuery)}" placeholder="Find a published post…" aria-label="Search published posts"></div><select aria-label="Filter published posts by topic" onchange="publishedTopic=this.value;renderPublished()"><option value="">All topics</option>${topics.map(topic => `<option value="${esc(topic)}" ${publishedTopic === topic ? "selected" : ""}>${esc(TOPIC_LABEL[topic] || topic)}</option>`).join("")}</select><span class="cap">${list.length} ${list.length === 1 ? "post" : "posts"}</span></div>
    <section class="sec" id="published-log"><div class="sh"><h2>The publishing journal</h2><span class="cap">Rate 1–10 · real numbers · useful lessons</span></div><div class="table-scroll"><table class="list published-table"><thead><tr><th>Date</th><th>Post</th><th>Topic</th><th>Rating</th><th>Impressions</th><th>Reactions</th><th>Comments</th><th>Your notes</th><th>Actions</th></tr></thead><tbody>
      ${list.map(d => `<tr><td class="num date-cell">${esc(fmtD(d.published_at))}</td><td class="post-cell"><a href="#compose" onclick="openDraft('${d.id}');return false">${esc(d.title)}</a><div class="cap">${esc(postOf(d).split("\n")[0].slice(0, 100))}</div></td><td><span class="chip">${esc(TOPIC_LABEL[d.topic] || d.topic || "Other")}</span></td>
        <td><select aria-label="Rating for ${esc(d.title)}" onchange="patchDoc('drafts','${d.id}',{rating:+this.value||null})"><option value="">—</option>${[1,2,3,4,5,6,7,8,9,10].map(n => `<option ${d.rating == n ? "selected" : ""}>${n}</option>`).join("")}</select></td>
        ${["impressions", "reactions", "comments"].map(key => `<td><input class="num stat-input" type="number" min="0" aria-label="${key} for ${esc(d.title)}" value="${esc((d.stats || {})[key] ?? "")}" placeholder="—" onchange="statSet('${d.id}','${key}',this.value)"></td>`).join("")}
        <td><input class="post-notes" type="text" value="${esc(d.notes || "")}" placeholder="What did you learn?" aria-label="Notes for ${esc(d.title)}" onchange="patchDoc('drafts','${d.id}',{notes:this.value},true)"></td><td><div class="row"><button class="btn sm icon ghost" aria-label="Copy ${esc(d.title)}" onclick="copyPost('${d.id}')">${ic("copy")}</button><button class="btn sm ghost" onclick="openDraft('${d.id}')">Open</button></div></td></tr>`).join("") || `<tr><td colspan="9">${emptyBox(all.length ? "No posts match that search" : "Your first post is the beginning", all.length ? "Try another word or choose all topics." : "Posts appear here after you mark them as posted in Compose.", "check", `<button class="btn sm" onclick="${all.length ? "publishedQuery='';publishedTopic='';renderPublished()" : "go('compose')"}">${all.length ? "Reset search" : "Open your drafts"}</button>`)}</td></tr>`}</tbody></table></div></section>
    <div class="insight-note">${ic("bulb")}<p>Give each post a little time to find its audience. Your ratings and notes help you understand what is worth writing again.</p></div>`;
  $("#published-search").oninput = debounce(e => { publishedQuery = e.target.value; renderPublished(); const input = $("#published-search"); input.focus(); input.setSelectionRange(input.value.length, input.value.length); }, 250);
}
window.statSet = (id, k, v) => { const d = S.drafts[id]; const n = v === "" ? null : Math.max(0, Number(v) || 0); patchDoc("drafts", id, { stats: Object.assign({}, d.stats || {}, { [k]: n }) }); };
window.exportPublished = () => { const list = drafts(d => d.status === "published").sort((a, b) => String(b.published_at || "").localeCompare(String(a.published_at || ""))); copy(list.map(d => `## ${fmtD(d.published_at)} — ${d.title}\nrating: ${d.rating || "-"} | impressions: ${(d.stats || {}).impressions || "-"} | topic: ${d.topic || ""}\n\n${postOf(d)}\n\n${commentOf(d)}\n`).join("\n---\n\n"), "Markdown copied. Paste the best ones into content/examples.md."); };

/* ================================================================ Library */
let libraryQuery = "", libraryType = "";
window.copyLibraryResource = key => copy((D.content || {})[key] || "", "Reference copied");
window.copyHook = index => { const hook = (D.content.hooks || [])[index]; if (hook) copy(hook.text || hook, "Hook copied"); };
function renderLibrary() {
  const hooks = (D.content.hooks || []).map((h, index) => ({ h, index })).filter(({ h }) => (!libraryType || h.type === libraryType) && (!libraryQuery || (String(h.text || h) + " " + (h.type || "")).toLowerCase().includes(libraryQuery.toLowerCase())));
  const types = Array.from(new Set((D.content.hooks || []).map(h => h.type).filter(Boolean)));
  $("#s-library").innerHTML = `${pageIntro("A REFERENCE SHELF FOR YOUR BEST WORK", "Sound a little more like you.", "Keep your voice close. Browse writing hooks, revisit your guidelines, and learn from your best examples.")}
    <div class="library-grid">${[["voice", "pen", "Your voice", "The perspective, audience, and tone that make this yours.", "Voice profile"], ["rules", "check", "A better LinkedIn post", "The practical guardrails for clear, useful writing.", "LinkedIn rules"], ["examples", "book", "Learn from the good ones", "Reference posts to help shape your next draft.", "Example posts"]].map(([key, icon, title, description, label]) => `<article class="library-card"><div class="library-icon">${ic(icon)}</div><span class="eyebrow">${esc(label)}</span><h3>${esc(title)}</h3><p>${esc(description)}</p><details><summary>Read ${esc(label.toLowerCase())}</summary><pre class="excerpt">${esc(D.content[key] || "No reference added yet.")}</pre></details><button class="btn sm ghost" onclick="copyLibraryResource('${key}')">${ic("copy")}Copy reference</button></article>`).join("")}</div>
    <section class="sec"><div class="sh"><h2>Hook library</h2><span class="cap">A strong first line opens the door.</span></div><div class="screen-toolbar"><div class="search-field">${ic("search")}<input id="hook-search" type="search" value="${esc(libraryQuery)}" placeholder="Find the right opening…" aria-label="Search hooks"></div><select aria-label="Filter hook type" onchange="libraryType=this.value;renderLibrary()"><option value="">Every kind of opening</option>${types.map(type => `<option value="${esc(type)}" ${libraryType === type ? "selected" : ""}>${esc(type)}</option>`).join("")}</select><span class="cap">${hooks.length} hooks</span></div><div class="hook-grid">${hooks.map(({ h, index }) => `<article class="hook"><span class="chip purple">${esc(h.type || "Opening")}</span><p class="tx">${esc(h.text || h)}</p><button class="btn sm icon ghost" aria-label="Copy hook: ${esc(h.text || h)}" onclick="copyHook(${index})">${ic("copy")}</button></article>`).join("") || emptyBox("A different opening might fit", "Try another word or choose every kind of opening.", "search")}</div></section>`;
  $("#hook-search").oninput = debounce(e => { libraryQuery = e.target.value; renderLibrary(); const input = $("#hook-search"); input.focus(); input.setSelectionRange(input.value.length, input.value.length); }, 250);
}
/* ================================================================ Settings */
function renderSettings() {
  const p = settings(), dark = document.body.classList.contains("dark");
  $("#topActions").innerHTML = `<button class="btn sm primary" onclick="saveSettings()">${ic("check")}Save preferences</button>`;
  $("#s-settings").innerHTML = `${pageIntro("A WORKSPACE THAT FEELS LIKE YOURS", "Make yourself at home.", "Set your voice, choose your publishing rhythm, and make a little room for the way you work.")}
    <div class="settings-grid"><div class="settings-column form">
      <section class="sec settings-card"><div class="sh"><h2>${ic("pen")}Your perspective</h2><span class="chip purple">Writing preferences</span></div><p class="t3">A little context helps the writer stay true to your experience.</p><label class="f" for="st-note">Your personal experience</label><textarea id="st-note" placeholder="What have you tried, learned, or seen first-hand?">${esc(p.personal_note || "")}</textarea><p class="cap">Only real experience you want the writer to use in the first person.</p><label class="f" for="st-aud">Who are you writing for?</label><input type="text" id="st-aud" value="${esc(p.audience || "")}" placeholder="e.g. freelancers and small business owners in Pakistan"><p class="cap">Leave this empty to use the audience in your voice profile.</p></section>
      <section class="sec settings-card"><div class="sh"><h2>${ic("calendar")}Your publishing rhythm</h2></div><p class="t3">Consistency should work with your week. Choose a goal and a few good openings.</p><label class="f" for="st-target">Posts each week</label><div class="target-field"><input type="number" id="st-target" min="1" max="14" value="${esc(p.postsPerWeek || 4)}"><span class="t3">A goal to guide you, from 1 to 14.</span></div><label class="f" for="st-slots">Preferred posting slots</label><textarea id="st-slots" class="slots-input" placeholder="Tue 09:00&#10;Thu 09:00">${esc(slots().join("\n"))}</textarea><p class="cap">One per line: day and time, such as Tue 09:00. Times follow your device's timezone.</p><div class="row settings-actions"><button class="btn primary" onclick="saveSettings()">${ic("check")}Save preferences</button><span class="cap" id="settings-save-msg" role="status"></span></div></section>
      <section class="sec settings-card"><div class="sh"><h2>${LI}&nbsp; Your publishing channel</h2><span class="chip ok">LinkedIn</span></div><p class="t3">Studio prepares the post and first comment. You open LinkedIn, share it, and mark it as posted when you are ready.</p><div class="channel-status"><span class="dot ok"></span><span>Connected to your manual publishing workflow</span></div></section>
    </div><div class="settings-column">
      <section class="sec settings-card"><div class="sh"><h2>${ic("sun")}A comfortable space</h2></div><p class="t3">Choose the light that feels right.</p><div class="appearance-options"><button class="appearance-option ${!dark ? "active" : ""}" data-theme="light" aria-pressed="${!dark}" onclick="setStudioTheme(false)"><span class="theme-sample light-sample"></span>${ic("sun")}Light</button><button class="appearance-option ${dark ? "active" : ""}" data-theme="dark" aria-pressed="${dark}" onclick="setStudioTheme(true)"><span class="theme-sample dark-sample"></span>${ic("moon")}Dark</button></div><button class="btn sm ghost" onclick="$('#sidebtn').click()">${ic("panel")}Toggle sidebar</button></section>
      <section class="sec settings-card"><div class="sh"><h2>${ic("bolt")}Your workspace, saved</h2><span class="chip ${MODE === "firebase" ? "ok" : ""}">${MODE === "firebase" ? "Live sync" : "This device"}</span></div><p class="t3">${MODE === "firebase" ? "Your workspace uses Firebase live sync. Changes are kept on this device when a connection is unavailable." : "You are working from a local file. Your edits are saved in this browser on this device."}</p><p class="cap">Loaded ${esc(loadedAt ? loadedAt.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }) : "just now")} · workspace built ${esc(D.updated)}</p><div class="row"><button class="btn sm" onclick="location.reload()">${ic("undo")}Refresh workspace</button><button class="btn sm ghost danger" data-confirm="Forget access on this device?" onclick="confirmThen(this,()=>{localStorage.removeItem('unlock');localStorage.removeItem('boardkey');location.reload()})">Sign out of this device</button></div></section>
      <section class="sec settings-card"><div class="sh"><h2>${ic("bolt")}A few useful shortcuts</h2></div><div class="list">${[["1 – 8", "Move between screens"], [MOD + " K", "Find a screen or action"], [MOD + " \\", "Show or hide the sidebar"], [MOD + " ↵", "Approve or find the next slot"], [MOD + " ⇧ C", "Copy your post"], ["/", "Search in Discover"], ["?", "Open these preferences"], ["Esc", "Close an overlay"]].map(([k, v]) => `<div class="chan"><span class="t3">${esc(v)}</span><kbd>${esc(k)}</kbd></div>`).join("")}</div></section>
      <section class="sec settings-card advanced-settings"><details><summary>Pipeline &amp; advanced setup</summary><p class="t3">${D.mode === "api" ? "API mode: Claude agents draft and verify selected stories." : "Free mode: rules triage and article fetching; write using your subscription."}</p><code class="cmd">python run_pipeline.py
python run_pipeline.py --mode api
python run_pipeline.py --triage
python run_pipeline.py --dry-run
python run_pipeline.py --status</code><button class="btn sm ghost" onclick="copy('python run_pipeline.py','Pipeline command copied')">${ic("copy")}Copy run command</button><p class="cap">Free triage runs inside the hourly news job. Start the Content pipeline workflow in Actions to run API drafting. ${MODE !== "firebase" ? "Configure FIREBASE_URL to share state with your agents and other devices." : ""} Voice references are maintained in the content folder.</p></details></section>
    </div></div>`;
}
window.setStudioTheme = dark => { localStorage.setItem("theme", dark ? "dark" : "light"); applyTheme(dark); };
window.saveSettings = () => {
  const goal = Number($("#st-target").value), inputSlots = $("#st-slots").value.split("\n").map(value => value.trim()).filter(Boolean);
  if (!Number.isInteger(goal) || goal < 1 || goal > 14) { toast("Choose a weekly goal from 1 to 14 posts."); $("#st-target").focus(); return; }
  if (!inputSlots.length || inputSlots.some(value => !parseSlot(value))) { toast("Use a day and time for each slot, such as Tue 09:00."); $("#st-slots").focus(); return; }
  patchDoc("settings", "profile", { personal_note: $("#st-note").value.trim(), audience: $("#st-aud").value.trim(), postsPerWeek: goal, slots: Array.from(new Set(inputSlots)) });
  toast("Preferences saved" + (MODE === "firebase" ? ". Your agents will use them on their next run." : " on this device."));
};
/* ================================================================ command palette + keyboard */
function commands() {
  const list = ORDER.map((s, i) => ({ grp: "Go to", label: SCREENS[s][0], kbd: String(i + 1), run: () => go(s) }));
  const d = composeId && S.drafts[composeId];
  if (CUR === "compose" && d) {
    if (d.status === "draft") list.unshift({ grp: "Draft", label: "Approve this draft", kbd: MOD + "↵", run: () => setDraft(d.id, { status: "approved" }, "Approved") });
    if (d.status === "approved") list.unshift({ grp: "Draft", label: "Schedule next free slot", kbd: MOD + "↵", run: () => scheduleNext(d.id) });
    list.unshift({ grp: "Draft", label: "Copy post", kbd: MOD + "⇧C", run: () => copyPost(d.id) });
    list.unshift({ grp: "Draft", label: "Copy writer prompt", kbd: "", run: () => copyPrompt(d.id) });
  }
  list.push({ grp: "View", label: "Toggle dark / light", kbd: "", run: () => $("#themebtn").click() });
  list.push({ grp: "View", label: "Toggle sidebar", kbd: MOD + "\\", run: () => $("#sidebtn").click() });
  list.push({ grp: "Pipeline", label: "Copy run command", kbd: "", run: () => copy("python run_pipeline.py", "Copied") });
  return list;
}
let palSel = 0, paletteReturnFocus = null;
function openPalette() { if (!$("#lock").hidden) return; paletteReturnFocus = document.body.classList.contains("sb-open") ? $("#sidebtn") : document.activeElement; closeSidebar(); $("#palette").hidden = false; syncOverlayAccess(); const q = $("#pal-q"); q.value = ""; palSel = 0; renderPalette(); q.focus(); }
function closePalette() { $("#palette").hidden = true; syncOverlayAccess(); if (mobileSidebar() && document.body.classList.contains("sb-open")) { const active = $("#sidebar .navitem.active") || $("#sidebar .navitem"); if (active) active.focus(); } else if (paletteReturnFocus && paletteReturnFocus.isConnected && !paletteReturnFocus.closest("[hidden], [inert]")) paletteReturnFocus.focus(); else if ($("#workspace")) $("#workspace").focus(); }
function renderPalette() {
  const q = $("#pal-q").value.toLowerCase().trim();
  const items = commands().filter(c => !q || (c.grp + " " + c.label).toLowerCase().includes(q));
  palSel = Math.max(0, Math.min(palSel, items.length - 1));
  $("#pal-list").innerHTML = items.map((c, i) => `<div class="pal-item ${i === palSel ? "sel" : ""}" id="pal-option-${i}" data-i="${i}" role="option" aria-selected="${i === palSel}"><span class="grp">${esc(c.grp)}</span><span>${esc(c.label)}</span>${c.kbd ? `<kbd>${esc(c.kbd)}</kbd>` : ""}</div>`).join("") || '<div class="pal-item"><span class="grp">No match</span></div>';
  if (items.length) $("#pal-q").setAttribute("aria-activedescendant", "pal-option-" + palSel); else $("#pal-q").removeAttribute("aria-activedescendant");
  $$("#pal-list .pal-item[data-i]").forEach(el => el.onclick = () => { items[+el.dataset.i].run(); closePalette(); });
  $("#pal-list")._items = items;
}
$("#pal-q").addEventListener("input", () => { palSel = 0; renderPalette(); });
$("#pal-q").addEventListener("keydown", e => {
  const items = $("#pal-list")._items || [];
  if (e.key === "ArrowDown") { palSel = Math.min(palSel + 1, items.length - 1); renderPalette(); e.preventDefault(); }
  else if (e.key === "ArrowUp") { palSel = Math.max(palSel - 1, 0); renderPalette(); e.preventDefault(); }
  else if (e.key === "Enter") { if (items[palSel]) { items[palSel].run(); closePalette(); } }
});
$("#palette").addEventListener("click", e => { if (e.target.id === "palette") closePalette(); });
$("#palette").addEventListener("keydown", e => {
  if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closePalette(); return; }
  trapFocus(e, $("#palette"));
});
$("#palettebtn").onclick = openPalette;
window.openPalette = openPalette;
document.addEventListener("keydown", e => {
  if (!$("#lock").hidden) return;
  const mod = isMac ? e.metaKey : e.ctrlKey;
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target || {}).tagName) || (e.target || {}).isContentEditable;
  if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); $("#palette").hidden ? openPalette() : closePalette(); return; }
  if (!$("#palette").hidden) return;
  if (mod && e.key === "\\") { e.preventDefault(); $("#sidebtn").click(); return; }
  if (mobileSidebar() && document.body.classList.contains("sb-open")) { if (e.key === "Escape") { e.preventDefault(); closeSidebar(); } return; }
  const d = composeId && S.drafts[composeId];
  if (mod && e.key === "Enter" && CUR === "compose" && d) { e.preventDefault(); if (d.status === "draft") setDraft(d.id, { status: "approved" }, "Approved"); else if (d.status === "approved") scheduleNext(d.id); return; }
  if (mod && e.shiftKey && e.key.toLowerCase() === "c" && CUR === "compose" && d) { e.preventDefault(); copyPost(d.id); return; }
  if (typing || mod || e.altKey) return;
  if (e.key >= "1" && e.key <= "8") { go(ORDER[+e.key - 1]); return; }
  if (e.key === "/") { e.preventDefault(); if (CUR !== "discover") go("discover"); const q = $("#disc-q"); if (q) q.focus(); return; }
  if (e.key === "?") { go("settings"); return; }
  if (e.key === "Escape") { if (document.body.classList.contains("sb-open")) closeSidebar(); else document.activeElement && document.activeElement.blur(); }
});

/* ================================================================ boot */
$$(".navitem").forEach(a => a.onclick = e => { e.preventDefault(); go(a.dataset.screen); });
async function boot() {
  if ($("#workspaceDate")) $("#workspaceDate").textContent = new Date().toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" });
  await loadState();
  go(location.hash.slice(1) || "today");
}
if (LOCKHASH && localStorage.getItem("unlock") !== LOCKHASH) { $("#lock").hidden = false; syncOverlayAccess(); setTimeout(() => $("#lockcode").focus(), 0); }
else boot();
window.__S = S; window.__D = D; window.checkPost = checkPost; window.patchDoc = patchDoc; window.rerender = rerender;
