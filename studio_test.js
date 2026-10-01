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
  ok(d.getElementById("s-today").textContent.includes("drafts to review"), "Today shows stats");
  ok(d.getElementById("nc-ideas").textContent === "2", "Ideas nav count = 2 new candidates");
  ok(d.getElementById("nc-compose").textContent === "1", "Compose nav count = 1 draft");
  ok(d.getElementById("s-today").textContent.includes("$0.210"), "last pipeline run cost shown");

  w.go("discover"); await sleep(50);
  ok(visible("discover") && d.querySelectorAll("#disc-body .item").length > 10, "Discover lists news cards");
  const q = d.getElementById("disc-q"); q.value = "zzzz-nothing"; q.dispatchEvent(new w.Event("input")); await sleep(400);
  ok(d.getElementById("disc-body").textContent.includes("Nothing matches"), "Discover search filters");
  w.discSet("q", ""); w.discSet("sub", "agents"); await sleep(50);
  ok(d.querySelectorAll("#disc-body .fchip").length > 3, "Agents & AI chips render");
  w.discSet("sub", "pulse"); await sleep(200);
  ok(d.getElementById("disc-body").textContent.includes("Claude") && d.getElementById("disc-body").textContent.includes("rate limits"), "Pulse renders trends + pain points");
  w.discSet("sub", "news"); await sleep(50);
  const firstKey = w.__D.news[0].k; await w.saveIdea(firstKey, "news"); await sleep(50);
  ok(w.__S.candidates[firstKey] && w.__S.candidates[firstKey].status === "shortlisted", "Save as idea creates a shortlisted candidate");

  w.go("ideas"); await sleep(50);
  ok(visible("ideas") && d.querySelectorAll(".kcol").length === 3, "Ideas kanban has 3 columns");
  w.setCand("c2", "shortlisted"); await sleep(50);
  ok(w.__S.candidates.c2.status === "shortlisted", "shortlist works");
  w.draftCmd("c2"); ok(/run_pipeline\.py --mode api --draft --ids .*c2/.test(w.__clip), "draft command copied with ids: " + w.__clip);
  const ovr = JSON.parse(w.localStorage.getItem("studio_overrides"));
  ok(ovr.candidates && ovr.candidates.c2.status === "shortlisted", "local-mode edits persisted to localStorage overrides");
  await w.manualDraft("c2"); await sleep(50);
  ok(visible("compose") && w.__S.drafts.c2 && w.__S.drafts.c2.manual, "Write myself creates a manual draft and opens Compose");
  ok(d.getElementById("ed-facts"), "manual draft shows the facts box");
  w.copyPrompt("c2"); ok(/facts first/.test(d.getElementById("toast").textContent), "prompt refused without facts");
  ok(d.getElementById("ed-fetch"), "fetch-article button offered when no source text");
  w.fetch = async (url, opts = {}) => { if (String(url).startsWith("https://r.jina.ai/")) return { ok: true, status: 200, text: async () => "Title: x\nURL Source: y\nMarkdown Content:\n" + "The company said prices fell 40% for API users from 15 October, according to the announcement. ".repeat(8) + "\n\n\"We want this to be the default,\" said Sarah Chen, head of platform." }; const ok2 = body => ({ ok: true, status: 200, json: async () => body }); if (String(url).startsWith("pipeline.json")) return ok2(STATE); if (String(url).startsWith("pulse.json")) return ok2(PULSE); throw new Error("unexpected fetch " + url); };
  await w.fetchArticle("c2"); await sleep(50);
  ok(w.__S.sources.c2 && w.__S.sources.c2.excerpt.includes("40%") && w.__S.sources.c2.quotes.length === 1, "in-Studio fetch builds a source pack with quotes");
  ok(!d.getElementById("ed-facts") && d.getElementById("compose-editor").textContent.includes("Source text loaded"), "editor switches to the loaded-source state");
  w.copyPrompt("c2"); ok(/SOURCE TEXT/.test(w.__clip) && /15 October/.test(w.__clip), "prompt now carries the fetched article");
  delete w.__S.sources.c2; w.OVR && delete w.OVR; w.localStorage.setItem("studio_overrides", JSON.stringify({})); w.rerender(); await sleep(30);
  d.getElementById("ed-facts").value = "Price fell 40%."; w.copyPrompt("c2"); ok(/SOURCE TEXT/.test(w.__clip) && /Price fell 40%/.test(w.__clip), "prompt copied with facts");

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
  w.scheduleNext("c1"); await sleep(50);
  ok(w.__S.drafts.c1.status === "scheduled" && w.__S.drafts.c1.scheduled_for, "next free slot scheduled: " + w.__S.drafts.c1.scheduled_for);
  ok(new Date(w.__S.drafts.c1.scheduled_for).getMinutes() === 0, "slot lands on a configured slot time");
  w.go("schedule"); await sleep(50);
  ok(visible("schedule") && d.querySelectorAll(".day").length === 14 && d.querySelectorAll(".day .slot:not(.free)").length === 1, "Schedule shows 14 days with the one queued post");
  ok(d.getElementById("nc-schedule").textContent === "1", "Schedule nav count");
  w.postNow("c1"); await sleep(120);
  ok(visible("compose") && /A clinic group/.test(w.__clip) && /#ai #healthcare/.test(w.__clip), "Post now copies post + hashtags");
  const mp = Array.from(d.querySelectorAll("#compose-editor button")).find(b => b.textContent.includes("Mark as posted"));
  mp.click(); ok(mp.textContent.includes("Click again"), "mark as posted asks for a second click");
  mp.click(); await sleep(80);
  ok(w.__S.drafts.c1.status === "published" && w.__S.drafts.c1.published_at, "second click marks as posted");
  ok(visible("published"), "lands on Published");
  const sel = d.querySelector("#s-published select"); sel.value = "8"; sel.dispatchEvent(new w.Event("change")); await sleep(50);
  ok(w.__S.drafts.c1.rating === 8, "rating saved");
  w.exportPublished(); ok(/rating: 8/.test(w.__clip), "markdown export includes rating");
  w.go("today"); await sleep(50);
  ok(d.getElementById("s-today").textContent.includes("1/4"), "Today counts this week's post toward the target");

  w.go("library"); await sleep(50);
  ok(visible("library") && d.getElementById("s-library").textContent.includes("Hook library") && d.getElementById("s-library").textContent.includes("Who I am"), "Library shows hooks + voice");
  w.go("settings"); await sleep(50);
  d.getElementById("st-note").value = "I tested this myself"; d.getElementById("st-target").value = "5"; d.getElementById("st-slots").value = "Tue 10:00\nThu 10:00";
  w.saveSettings(); await sleep(50);
  ok(w.__S.settings.profile.personal_note === "I tested this myself" && w.__S.settings.profile.postsPerWeek === 5 && w.__S.settings.profile.slots.length === 2, "settings saved");
  ok(d.getElementById("s-settings").textContent.includes("local file"), "settings shows sync mode");
  w.go("nope"); await sleep(20); ok(visible("today"), "unknown route falls back to Today");

  // ---- manual write flow: copy prompt -> paste JSON -> parsed draft -> fact-check
  w.openDraft("c2"); await sleep(50);
  d.getElementById("ed-facts").value = "Price fell 40%.";
  w.copyPrompt("c2"); ok(/STEP 1 — ANGLES/.test(w.__clip) && /Price fell 40%/.test(w.__clip) && /json fence/.test(w.__clip), "writer prompt built from facts with the JSON contract");
  d.getElementById("ed-paste").value = "garbage"; await w.parseAnswer("c2"); ok(/Could not read/.test(d.getElementById("ed-parse-msg").textContent), "bad paste reports an error");
  const answer = { angles: [{ angle: "Cheaper model changes who can afford AI", hook: "Price fell 40%. Here is who that helps.", format: "text", mode: "insight", why: "cost" }], chosen: 0,
    post: "Price fell 40%. Here is who that helps.\n\n" + "A real paragraph about small businesses and freelancers who could not justify the old price. ".repeat(6) + "\n\nI think the interesting part is what people build once the meter runs slower.",
    first_comment: "Source: OpenAI — https://example.com/2", hashtags: ["ai", "#pricing"], claims: [{ claim: "40% cheaper", support: "Price fell 40%.", kind: "reported_fact" }], review_notes: "last paragraph is my view", status: "draft" };
  d.getElementById("ed-paste").value = "Here you go:\n```json\n" + JSON.stringify(answer) + "\n```"; await w.parseAnswer("c2"); await sleep(50);
  ok(w.__S.drafts.c2.post.startsWith("Price fell 40%") && w.__S.drafts.c2.hashtags.join(" ") === "#ai #pricing", "parsed answer fills post + normalised hashtags");
  ok(w.__S.drafts.c2.angle && w.__S.drafts.c2.angle.mode === "insight" && w.__S.drafts.c2.claims.length === 1, "angle + claims stored");
  ok(w.__S.drafts.c2.verify.verdict === "pass" && w.__S.drafts.c2.verify.engine === "manual", "client checks ran on the parsed post: " + JSON.stringify(w.__S.drafts.c2.verify.issues));
  ok(d.getElementById("ed-post").value.startsWith("Price fell 40%"), "editor shows the parsed post");
  w.copyJudgePrompt("c2"); ok(/fact-checker/.test(w.__clip) && /Price fell 40%/.test(w.__clip), "fact-check prompt copied");
  d.getElementById("ed-paste").value = JSON.stringify({ unsupported_claims: ["'small businesses could not justify'"], misattributed: [], ai_smell: 4, specificity: 3, fixes: ["cut the small-business claim"], summary: "one unsupported claim" });
  await w.parseAnswer("c2"); await sleep(50);
  ok(w.__S.drafts.c2.verify.verdict === "fail" && w.__S.drafts.c2.verify.judge.fixes[0] === "cut the small-business claim", "fact-check answer merged into checks");
  ok(d.getElementById("ed-issues").textContent.includes("small businesses") && d.getElementById("ed-issues").textContent.includes("reads generic"), "issues panel shows judge findings");
  w.go("ideas"); await sleep(50);
  ok(Array.from(d.querySelectorAll("#s-ideas button")).some(b => b.textContent.includes("Write")) && !Array.from(d.querySelectorAll("#s-ideas button")).some(b => b.textContent.includes("Draft with API")), "free mode: Write button shown, API draft hidden");

  console.log(fails.length ? `\n${fails.length} FAILED` : "\nALL PASSED");
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
