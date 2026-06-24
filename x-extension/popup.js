/* AI Radar — popup. On click: ask the content script for the current tweet,
   then write it to Firebase /x_captures. Nothing happens without your click. */

// Your AI Radar Studio Firebase Realtime DB (public URL — same one the studio uses).
const FIREBASE_URL = "https://aixahmad-studio-default-rtdb.asia-southeast1.firebasedatabase.app";

const prevEl = document.getElementById("prev");
const stEl = document.getElementById("st");
const btn = document.getElementById("send");

function setStatus(msg, cls) { stEl.textContent = msg; stEl.className = "st" + (cls ? " " + cls : ""); }

function grab() {
  return new Promise(resolve => {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      const tab = tabs[0];
      if (!tab || !/https:\/\/(x|twitter)\.com\//.test(tab.url || "")) { resolve({ _notx: true }); return; }
      chrome.tabs.sendMessage(tab.id, "grab", data => {
        if (chrome.runtime.lastError) { resolve(null); return; }
        resolve(data);
      });
    });
  });
}

// Preview on open
grab().then(d => {
  if (d && d._notx) { prevEl.textContent = "Open a tweet on x.com first."; btn.disabled = true; }
  else if (d && d.post_text) { prevEl.textContent = (d.author_name ? d.author_name + " " + d.author_handle + "\n" : "") + d.post_text.slice(0, 240); }
  else { prevEl.textContent = "Couldn't find a post on this page — open a tweet."; }
});

btn.onclick = async () => {
  btn.disabled = true; setStatus("Reading post…");
  const d = await grab();
  if (!d || d._notx || !d.post_text) { setStatus("Couldn't read a post — open a tweet and retry.", "err"); btn.disabled = false; return; }
  const id = (d.post_id && String(d.post_id)) || String(Date.now());
  const now = new Date().toISOString();
  const body = {
    id, source_url: d.source_url || "", post_id: d.post_id || "",
    author_name: d.author_name || "", author_handle: d.author_handle || "",
    post_text: d.post_text || "", screenshot_url: "", topic: "",
    status: "captured", selected_reply: "", replies: [],
    created_at: now, updated_at: now
  };
  setStatus("Sending to Radar…");
  try {
    const r = await fetch(FIREBASE_URL + "/x_captures/" + id + ".json", {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    });
    if (r.ok) setStatus("✅ Sent! Open Studio → X Replies.", "ok");
    else setStatus("Blocked — add an x_captures rule in Firebase.", "err");
  } catch (e) {
    setStatus("Failed: " + e.message, "err");
  }
  btn.disabled = false;
};
