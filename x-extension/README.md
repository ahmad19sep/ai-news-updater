# AI Radar — "Send to Studio" Chrome extension

Capture the X (Twitter) post you're viewing and send it to **AI Radar Studio →
X Replies**, where you generate 7 reply styles, pick one, and copy it. It only
acts when you click the toolbar button — it never scrapes in the background and
never posts anything for you.

## Install (one time, ~1 minute)

1. Open **chrome://extensions** in Chrome (or Edge: `edge://extensions`).
2. Turn on **Developer mode** (top-right).
3. Click **Load unpacked** and pick this `x-extension` folder.
4. Pin the **AI Radar — Send to Studio** icon to your toolbar.

## Use

1. On **x.com**, open (or scroll to) the post you want to reply to.
2. Click the extension icon → **📤 Send this post to Radar**.
3. Open **AI Radar Studio → X Replies** tab. Your post is there.
4. Click **🤖 Copy reply prompt**, paste it into Claude, paste the 7 replies
   back, then **Copy**/**Select** the one you like and reply on X yourself.

## One-time Firebase rule

Add this to your Realtime Database rules (alongside the others) and Publish:

```json
"x_captures": { ".read": true, ".write": true }
```

## Notes
- The Firebase URL is set in `popup.js` (`FIREBASE_URL`) — already your studio's DB.
- No auto-posting, no background scraping. Manual capture, human-approved replies.
