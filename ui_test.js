/* UI regression test for the LinkedIn-first studio.
   Run: node ui_test.js   (needs: npm i --no-save jsdom)
   Boots docs/studio.html in JSDOM, unlocks it, walks every tab, and drives the
   whole LinkedIn draft flow on a real story from the baked-in feed. Makes no
   network, Firebase, model or account calls. */
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
const { webcrypto } = require("crypto");
const ROOT = __dirname;
const html = fs.readFileSync(path.join(ROOT, "docs", "studio.html"), "utf8");
const LOCKHASH = html.match(/const LOCKHASH = "([a-f0-9]*)"/)[1];

const errors = [];
let copied = "";
const dom = new JSDOM(html, {
  url: "https://ahmad19sep.github.io/ai-news-updater/studio.html",
  runScripts: "dangerously", resources: "usable", pretendToBeVisual: true,
  beforeParse(w) {
    Object.defineProperty(w, "crypto", { value: webcrypto });
    w.prompt = () => ""; w.confirm = () => true; w.alert = () => {};
    w.fetch = () => Promise.resolve({ ok: false, json: async () => ({}) });
    Object.defineProperty(w.navigator, "clipboard",
      { value: { writeText: t => { copied = t; return Promise.resolve(); } } });
    w.open = () => null;
    w.localStorage.setItem("unlock", LOCKHASH);   // already-unlocked device
    w.onerror = m => errors.push(String(m));
    w.addEventListener("error", e => errors.push(String(e.message || e.error)));
    const ce = w.console.error; w.console.error = (...a) => { errors.push(a.join(" ")); ce(...a); };
  },
});

const AI_WITH_VISUAL = `
[[STATUS]]
draft
[[POST]]
A short approved post about agent review.
[[SOURCES]]
Example Corp - https://example.com
[[REVIEW]]
Interpretation flagged.
[[MISSING]]
[[VISUAL]]
A CHECKLIST SHEET layout, 4:5, cream background, one blue accent.
[[END]]`;

const AI_OUTPUT = `
[[STATUS]]
draft
[[POST]]
Most teams evaluating an AI coding tool skip the only question that matters later: what can it change without asking?
The announcement says review stays manual. That is the part worth checking before anyone wires it into a repo.
[[SOURCES]]
Example Corp announcement - https://example.com
[[REVIEW]]
"review stays manual" comes from the supplied excerpt. The framing about repos is my interpretation, not reported.
[[MISSING]]
[[END]]`;

setTimeout(() => {
  const w = dom.window, d = w.document;
  /* the page loads templates.js by relative URL, which JSDOM can't fetch from a
     github.io origin - evaluate the real file into the page instead */
  w.eval(fs.readFileSync(path.join(ROOT, "docs", "templates.js"), "utf8"));
  const fails = [];
  const check = (name, fn) => {
    const before = errors.length;
    try { fn(); } catch (e) { fails.push(name + ": threw " + e.message); return; }
    if (errors.length > before) fails.push(name + ": " + errors.slice(before).join(" | ").slice(0, 200));
    else console.log("ok   - " + name);
  };

  check("gate is unlocked, app is visible", () => {
    if (!d.getElementById("lock").hidden) throw new Error("still locked");
  });

  const tabs = [...d.querySelectorAll(".navitem")].map(b => b.id.replace("tabbtn-", ""));
  check("every nav tab switches cleanly (" + tabs.join(", ") + ")", () => {
    tabs.forEach(t => w.switchTab(t));
    w.switchTab("news");
  });

  /* use a REAL story from the baked-in feed so done-tracking behaves like production.
     top-level let/const are not window properties, so reach them through page eval */
  const story = JSON.parse(w.eval("JSON.stringify(ITEMS.find(i => i.u && !doneSet.has(i.u)))"));
  const isDone = () => w.eval("doneSet.has(" + JSON.stringify(story.u) + ")");
  check("LinkedIn draft opens on a real story from the feed", () => {
    if (!story || !story.u) throw new Error("no usable story in the feed");
    w.openNewsroom(story);
    if (d.getElementById("nrmodal").hidden) throw new Error("modal did not open");
    if (!d.getElementById("nr-story").textContent.includes(story.t.slice(0, 20)))
      throw new Error("wrong story shown");
  });

  check("insight prompt carries the pasted evidence + audience", () => {
    d.getElementById("nr-excerpt").value = "Example Corp said review stays manual.";
    d.getElementById("nr-aud").value = "engineering leads";
    d.getElementById("nr-copy").click();
    if (!copied.includes("Example Corp said review stays manual.")) throw new Error("excerpt missing from prompt");
    if (!copied.includes("engineering leads")) throw new Error("audience missing from prompt");
    if (!copied.includes("MODE: NEWS INSIGHT")) throw new Error("wrong mode");
  });

  check("practical button uses the other mode", () => {
    d.getElementById("nr-value").click();
    if (!copied.includes("MODE: PRACTICAL TAKEAWAY")) throw new Error("wrong mode");
  });

  check("validate splits post / sources / private review", () => {
    d.getElementById("nr-in").value = AI_OUTPUT;
    d.getElementById("nr-parse").click();
    if (d.getElementById("nr-parsed").hidden) throw new Error("preview stayed hidden");
    const post = d.getElementById("nr-post").value;
    if (!post.includes("what can it change without asking")) throw new Error("post text missing");
    if (post.includes("my interpretation")) throw new Error("review notes leaked into the post");
    if (!d.getElementById("nr-review").textContent.includes("my interpretation")) throw new Error("review notes missing");
    if (!d.getElementById("nr-sources").textContent.includes("example.com")) throw new Error("sources missing");
  });

  check("one answer carries the post AND its picture prompt", () => {
    d.getElementById("nr-in").value = AI_WITH_VISUAL;
    d.getElementById("nr-parse").click();
    if (d.getElementById("nr-vwrap").hidden) throw new Error("picture panel stayed hidden");
    const vis = d.getElementById("nr-visual").value;
    if (!vis.includes("CHECKLIST SHEET layout")) throw new Error("image prompt not extracted");
    if (d.getElementById("nr-post").value.includes("CHECKLIST SHEET")) throw new Error("image prompt leaked into the post");
    d.getElementById("nr-vcopy").click();
    if (!copied.includes("CHECKLIST SHEET layout")) throw new Error("copy image prompt did not copy it");
  });

  check("a post with no picture hides the panel", () => {
    d.getElementById("nr-in").value = AI_OUTPUT;      // no [[VISUAL]] section
    d.getElementById("nr-parse").click();
    if (!d.getElementById("nr-vwrap").hidden) throw new Error("empty picture panel shown anyway");
  });

  check("copy takes the post only, not the JSON/markers", () => {
    d.getElementById("nr-copypost").click();
    if (copied.includes("[[")) throw new Error("markers copied");
    if (!copied.includes("Most teams evaluating")) throw new Error("post not copied");
  });

  check("needs_input shows the ask and disables posting", () => {
    d.getElementById("nr-in").value = "[[STATUS]]\nneeds_input\n[[POST]]\n[[MISSING]]\nTwo sentences from the announcement.\n[[END]]";
    d.getElementById("nr-parse").click();
    if (!d.getElementById("nr-status").textContent.includes("Two sentences")) throw new Error("ask not shown");
    if (!d.getElementById("nr-posted").disabled) throw new Error("Mark as posted should be disabled");
  });

  check("optional visual + X + Reddit extras build from the approved post", () => {
    d.getElementById("nr-in").value = AI_OUTPUT;
    d.getElementById("nr-parse").click();
    d.getElementById("nr-post").value = "EDITED POST TEXT the operator approved.";

    d.getElementById("nr-info").click();
    if (!copied.includes("EDITED POST TEXT")) throw new Error("infographic ignored the edited post");
    ["HUB & SPOKE", "DECISION TREE", "CHECKLIST SHEET"].forEach(f => {
      if (!copied.includes(f)) throw new Error("infographic format library missing: " + f);
    });
    if (/like ❤️ & share/.test(copied)) throw new Error("engagement-bait footer is back on the image");

    d.getElementById("nr-poster").click();
    if (!copied.includes("ART DIRECTOR")) throw new Error("poster prompt missing");

    d.getElementById("nr-xver").click();
    if (!copied.includes("EDITED POST TEXT")) throw new Error("X version ignored the approved post");
    if (!copied.includes("No thread")) throw new Error("X adaptation lost its no-thread rule");

    w.prompt = () => "r/test - rules: no self promotion";
    d.getElementById("nr-reddit").click();
    if (!copied.includes("review_rules")) throw new Error("Reddit check lost its rules gate");
    if (!copied.includes("no promotional link")) throw new Error("Reddit check lost its no-promo rule");
  });

  check("extras are disabled until there is a draft", () => {
    d.getElementById("nr-in").value = "[[STATUS]]\nskip\n[[REVIEW]]\nno angle\n[[END]]";
    d.getElementById("nr-parse").click();
    ["nr-info", "nr-poster", "nr-xver", "nr-reddit"].forEach(id => {
      if (!d.getElementById(id).disabled) throw new Error(id + " should be disabled on skip");
    });
  });

  check("validating never marks the story handled", () => {
    if (isDone()) throw new Error("parsing already marked the story handled");
  });

  check("only the explicit tick marks it handled", () => {
    d.getElementById("nr-in").value = AI_OUTPUT;
    d.getElementById("nr-parse").click();
    if (isDone()) throw new Error("re-validating marked it handled");
    d.getElementById("nr-posted").click();
    if (!isDone()) throw new Error("the tick did not mark it handled");
    if (!d.getElementById("nrmodal").hidden) throw new Error("modal should close after the tick");
  });

  console.log(fails.length ? "\n" + fails.map(f => "FAIL " + f).join("\n") : "\nall UI checks passed");
  process.exit(fails.length ? 1 : 0);
}, 2000);
