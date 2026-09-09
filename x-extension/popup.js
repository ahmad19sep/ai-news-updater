/* AI Radar — popup. On click, ask the content script for the post, then write it
   to Firebase: "Repurpose" -> /social_captures (X or LinkedIn), "Write" ->
   /x_mini_drafts. Nothing happens without your click.
   The Reply capture was removed with the studio's X Replies tab. */

const FIREBASE_URL = "https://aixahmad-studio-default-rtdb.asia-southeast1.firebasedatabase.app";

const prevEl = document.getElementById("prev");
const platEl = document.getElementById("plat");
const stEl = document.getElementById("st");
const repBtn = document.getElementById("rep");
const xminiBtn = document.getElementById("xmini");

function setStatus(msg, cls) { stEl.textContent = msg; stEl.className = "st" + (cls ? " " + cls : ""); }

function grab() {
  return new Promise(resolve => {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      const tab = tabs[0];
      const onX = /https:\/\/(x|twitter)\.com\//.test(tab && tab.url || "");
      const onLi = /https:\/\/(www\.)?linkedin\.com\//.test(tab && tab.url || "");
      if (!tab || (!onX && !onLi)) { resolve({ _bad: true }); return; }
      const ask = retry => chrome.tabs.sendMessage(tab.id, "grab", data => {
        if (chrome.runtime.lastError || !data) {
          // content script not loaded (tab not refreshed after install/reload) -> inject it, retry once
          if (retry && chrome.scripting) {
            chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] }, () => {
              if (chrome.runtime.lastError) { resolve(null); return; }
              ask(false);
            });
          } else { resolve(data || null); }
          return;
        }
        resolve(data);
      });
      ask(true);
    });
  });
}

let current = null;
grab().then(d => {
  current = d;
  if (d && d._bad) { prevEl.textContent = "Open a post on X or LinkedIn first."; platEl.textContent = "—"; repBtn.disabled = true; xminiBtn.disabled = true; return; }
  if (d && d.post_text) {
    platEl.textContent = d.platform === "linkedin" ? "LinkedIn" : "X";
    xminiBtn.disabled = false;
    prevEl.textContent = (d.author_name ? d.author_name + " " + (d.author_handle || "") + "\n" : "") + d.post_text.slice(0, 280);
  } else { prevEl.textContent = "Couldn't read this post. On LinkedIn, select the post text first; on X, open the tweet — then reopen this."; }
});

async function send(node, build, label) {
  setStatus("Reading post…");
  repBtn.disabled = xminiBtn.disabled = true;
  const d = current || await grab();
  current = d;
  if (!d || d._bad || !d.post_text) {
    setStatus("Couldn't read a post — open the tweet (or select the text), then retry.", "err");
    repBtn.disabled = false; xminiBtn.disabled = false; return;
  }
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
  repBtn.disabled = false; xminiBtn.disabled = false;
}

repBtn.onclick = () => send("social_captures", (d, id) => {
  const now = new Date().toISOString();
  return {
    id, platform: d.platform || "x", source_url: d.source_url || "", author_name: d.author_name || "",
    author_handle: d.author_handle || "", post_text: d.post_text || "", screenshot_url: "",
    image_url: d.image_url || "",
    post_type: "", best_action: "", status: "captured", ai_analysis: "", recommended_output: "",
    outputs: [], created_at: now, updated_at: now
  };
}, "Repurpose");

// Send the selected/visible text to the X Mini engine as a seed idea (works anywhere).
xminiBtn.onclick = () => send("x_mini_drafts", (d, id) => {
  const now = new Date().toISOString();
  return {
    id, seed: d.post_text || "", platform: d.platform || "web", source_url: d.source_url || "",
    status: "captured", created_at: now, updated_at: now
  };
}, "X Mini");
