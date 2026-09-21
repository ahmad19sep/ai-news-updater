# AI Radar — "Send to Studio" extension (X + LinkedIn)

Capture a post you're viewing on **X or LinkedIn** and send it to AI Radar Studio.
Three destinations from one popup:

- **Save to AI Radar** → copies a structured local capture and opens Studio. In
  **Agents & AI**, choose **Add a discovery → Import copied discovery**, review
  the source text and type, then save. This path does not put the raw post into
  Firebase.

- **♻️ Repurpose this post** → Studio **Repurpose** tab. The AI decides the smartest
  move and writes original X / LinkedIn / comment versions for your brand (no copying).
  Works on **X and LinkedIn**.
  shown, performance tracking.
- **✍️ Write with Anthropic** → Studio **Write** tab (Anthropic Write Engine): sends the
  selected/visible text as a seed for a short, original text-only post (best + 2 backups,
  style profiles, refine buttons, performance learning). Works on X, LinkedIn, anywhere.

It only acts when you click — it never scrapes in the background and never posts.

## Install (one time, ~1 minute)
1. Open **chrome://extensions** (Edge: `edge://extensions`).
2. Turn on **Developer mode** (top-right).
3. **Load unpacked** → pick this `x-extension` folder. Pin the icon.

## Use
1. On **x.com** or **linkedin.com**, open a post.
   - On **LinkedIn**, **select the post text first** (most reliable).
2. Click the extension → **Save to AI Radar**, **♻️ Repurpose**, or **✍️ Write**.
3. Open Studio → **Repurpose** → **🤖 Open in Claude / ⚡ ChatGPT**,
   paste the JSON it returns back, **Save**, then Copy the version you like.

## One-time Firebase rules
Add these to your Realtime Database rules (alongside the others) and Publish:

```json
"x_performance":         { ".read": true, ".write": true },
"social_captures":       { ".read": true, ".write": true },
"repurpose_performance": { ".read": true, ".write": true },
"x_mini_drafts":         { ".read": true, ".write": true },
"x_mini_performance":    { ".read": true, ".write": true }
```

## Notes
- The Firebase URL is set in `popup.js` (`FIREBASE_URL`) — your studio's DB.
- No auto-posting, no background scraping. Manual capture, human-approved output.
