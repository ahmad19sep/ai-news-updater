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

/* ---------- 1. the prompt library exports what the studio actually calls ---------- */
const tpl = fs.readFileSync(path.join(__dirname, "docs", "templates.js"), "utf8");
const win = {};
new Function("window", tpl)(win);
{
  ["HUMAN_VOICE", "LINKEDIN_CONTRACT", "buildLinkedInPrompt", "buildXPrompt",
    "buildPostRepurposePrompt", "buildMePosterPrompt", "buildAnthropicWritePrompt", "INSPIRE_IDEAS"]
    .forEach(k => { if (!win[k]) fail("templates.js no longer exports " + k); });
  /* the Create wizard and its TikTok/IG/FB/WhatsApp video libraries are retired */
  ["WIZ", "POST_TEMPLATES", "SOCIAL", "XREPLY_STYLES", "buildXReplyPrompt"].forEach(k => { if (win[k]) fail("retired library still present: " + k); });
  ok("prompt library exports the live builders, retired libraries gone");
}

/* ---------- 2. the LinkedIn writer: one post, both modes, evidence rules ---------- */
{
  const full = win.buildLinkedInPrompt({ mode: "insight", title: "Test story",
    source: "https://example.com", excerpt: "The company said X changed.", audience: "freelancers" });
  const bare = win.buildLinkedInPrompt({ mode: "practical", title: "Test story", source: "https://example.com" });

  ["[[STATUS]]", "[[POST]]", "[[SOURCES]]", "[[REVIEW]]", "[[MISSING]]", "[[END]]"]
    .forEach(m => { if (!full.includes(m)) fail("marker missing: " + m); });
  if (full === win.buildLinkedInPrompt({ mode: "practical", title: "Test story" }))
    fail("insight and practical modes produce the same prompt");
  if (!/MODE: NEWS INSIGHT/.test(full)) fail("insight mode block missing");
  if (!/MODE: PRACTICAL TAKEAWAY/.test(bare)) fail("practical mode block missing");

  /* one platform only — the retired ones must not come back through a prompt */
  ["Facebook", "Instagram", "TikTok", "WhatsApp", "YouTube", "[[X]]", "[[REDDIT]]"]
    .forEach(p => { if (full.includes(p)) fail("retired platform still in the prompt: " + p); });

  /* evidence honesty: no pretending it opened the link, ask instead of inventing */
  if (/open and read the source/i.test(full)) fail("prompt still tells the AI to open the link");
  if (!/cannot open links/i.test(full)) fail("missing the 'you cannot open links' rule");
  if (!bare.includes("needs_input")) fail("headline-only run must be told to return needs_input");
  if (!/never invent/i.test(full)) fail("missing the no-invention rule");
  if (!/personal note/i.test(full)) fail("missing the firsthand-claim guard");

  ok("LinkedIn writer: two modes, LinkedIn-only output, evidence + needs_input rules");
}

/* ---------- 3. no engagement bait is forced on any post ---------- */
{
  const p = win.buildLinkedInPrompt({ mode: "insight", title: "t", excerpt: "e" });
  if (/CTA RULE/i.test(p)) fail("a mandatory CTA block is back in the writer");
  if (/@aixahmad/.test(p)) fail("handle promotion is back in the writer");
  if (/must (include|end with)[^.]{0,80}(follow|like|share)/i.test(p)) fail("mandatory follow/like line is back");
  if (!/NO forced call to action/i.test(p)) fail("the no-forced-CTA rule went missing");
  ["buildNewsroomPrompt", "buildValuePostPrompt", "buildSocialPrompt"].forEach(k => {
    if (win[k]) fail("retired multi-platform builder still exported: " + k);
  });
  ok("no forced CTA, no handle promotion, retired builders gone");
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
