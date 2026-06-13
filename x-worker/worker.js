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
  const lang = b.lang === "ur"
    ? "Write in simple Roman Urdu with light English."
    : "Write in clear, simple English for a global audience.";
  const prompt =
`You write X (Twitter) content for "AI x Ahmad" (@aixahmad) — smart, clear takes on AI news
for a worldwide audience. ${lang}

STORY: ${b.title || ""}
SUMMARY: ${b.summary || "(use the title)"}
LINK: ${b.url || ""}

Format requested: ${b.template || "engaging thread"}.

Make it genuinely ENGAGING (this is the priority):
- Tweet 1 = a scroll-stopping hook: a surprising fact, a bold claim, or a "wait, what?" line. No "Thread 🧵" filler.
- Short punchy lines, simple words, one idea per tweet, build curiosity so people read the next one.
- Sound like a smart friend, not a press release. A little personality. Emojis only where natural (1 per tweet max).
- Last tweet: a sharp takeaway any reader can use + a soft CTA to follow @aixahmad.

Rules:
- Base everything ONLY on the story above — do not invent facts, numbers, or quotes.
- Each tweet MUST be <= 270 characters.
- Thread length: 3–6 tweets (or 1 for a single post).
- Max 2 hashtags total, only on the last tweet.
- Respectful tone, never mocking real tragedy.

Return ONLY a JSON array of tweet strings, nothing else. Example: ["tweet 1","tweet 2"]`;

  const provider = (env.WRITER || "cloudflare").toLowerCase();
  let text = "";
  if (provider === "cloudflare" || provider === "workers-ai") text = await callCloudflare(env, prompt);
  else if (provider === "gemini") text = await callGemini(env, prompt);
  else if (provider === "groq") text = await callGroq(env, prompt);
  else if (provider === "anthropic") text = await callAnthropic(env, prompt);
  else if (provider === "openai") text = await callOpenAI(env, prompt);
  else throw new Error("unknown WRITER: " + provider);

  const arr = parseTweets(text);
  if (!arr.length) throw new Error("writer returned no tweets");
  return arr.map(t => String(t).slice(0, 275)).slice(0, 8);
}

function parseTweets(text) {
  if (text == null) return [];
  if (typeof text !== "string") text = (text.response || text.result || text.text || JSON.stringify(text));
  text = String(text);
  if (!text) return [];
  const m = text.match(/\[[\s\S]*\]/);   // pull the JSON array out of any wrapper text
  if (m) { try { const a = JSON.parse(m[0]); if (Array.isArray(a)) return a.filter(Boolean); } catch (e) {} }
  // fallback: split numbered lines
  return text.split(/\n+/).map(l => l.replace(/^\s*\d+[.)]\s*/, "").trim()).filter(l => l.length > 3);
}

/* Cloudflare Workers AI — free daily allowance, no API key. Needs an "AI" binding
   on the Worker (Settings -> Bindings -> add Workers AI, variable name AI). */
async function callCloudflare(env, prompt) {
  if (!env.AI) throw new Error("Add an 'AI' binding (Worker Settings -> Bindings -> Workers AI, name it AI)");
  // 70B = best engaging copy on the free tier; if it ever errors, set WRITER_MODEL=@cf/meta/llama-3.1-8b-instruct
  const model = env.WRITER_MODEL || "@cf/meta/llama-3.3-70b-instruct-fp8-fast";
  const out = await env.AI.run(model, { messages: [{ role: "user", content: prompt }] });
  let t = (out && typeof out === "object") ? (out.response ?? out.result ?? out.text ?? "") : out;
  if (typeof t !== "string") t = JSON.stringify(t);
  return t;
}

/* Groq — free tier, fast. Set WRITER=groq and WRITER_KEY to a groq.com key. */
async function callGroq(env, prompt) {
  const model = env.WRITER_MODEL || "llama-3.3-70b-versatile";
  const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + env.WRITER_KEY },
    body: JSON.stringify({ model, messages: [{ role: "user", content: prompt }] }) });
  const d = await r.json();
  if (!r.ok) throw new Error("Groq: " + (d.error && d.error.message || r.status));
  return ((d.choices || [])[0] || {}).message?.content || "";
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
