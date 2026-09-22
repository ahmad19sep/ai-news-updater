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

const AGENT_BRIEF_OUTPUT = `
[[BRIEF_VERSION]]
2
[[ITEM_KEY]]
__ITEM_KEY__
[[SOURCE_REVISION]]
__SOURCE_REVISION__
[[STATUS]]
ready
[[SUPPORTED_FACTS]]
- [S1] File writes require explicit approval before execution.
- [S1] Approval occurs before the runtime performs the proposed file write.
[[ATTRIBUTED_CLAIMS]]
- [S1] The supplied excerpt describes this as an explicit approval requirement.
[[UNKNOWNS]]
- The supplied evidence does not name a model, benchmark, or customer deployment.
[[ORIGINAL_SYSTEM]]
[S1] The evidenced flow is a runtime proposing a file write and requiring explicit approval before that external side effect executes.
[[PLAIN_EXPLANATION]]
[S1] The system does not let a model write a file immediately; an approval gate must allow the proposed change first.
[[CONCRETE_EXAMPLE]]
[S1] A model proposes changing config.json, the runtime pauses, and the write happens only after approval.
[[SYSTEM_TYPE]]
agentic_system candidate, supported only by the described proposal and approval boundary [S1].
[[PROPOSED_BLUEPRINT]]
PROPOSED: build a small file-edit assistant that emits a structured diff, pauses for manual approval, and applies only an accepted change.
[[IMPLEMENTATION_STEPS]]
1. Define a structured file-change proposal.
2. Validate paths and show a diff.
3. Require an explicit approval token before writing.
[[TEST_PLAN]]
- Attempt a write without approval; expect the file to remain unchanged.
- Approve a valid diff; expect exactly the proposed change.
[[FAILURE_CASES]]
- Path traversal or stale diffs; reject them and request a fresh proposal.
[[PERMISSIONS_APPROVALS]]
- Grant read access first and require human approval for every write.
[[COST_TRADEOFFS]]
- Model calls add latency and cost; deterministic validation adds code but reduces side-effect risk.
[[LEARNING_TAKEAWAYS]]
- Separate model intent from deterministic authorization.
[[PRACTICAL_EXERCISE]]
Implement a dry-run diff and prove that no write occurs without approval.
[[LINKEDIN_ANGLES]]
- Agent autonomy is a permissions design problem | supported by [S1] | no deployment evidence supplied.
[[MODEL_PRODUCT_VERSION]]
Example Agent Runtime 1.0
[[EVENT_DATE]]
unknown
[[AVAILABILITY]]
preview
[[SOURCE_TYPE]]
official_release
[[WHAT_CHANGED]]
Example Corp added explicit tool approval to its agent runtime.
[[HOW_IT_WORKS]]
The supplied facts say file writes require approval before execution.
[[WHY_IT_MATTERS]]
Teams can separate model-suggested actions from deterministic authorization.
[[SYSTEM_PATTERN]]
bounded_agent
[[AGENT_LOOP]]
Goal -> context -> proposed tool call -> approval -> execution -> observation.
[[RAG_CONTEXT_ROLE]]
No retrieval role was established by the supplied facts.
[[AUTONOMY_BOUNDARY]]
The model proposes a file write; policy or a human approves it.
[[VERIFIED_FACTS]]
- [S1] File writes require explicit approval before execution.
- [S1] Approval occurs before execution.
[[CLAIM_STATUS]]
- Source fact: file writes require explicit approval.
- Interpretation: this separates suggestion from authorization.
[[LIMITATIONS]]
- No benchmark numbers were supplied.
[[PREREQUISITES]]
- A runtime with policy checks.
[[LEARN_NEXT]]
Study tool authorization and idempotent side effects.
[[EXPERIMENT]]
Build a toy agent that must request approval before writing a file.
[[PRACTICAL_TASK]]
Review a proposed file write before execution.
[[USER_BUYER]]
Engineering teams adopting coding agents.
[[STACK_TOOLS]]
Agent runtime, policy checks, and a file-writing tool.
[[WORKFLOW]]
Request -> proposed write -> policy check -> human approval -> execution.
[[HUMAN_APPROVALS]]
A person approves the file write.
[[BUSINESS_MODEL]]
unknown
[[GO_TO_MARKET]]
unknown
[[PROOF_OF_USE]]
Official preview announcement; no customer deployment supplied.
[[BUSINESS_CAVEATS]]
- No pricing, customer, or measured outcome was supplied.
[[BUILD_TEST]]
Build a file agent that blocks every write until approval.
[[CONTENT_QUESTION]]
What should an AI agent be allowed to change without asking?
[[EXPLANATORY_ANGLE]]
Agent autonomy is mostly a permissions design problem.
[[ENGINEERING_ANGLE]]
Put approval between model intent and side effects.
[[MUST_NOT_CLAIM]]
- Do not claim the system is fully autonomous.
[[CONTENT_READINESS]]
ready
[[SOURCES]]
Selected source | __SOURCE_URL__ | unknown
[[PRIVATE_REVIEW_NOTES]]
No firsthand testing was supplied.
[[END]]`;

function runChecks() {
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

  check("Agents & AI renders distinct research and workspace tabs", () => {
    if (!(w.__AGENT_ITEMS || []).length) {
      w.__AGENT_ITEMS.push({ ak: "agenttest001", t: "Example agent runtime adds approval",
        u: "https://example.com/agent", s: "Example Corp", p: 2,
        pub: "2026-09-01T00:00:00+00:00", col: "2026-09-02T00:00:00+00:00",
        sm: "", sc: 1, links: [], primary: "agent_loops",
        topics: ["agent_loops", "eval_safety"], secondary: ["tool calling"],
        practical: ["built", "operations"],
        tabs: ["agent_builds", "workflows", "builders"], matchReasons: ["Agent Builds: I built"],
        sourceType: "official" });
    }
    w.switchTab("agents");
    if (d.getElementById("tab-agents").hidden) throw new Error("agents tab stayed hidden");
    if (!d.getElementById("agent-topicbar").textContent.includes("Agent Loops"))
      throw new Error("topic filters missing");
    ["Today", "Agent Builds", "Real-World Workflows", "MVPs & Products", "Agent Skills",
      "MCP & Integrations", "Models & Frameworks", "Builders", "My Learning", "LinkedIn Queue"]
      .forEach(label => { if (!d.getElementById("agent-modebar").textContent.includes(label)) throw new Error("missing tab: " + label); });
    ["today", "agent_builds", "workflows", "mvps", "skills", "mcp", "models_frameworks", "builders", "my_learning", "linkedin_queue"]
      .forEach(value => {
        const button = d.querySelector('#agent-modebar button[data-v="' + value + '"]');
        if (!button) throw new Error("missing tab control: " + value);
        button.click();
        if (button.getAttribute("aria-selected") !== "true" && !d.querySelector('#agent-modebar button[data-v="' + value + '"]').classList.contains("active"))
          throw new Error("tab did not activate: " + value);
      });
    if (!d.getElementById("tab-agents").textContent.includes("Model proposes"))
      throw new Error("agent-loop explainer missing");
    if (!d.getElementById("agent-health").textContent) throw new Error("source health missing");
  });

  check("manual discovery capture keeps raw source text local", () => {
    d.getElementById("agent-cap-title").value = "Builder ships a content agent";
    d.getElementById("agent-cap-url").value = "https://example.com/content-agent";
    d.getElementById("agent-cap-author").value = "Example Builder";
    d.getElementById("agent-cap-kind").value = "agent_builds";
    d.getElementById("agent-cap-text").value = "The builder says research and drafting are automated, while publishing remains manual.";
    w.agentSaveCapture();
    const captures = JSON.parse(w.localStorage.getItem("agentCaptures") || "{}");
    const item = Object.values(captures).find(x => x.u === "https://example.com/content-agent");
    if (!item || !item.sm.includes("publishing remains manual")) throw new Error("manual capture was not stored locally");
    if (w.boardState().agentCaptures) throw new Error("raw manual captures leaked into convenience sync");
    const synced = w.boardState().agentLearning[item.ak];
    if (!synced || !synced.snapshot || synced.snapshot.sm) throw new Error("manual source text leaked through the saved-learning snapshot");
    w.agentOpen(item.ak);
    if (!d.getElementById("agent-modal-body").textContent.includes("Export with local source text"))
      throw new Error("manual source export was not made an explicit choice");
    w.agentToggleFollow(item.ak);
    w.agentToggleFollow(item.ak);
    w.agentQueueSet(item.ak, "researching");
    w.agentQueueSet(item.ak, "remove");
    const removed = w.boardState();
    const followKey = item.author.toLowerCase();
    if (!removed.agentFollows[followKey].deleted || !removed.agentQueue[item.ak].deleted)
      throw new Error("queue/follow removals did not create sync tombstones");
    w.applyBoard({
      agentFollows: { [followKey]: { name:item.author, updatedAt:"2000-01-01T00:00:00Z" } },
      agentQueue: { [item.ak]: { storyKey:item.ak, stage:"researching", updatedAt:"2000-01-01T00:00:00Z" } }
    });
    if (w.agentIsFollowing(item.author) || w.agentQueueEntry(item.ak))
      throw new Error("an older device resurrected removed queue/follow state");
    const hostileKey = "bad');window.__agentInjected=true;//";
    w.applyBoard({ agentLearning: { hostile: { saved:true, updatedAt:new Date().toISOString(),
      snapshot:{ ak:hostileKey, t:"Injected item", u:"javascript:alert(1)", manual:true } } } });
    if (w.agentFind(hostileKey)) throw new Error("unsafe synced item key entered the rendered research collection");
    if (w.boardState().agentLearning.hostile) throw new Error("unsafe synced snapshot was retained for re-sync");
  });

  check("Agent learning rejects generic text and hands off only reviewed evidence", () => {
    const it = (w.__AGENT_ITEMS || [])[0];
    if (!it || !it.ak) throw new Error("no agent item available");
    const wasDone = w.__doneSet.has(it.u);
    w.agentOpen(it.ak);
    if (d.getElementById("agentmodal").hidden) throw new Error("agent modal did not open");
    d.getElementById("agent-facts").value = "File writes require explicit approval before execution.";
    w.agentRefreshPrompt(false);
    w.agentCopyPrompt();
    if (!copied.includes("SOURCE MATERIAL")) throw new Error("selected evidence missing from prompt");
    if (!copied.includes("[S1]")) throw new Error("numbered source pack missing");
    if (!copied.includes("[[ITEM_KEY]]")) throw new Error("versioned identity contract missing");
    d.getElementById("agent-raw").value = "This is a useful agent that saves time for businesses.";
    w.agentValidateBrief();
    if ((JSON.parse(w.localStorage.getItem("agentBriefs") || "{}"))[it.ak])
      throw new Error("generic paragraph was accepted as a brief");
    const response = AGENT_BRIEF_OUTPUT
      .replace("__ITEM_KEY__", it.ak)
      .replace("__SOURCE_REVISION__", w.agentSourceRevision(it, d.getElementById("agent-facts").value))
      .replace("__SOURCE_URL__", it.u);
    d.getElementById("agent-raw").value = response.replace(/\[S1\]/g, "[S9]");
    w.agentValidateBrief();
    if ((JSON.parse(w.localStorage.getItem("agentBriefs") || "{}"))[it.ak])
      throw new Error("unsupported source IDs were accepted");
    d.getElementById("agent-raw").value = response;
    w.agentValidateBrief();
    let saved = JSON.parse(w.localStorage.getItem("agentBriefs") || "{}")[it.ak];
    if (!saved || saved.contentReadiness !== "ready") throw new Error("brief was not saved as ready");
    if (saved.reviewed) throw new Error("parsing incorrectly marked claims reviewed");
    const beforeWrongItem = saved.updatedAt;
    d.getElementById("agent-raw").value = response.replace(it.ak, "another-item");
    w.agentValidateBrief();
    saved = JSON.parse(w.localStorage.getItem("agentBriefs") || "{}")[it.ak];
    if (saved.updatedAt !== beforeWrongItem) throw new Error("wrong-item response overwrote a good brief");
    w.agentToggleClaim(0, true);
    w.agentToggleClaim(1, true);
    saved = JSON.parse(w.localStorage.getItem("agentBriefs") || "{}")[it.ak];
    if (!saved.reviewed) throw new Error("claim review did not produce reviewed state");
    w.agentSetView("build");
    if (!d.getElementById("agent-view-body").textContent.includes("small file-edit assistant"))
      throw new Error("proposed build plan not shown");
    w.agentSetView("content");
    if (!d.getElementById("agent-view-body").textContent.includes("Ready to draft"))
      throw new Error("content readiness not shown");
    w.agentUseLinkedIn(it.ak);
    if (d.getElementById("nrmodal").hidden) throw new Error("LinkedIn draft did not open");
    if (!d.getElementById("nr-excerpt").value.includes("File writes require explicit approval"))
      throw new Error("verified facts did not hand off");
    if (d.getElementById("nr-note").value && d.getElementById("nr-note").value.includes("tested"))
      throw new Error("handoff fabricated a firsthand note");
    if (w.__doneSet.has(it.u) !== wasDone) throw new Error("Agent handoff changed done/posted state");
    w.closeNewsroom();
    w.agentClose();
  });

  check("source-excerpt LinkedIn fast path does not require a full teardown", () => {
    const it = (w.__AGENT_ITEMS || []).find(x => x.sm && x.u);
    if (!it) return;
    const wasDone = w.__doneSet.has(it.u);
    w.agentFastLinkedIn(it.ak);
    if (d.getElementById("nrmodal").hidden) throw new Error("fast LinkedIn path did not open writer");
    if (!d.getElementById("nr-excerpt").value.includes(it.sm.slice(0, 30))) throw new Error("source excerpt was not handed off");
    if (w.__doneSet.has(it.u) !== wasDone) throw new Error("fast handoff changed posted state");
    w.closeNewsroom();
  });

  /* use a REAL story from the baked-in feed so done-tracking behaves like production.
     top-level let/const are not window properties, so reach them through page eval */
  const story = (w.__ITEMS || []).find(i => i.u && !w.__doneSet.has(i.u));
  const isDone = () => w.__doneSet.has(story.u);
  check("LinkedIn draft opens on a real story from the feed", () => {
    if (!story || !story.u) throw new Error("no usable story in the feed");
    w.openNewsroom(story);
    if (d.getElementById("nrmodal").hidden) throw new Error("modal did not open");
    if (!d.getElementById("nr-story").textContent.includes(story.t.slice(0, 20)))
      throw new Error("wrong story shown");
  });

  /* A modal with no overlay CSS still reports hidden=false while rendering as a
     plain block at the bottom of the page - it "opens" and the user sees nothing.
     Assert it is actually positioned over the page. */
  check("open modals are positioned overlays, not blocks at the page bottom", () => {
    ["nrmodal", "xmodal", "pubmodal", "agentmodal"].forEach(id => {
      const el = d.getElementById(id);
      if (!el) throw new Error("missing modal: " + id);
      const wasHidden = el.hidden;
      el.hidden = false;
      const cs = w.getComputedStyle(el);
      if (cs.position !== "fixed") throw new Error(id + " is not position:fixed (it renders inline)");
      if (cs.display === "none") throw new Error(id + " stays display:none while open");
      if (!cs.zIndex || cs.zIndex === "auto") throw new Error(id + " has no stacking order");
      el.hidden = true;
      if (w.getComputedStyle(el).display !== "none") throw new Error(id + " still shows when hidden");
      el.hidden = wasHidden;
    });
    d.getElementById("nrmodal").hidden = false;   // leave the draft open for the checks below
  });

  check("the feed summary pre-fills the source facts", () => {
    w.openNewsroom({ t: "Story with a summary", u: "https://example.com/s",
                     sm: "The company said the agent runs on-device and keeps data local." });
    const pre = d.getElementById("nr-excerpt").value;
    if (!pre.includes("runs on-device")) throw new Error("feed summary did not pre-fill the facts box");
    w.openNewsroom({ t: "Story without one", u: "https://example.com/n" });
    if (d.getElementById("nr-excerpt").value !== "") throw new Error("stale facts carried into the next story");
    w.openNewsroom(story);   // back to the real story for the checks below
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
}

function waitForBoot(tries) {
  const w = dom.window;
  if (typeof w.switchTab === "function" && Array.isArray(w.__ITEMS)) return runChecks();
  if (tries > 80) {
    console.error("FAIL: studio did not finish booting in JSDOM");
    process.exit(1);
  }
  setTimeout(() => waitForBoot(tries + 1), 100);
}
waitForBoot(0);
