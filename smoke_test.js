/* Smoke test for the multi-editor workflow (not shipped; run: node smoke_test.js) */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const html = fs.readFileSync(path.join(__dirname, "docs", "index.html"), "utf8");
const { webcrypto } = require("crypto");

const prompts = [];
const dom = new JSDOM(html, {
  url: "https://ahmad19sep.github.io/ai-news-updater/",
  runScripts: "dangerously",
  resources: "usable",
  pretendToBeVisual: true,
  beforeParse(window) {
    Object.defineProperty(window, "crypto", { value: webcrypto });
    window.prompt = () => prompts.shift() ?? "";
    window.confirm = () => true;
    window.alert = m => { throw new Error("alert: " + m); };
  },
});

const fail = m => { console.error("FAIL:", m); process.exit(1); };
const ok = m => console.log("ok -", m);

dom.window.addEventListener("load", () => {
  setTimeout(async () => {
    const w = dom.window;
    const d = w.document;
    const ev = s => w.eval(s);
    try {
      // Editors tab exists and is empty
      ev('switchTab("editors")');
      if (d.getElementById("tab-editors").hidden) fail("editors tab not shown");
      ok("Editors tab opens");

      // add an editor with password
      prompts.push("Hamza", "secret123");
      await ev("addEditor()");
      if (ev("editors.length") !== 1) fail("editor not created");
      if (!ev("editors[0].ph")) fail("password hash not stored");
      ok("editor created with password hash");

      // owner workspace shows link/password buttons
      if (!d.getElementById("ed-link") || !d.getElementById("ed-pass")) fail("link/password buttons missing");
      ok("workspace has Copy link + Password buttons");

      // the private link embeds id + password-key + name, so the gate is password-only
      const link = ev("editorLink(editors[0])");
      if (!link.includes("#editor=" + ev("editors[0].id") + "." + ev("editors[0].ph") + ".Hamza"))
        fail("link format wrong: " + link);
      ok("private link carries id + key + name (password-only gate)");

      // create a plan and send it to the editor
      ev('plans.unshift({ id: 111, title: "Test video", url: "", notes: "brief here",' +
        'status: "editing", assignee: "Ahmad", platforms: ["yt"], when: "", ctype: "short", chk: {}, ftitle: "" });' +
        "savePlans(); sendToEditor(plans.find(p => p.id === 111), editors[0]);");
      if (ev('plans.find(p => p.id === 111).assignee') !== "Editor") fail("sendToEditor did not assign");
      ok("item assigned to editor");

      // hand-off keeps the SAME sequence stage: script item stays in editor's Script (wizard)
      ev('plans.unshift({ id: 333, title: "Seq video", url: "", notes: "", status: "script",' +
        'assignee: "Ahmad", platforms: ["yt"], when: "", ctype: "short", chk: {}, ftitle: "" });' +
        "savePlans(); sendToEditor(plans.find(p => p.id === 333), editors[0]);");
      if (ev('plans.find(p => p.id === 333).status') !== "script") fail("script item changed stage on handoff");
      // a bare idea starts the sequence at Script
      ev('plans.unshift({ id: 444, title: "Idea topic", url: "", notes: "", status: "idea",' +
        'assignee: "Ahmad", platforms: ["yt"], when: "", ctype: "", chk: {}, ftitle: "" });' +
        "savePlans(); sendToEditor(plans.find(p => p.id === 444), editors[0]);");
      if (ev('plans.find(p => p.id === 444).status') !== "script") fail("idea did not start at script");
      ok("handoff keeps the same workflow sequence (idea starts at Script)");

      // editor's Script section shows the same wizard (topic input + type cards)
      ev('ROLE = editors[0].id; applyRole(); edView = "script"; renderEditorsTab();');
      if (!d.getElementById("wtopic")) fail("script wizard missing in editor workspace");
      if (d.getElementById("edwork").textContent.includes("+ Custom topic")) fail("custom topic leaked to editor");
      ok("editor Script section = same wizard as owner");
      ev('ROLE = "owner"; applyRole(true); switchTab("plan");');

      // Assigned Tasks tab shows task + editor + status
      ev('boardView = "assigned"; renderBoard();');
      const atxt = d.getElementById("boardview").textContent;
      if (!atxt.includes("Seq video") || !atxt.includes("Hamza") || !atxt.includes("Script")) fail("Assigned view incomplete: " + atxt.slice(0, 150));
      ok("Assigned Tasks tab shows task, editor, status");

      // item must disappear from owner's Buffer editing view
      ev('switchTab("plan"); boardView = "editing"; renderBoard();');
      if (d.getElementById("boardview").textContent.includes("Test video")) fail("assigned item still in owner Buffer");
      ok("assigned item left the owner's Buffer");

      // editor sends it back
      ev("sendToOwner(plans.find(p => p.id === 111), editors[0])");
      if (!ev('plans.find(p => p.id === 111).eready && plans.find(p => p.id === 111).status === "publish" && plans.find(p => p.id === 111).ereadyAt ? 1 : 0')) fail("sendToOwner state wrong");
      if (!ev("ehist.length")) fail("history not recorded");
      ok("Send Back to Owner works + history recorded");

      // Ready to Post tab shows it with editor name
      ev('boardView = "ready"; renderBoard();');
      const txt = d.getElementById("boardview").textContent;
      if (!txt.includes("Test video") || !txt.includes("Hamza") || !txt.includes("completed")) fail("Ready to Post missing info: " + txt.slice(0, 200));
      ok("Ready to Post shows item + editor name + status");

      // reject with notes -> back to editor's Editing with the note attached
      prompts.push("Audio is out of sync, fix captions");
      ev('boardView = "ready"; renderBoard();');
      d.querySelector(".re-btn").click();
      const rp = ev('JSON.stringify(plans.find(p => p.id === 111))');
      const rpo = JSON.parse(rp);
      if (rpo.status !== "editing" || rpo.assignee !== "Editor" || !rpo.revnote) fail("reject flow broken: " + rp);
      ok("reject sends item back to editor with notes");
      // the editor sees the note on their Editing card; resending clears it
      ev('ROLE = editors[0].id; applyRole(); edView = "editing"; renderEditorsTab();');
      if (!d.getElementById("edwork").textContent.includes("Audio is out of sync")) fail("revision note not visible to editor");
      ok("editor sees the owner's revision note");
      ev('ROLE = "owner"; applyRole(true); sendToOwner(plans.find(p => p.id === 111), editors[0]); switchTab("plan");');
      if (ev('plans.find(p => p.id === 111).revnote') !== undefined) fail("revnote not cleared on resend");
      ok("resend clears the revision note");

      // a rejected POST returns to the editor's Script wizard, not Editing
      ev('plans.unshift({ id: 555, title: "X post", url: "", notes: "text", status: "script",' +
        'assignee: "Editor", eid: editors[0].id, platforms: ["x"], when: "", ctype: "post", chk: {}, ftitle: "" });' +
        "savePlans(); sendToOwner(plans.find(p => p.id === 555), editors[0]);");
      prompts.push("Hashtags ghalat hain");
      ev('boardView = "ready"; renderBoard();');
      [...d.querySelectorAll(".qrow")].find(r => r.textContent.includes("X post")).querySelector(".re-btn").click();
      if (ev('plans.find(p => p.id === 555).status') !== "script") fail("rejected post not in script stage");
      if (ev('plans.find(p => p.id === 555).assignee') !== "Editor") fail("rejected post not with editor");
      ok("rejected post returns to editor's Script wizard with note");

      // assigned work ALWAYS runs the full sequence: even a post goes Script -> Filming
      ev('var ta = document.createElement("textarea"); ta.id = "wizfinal"; ta.value = "final text";' +
        'document.body.appendChild(ta); wizBind = 555; wiz.type = "post"; wiz.plats = ["x"];' +
        "saveWiz(); ta.remove();");
      if (ev('plans.find(p => p.id === 555).status') !== "filming") fail("editor post skipped filming: " + ev('plans.find(p => p.id === 555).status'));
      ok("editor's finished post script goes to Filming (full sequence)");

      // the OWNER's own work follows the same sequence: post script -> Filming too
      ev('var ta2 = document.createElement("textarea"); ta2.id = "wizfinal"; ta2.value = "own post";' +
        'document.body.appendChild(ta2); wizBind = null; wiz.topic = "Own topic"; wiz.url = "";' +
        'wiz.type = "post"; wiz.plats = ["x"]; saveWiz(); ta2.remove();');
      if (ev('plans.find(p => p.title === "Own topic").status') !== "filming") fail("owner post skipped filming");
      ok("owner's own script also goes to Filming (no skipping)");

      // owner can delete an assigned task from the Assigned tab
      ev('switchTab("plan"); boardView = "assigned"; renderBoard();');
      const before = ev("plans.length");
      const delRow = [...d.querySelectorAll("#boardview .qrow")].find(r => r.textContent.includes("Idea topic"));
      if (!delRow) fail("assigned row for delete test missing");
      delRow.querySelector(".rowdel").click();
      if (ev("plans.length") !== before - 1) fail("assigned task delete failed");
      ok("owner can delete tasks in Assigned tab");

      // publish 'Ready to schedule' must NOT show it until approved
      ev('boardView = "publish"; renderBoard();');
      if (d.getElementById("boardview").textContent.includes("Test video")) fail("eready item leaked into Publish");
      ev('plans.find(x => x.id === 111).eready = false; renderBoard();');
      if (!d.getElementById("boardview").textContent.includes("Test video")) fail("approved item not in Publish");
      ok("approve flow moves item into Publish");

      // editor-mode lockdown
      ev("ROLE = editors[0].id; applyRole();");
      if (d.getElementById("tabbtn-plan").style.display !== "none") fail("Buffer tab visible to editor");
      if (d.getElementById("tab-editors").hidden) fail("editor not on Editors tab");
      if (d.getElementById("edwork").textContent.includes("Remove editor")) fail("owner controls visible to editor");
      ok("editor mode: Buffer hidden, only own workspace");

      // editor task flow with performance stats (late task)
      ev('etasks.unshift({ id: 222, title: "Make 3 banners", eid: editors[0].id, due: "2020-01-01", done: false });' +
        'saveEtasks(); edView = "work"; renderEditorsTab();');
      const chk = d.querySelector(".et-chk");
      if (!chk) fail("editor task checkbox missing");
      chk.checked = true;
      chk.dispatchEvent(new w.Event("change"));
      if (!ev('ehist.some(h => h.kind === "task" && h.late) ? 1 : 0')) fail("late task not tracked");
      const stats = d.getElementById("edwork").textContent;
      if (!stats.includes("Late")) fail("stats panel missing");
      ok("task completion tracked (late detected) + stats render");

      // editor password gate check (hash comparison)
      const phOk = await ev('sha256("secret123")');
      if (phOk !== ev("editors[0].ph")) fail("password hash mismatch");
      ok("gate password hash verifies");

      console.log("ALL SMOKE TESTS PASSED");
      process.exit(0);
    } catch (e) {
      fail(e.stack || String(e));
    }
  }, 300);
});
