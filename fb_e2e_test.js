/* End-to-end test: real page + real Firebase (run: node fb_e2e_test.js) */
const fs = require("fs");
const { JSDOM } = require("jsdom");
const { webcrypto } = require("crypto");

const FB_URL = "https://aixahmad-studio-default-rtdb.asia-southeast1.firebasedatabase.app";
const html = fs.readFileSync("docs/index.html", "utf8");

const dom = new JSDOM(html, {
  url: "https://ahmad19sep.github.io/ai-news-updater/",
  runScripts: "dangerously",
  resources: "usable",
  pretendToBeVisual: true,
  beforeParse(window) {
    Object.defineProperty(window, "crypto", { value: webcrypto });
    window.fetch = (...a) => fetch(...a);              // real network
    window.prompt = () => FB_URL;                      // owner pastes the DB URL
    window.confirm = () => true;                       // OK = reconnect/switch
    window.alert = m => console.log("ALERT:", m);
    window.EventSource = class { constructor(u) { this.url = u; } addEventListener() {} close() {} };
  },
});

const fail = m => { console.error("FAIL:", m); process.exit(1); };

dom.window.addEventListener("error", e => console.log("PAGE JS ERROR:", e.message));

dom.window.addEventListener("load", () => {
  setTimeout(async () => {
    const w = dom.window;
    const ev = s => w.eval(s);
    try {
      // make some board data
      ev('plans.unshift({ id: 9001, title: "Sync test item", url: "", notes: "", status: "idea",' +
        'assignee: "Ahmad", platforms: ["yt"], when: "", ctype: "", chk: {}, ftitle: "" }); savePlans();');

      // user clicks the cloud button (no sync configured in this fresh env)
      await ev("cloudClick()");
      await new Promise(r => setTimeout(r, 2500));

      const cfg = ev('localStorage.getItem("synccfg") || ""');
      console.log("synccfg after click:", cfg.slice(0, 60) + "...");
      if (!cfg.startsWith("fb:")) fail("Firebase sync was not enabled: " + cfg);

      // verify the board really landed in Firebase
      const url = ev("syncURL()");
      console.log("board URL:", url);
      const r = await fetch(url);
      const remote = await r.json();
      if (!remote || !remote.plans) fail("no board in Firebase: " + JSON.stringify(remote).slice(0, 120));
      if (!remote.plans.some(p => p.id === 9001)) fail("test item missing from remote board");
      console.log("ok - board pushed to Firebase, rev:", remote.rev, "plans:", remote.plans.length);

      // simulate the EDITOR device: fresh browser, link carries the sync config
      const link = ev("editorLink({ id: 'eTEST', ph: 'cafe01', name: 'usman' })");
      console.log("editor link:", link.slice(0, 120) + "...");
      if (!link.includes("&s=fb%3A")) fail("editor link missing firebase sync config");

      // pull as if we were the editor device with that config
      const cfg2 = decodeURIComponent(link.split("&s=")[1]);
      const url2 = cfg2.slice(3).split("|");
      const r2 = await fetch(url2[0] + "/boards/" + url2[1] + ".json");
      const remote2 = await r2.json();
      if (!remote2.plans.some(p => p.id === 9001)) fail("editor device would not see the task");
      console.log("ok - editor device receives the board through the link config");

      // file attachment round-trip: upload a "poster" to Firebase, read it back
      const poster = new w.File(["fake-poster-bytes"], "poster.png", { type: "image/png" });
      await w.eval("uploadFile")(w.eval('plans.find(p => p.id === 9001)'), poster);
      await new Promise(r => setTimeout(r, 500));
      const meta = ev('(plans.find(p => p.id === 9001).files || [])[0]');
      if (!meta) fail("file meta not saved on plan");
      const fUrl = ev("fileNode('" + meta.id + "')");
      const fr = await fetch(fUrl);
      const fjson = await fr.json();
      if (!fjson || fjson.name !== "poster.png" || !fjson.data.startsWith("data:image/png")) fail("file not in Firebase: " + JSON.stringify(fjson).slice(0, 100));
      console.log("ok - poster uploaded to Firebase and readable on any device");
      await fetch(fUrl, { method: "DELETE" });

      // cleanup: remove the test board node
      await fetch(url, { method: "DELETE" });
      console.log("ALL FIREBASE E2E CHECKS PASSED");
      process.exit(0);
    } catch (e) {
      fail(e.stack || String(e));
    }
  }, 300);
});
