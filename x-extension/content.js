/* AI Radar — content script.
   Runs ONLY when you click the toolbar button (it just answers a "grab" message).
   It never scrapes in the background and never sends anything on its own. */

function grabCurrentTweet() {
  const idM = location.pathname.match(/status\/(\d+)/);
  const arts = Array.from(document.querySelectorAll('article[data-testid="tweet"]'));
  if (!arts.length) return null;

  // On a /status/ page, prefer the primary tweet (matching the URL id); else the
  // first tweet in view.
  let art = null;
  if (idM) {
    art = arts.find(a => a.querySelector('a[href*="/status/' + idM[1] + '"]')) || arts[0];
  } else {
    art = arts[0];
  }
  if (!art) return null;

  const text = Array.from(art.querySelectorAll('[data-testid="tweetText"]'))
    .map(n => n.innerText).join("\n").trim();

  let author_name = "", author_handle = "";
  const nameBlock = art.querySelector('[data-testid="User-Name"]');
  if (nameBlock) {
    const lines = nameBlock.innerText.split("\n").map(s => s.trim()).filter(Boolean);
    author_name = lines[0] || "";
    const h = nameBlock.innerText.match(/@\w+/);
    author_handle = h ? h[0] : "";
  }

  // Best status URL + post id
  let post_id = idM ? idM[1] : "";
  let source_url = location.href.split("?")[0];
  const statusLink = art.querySelector('a[href*="/status/"]');
  if (statusLink) {
    const m = statusLink.getAttribute("href").match(/status\/(\d+)/);
    if (m) { post_id = post_id || m[1]; if (!idM) source_url = "https://x.com" + statusLink.getAttribute("href").split("?")[0]; }
  }

  return { post_text: text, author_name, author_handle, source_url, post_id };
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg === "grab") { sendResponse(grabCurrentTweet()); }
  return true;
});
