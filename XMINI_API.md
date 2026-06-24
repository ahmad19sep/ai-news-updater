# Optional: one-click generation with the Anthropic API (key stays safe)

The X Mini, Repurpose, and X Reply engines all work **right now** with **$0** by copying
the prompt into Claude/ChatGPT and pasting the JSON back. That needs no API key and no server.

If you'd rather press **one button** and get the posts back automatically, you can add the
Anthropic API. The golden rule (from your research doc): **the API key must NEVER live in
the website or the extension** — both are public and would leak it. The key must sit on a
tiny server. The cheapest correct option is a **free Cloudflare Worker** that holds the key
and calls Anthropic for you.

You pay Anthropic only for tokens used — roughly **$0.003–$0.02 per generation** (Haiku/Sonnet).

## 1. Create the Worker (free)
1. Sign up at <https://workers.cloudflare.com> → **Create Worker**.
2. Paste this code and deploy:

```js
export default {
  async fetch(req, env) {
    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "content-type",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
    };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST") return new Response("POST only", { status: 405, headers: cors });
    const { prompt, model, max_tokens, temperature } = await req.json();
    if (!prompt) return new Response(JSON.stringify({ error: "no prompt" }), { status: 400, headers: cors });
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": env.ANTHROPIC_API_KEY,          // <-- secret, set below
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: model || "claude-haiku-4-5-20251001", // Haiku = cheap; use a Sonnet id for nicer copy
        max_tokens: max_tokens || 1200,
        temperature: temperature ?? 0.6,
        messages: [{ role: "user", content: prompt }],
      }),
    });
    const data = await r.json();
    const text = (data.content && data.content[0] && data.content[0].text) || "";
    return new Response(JSON.stringify({ text, raw: data }), {
      headers: { ...cors, "content-type": "application/json" },
    });
  },
};
```

3. In the Worker's **Settings → Variables → Add secret**, add
   `ANTHROPIC_API_KEY` = your key from <https://console.anthropic.com>. (Never commit it.)
4. Copy your Worker URL, e.g. `https://x-writer.<you>.workers.dev`.

## 2. Turn it on in the Studio
This is the only step that needs me — tell me your Worker URL and I'll wire a
**⚡ Generate (API)** button into X Mini / Repurpose / X Replies that POSTs
`{prompt}` to your Worker and fills the results automatically (no copy-paste).
The Studio stores only the **URL** (public, harmless) — never the key.

## Why this is the right shape
- Key lives in the Worker's encrypted env, not in any public file — matches the security
  guidance in your architecture doc.
- The extension still only captures on your click; nothing auto-posts.
- You can flip back to the free copy-paste flow any time.
