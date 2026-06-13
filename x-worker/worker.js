/* AI x Ahmad — X auto-post Worker (Cloudflare Workers, free tier)
 *
 * Holds the writer key + X OAuth keys (set as Worker Secrets, never in the website).
 * The app calls this with a shared APP_TOKEN. Actions:
 *   { action:"write",     ...story }            -> { tweets:[...] }   (draft only)
 *   { action:"post",      tweets:[...] }         -> { url }           (publish a thread)
 *   { action:"writepost", ...story }            -> { tweets, url }   (do both)
 *
 * Secrets expected (Worker → Settings → Variables and Secrets):
 *   APP_TOKEN, WRITER (gemini|anthropic|openai), WRITER_KEY, WRITER_MODEL (optional),
 *   X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
 */

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    if (request.method !== "POST") return json({ error: "POST only" }, 405);

    let body;
    try { body = await request.json(); } catch (e) { return json({ error: "bad json" }, 400); }
    if (!env.APP_TOKEN || body.token !== env.APP_TOKEN) return json({ error: "unauthorized" }, 401);

    try {
      const action = body.action || "writepost";
      let tweets = Array.isArray(body.tweets) ? body.tweets : null;

      if (action === "write" || action === "writepost") {
        tweets = await writeThread(env, body);
        if (action === "write") return json({ tweets });
      }
      if (!tweets || !tweets.length) return json({ error: "no tweets" }, 400);

      const url = await postThread(env, tweets);
      return json({ tweets, url });
    } catch (e) {
      return json({ error: String(e && e.message || e) }, 500);
    }
  },
};

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}

/* ---------------- 1) write the thread with the chosen LLM ---------------- */
async function writeThread(env, b) {
  const lang = b.lang === "en"
    ? "Write in simple, friendly English."
    : "Write in simple Roman Urdu with light English (easy to read).";
  const prompt =
`You write X (Twitter) content for "AI x Ahmad" (@aixahmad) — AI explained simply for
Pakistan & India. ${lang}

STORY: ${b.title || ""}
SUMMARY: ${b.summary || "(use the title)"}
LINK: ${b.url || ""}

Format requested: ${b.template || "engaging thread"}.

Rules:
- Base everything ONLY on the story above — do not invent facts, numbers, or quotes.
- Each tweet MUST be <= 270 characters.
- First tweet = a strong scroll-stopping hook.
- If it's a thread, 3–6 tweets, each one idea; last tweet ends with a soft CTA to follow @aixahmad.
- No more than 2 hashtags total, on the last tweet only.
- Respectful tone, never mocking real tragedy.

Return ONLY a JSON array of tweet strings, nothing else. Example: ["tweet 1","tweet 2"]`;

  const provider = (env.WRITER || "gemini").toLowerCase();
  let text = "";
  if (provider === "gemini") text = await callGemini(env, prompt);
  else if (provider === "anthropic") text = await callAnthropic(env, prompt);
  else if (provider === "openai") text = await callOpenAI(env, prompt);
  else throw new Error("unknown WRITER: " + provider);

  const arr = parseTweets(text);
  if (!arr.length) throw new Error("writer returned no tweets");
  return arr.map(t => String(t).slice(0, 275)).slice(0, 8);
}

function parseTweets(text) {
  if (!text) return [];
  const m = text.match(/\[[\s\S]*\]/);   // pull the JSON array out of any wrapper text
  if (m) { try { const a = JSON.parse(m[0]); if (Array.isArray(a)) return a.filter(Boolean); } catch (e) {} }
  // fallback: split numbered lines
  return text.split(/\n+/).map(l => l.replace(/^\s*\d+[.)]\s*/, "").trim()).filter(l => l.length > 3);
}

async function callGemini(env, prompt) {
  const model = env.WRITER_MODEL || "gemini-2.0-flash";
  const r = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.WRITER_KEY}`,
    { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }) });
  const d = await r.json();
  if (!r.ok) throw new Error("Gemini: " + (d.error && d.error.message || r.status));
  return (((d.candidates || [])[0] || {}).content || {}).parts?.[0]?.text || "";
}

async function callAnthropic(env, prompt) {
  const model = env.WRITER_MODEL || "claude-sonnet-4-6";
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": env.WRITER_KEY,
      "anthropic-version": "2023-06-01" },
    body: JSON.stringify({ model, max_tokens: 1024, messages: [{ role: "user", content: prompt }] }) });
  const d = await r.json();
  if (!r.ok) throw new Error("Claude: " + (d.error && d.error.message || r.status));
  return (d.content || []).map(c => c.text || "").join("");
}

async function callOpenAI(env, prompt) {
  const model = env.WRITER_MODEL || "gpt-4o-mini";
  const r = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + env.WRITER_KEY },
    body: JSON.stringify({ model, messages: [{ role: "user", content: prompt }] }) });
  const d = await r.json();
  if (!r.ok) throw new Error("OpenAI: " + (d.error && d.error.message || r.status));
  return ((d.choices || [])[0] || {}).message?.content || "";
}

/* ---------------- 2) post the thread to X (OAuth 1.0a) ---------------- */
async function postThread(env, tweets) {
  let replyTo = null, firstId = null;
  for (const text of tweets) {
    const payload = { text };
    if (replyTo) payload.reply = { in_reply_to_tweet_id: replyTo };
    const res = await xPost(env, "https://api.twitter.com/2/tweets", payload);
    const id = res && res.data && res.data.id;
    if (!id) throw new Error("X post failed: " + JSON.stringify(res));
    if (!firstId) firstId = id;
    replyTo = id;
  }
  return "https://x.com/i/web/status/" + firstId;
}

async function xPost(env, url, payload) {
  const oauth = {
    oauth_consumer_key: env.X_API_KEY,
    oauth_token: env.X_ACCESS_TOKEN,
    oauth_signature_method: "HMAC-SHA1",
    oauth_timestamp: Math.floor(Date.now() / 1000).toString(),
    oauth_nonce: crypto.randomUUID().replace(/-/g, ""),
    oauth_version: "1.0",
  };
  // For JSON bodies, only the oauth_* params are signed (no body params).
  const baseParams = Object.keys(oauth).sort()
    .map(k => enc(k) + "=" + enc(oauth[k])).join("&");
  const baseString = "POST&" + enc(url) + "&" + enc(baseParams);
  const signingKey = enc(env.X_API_SECRET) + "&" + enc(env.X_ACCESS_SECRET);
  oauth.oauth_signature = await hmacSha1(signingKey, baseString);
  const header = "OAuth " + Object.keys(oauth).sort()
    .map(k => enc(k) + '="' + enc(oauth[k]) + '"').join(", ");

  const r = await fetch(url, {
    method: "POST",
    headers: { "Authorization": header, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return await r.json();
}

function enc(s) {
  return encodeURIComponent(s).replace(/[!*'()]/g, c => "%" + c.charCodeAt(0).toString(16).toUpperCase());
}

async function hmacSha1(key, msg) {
  const k = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(key),
    { name: "HMAC", hash: "SHA-1" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(msg));
  return btoa(String.fromCharCode(...new Uint8Array(sig)));
}
