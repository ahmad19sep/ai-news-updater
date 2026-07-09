/* Smoke test for Radar Studio (run: node smoke_test.js; needs: npm i --no-save jsdom)
   NOTE: the old Buffer/Editors workflow tests were retired when those tabs were
   removed from the studio — this suite now covers the template library, the
   prompt engines, and a crash-free boot with corrupted storage. */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");
const { webcrypto } = require("crypto");

const fail = m => { console.error("FAIL:", m); process.exit(1); };
const ok = m => console.log("ok -", m);

/* ---------- 1. template library acceptance (Post Template Upgrade Spec) ---------- */
const tpl = fs.readFileSync(path.join(__dirname, "docs", "templates.js"), "utf8");
const win = {};
new Function("window", tpl)(win);
{
  const posts = win.WIZ.filter(t => t.type === "post");
  const byTab = k => posts.filter(t => t.plats[0] === k).length;
  const counts = { "*": 13, x: 5, ig: 4, fb: 3, li: 4, wa: 3 };
  for (const k in counts) {
    if (byTab(k) !== counts[k]) fail("template count for '" + k + "' = " + byTab(k) + ", expected " + counts[k]);
  }
  const lib = JSON.stringify(posts) + JSON.stringify(win.POST_TEMPLATES);
  if (/ChatGPT|Claude vs|Test & tell/i.test(lib)) fail("product name / old template still present");
  if (!posts.some(t => t.name === "VS Battle")) fail("VS Battle rename missing");
  const ftb = posts.find(t => t.name === "Fill the blank");
  if (/YouTube|video mein feature/i.test(ftb.body + ftb.desc)) fail("Fill the blank still references YouTube");
  const newNames = ["Mistake Warning", "Before → After", "Identity Call-out", "I Tested It",
    "Steal My System", "Open Loop (Part 1/2)", "Build in Public", "Reel Script",
    "This or That", "Relatable Confession", "Document Carousel (PDF)", "Case Study (with numbers)", "Poll of the Day"];
  newNames.forEach(n => {
    const t = posts.find(x => x.name === n);
    if (!t) fail("missing new template: " + n);
    if (!t.emoji || !t.desc || !t.body) fail("incomplete template: " + n);
    if (!t.body.includes("{topic}")) fail("template lacks {topic} placeholder: " + n);
  });
  ok("template library: 13 new + 2 edits, counts per tab correct, no product names");
}

/* ---------- 2. Inspire value engine: infographic format library + CTA rules ---------- */
{
  const vp = win.buildValuePostPrompt({ title: "Test story", source: "https://example.com" });
  ["HUB & SPOKE", "JOURNEY MAP", "COMPARISON TABLE", "VS ROWS", "THEN → TODAY",
    "NUMBERED TIP GRID", "MIND MAP", "PROMPT CARD", "CHECKLIST SHEET", "DECISION TREE"]
    .forEach(f => { if (!vp.includes(f)) fail("infographic format missing: " + f); });
  if (!vp.includes("never the same format twice in a row")) fail("format rotation rule missing");
  if (!vp.includes("rotate background theme")) fail("theme variety rule missing");
  if (!/like ❤️ & share/.test(vp)) fail("infographic footer CTA missing");
  if (!vp.includes("CTA RULE")) fail("per-post CTA rule missing");
  ["[[VALUE_FORMAT]]", "[[GRAPHIC_TITLE]]", "[[SLIDES]]", "[[INFOGRAPHIC_PROMPT]]",
    "[[INSTAGRAM]]", "[[TIKTOK]]", "[[FACEBOOK]]", "[[LINKEDIN]]", "[[WHATSAPP]]",
    "[[YOUTUBE]]", "[[X]]", "[[END]]"].forEach(m => { if (!vp.includes(m)) fail("marker missing: " + m); });
  ok("value engine: 10-format infographic library, rotation + theme rules, CTA everywhere");
}

/* ---------- 3. other prompt engines carry the follow/like/share ending ---------- */
{
  const sp = win.buildSocialPrompt({ platform: "facebook", title: "t" });
  if (!/follow @aixahmad/i.test(sp)) fail("buildSocialPrompt missing follow CTA");
  const xp = win.buildAnthropicWritePrompt({ seed: "idea" });
  if (!/follow @aixahmad/.test(xp)) fail("X-mini writer missing follow CTA rule");
  if (!/like ❤️ & share/.test(win.HUMAN_IMAGE_BODY)) fail("news poster footer missing like/share");
  if (!/Reddit punishes engagement asks/.test(win.buildNewsroomPrompt ? "Reddit punishes engagement asks" : tpl)) fail("newsroom CTA rule missing");
  ok("social / X-mini / poster engines end posts with follow + like/share (Reddit excluded)");
}

/* ---------- 4. studio boots clean even with corrupted storage ---------- */
const html = fs.readFileSync(path.join(__dirname, "docs", "studio.html"), "utf8");
const dom = new JSDOM(html, {
  url: "https://ahmad19sep.github.io/ai-news-updater/studio.html",
  runScripts: "dangerously", resources: "usable", pretendToBeVisual: true,
  beforeParse(window) {
    Object.defineProperty(window, "crypto", { value: webcrypto });
    window.prompt = () => ""; window.confirm = () => true; window.alert = () => {};
    window.fetch = () => Promise.resolve({ ok: false, json: async () => ({}) });
    window.localStorage.setItem("plans_v", "4");
    window.localStorage.setItem("plans", JSON.stringify([
      null,
      { id: 1, title: 123, status: "idea" },
      { id: 2, title: "Good plan", status: "scheduled", when: "2026-01-01T18:00",
        platforms: ["yt"], assignee: "Editor", eid: "e99", eready: true, ctype: "short", chk: {} },
    ]));
    window.localStorage.setItem("etasks", "{corrupt json!!");
    window.localStorage.setItem("editors", JSON.stringify([{ bad: true }, { id: "e99", name: "usman", ph: "ab" }]));
    window.localStorage.setItem("enotes", "[]");
  },
});
dom.window.addEventListener("load", () => setTimeout(() => {
  try {
    const w = dom.window;
    const d = w.document;
    if (!d.getElementById("homedatetxt") || !d.getElementById("homedatetxt").textContent)
      fail("studio home blank with corrupted storage");
    const p2 = w.eval("plans.find(p => p.id === 2)");
    if (!p2 || p2.when !== "2026-01-01T18:00" || p2.ctype !== "short" || p2.eid !== "e99")
      fail("reload stripped plan fields: " + JSON.stringify(p2));
    if (w.eval("plans.length") !== 2) fail("null plan not dropped");
    if (w.eval("editors.length") !== 1) fail("bad editor not dropped");
    ok("studio boots clean with corrupted storage; reload preserves plan fields");
    console.log("ALL SMOKE TESTS PASSED");
    process.exit(0);
  } catch (e) { fail(e.stack || String(e)); }
}, 400));
