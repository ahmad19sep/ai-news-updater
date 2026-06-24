/* AI Radar — content script (X + LinkedIn).
   Runs only when you click the toolbar button (answers a "grab" message).
   Prefers your selected text; else the visible post. Never scrapes in the
   background, never sends anything on its own. */

function platformOf() {
  return /linkedin\.com/.test(location.host) ? "linkedin" : "x";
}

function selectedText() {
  try { return (window.getSelection ? window.getSelection().toString() : "").trim(); }
  catch (e) { return ""; }
}

function grabTweet() {
  const idM = location.pathname.match(/status\/(\d+)/);
  const arts = Array.from(document.querySelectorAll('article[data-testid="tweet"]'));
  if (!arts.length) return null;
  let art = idM ? (arts.find(a => a.querySelector('a[href*="/status/' + idM[1] + '"]')) || arts[0]) : arts[0];
  if (!art) return null;
  const text = Array.from(art.querySelectorAll('[data-testid="tweetText"]')).map(n => n.innerText).join("\n").trim();
  let author_name = "", author_handle = "";
  const nameBlock = art.querySelector('[data-testid="User-Name"]');
  if (nameBlock) {
    const lines = nameBlock.innerText.split("\n").map(s => s.trim()).filter(Boolean);
    author_name = lines[0] || "";
    const h = nameBlock.innerText.match(/@\w+/); author_handle = h ? h[0] : "";
  }
  let post_id = idM ? idM[1] : "", source_url = location.href.split("?")[0];
  const link = art.querySelector('a[href*="/status/"]');
  if (link) { const m = link.getAttribute("href").match(/status\/(\d+)/); if (m) { post_id = post_id || m[1]; if (!idM) source_url = "https://x.com" + link.getAttribute("href").split("?")[0]; } }
  let image_url = "";
  const pic = art.querySelector('[data-testid="tweetPhoto"] img, img[src*="twimg.com/media"]');
  if (pic) image_url = (pic.src || "").replace(/&name=\w+/, "&name=large");
  return { platform: "x", post_text: text, author_name, author_handle, source_url, post_id, image_url };
}

function grabLinkedIn() {
  const sel = selectedText();
  // Find the post container that's most in view (or the one holding the selection).
  const cards = Array.from(document.querySelectorAll(
    '.feed-shared-update-v2, .update-components-update-v2, div[data-urn*="activity"], article'));
  let card = null;
  if (sel) card = cards.find(c => (c.innerText || "").includes(sel.slice(0, 40)));
  if (!card) {
    // topmost reasonably-visible card
    card = cards.find(c => { const r = c.getBoundingClientRect(); return r.top > -120 && r.top < 360 && r.height > 80; }) || cards[0];
  }
  let post_text = sel;
  if (!post_text && card) {
    const t = card.querySelector('.update-components-text, .feed-shared-update-v2__description, .feed-shared-text, [data-test-id="main-feed-activity-card"]');
    post_text = (t ? t.innerText : card.innerText || "").trim().slice(0, 1500);
  }
  let author_name = "", author_handle = "", source_url = location.href.split("?")[0];
  if (card) {
    const a = card.querySelector('.update-components-actor__name, .update-components-actor__title, .feed-shared-actor__name');
    if (a) author_name = (a.innerText || "").split("\n")[0].trim();
    const prof = card.querySelector('a[href*="/in/"], a[href*="/company/"]');
    if (prof) { author_handle = prof.getAttribute("href").split("?")[0]; if (author_handle.startsWith("/")) author_handle = "https://www.linkedin.com" + author_handle; }
  }
  let image_url = "";
  if (card) { const im = card.querySelector('.update-components-image img, .feed-shared-image img, img[src*="media.licdn.com"]'); if (im) image_url = im.src || ""; }
  return { platform: "linkedin", post_text, author_name, author_handle, source_url, post_id: "", image_url };
}

function grab() {
  try {
    const sel = selectedText();
    if (platformOf() === "x") {
      const t = grabTweet();
      if (t && sel) t.post_text = sel;        // honor a manual selection on X too
      // last resort: if no tweet detected but text is selected, use the selection
      if ((!t || !t.post_text) && sel) return { platform: "x", post_text: sel, author_name: "", author_handle: "", source_url: location.href.split("?")[0], post_id: (location.pathname.match(/status\/(\d+)/) || [])[1] || "" };
      return t;
    }
    return grabLinkedIn();
  } catch (e) {
    const sel = selectedText();
    return sel ? { platform: platformOf(), post_text: sel, author_name: "", author_handle: "", source_url: location.href.split("?")[0], post_id: "" } : null;
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg === "grab") { try { sendResponse(grab()); } catch (e) { sendResponse(null); } }
  return true;
});
