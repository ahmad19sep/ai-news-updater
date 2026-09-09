/* Regenerates PROMPTS.md from docs/templates.js — run: node dump_prompts.js
   The templates file is the ONE source of truth. This dump exists so the prompts
   are readable (and editable in a chat) without digging through JS; it is
   overwritten on every run, so it can never quietly drift from what ships. */
const fs = require("fs");
const path = require("path");

const win = {};
new Function("window", fs.readFileSync(path.join(__dirname, "docs", "templates.js"), "utf8"))(win);

const IDEA = "<<YOUR IDEA OR THE SELECTED TEXT>>";
const STORY = { title: "<<STORY HEADLINE>>", source: "<<SOURCE LINK>>" };

/* [heading, builder name, rendered prompt] — add a row when you add a builder */
const SECTIONS = [
  ["LinkedIn writer — insight mode", "buildLinkedInPrompt",
    win.buildLinkedInPrompt(Object.assign({ mode: "insight",
      excerpt: "<<THE FACTS YOU PASTED FROM THE SOURCE>>",
      audience: "<<WHO THIS IS FOR>>", note: "<<YOUR OWN EXPERIENCE, IF ANY>>" }, STORY))],
  ["LinkedIn writer — practical mode", "buildLinkedInPrompt",
    win.buildLinkedInPrompt(Object.assign({ mode: "practical",
      excerpt: "<<THE FACTS YOU PASTED FROM THE SOURCE>>",
      audience: "<<WHO THIS IS FOR>>" }, STORY))],
  ["X post (optional channel)", "buildXPrompt",
    win.buildXPrompt({ title: STORY.title, source: STORY.source, format: "single", voice: "breaking", hook: "curiosity" })],
  ["Repurpose a post you saw", "buildPostRepurposePrompt", win.buildPostRepurposePrompt({ post_text: IDEA })],
  ["Write engine", "buildAnthropicWritePrompt", win.buildAnthropicWritePrompt({ seed: IDEA })],
  ["Infographic from an approved post (optional)", "buildVisualPrompt",
    win.buildVisualPrompt({ kind: "infographic", post: "<<YOUR APPROVED LINKEDIN POST>>", title: "<<GRAPHIC HEADING>>" })],
  ["Poster from an approved post (optional)", "buildVisualPrompt",
    win.buildVisualPrompt({ kind: "poster", post: "<<YOUR APPROVED LINKEDIN POST>>", title: "<<HEADLINE ON THE IMAGE>>" })],
  ["X version of an approved post (optional)", "buildAdaptPrompt",
    win.buildAdaptPrompt({ platform: "x", post: "<<YOUR APPROVED LINKEDIN POST>>", source: STORY.source })],
  ["Reddit community check (optional)", "buildAdaptPrompt",
    win.buildAdaptPrompt({ platform: "reddit", post: "<<YOUR APPROVED LINKEDIN POST>>", community: "<<SUBREDDIT + ITS CURRENT RULES>>" })],
  ["Your own poster (Me tab)", "buildMePosterPrompt",
    win.buildMePosterPrompt({ headline: "<<HEADLINE ON THE POSTER>>", story: STORY.title })],
];

const out = [
  "# AI Radar Studio — the prompts the app actually sends",
  "",
  "**Generated file — do not edit by hand.** Change `docs/templates.js`, then run",
  "`node dump_prompts.js` to refresh this. Keep the `<<...>>` tokens and the",
  "`[[MARKER]]` shapes: the studio parses those.",
  "",
  "The studio is LinkedIn-first. X is an optional channel, Reddit is not a posting",
  "queue, and Facebook / Instagram / TikTok / WhatsApp / YouTube outputs were retired.",
  "The image prompts re-roll their assigned designer on every use, so what you see",
  "below is one example assignment.",
  "",
  "---",
  "",
];
SECTIONS.forEach(([heading, fn, text], i) => {
  out.push("## " + (i + 1) + ") " + heading + "  (`" + fn + "`)", "", "```text", text, "```", "", "---", "");
});
out.push("## Shared rule blocks", "");
[["LINKEDIN_CONTRACT", win.LINKEDIN_CONTRACT], ["HUMAN_VOICE", win.HUMAN_VOICE],
 ["HUMAN_IMAGE_BODY", win.HUMAN_IMAGE_BODY]].forEach(([name, body]) => {
  out.push("### `window." + name + "`", "", "```text", body, "```", "");
});

fs.writeFileSync(path.join(__dirname, "PROMPTS.md"), out.join("\n"), "utf8");
console.log("PROMPTS.md rewritten from docs/templates.js (" + SECTIONS.length + " prompts)");
