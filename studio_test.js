/* Studio UI test — boots docs/studio.html in JSDOM with a fake pipeline state
   and drives the whole flow: Today -> Ideas (shortlist) -> Compose (edit,
   checks, approve) -> Schedule (slot) -> mark posted -> Published (rate) ->
   Settings (save). No network: fetch is stubbed.

     npm i --no-save jsdom && node studio_test.js
*/
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

// The deployed page carries the real lock hash + Firebase URL; the test runs the
// same code unlocked and in local-file mode so it never touches the network.
const html = fs.readFileSync(path.join(__dirname, "docs", "studio.html"), "utf8")
  .replace(/"lockHash": ?"[0-9a-f]*"/, '"lockHash": ""').replace(/"fbUrl": ?"[^"]*"/, '"fbUrl": ""');
const ARTICLE = "Acme Health said its triage assistant cut average waiting time by 32% across 4 clinics in Lahore. The pilot ran for 6 months.";
const STATE = {
  candidates: {
    c1: { id: "c1", title: "Lahore clinics cut waiting time with AI triage", url: "https://example.com/1", source: "Acme", score: 9, topic: "health", status: "new", reason: "real outcome", angle_hint: "paperwork not doctors", published: new Date().toISOString() },
    c2: { id: "c2", title: "OpenAI drops price of smallest model", url: "https://example.com/2", source: "OpenAI", score: 7, topic: "models", status: "new", reason: "cost change", published: new Date().toISOString() },
    c3: { id: "c3", title: "Some low story", url: "https://example.com/3", source: "x", score: 4, topic: "other", status: "low" },
  },
  sources: { c1: { title: "Lahore clinics cut waiting time with AI triage", excerpt: ARTICLE, chars: ARTICLE.length, quotes: [], thin: false } },
  drafts: {
    c1: { id: "c1", candidate_id: "c1", title: "Lahore clinics cut waiting time with AI triage", url: "https://example.com/1", source: "Acme", topic: "health", score: 9, format: "text",
          post: "A clinic group in Lahore cut waiting time by 32%. The AI never touched a diagnosis.\n\nAcme Health says its assistant handled intake across 4 clinics for 6 months. " + "More detail here. ".repeat(20),
          first_comment: "Source: Acme — https://example.com/1", hashtags: ["#ai", "#healthcare"], claims: [{ claim: "32% cut", support: "cut average waiting time by 32%", kind: "reported_fact" }],
          review_notes: "interpretation in para 3", verify: { verdict: "pass", issues: [], judge: { summary: "fine", ai_smell: 2, specificity: 4, fixes: [] } }, status: "draft", created: new Date().toISOString(), channel: "linkedin" },
  },
  settings: { profile: { slots: ["Mon 09:00", "Tue 09:00", "Wed 09:00", "Thu 09:00", "Fri 09:00", "Sat 09:00", "Sun 09:00"], postsPerWeek: 4 } },
  runs: { r1: { ts: new Date().toISOString(), cost: { usd: 0.21 }, summary: "drafts:1" } },
};
const PULSE = { generated_at: new Date().toISOString(), meta: { sources_used: ["reddit"], mode: "raw" }, trends: [{ name: "Claude", momentum: "hot", category: "tool", platforms: ["reddit"], linkedin_angle: "why", sources: [{ url: "https://r.example" }] }], pain_points: [{ text: "rate limits" }] };

const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://ahmad19sep.github.io/ai-news-updater/studio.html",
  beforeParse(window) {
    window.crypto = require("crypto").webcrypto;
    window.fetch = async (url, opts = {}) => {
      const u = String(url);
      const ok = body => ({ ok: true, status: 200, json: async () => body });
      if (u.startsWith("pipeline.json")) return ok(JSON.parse(JSON.stringify(STATE)));
      if (u.startsWith("pulse.json")) return ok(PULSE);
      throw new Error("unexpected fetch " + u + " " + (opts.method || "GET"));
    };
    window.navigator.clipboard = { writeText: async t => { window.__clip = t; } };
    window.open = () => null;
    window.scrollTo = () => {};
    window.EventSource = undefined;
  } });
const w = dom.window, d = w.document;
const fails = [];
const ok = (cond, msg) => { if (!cond) fails.push(msg); console.log((cond ? "  ok   " : "  FAIL ") + msg); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const visible = id => !d.getElementById("s-" + id).hidden;

(async () => {
  await sleep(300);
  ok(d.getElementById("lock").hidden, "no passcode baked in -> lock hidden");
  ok(visible("today"), "Today renders first");
  ok(d.getElementById("s-today").textContent.includes("Drafts to review"), "Today shows drafts awaiting review");
  ok(d.getElementById("nc-ideas").textContent === "2", "Ideas nav count = 2 new candidates");
  ok(d.getElementById("nc-compose").textContent === "1", "Compose nav count = 1 draft");
  ok(d.getElementById("s-today").textContent.includes("0/4"), "Today shows the actual weekly progress");
  const ideaQuickCard = Array.from(d.querySelectorAll("#s-today button")).find(button => button.textContent.includes("Fresh ideas"));
  ideaQuickCard.click(); ok(visible("ideas"), "dashboard idea metric opens Ideas");
  ok(d.querySelector('[data-screen="ideas"]').getAttribute("aria-current") === "page", "navigation identifies the current screen");
  const originalWidth = w.innerWidth; Object.defineProperty(w, "innerWidth", { value: 390, configurable: true });
  d.getElementById("sidebtn").click(); ok(d.body.classList.contains("sb-open") && d.getElementById("sidebtn").getAttribute("aria-expanded") === "true", "mobile sidebar opens with accurate expanded state");
  ok(!d.getElementById("sidebar").inert && d.getElementById("workspace").inert && d.activeElement.closest("#sidebar") && d.getElementById("sidebar-backdrop").getAttribute("aria-hidden") === "false", "open mobile navigation takes focus and makes the workspace inert");
  ok(d.querySelector(".skip-link").inert, "mobile navigation disables the outside skip link");
  d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "7", bubbles: true }));
  ok(visible("ideas"), "mobile drawer blocks workspace navigation shortcuts");
  d.querySelector('[data-screen="today"]').click(); ok(!d.body.classList.contains("sb-open") && visible("today"), "mobile navigation closes the sidebar");
  ok(d.getElementById("sidebar").inert && !d.getElementById("workspace").inert && d.activeElement.id === "sidebtn", "closing mobile navigation restores workspace access and toggle focus");
  d.getElementById("sidebtn").click(); d.getElementById("sidebar-backdrop").click(); ok(!d.body.classList.contains("sb-open"), "mobile backdrop closes the sidebar");
  d.getElementById("sidebtn").click(); d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  ok(!d.body.classList.contains("sb-open") && d.activeElement.id === "sidebtn", "Escape closes mobile navigation without clearing restored focus");
  d.getElementById("sidebtn").click(); d.getElementById("sidebar-close").click();
  ok(d.getElementById("sidebar").inert && d.activeElement.id === "sidebtn", "the mobile drawer close button restores toggle focus");
  Object.defineProperty(w, "innerWidth", { value: originalWidth, configurable: true });
  w.dispatchEvent(new w.Event("resize")); d.getElementById("sidebtn").click();
  ok(d.getElementById("sidebar").inert && !d.getElementById("workspace").inert, "collapsed desktop navigation is removed from keyboard focus");
  d.getElementById("sidebtn").click();

  w.go("discover"); await sleep(50);
  ok(visible("discover") && d.querySelectorAll("#disc-body .item").length > 10, "Discover lists news cards");
  const q = d.getElementById("disc-q"); q.value = "zzzz-nothing"; q.dispatchEvent(new w.Event("input")); await sleep(400);
  ok(!d.querySelector("#disc-body .item") && d.getElementById("disc-body").textContent.includes("fresh search"), "Discover search filters to an actionable empty result");
  w.discSet("q", "");
  d.getElementById("tab-news").focus(); d.getElementById("tab-news").dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
  ok(d.getElementById("tab-agents").getAttribute("aria-selected") === "true" && d.activeElement.id === "tab-agents" && d.getElementById("disc-body").getAttribute("aria-labelledby") === "tab-agents", "arrow keys move and select the Discover tabs accessibly");
  w.discSet("q", ""); w.discSet("sub", "agents"); await sleep(50);
  ok(d.querySelectorAll("#disc-body .fchip").length > 3, "Agents & AI chips render");
  w.discSet("sub", "pulse"); await sleep(200);
  ok(d.getElementById("disc-body").textContent.includes("Claude") && d.getElementById("disc-body").textContent.includes("rate limits"), "Pulse renders trends + pain points");
  w.discSet("sub", "news"); await sleep(50);
  const normalFetch = w.fetch; let finishPulse;
  w.fetch = (url, opts) => String(url).startsWith("pulse.json") ? new Promise(resolve => { finishPulse = () => resolve({ ok: true, json: async () => PULSE }); }) : normalFetch(url, opts);
  w.discSet("sub", "pulse"); w.discSet("sub", "news"); finishPulse(); await sleep(30);
  ok(d.getElementById("disc-q") && d.getElementById("tab-news").getAttribute("aria-selected") === "true", "a late Pulse response cannot overwrite the News tab");
  w.fetch = normalFetch;
  const firstKey = w.__D.news[0].k; await w.saveIdea(firstKey, "news"); await sleep(50);
  ok(w.__S.candidates[firstKey] && w.__S.candidates[firstKey].status === "shortlisted", "Save as idea creates a shortlisted candidate");

  w.go("ideas"); await sleep(50);
  ok(visible("ideas") && d.getElementById("s-ideas").textContent.includes("Fresh discoveries") && d.getElementById("s-ideas").textContent.includes("The shortlist") && d.getElementById("s-ideas").textContent.includes("For another day"), "Ideas shows new, shortlisted and later groups");
  w.setCand("c2", "shortlisted"); await sleep(50);
  ok(w.__S.candidates.c2.status === "shortlisted", "shortlist works");
  w.draftCmd("c2"); ok(/run_pipeline\.py --mode api --draft --ids .*c2/.test(w.__clip), "draft command copied with ids: " + w.__clip);
  const ovr = JSON.parse(w.localStorage.getItem("studio_overrides"));
  ok(ovr.candidates && ovr.candidates.c2.status === "shortlisted", "local-mode edits persisted to localStorage overrides");
  await w.manualDraft("c2"); await sleep(50);
  ok(visible("compose") && w.__S.drafts.c2 && w.__S.drafts.c2.manual, "Write myself creates a manual draft and opens Compose");
  ok(d.getElementById("ed-facts"), "manual draft shows the facts box");
  ok(d.getElementById("ed-image-prompt").disabled && d.getElementById("ed-judge-prompt").disabled, "empty drafts disable image and fact-check prompts");
  d.getElementById("ed-post").value = "A post being typed now."; d.getElementById("ed-post").dispatchEvent(new w.Event("input"));
  ok(!d.getElementById("ed-image-prompt").disabled && !d.getElementById("ed-judge-prompt").disabled, "typing a post enables image and fact-check prompts immediately");
  d.getElementById("ed-post").value = " "; d.getElementById("ed-post").dispatchEvent(new w.Event("input"));
  ok(d.getElementById("ed-image-prompt").disabled && d.getElementById("ed-judge-prompt").disabled, "clearing a post disables image and fact-check prompts again");
  w.copyPrompt("c2"); await sleep(30); ok(/STORY: OpenAI drops price/.test(w.__clip) && /SOURCE WARNING: only the headline/.test(w.__clip) && /headline and feed summary/.test(d.getElementById("toast").textContent), "prompt copies from the headline + summary when there is no article text");
  ok(d.getElementById("ed-fetch"), "fetch-article button offered when no source text");
  w.fetch = async (url, opts = {}) => { if (String(url).startsWith("https://r.jina.ai/")) return { ok: true, status: 200, text: async () => "Title: x\nURL Source: y\nMarkdown Content:\n" + "The company said prices fell 40% for API users from 15 October, according to the announcement. ".repeat(8) + "\n\n\"We want this to be the default,\" said Sarah Chen, head of platform." }; const ok2 = body => ({ ok: true, status: 200, json: async () => body }); if (String(url).startsWith("pipeline.json")) return ok2(STATE); if (String(url).startsWith("pulse.json")) return ok2(PULSE); throw new Error("unexpected fetch " + url); };
  w.__S.drafts.c2.url = "https://news.google.com/rss/articles/abc?oc=5"; w.__S.drafts.c2.first_comment = "Source: OpenAI — https://news.google.com/rss/articles/abc?oc=5"; w.rerender(); await sleep(30);
  ok(/Google News/.test(d.getElementById("ed-fetch-msg").textContent), "Google News link is explained before fetching");
  await w.fetchArticle("c2"); await sleep(30);
  ok(!w.__S.sources.c2 && /Google News/.test(d.getElementById("ed-fetch-msg").textContent), "fetch refuses the Google News link instead of calling the reader");
  d.getElementById("ed-url").value = "https://example.com/2";
  d.getElementById("ed-post").value = "Keep this edit while the article loads."; d.getElementById("ed-post").dispatchEvent(new w.Event("input"));
  d.getElementById("ed-comment").value = "My comment: https://news.google.com/rss/articles/abc?oc=5"; d.getElementById("ed-comment").dispatchEvent(new w.Event("input"));
  await w.fetchArticle("c2"); await sleep(50);
  ok(w.__S.sources.c2 && w.__S.sources.c2.excerpt.includes("40%") && w.__S.sources.c2.quotes.length === 1, "in-Studio fetch builds a source pack with quotes");
  ok(w.__S.drafts.c2.url === "https://example.com/2" && w.__S.drafts.c2.first_comment === "Source: OpenAI — https://example.com/2", "publisher URL replaces the Google News link in the draft and first comment");
  ok(d.getElementById("ed-post").value === "Keep this edit while the article loads." && w.__S.drafts.c2.edited_post === "Keep this edit while the article loads." && d.getElementById("ed-comment").value === "My comment: https://example.com/2", "article fetching preserves pending edits and updates the edited source link");
  ok(!d.getElementById("ed-facts") && d.getElementById("compose-editor").textContent.includes("Source text loaded"), "editor switches to the loaded-source state");
  w.copyPrompt("c2"); ok(/SOURCE TEXT/.test(w.__clip) && /15 October/.test(w.__clip), "prompt now carries the fetched article");
  delete w.__S.sources.c2; w.OVR && delete w.OVR; w.localStorage.setItem("studio_overrides", JSON.stringify({})); w.rerender(); await sleep(30);
  d.getElementById("ed-facts").value = "Price fell 40%."; w.copyPrompt("c2"); ok(/SOURCE TEXT/.test(w.__clip) && /Price fell 40%/.test(w.__clip), "prompt copied with facts");
  const quickEdit = d.getElementById("ed-post"); quickEdit.value = "The last words before switching drafts."; quickEdit.dispatchEvent(new w.Event("input"));
  w.openDraft("c1");
  ok(w.__S.drafts.c2.edited_post === "The last words before switching drafts.", "switching drafts flushes edits before the autosave timer");
  w.openDraft("c2"); d.getElementById("ed-post").value = ""; d.getElementById("ed-post").dispatchEvent(new w.Event("input")); w.go("ideas");
  ok(w.__S.drafts.c2.edited_post === "", "leaving Compose flushes the latest edit immediately");

  w.openDraft("c1"); await sleep(50);
  ok(d.getElementById("ed-post").value.startsWith("A clinic group"), "Compose loads the pipeline draft");
  ok(d.getElementById("ed-verdict").textContent.trim() === "pass", "checks pass on the good draft");
  ok(d.getElementById("ed-preview").textContent.includes("A clinic group"), "LinkedIn preview shows the hook");
  const ta = d.getElementById("ed-post"); ta.value = ta.value.replace("32%", "57%") + "\n\nThis is a game changer."; ta.dispatchEvent(new w.Event("input")); await sleep(900);
  ok(d.getElementById("ed-verdict").textContent.trim() === "fail", "invented number + banned phrase -> fail");
  ok(d.getElementById("ed-issues").textContent.includes("57%") && d.getElementById("ed-issues").textContent.includes("game changer"), "issues list names the problems");
  ok(w.__S.drafts.c1.edited_post.includes("57%"), "edits persisted to the draft (edited_post)");
  ta.value = w.__S.drafts.c1.post; ta.dispatchEvent(new w.Event("input")); await sleep(900);
  ok(d.getElementById("ed-verdict").textContent.trim() === "pass", "restoring the text passes again");
  const r = w.checkPost("x".repeat(230) + "\n\nbody", {}, "", []); ok(r.issues.some(i => i.code === "hook" && i.level === "fail"), "checkPost: long hook fails");

  w.setDraft("c1", { status: "approved" }); await sleep(50);
  ok(w.__S.drafts.c1.status === "approved" && d.getElementById("ed-when"), "approve -> schedule box appears");
  d.getElementById("ed-when").value = ""; w.saveDraftSlot("c1");
  ok(w.__S.drafts.c1.status === "approved" && !w.__S.drafts.c1.scheduled_for, "Compose rejects an empty scheduling time without losing approval");
  d.getElementById("ed-when").value = "2000-01-01T09:00"; w.saveDraftSlot("c1");
  ok(w.__S.drafts.c1.status === "approved" && !w.__S.drafts.c1.scheduled_for, "Compose rejects a past scheduling time");
  w.scheduleNext("c1"); await sleep(50);
  ok(w.__S.drafts.c1.status === "scheduled" && w.__S.drafts.c1.scheduled_for, "next free slot scheduled: " + w.__S.drafts.c1.scheduled_for);
  ok(new Date(w.__S.drafts.c1.scheduled_for).getMinutes() === 0, "slot lands on a configured slot time");
  const ownSlot = w.__S.drafts.c1.scheduled_for; d.getElementById("ed-when").value = w.toLocalInput(ownSlot); w.saveDraftSlot("c1");
  ok(w.__S.drafts.c1.scheduled_for === ownSlot, "a scheduled post can keep its own slot");
  w.go("schedule"); await sleep(50);
  ok(visible("schedule") && d.querySelectorAll(".day").length === 14 && d.querySelectorAll(".day .slot:not(.free)").length === 1, "Schedule shows 14 days with the one queued post");
  ok(d.getElementById("nc-schedule").textContent === "1", "Schedule nav count");
  const initialDate = d.querySelector(".day .dh b").textContent; w.shiftSchedule(14);
  const futureDate = new Date(); futureDate.setDate(futureDate.getDate() + 14);
  ok(d.querySelector(".day .dh b").textContent === String(futureDate.getDate()) && d.querySelectorAll(".day").length === 14, "calendar paging moves the actual two-week date range");
  w.shiftSchedule(0); ok(d.querySelector(".day .dh b").textContent === initialDate, "calendar Today returns to the current date range");
  await w.patchDoc("drafts", "c2", { status: "approved" });
  d.querySelector(".day .slot.free").click(); const slotChoice = d.getElementById("slot-draft"); slotChoice.value = "c2";
  const placeButton = Array.from(d.querySelectorAll("#slot-picker button")).find(button => button.textContent.includes("Place on this slot")); placeButton.click();
  ok(w.__S.drafts.c2.status === "scheduled" && w.__S.drafts.c2.scheduled_for !== w.__S.drafts.c1.scheduled_for, "clicking a free calendar opening schedules the selected approved draft");
  await w.patchDoc("drafts", "c2", { status: "approved", scheduled_for: null });
  w.selectSlot(w.__S.drafts.c1.scheduled_for); w.placeInSlot("c2");
  ok(w.__S.drafts.c2.status === "approved" && !w.__S.drafts.c2.scheduled_for && d.getElementById("toast").textContent.includes("no longer available"), "slot collision is rechecked before scheduling and preserves the draft");
  w.selectSlot("invalid-date"); w.placeInSlot("c2"); ok(w.__S.drafts.c2.status === "approved", "an invalid calendar time cannot schedule a draft");
  w.openDraft("c2"); d.getElementById("ed-when").value = w.toLocalInput(w.__S.drafts.c1.scheduled_for); w.saveDraftSlot("c2");
  ok(w.__S.drafts.c2.status === "approved" && !w.__S.drafts.c2.scheduled_for, "Compose rejects a slot occupied by another post");
  const manualTime = new Date(new Date(w.__S.drafts.c1.scheduled_for).getTime() + 2 * 36e5).toISOString();
  d.getElementById("ed-post").value = "Preserve my latest words while scheduling."; d.getElementById("ed-post").dispatchEvent(new w.Event("input"));
  d.getElementById("ed-when").value = w.toLocalInput(manualTime); w.saveDraftSlot("c2");
  ok(w.__S.drafts.c2.status === "scheduled" && w.__S.drafts.c2.scheduled_for === manualTime && w.__S.drafts.c2.edited_post === "Preserve my latest words while scheduling.", "Compose saves a valid custom slot and preserves pending edits");
  await w.patchDoc("drafts", "c2", { status: "draft", scheduled_for: null });
  w.postNow("c1"); await sleep(120);
  ok(visible("compose") && /A clinic group/.test(w.__clip) && /#ai #healthcare/.test(w.__clip), "Post now copies post + hashtags");
  const mp = Array.from(d.querySelectorAll("#compose-editor button")).find(b => b.textContent.includes("Mark as posted"));
  mp.click(); ok(mp.textContent.includes("Click again"), "mark as posted asks for a second click");
  mp.click(); await sleep(80);
  ok(w.__S.drafts.c1.status === "published" && w.__S.drafts.c1.published_at, "second click marks as posted");
  ok(visible("published"), "lands on Published");
  const sel = d.querySelector("#s-published .published-table select"); sel.value = "8"; sel.dispatchEvent(new w.Event("change")); await sleep(50);
  ok(w.__S.drafts.c1.rating === 8, "rating saved");
  w.exportPublished(); ok(/rating: 8/.test(w.__clip), "markdown export includes rating");
  w.go("today"); await sleep(50);
  ok(d.getElementById("s-today").textContent.includes("1/4"), "Today counts this week's post toward the target");

  w.go("library"); await sleep(50);
  ok(visible("library") && d.getElementById("s-library").textContent.includes("Hook library") && d.getElementById("s-library").textContent.includes("Who I am"), "Library shows hooks + voice");
  w.__D.content.hooks.push({ type: "Test", text: 'A writer\'s "quiet win" starts here.' }); w.rerender();
  d.getElementById("hook-search").value = "quiet win"; d.getElementById("hook-search").dispatchEvent(new w.Event("input")); await sleep(350);
  ok(d.querySelectorAll("#s-library .hook").length === 1, "Library search finds a quoted hook");
  d.querySelector("#s-library .hook button").click(); ok(w.__clip === 'A writer\'s "quiet win" starts here.', "Library copy preserves apostrophes and double quotes");
  w.openPalette(); await sleep(20); ok(!d.getElementById("palette").hidden && d.querySelectorAll("#pal-list .pal-item").length > 8, "command palette opens with commands");
  ok(d.querySelector(".app").inert && d.querySelector(".skip-link").inert, "command palette isolates the background workspace and skip link");
  const sidebarCollapsed = d.body.classList.contains("nosb"); d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "\\", ctrlKey: true, bubbles: true }));
  ok(d.body.classList.contains("nosb") === sidebarCollapsed, "palette blocks shortcuts that toggle the background sidebar");
  d.getElementById("pal-q").value = "sched"; d.getElementById("pal-q").dispatchEvent(new w.Event("input")); d.getElementById("pal-q").dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter" })); await sleep(30);
  ok(d.getElementById("palette").hidden && visible("schedule"), "palette filters and runs a command");
  d.getElementById("palettebtn").focus(); d.getElementById("palettebtn").click();
  d.querySelector(".pal-close").focus(); d.querySelector(".pal-close").dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  ok(d.getElementById("palette").hidden && d.activeElement.id === "palettebtn" && !d.querySelector(".app").inert && !d.querySelector(".skip-link").inert, "Escape from the palette close button restores focus and workspace access");
  d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "7", bubbles: true })); await sleep(20); ok(visible("library"), "number key switches screens");
  w.go("settings"); await sleep(50);
  const unsavedNote = "This note is still being written"; d.getElementById("st-note").value = unsavedNote;
  const oldTheme = d.body.classList.contains("dark"); d.getElementById("themebtn").click();
  ok(d.querySelector('.appearance-option.active').dataset.theme === (oldTheme ? "light" : "dark") && d.querySelector('.appearance-option.active').getAttribute("aria-pressed") === "true" && d.getElementById("st-note").value === unsavedNote, "sidebar theme changes update Appearance without discarding unsaved preferences");
  d.getElementById("st-note").value = "I tested this myself"; d.getElementById("st-target").value = "5"; d.getElementById("st-slots").value = "Tue 10:00\nThu 10:00";
  w.saveSettings(); await sleep(50);
  ok(w.__S.settings.profile.personal_note === "I tested this myself" && w.__S.settings.profile.postsPerWeek === 5 && w.__S.settings.profile.slots.length === 2, "settings saved");
  ok(d.getElementById("s-settings").textContent.includes("local file"), "settings shows sync mode");
  d.getElementById("st-slots").value = "Tue 25:90"; w.saveSettings();
  ok(w.__S.settings.profile.slots[0] === "Tue 10:00" && d.activeElement.id === "st-slots", "invalid posting hours are rejected without overwriting preferences");
  w.go("nope"); await sleep(20); ok(visible("today"), "unknown route falls back to Today");

  // ---- manual write flow: copy prompt -> paste JSON -> parsed draft -> fact-check
  w.openDraft("c2"); await sleep(50);
  d.getElementById("ed-facts").value = "Price fell 40%.";
  w.copyPrompt("c2"); ok(/STEP 1 — ANGLES/.test(w.__clip) && /Price fell 40%/.test(w.__clip) && /json fence/.test(w.__clip), "writer prompt built from facts with the JSON contract");
  d.getElementById("ed-paste").value = "garbage"; await w.parseAnswer("c2"); ok(/Could not read/.test(d.getElementById("ed-parse-msg").textContent), "bad paste reports an error");
  d.getElementById("ed-paste").value = '{"angles":[],"chosen":0,"post":"Line one.\n\nLine two.","first_comment":"c","hashtags":[],"claims":[],"review_notes":"","status":"draft",}'; await w.parseAnswer("c2"); await sleep(50);
  ok(w.__S.drafts.c2.post === "Line one.\n\nLine two.", "raw line breaks and a trailing comma are repaired");
  d.getElementById("ed-paste").value = '{"angles":[],"chosen":0,"post":"She called it "a quiet win" for the team.\n\nSaid the CEO: "we will see".","first_comment":"c","hashtags":[],"claims":[{"claim":"a "quiet win"","support":"","kind":"attributed_claim"}],"review_notes":"","status":"draft"}'; await w.parseAnswer("c2"); await sleep(50);
  ok(w.__S.drafts.c2.post === 'She called it "a quiet win" for the team.\n\nSaid the CEO: "we will see".', "unescaped quotes inside values are repaired");
  d.getElementById("ed-paste").value = "KEEP"; d.getElementById("ed-paste").dispatchEvent(new w.Event("input")); w.rerender(); await sleep(30);
  ok(d.getElementById("ed-paste").value === "KEEP", "pasted answer survives a re-render");
  d.getElementById("ed-paste").value = ""; d.getElementById("ed-paste").dispatchEvent(new w.Event("input"));
  const answer = { angles: [{ angle: "Cheaper model changes who can afford AI", hook: "Price fell 40%. Here is who that helps.", format: "text", mode: "insight", why: "cost" }], chosen: 0,
    post: "Price fell 40%. Here is who that helps.\n\n" + "A real paragraph about small businesses and freelancers who could not justify the old price. ".repeat(6) + "\n\nI think the interesting part is what people build once the meter runs slower.",
    first_comment: "Source: OpenAI — https://example.com/2", hashtags: ["ai", "#pricing"], claims: [{ claim: "40% cheaper", support: "Price fell 40%.", kind: "reported_fact" }], review_notes: "last paragraph is my view", status: "draft" };
  d.getElementById("ed-paste").value = "Here you go:\n```json\n" + JSON.stringify(answer) + "\n```"; await w.parseAnswer("c2"); await sleep(50);
  ok(w.__S.drafts.c2.post.startsWith("Price fell 40%") && w.__S.drafts.c2.hashtags.join(" ") === "#ai #pricing", "parsed answer fills post + normalised hashtags");
  ok(w.__S.drafts.c2.angle && w.__S.drafts.c2.angle.mode === "insight" && w.__S.drafts.c2.claims.length === 1, "angle + claims stored");
  ok(w.__S.drafts.c2.verify.verdict === "pass" && w.__S.drafts.c2.verify.engine === "manual", "client checks ran on the parsed post: " + JSON.stringify(w.__S.drafts.c2.verify.issues));
  ok(d.getElementById("ed-post").value.startsWith("Price fell 40%"), "editor shows the parsed post");
  w.copyJudgePrompt("c2"); ok(/fact-checker/.test(w.__clip) && /Price fell 40%/.test(w.__clip), "fact-check prompt copied");
  const currentImagePost = "The current edited post must shape the image.";
  d.getElementById("ed-post").value = currentImagePost; d.getElementById("ed-post").dispatchEvent(new w.Event("input"));
  w.copyImagePrompt("c2"); await sleep(30); ok(/WHAT THE IMAGE NEEDS/.test(w.__clip) && w.__clip.includes("POST (the image may only say what this says):\n" + currentImagePost) && /4:5/.test(w.__clip), "image brief copies the current unsaved post with the image guidelines");
  d.getElementById("ed-paste").value = JSON.stringify({ unsupported_claims: ["'small businesses could not justify'"], misattributed: [], ai_smell: 4, specificity: 3, fixes: ["cut the small-business claim"], summary: "one unsupported claim" });
  await w.parseAnswer("c2"); await sleep(50);
  ok(w.__S.drafts.c2.verify.verdict === "fail" && w.__S.drafts.c2.verify.judge.fixes[0] === "cut the small-business claim", "fact-check answer merged into checks");
  ok(d.getElementById("ed-issues").textContent.includes("small businesses") && d.getElementById("ed-issues").textContent.includes("reads generic"), "issues panel shows judge findings");
  w.go("ideas"); await sleep(50);
  ok(Array.from(d.querySelectorAll("#s-ideas button")).some(b => b.textContent.includes("Write")) && !Array.from(d.querySelectorAll("#s-ideas button")).some(b => b.textContent.includes("Draft with API")), "free mode: Write button shown, API draft hidden");

  // A locked workspace ignores global shortcuts and programmatic routing.
  let lockedFetches = 0;
  const lockedDom = new JSDOM(html.replace(/"lockHash": ?""/, '"lockHash": "' + "f".repeat(64) + '"'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://example.com/studio.html", beforeParse(window) { window.scrollTo = () => {}; window.fetch = async () => { lockedFetches++; return { ok: true, json: async () => ({}) }; }; } });
  const lw = lockedDom.window, ld = lw.document; await sleep(30);
  ld.getElementById("lockcode").dispatchEvent(new lw.KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }));
  lw.openPalette(); lw.go("settings"); ld.dispatchEvent(new lw.KeyboardEvent("keydown", { key: "2", bubbles: true }));
  ok(!ld.getElementById("lock").hidden && ld.getElementById("palette").hidden && ld.getElementById("pageTitle").textContent === "Today" && ld.querySelector(".app").inert && lockedFetches === 0, "the lock blocks palette, global keyboard navigation, routes and data loading");
  ok(ld.querySelector(".skip-link").inert, "locked workspace also disables the outside skip link");
  ld.getElementById("lockcode").focus(); ld.getElementById("lockcode").dispatchEvent(new lw.KeyboardEvent("keydown", { key: "Tab", shiftKey: true, bubbles: true, cancelable: true }));
  ok(ld.activeElement.id === "lockbtn", "Shift Tab at the lock input stays inside the dialog");
  ld.getElementById("lockbtn").dispatchEvent(new lw.KeyboardEvent("keydown", { key: "Tab", bubbles: true, cancelable: true }));
  ok(ld.activeElement.id === "lockcode", "Tab at the lock button returns to the access-code input");
  lockedDom.window.close();

  // A real remote update must preserve composer clicks and edits awaiting autosave.
  const cloudState = JSON.parse(JSON.stringify(STATE)); let cloudStream; let cloudWrites = 0;
  const cloudDom = new JSDOM(html.replace(/"fbUrl": ?""/, '"fbUrl": "https://firebase.example"'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://example.com/studio.html",
    beforeParse(window) {
      window.crypto = require("crypto").webcrypto; window.localStorage.setItem("boardkey", "test-key");
      window.navigator.clipboard = { writeText: async t => { window.__clip = t; } }; window.open = () => null; window.scrollTo = () => {};
      window.EventSource = class { constructor() { this.listeners = {}; cloudStream = this; } addEventListener(name, fn) { this.listeners[name] = fn; } };
      window.fetch = async (url, opts = {}) => {
        const u = String(url); const response = body => ({ ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(body)) });
        if (u.startsWith("https://firebase.example/")) {
          if (opts.method === "PATCH") { const match = /\/([^/]+)\/([^/]+)\.json$/.exec(u); Object.assign(cloudState[match[1]][match[2]], JSON.parse(opts.body)); cloudWrites++; }
          return response(cloudState);
        }
        if (u.startsWith("pipeline.json")) return response(cloudState);
        if (u.startsWith("pulse.json")) return response(PULSE);
        throw new Error("unexpected cloud fetch " + u);
      };
    } });
  const cw = cloudDom.window, cd = cw.document; await sleep(150); cw.openDraft("c1");
  const cloudPost = cd.getElementById("ed-post"); cloudPost.focus();
  cloudState.candidates.c2.reason = "remote update"; cloudStream.listeners.patch({ data: "{}" }); await sleep(850);
  ok(cd.getElementById("ed-post") === cloudPost, "remote update waits while the composer is focused");
  const cloudCopy = Array.from(cd.querySelectorAll("#compose-editor button")).find(b => b.textContent.includes("Copy post"));
  cloudCopy.focus();
  ok(cloudCopy.isConnected && cd.getElementById("ed-post") === cloudPost, "moving to a composer button does not rebuild it before the click");
  cloudCopy.click(); await sleep(20); ok(/A clinic group/.test(cw.__clip), "the first composer button click still works after a remote update");
  cloudPost.focus(); cloudPost.value = "Latest unsaved keystrokes"; cloudPost.dispatchEvent(new cw.Event("input"));
  cd.getElementById("cloudbtn").focus(); await sleep(30);
  ok(cd.getElementById("ed-post").value === "Latest unsaved keystrokes" && cw.__S.drafts.c1.edited_post === "Latest unsaved keystrokes", "leaving the composer flushes pending autosave before the remote rebuild");
  await sleep(750);
  ok(cloudWrites === 1 && cloudState.drafts.c1.edited_post === "Latest unsaved keystrokes", "flushed autosave reaches the cloud once and cancels its pending timer");
  cloudDom.window.close();

  console.log(fails.length ? `\n${fails.length} FAILED` : "\nALL PASSED");
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
