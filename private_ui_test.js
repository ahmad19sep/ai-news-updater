/* Offline generated-Studio integration: node private_ui_test.js. Requires jsdom. */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const ROOT = __dirname;
const copy = value => JSON.parse(JSON.stringify(value));
const FIXTURE_TITLE = "Private owner integration fixture";
const ARTICLE = "The research team released an open tool. Its documentation explains the evaluation process and limitations. ".repeat(7);
const POST = "An open research tool is available.\n\nThe team documents its evaluation process and limitations. " + "Read the methodology before choosing it for your work. ".repeat(8);
const now = new Date().toISOString();
const STATE = {
  schema_version: 1, updated: now, _deleted_revisions: {},
  candidates: { story: { id: "story", _revision: 1, title: FIXTURE_TITLE, url: "https://example.com/research", source: "Fixture Research", score: 8, topic: "science", status: "new", reason: "fixture reason", created: now, published: now } },
  sources: { story: { id: "story", _revision: 1, title: FIXTURE_TITLE, url: "https://example.com/research", source: "Fixture Research", excerpt: ARTICLE, chars: ARTICLE.length, quotes: [], thin: false, published: now } },
  drafts: { draft: { id: "draft", _revision: 1, revision: 1, candidate_id: "story", title: FIXTURE_TITLE, url: "https://example.com/research", source: "Fixture Research", topic: "science", post: POST, first_comment: "Source: https://example.com/research", hashtags: ["#research"], claims: [], review_notes: "Private editorial fixture", verify: { verdict: "none", issues: [] }, status: "draft", created: now, channel: "linkedin", format: "text" } },
  settings: { profile: { id: "profile", _revision: 1, personal_note: "Owner-only profile fixture", postsPerWeek: 4, slots: ["Tue 09:00", "Wed 09:00", "Thu 09:00"] } },
  runs: {},
};
let authenticated = false, offlinePatch = false, stateReads = 0, exported = 0, delayNextPatch = false, releasePatch = null;
const requests = [], downloads = [], errors = [], results = [];
const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => copy(body) });
const virtualConsole = new VirtualConsole();
virtualConsole.on("jsdomError", error => errors.push(error.message));
let html = fs.readFileSync(path.join(ROOT, "docs", "studio.html"), "utf8");
html = html.replace(/window\.STUDIO_DATA = ([^\n]*);/, (_, encoded) => {
  const data = JSON.parse(encoded); data.privateApi = "/api"; data.lockHash = ""; data.fbUrl = "";
  return "window.STUDIO_DATA = " + JSON.stringify(data).replace(/<\//g, "<\\/") + ";";
});
const dom = new JSDOM(html, {
  url: "http://127.0.0.1:8765/studio.html", runScripts: "dangerously", pretendToBeVisual: true, virtualConsole,
  beforeParse(window) {
    window.scrollTo = () => {};
    window.open = () => null;
    window.navigator.clipboard = { writeText: async value => { window.__clip = value; } };
    window.URL.createObjectURL = blob => { if (blob.type === "application/json") exported++; return "blob:fixture-export"; };
    window.URL.revokeObjectURL = () => {};
    window.HTMLAnchorElement.prototype.click = function () { downloads.push(this.download); };
    window.EventSource = class { constructor() { throw new Error("Unexpected event stream"); } };
    window.addEventListener("error", event => errors.push(event.message));
    window.fetch = async (input, options = {}) => {
      const url = String(input), method = options.method || "GET";
      requests.push({ url, method });
      if (url === "/api/session" && method === "POST") {
        if (JSON.parse(options.body).passcode !== "test-owner-fixture-only") return response({ error: "Invalid fixture login" }, 401);
        authenticated = true;
        return response({ authenticated: true, csrf_token: "csrf-fixture-value" });
      }
      if (url === "/api/session" && method === "DELETE") {
        if (options.headers["X-Studio-CSRF"] !== "csrf-fixture-value") return response({ error: "CSRF denied" }, 403);
        authenticated = false;
        return response({ authenticated: false, csrf_token: null });
      }
      if (url === "/api/session") return response({ authenticated, csrf_token: authenticated ? "csrf-fixture-value" : null });
      if (url === "/api/state") { stateReads++; return authenticated ? response(STATE) : response({ error: "Sign in required" }, 401); }
      if (url.startsWith("/api/records/") && method === "PATCH") {
        if (offlinePatch) throw new Error("Fixture offline");
        if (!authenticated) return response({ error: "Session expired" }, 401);
        if (options.headers["X-Studio-CSRF"] !== "csrf-fixture-value") return response({ error: "CSRF denied" }, 403);
        const [, , , collection, id] = url.split("/");
        const payload = JSON.parse(options.body), previous = STATE[collection][id] || { id, _revision: 0 };
        if (previous._revision !== payload.expected_revision) return response({ error: "Stale record", current: previous }, 409);
        STATE[collection][id] = { ...previous, ...payload.fields, _revision: previous._revision + 1 };
        const result = response({ record: STATE[collection][id], related_drafts: {} });
        if (delayNextPatch) { delayNextPatch = false; return new Promise(resolve => { releasePatch = () => resolve(result); }); }
        return result;
      }
      if (url.startsWith("pulse.json")) return response({ generated_at: now, trends: [], pain_points: [], meta: { sources_used: [], mode: "raw" } });
      throw new Error("Unexpected network destination");
    };
  },
});
const w = dom.window, d = w.document;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const check = (value, label) => { results.push({ label, passed: Boolean(value) }); console.log((value ? "PASS " : "FAIL ") + label); };
const hasPrivateText = () => d.body.textContent.includes(FIXTURE_TITLE) || d.body.textContent.includes("Owner-only profile fixture");
async function login() { d.getElementById("lockcode").value = "test-owner-fixture-only"; d.getElementById("lockbtn").click(); await sleep(150); }

(async () => {
  await sleep(120);
  check(!d.getElementById("lock").hidden && d.querySelector(".app").inert && stateReads === 0 && !hasPrivateText(), "Initial session lock blocks private state/content");
  d.getElementById("lockcode").value = "invalid-fixture"; d.getElementById("lockbtn").click(); await sleep(40);
  check(!d.getElementById("lock").hidden && stateReads === 0 && d.getElementById("lockerr").textContent.includes("Invalid"), "Rejected login preserves the lock");
  await login();
  check(d.getElementById("lock").hidden && stateReads > 0 && w.__S.drafts.draft && d.getElementById("lockcode").value === "", "Owner login loads private state and clears code field");
  let routes = true;
  for (const route of ["today", "discover", "ideas", "compose", "schedule", "published", "library", "settings"]) {
    w.go(route); await sleep(15);
    routes = routes && !d.getElementById("s-" + route).hidden && d.getElementById("pageTitle").textContent.toLowerCase() === route;
  }
  check(routes, "All eight existing routes render after login");
  w.openDraft("draft"); await sleep(30); w.copyPrompt("draft"); await sleep(10);
  check(w.__clip.includes(ARTICLE) && w.__clip.includes("PERSONAL NOTE"), "Manual writer prompt keeps source context available");
  w.copyPost("draft"); await sleep(10);
  check(w.__clip.startsWith(POST.trim()) && w.__clip.endsWith("#research") && (w.__clip.match(/#research/g) || []).length === 1, "Copy post includes current text and one hashtag suffix");
  w.go("settings"); await sleep(20);
  check(d.getElementById("s-settings").textContent.includes("Private server") && d.getElementById("s-settings").textContent.includes("saved to your private local server") && d.getElementById("syncLabel").textContent === "Saved privately", "Settings and sync label identify private local storage");
  offlinePatch = true; await w.patchDoc("drafts", "draft", { notes: "Fixture pending owner edit" }, true);
  const pending = JSON.parse(w.localStorage.getItem("studio_private_overrides"));
  check(pending.drafts.draft.fields.notes === "Fixture pending owner edit" && !d.getElementById("private-sync-notice").hidden, "Offline edits remain available with an actionable notice");
  w.exportLocalRecovery();
  check(exported === 1 && downloads.includes("studio-pending-edits.json"), "Pending edits export through the Settings action");
  await w.signOutStudio();
  check(authenticated && d.getElementById("lock").hidden, "Sign-out preserves unsynced edits and keeps the session open");
  offlinePatch = false;
  const retry = [...d.querySelectorAll("#private-sync-notice button")].find(button => button.textContent === "Retry saving");
  retry.click(); await sleep(80);
  check(STATE.drafts.draft.notes === "Fixture pending owner edit" && d.getElementById("syncLabel").textContent === "Saved privately", "Retry confirms pending edits at the authoritative server");
  await w.signOutStudio(); await sleep(25);
  check(!authenticated && !d.getElementById("lock").hidden && !hasPrivateText() && Object.keys(w.__S.drafts).length === 0 && w.localStorage.getItem("studio_private_overrides") === null, "Confirmed sign-out clears private DOM/state/cache");
  await login(); w.openDraft("draft"); await sleep(25);
  delayNextPatch = true;
  d.getElementById("ed-post").value = "First buffered edit.";
  d.getElementById("ed-post").dispatchEvent(new w.Event("input", {bubbles:true}));
  await sleep(780);
  check(typeof releasePatch === "function", "Autosave reaches the private transport after debounce");
  d.getElementById("ed-post").value = "Later keystrokes still in the editor.";
  d.getElementById("ed-post").dispatchEvent(new w.Event("input", {bubbles:true}));
  releasePatch(); await sleep(30);
  check(d.getElementById("ed-saved").textContent.includes("pending") && d.querySelector("#ed-editorial-actions .primary").disabled, "An earlier acknowledgement cannot mark newer editor keystrokes saved or approved");
  await sleep(760);
  check(STATE.drafts.draft.edited_post === "Later keystrokes still in the editor.", "Later buffered keystrokes are saved without loss");
  const expiryRevision = STATE.drafts.draft._revision;
  const expiryText = "Latest keystrokes before the session expires.";
  d.getElementById("ed-post").value = expiryText;
  d.getElementById("ed-post").dispatchEvent(new w.Event("input", {bubbles:true}));
  authenticated = false; await w.patchDoc("drafts", "draft", { notes: "Fixture edit after expiry" }, true); await sleep(25);
  const expiryPending = JSON.parse(w.localStorage.getItem("studio_private_overrides")).drafts.draft;
  check(expiryPending.fields.edited_post === expiryText && expiryPending.expected_revision === expiryRevision, "Session expiry retains debounce-buffered keystrokes and their original revision");
  check(!d.getElementById("lock").hidden && !hasPrivateText() && d.getElementById("compose-editor").innerHTML === "" && Object.keys(w.__S.drafts).length === 0, "Session expiry locks and wipes displayed private content");
  check(JSON.parse(w.localStorage.getItem("studio_private_overrides")).drafts.draft.fields.notes === "Fixture edit after expiry", "Session expiry preserves unsynced edit recovery");
  check(requests.every(request => request.url.startsWith("/api/") || request.url.startsWith("pulse.json")), "No Firebase or external network destination is used");
  check(errors.length === 0, "No JSDOM/browser exceptions during the private workflow");
  const failures = results.filter(result => !result.passed).length;
  console.log(`${results.length} checks, ${failures} failures`);
  dom.window.close(); process.exitCode = failures ? 1 : 0;
})().catch(error => { console.log("Integration harness failed: " + error.message); dom.window.close(); process.exitCode = 1; });
