/* AI Radar — popup. On click, ask the content script for the post, then write it
   to Firebase: "Repurpose" -> /social_captures (X or LinkedIn), "Reply" ->
   /x_captures (X only). Nothing happens without your click. */

const FIREBASE_URL = "https://aixahmad-studio-default-rtdb.asia-southeast1.firebasedatabase.app";

const prevEl = document.getElementById("prev");
const platEl = document.getElementById("plat");
const stEl = document.getElementById("st");
const repBtn = document.getElementById("rep");
const replyBtn = document.getElementById("reply");

function setStatus(msg, cls) { stEl.textContent = msg; stEl.className = "st" + (cls ? " " + cls : ""); }

function grab() {
  return new Promise(resolve => {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      const tab = tabs[0];
      const onX = /https:\/\/(x|twitter)\.com\//.test(tab && tab.url || "");
      const onLi = /https:\/\/(www\.)?linkedin\.com\//.test(tab && tab.url || "");
      if (!tab || (!onX && !onLi)) { resolve({ _bad: true }); return; }
      chrome.tabs.sendMessage(tab.id, "grab", data => {
        if (chrome.runtime.lastError) { resolve(null); return; }
        resolve(data);
      });
    });
  });
}

let current = null;
grab().then(d => {
  current = d;
  if (d && d._bad) { prevEl.textContent = "Open a post on X or LinkedIn first."; platEl.textContent = "—"; repBtn.disabled = true; replyBtn.disabled = true; return; }
  if (d && d.post_text) {
    platEl.textContent = d.platform === "linkedin" ? "LinkedIn" : "X";
    replyBtn.disabled = d.platform !== "x";   // reply engine is X-only
    prevEl.textContent = (d.author_name ? d.author_name + " " + (d.author_handle || "") + "\n" : "") + d.post_text.slice(0, 280);
  } else { prevEl.textContent = "Couldn't find a post — select the post text and reopen this."; }
});

async function send(node, build, label) {
  setStatus("Reading post…");
  repBtn.disabled = replyBtn.disabled = true;
  const d = current || await grab();
  if (!d || d._bad || !d.post_text) { setStatus("Couldn't read a post — select its text and retry.", "err"); repBtn.disabled = false; return; }
  const id = String(Date.now());
  const body = build(d, id);
  setStatus("Sending to Radar…");
  try {
    const r = await fetch(FIREBASE_URL + "/" + node + "/" + id + ".json", {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    });
    if (r.ok) setStatus("✅ Sent! Open Studio → " + label + ".", "ok");
    else setStatus("Blocked — add a /" + node + " Firebase rule.", "err");
  } catch (e) { setStatus("Failed: " + e.message, "err"); }
  repBtn.disabled = false; replyBtn.disabled = (current && current.platform !== "x");
}

repBtn.onclick = () => send("social_captures", (d, id) => {
  const now = new Date().toISOString();
  return {
    id, platform: d.platform || "x", source_url: d.source_url || "", author_name: d.author_name || "",
    author_handle: d.author_handle || "", post_text: d.post_text || "", screenshot_url: "",
    post_type: "", best_action: "", status: "captured", ai_analysis: "", recommended_output: "",
    outputs: [], created_at: now, updated_at: now
  };
}, "Repurpose");

replyBtn.onclick = () => send("x_captures", (d, id) => {
  const now = new Date().toISOString();
  return {
    id, source_url: d.source_url || "", post_id: d.post_id || "", author_name: d.author_name || "",
    author_handle: d.author_handle || "", post_text: d.post_text || "", screenshot_url: "", topic: "",
    status: "captured", selected_reply: "", replies: [], created_at: now, updated_at: now
  };
}, "X Replies");
