/* AI x Ahmad - template library.
   Edit wording freely - the site reloads it automatically. */

/* ===== Shared HUMAN VOICE rules — injected into every content prompt so output
   reads like a real creator, not an AI bot (X suppresses AI-smelling content). ===== */
window.HUMAN_VOICE = [
  "WRITE LIKE A REAL HUMAN — NOT LIKE AI. This matters most: posts that smell AI-generated get suppressed.",
  "- Simple, clear English a beginner / creator / freelancer / builder gets instantly.",
  "- A real person on X/LinkedIn, never a press release or brand voice. Smart, curious, a little opinionated, conversational.",
  "- Vary sentence length: mix short punchy lines with one longer line. Fragments are fine. Starting with 'and'/'but'/'so' is fine.",
  "- ONE clear idea per post. Don't explain everything — land one strong point.",
  "- MAKE IT REPLYABLE: a broadcast gets ignored; give the reader a job — a question they can answer in 5 seconds, a side to pick, or a take they'll want to argue with. If nobody would reply to it, rewrite it.",
  "- NO LINKS inside X posts — X suppresses link posts. If a link is needed, it goes in the first reply.",
  "- Add a personal angle when it fits: 'my take…', 'i think…', 'the part people ignore is…', 'for builders this means…', 'for beginners, the simple lesson is…'.",
  "- Strong HUMAN hook, e.g.: 'Most people are missing the real point here…' / 'This looks small, but it matters…' / 'I don't think this is just another AI update…' / 'The interesting part isn't the announcement — it's what comes next.' / 'Here's the simple version…'.",
  "- Don't make it too perfect — it should feel edited by a human, not generated.",
  "- Emojis: 0-2 max, only when they add meaning. Hashtags: X none or 1; LinkedIn 2-3 max.",
  "- No forced 'Follow me for more' — only a soft CTA sometimes. End with a natural question or a sharp takeaway, never a forced engagement line.",
  "- NEVER invent facts, names, numbers, dates, or company claims. If the source is unclear, say so carefully.",
  "- For a technical topic, cover: what happened, why it matters, who should care, my take.",
  "- BANNED phrases: game changer, game-changer, revolutionising/revolutionize the future, unlock the power, unlock value, next big thing, cutting-edge, seamless, transformative, in today's world, the future is here, AI is changing everything, this will disrupt every industry, leverage, harness, robust, paradigm shift, landscape, delve, dive in, deep dive, supercharge, elevate, testament, underscore.",
  "- BANNED AI sentence patterns: \"It's not just X, it's Y\"; \"The real X isn't Y, it's Z\"; \"Here's the thing\"; rule-of-three lists; a neat \"X. But Y.\" as the whole post; throat-clearing openers; summary closers ('At the end of the day', 'Ultimately')."
].join("\n");

/* ===== The Design Studio: 20 designers, each with their own creative mind.
   The studio (this code) randomly assigns a DIFFERENT designer per prompt, so no
   two posters look alike — the AI can't just keep picking its favorite. ===== */
window.DESIGN_ROSTER = [
"MARA — Swiss minimalist: huge type, strict grid, one color only, massive whitespace.",
"DIEGO — tabloid maximalist: loud condensed caps, dramatic crops, red/yellow highlight bars.",
"YUKI — magazine editorial: elegant serif+sans pairing, generous margins, quiet luxury.",
"TOMMY — social-native: sticker-style cutouts with white outlines, playful tilted elements, bold energy (still clean).",
"INGRID — brutalist: raw black/white, harsh contrast, mono-spaced type, one neon accent.",
"SAM — data-first: the number IS the design; huge stats, clean chart elements, sharp annotations.",
"LENA — cinematic: film-still lighting, moody depth of field, subtle grain, headline like movie titles.",
"KOFI — flat-vector infographic: friendly icons, rounded cards, soft palette + one strong accent.",
"PRIYA — newspaper heritage: column rules, serif headlines, ink-on-paper texture, modernized.",
"MARCO — collage punk: torn paper edges, tape, highlighter scribbles — controlled chaos.",
"AISHA — luxury tech: deep charcoal, gold or white type, premium product-shot lighting.",
"NOAH — photojournalist: the photo carries everything; minimal caption-style type at the bottom.",
"ELIF — geometric modernist: diagonal splits, big circles, bold shapes framing the photo.",
"JUN — retro print: 70s-90s print palettes, halftone dots, vintage type pairings.",
"CARLA — corporate clean: airy blue/white, rounded cards, trustworthy business look.",
"DEV — internet-fluent: split reaction panels, bold white captions, meme structure without cringe.",
"SOFIA — soft editorial: warm cream tones, gentle shadows, friendly rounded type.",
"RUSLAN — kinetic: tilted frames, motion-blur edges, speed lines, urgency in everything.",
"AMARA — human-first: candid people moments, warm natural light, headline that reads like a caption.",
"OWEN — schematic: blueprint lines, labels, annotation arrows, precise engineer aesthetic (no sci-fi glow)."
];
window.designStudio = function () {
  var pick = window.DESIGN_ROSTER[Math.floor(Math.random() * window.DESIGN_ROSTER.length)];
  return [
"YOU RUN A STUDIO OF 20 WORLD-CLASS GRAPHIC DESIGNERS, each with their own mind, taste and signature.",
"THE STUDIO HAS ASSIGNED THIS POST TO: " + pick,
"Design ENTIRELY through this designer's eyes — their layout instincts, their type choices, their color feelings. Start your output with [DESIGNER: name]. Only hand it to a different roster member if this designer's style truly cannot serve the story (then say why in one line).",
"THE FULL ROSTER (context for who they are):",
window.DESIGN_ROSTER.map(function (d, i) { return (i + 1) + ". " + d; }).join("\n"),
"Whoever designs it, the studio's base rules below still apply (realism, exact headline, legibility, footer)."
].join("\n");
};

/* ===== Shared REALISTIC IMAGE rules — an ART DIRECTOR, not one fixed template.
   window.HUMAN_IMAGE is a GETTER: every read re-rolls the assigned designer. ===== */
window.HUMAN_IMAGE_BODY = [
"ACT LIKE A NEWS ART DIRECTOR. Do NOT use one fixed layout for every story — analyze first, then design.",
"STEP 1 — classify the story: funding/numbers, partnership/MoU, product launch, policy/government, people (hire/founder/quote), research/report, controversy/drama, how-to/list, or AHMAD'S OWN announcement/opinion/tip (then use format 9).",
"STEP 2 — pick the ONE poster format that fits THIS story best. HARD RULE: never use the same format two posts in a row — rotate through ALL 13 formats over time so the feed never looks repetitive. If a format was likely used recently for a similar story, pick the next-best fit instead:",
"1. MARKER-HIGHLIGHT PHOTO — real photo of the actual event/subject (signing ceremony, stage, office); big bold headline across the lower half; the 1-2 KEY phrases sit on solid highlight bars (yellow or one brand color) behind the words. Best for partnerships, launches, announcements.",
"2. LOWER-THIRD BAND — real photo top ~70% (podium, flags, office, market); solid dark band bottom ~30% with a clean bold headline, key words in ONE accent color (green or blue), thin accent line on the left. Best for policy, government, economy, business.",
"3. TOP-HEADLINE CARD — the headline sits at the TOP with a solid colored highlight bar behind the opening words, and the photo/scene fills the area below. Best for tech/platform news and reports.",
"4. PEOPLE / QUOTE CARD — flat vivid single-color background; cut-out photo of the person with a white sticker outline; large quote marks with a short quote or announcement; their name + role in bold; a small badge tag on top (FUNDING / NEW HIRE / BIG MOVE). Best for hires, founder quotes, people stories.",
"5. PHOTO CAPTION CARD — natural candid photo of the person or scene; simple bold left-aligned caption text in the lower third over a soft dark gradient; understated, editorial. Best for funding rounds and profiles.",
"6. CATEGORY-TAG BOLD CAPS — dark moody photo; a small centered category chip (AI / STARTUPS / FUNDING) with a thin line; ALL-CAPS condensed white headline below it. Best for dramatic or viral stories.",
"7. BIG-NUMBER POSTER — one huge number dominates the design ($28M, 20,000, 15 YEARS) with a short supporting headline under it. Best when the number IS the story.",
"8. CUTOUT VIRAL CARD — cut-out photo of the KEY PERSON in the story, chest-up, centered over a dark blurred background; one or two CIRCLE inset images beside them (the product or thing the story is about); below, a thin divider line, then a big ALL-CAPS condensed headline filling the lower third: white text with the 2-3 most important words in the ACCENT COLOR; small 'SWIPE FOR MORE ➜' hint at the very bottom if it's a carousel cover. High-energy but clean. Best for big-company drama, leaks, viral moments, CEO/person-centered stories.",
"9. AHMAD PERSONAL BRAND CARD — uses AHMAD'S OWN PHOTO (attached/uploaded in this chat). His FACE must stay exactly as the attached photo — never regenerate or change it — but VARY HIS POSE AND SCENE to match the post (pick the one that fits, rotate between posts): working on a laptop (productivity/tools), reading a book or tablet (learning/explainers), writing notes on paper (tips/guides), pointing toward the headline (announcements), arms crossed with a confident smile (opinions/hot takes), hand on chin thinking (questions/debates), celebrating fist-up (milestones/wins), walking with a backpack in a city or airport (events/travel/future-of-work), late-night desk with coffee and warm lamp light (build-in-public). Layout: Ahmad cut out on one side, name 'AHMAD' bold + '@aixahmad' small under it, the headline/tip on the other side in clean editorial type with key words in the accent color, optional small circle inset of the tool/product. Best for: Ahmad's own announcements, opinions, my-take posts, tips, milestones. START the prompt with: 'Use the attached photo of Ahmad — keep his face exactly as provided, adapt only the pose, outfit and scene as described.'",
"10. BREAKING STRIP — a bold red 'BREAKING' tag strip in the top corner, full-bleed real photo of the subject, thick dark lower band with a tight, urgent headline; key word in the accent color. Best for urgent big announcements and just-happened news.",
"11. VS / MATCHUP CARD — split screen: the two rivals (tools, companies, models) on the left and right with their key person or product photo, names under each, a big 'VS' badge in the middle, and the question/headline in a band below. Best for comparisons, rivalries, benchmark fights.",
"12. THEN-VS-NOW TIMELINE — left side: the old state with its year label (muted/desaturated photo); right side: today with its year (vivid photo); a bold arrow between them; headline underneath. Best for progress stories, 'how far AI has come', anniversaries.",
"13. SOCIAL-POST QUOTE CARD — the key line presented as a clean rounded social-post card floating on a flat bold background: small round avatar circle, name + handle, the quote/fact in large text inside the card, light drop shadow. Use Ahmad's avatar/name ONLY for Ahmad's own takes — never fabricate a post screenshot from a real person. Best for hot takes, one-line truths, striking stats.",
"STEP 3 — write ONE detailed image prompt for the chosen format: the exact realistic scene (real people, real office/lab/podium/product, natural lighting, realistic shadows and textures — like a designer composed it in Photoshop/Figma, NOT an AI poster: no sci-fi glow, no glowing circuits, no floating holograms, no random symbols), the exact layout placement, ONE accent color, and clean modern editorial typography with proper spacing.",
"ACCENT COLOR: pick ONE per poster and VARY it between posts — electric blue, red, yellow, or green; match the story's mood (red = drama/warning/leak, yellow = money/opportunity, blue = tech/product, green = growth/policy). Never more than one accent color on a poster.",
"ALWAYS: vertical 4:5. Render the exact headline provided, word for word, spelled perfectly. Add ONE small, subtle footer line at the very bottom: 'Follow @aixahmad for more — like ❤️ & share' — small, clean, never competing with the headline. No other text, no logos, no watermarks. Headline large and perfectly legible on a phone."
].join("\n");
/* every read of HUMAN_IMAGE re-rolls the assigned designer, so each prompt differs */
Object.defineProperty(window, "HUMAN_IMAGE", {
  get: function () { return window.designStudio() + "\n\n" + window.HUMAN_IMAGE_BODY; },
  configurable: true
});

window.XLIB = {
  universal: `UNIVERSAL RULES (engagement-optimized for the 2026 X algorithm):
- Hook in the FIRST line; first 5-7 words must stop the scroll. Front-load the most specific/surprising fact (names, numbers, model versions).
- Write for REPLIES, BOOKMARKS, REPOSTS — not likes. Always end with an engagement mechanism: a sharp question, a debate trigger, a bookmark cue, or a follow CTA.
- LINK PLACEMENT: put the link at the very END — on its own line, as the final line of the LAST tweet/post, formatted as "🔗 <url>". Never put a link anywhere else in the text.
- Use 0-2 FUNCTIONAL emojis only (signposts: 🚨 breaking, 🤯 stunning, 🧵 thread, 👇 read-on). Never decorative emoji spam.
- 0-2 hashtags, final tweet ONLY (usually zero). 3+ hurts reach.
- Whitespace + short lines; one idea per line. No walls of text.
- Constructive/substantive tone — sharp is fine, pure negativity gets throttled.
- NEVER invent facts, numbers, or quotes. Use ONLY the source. Accuracy protects reach.`,
  formats: {
    single: { name: "Single post", body:
`FORMAT: ONE substantial single X post (NOT a thread). Structure it as:
- Line 1: a scroll-stopping HOOK (front-load the most specific/surprising fact — names, numbers, model versions).
- Then 3-5 SHORT lines: the concrete facts/points AND why it matters to a normal reader. One idea per line, lots of whitespace, zero fluff.
- Then ONE engagement line: a sharp question or a "Bookmark this" cue.
- Then the link on its OWN final line.
Make it meaty and skimmable — roughly 6-9 lines (~500-900 characters). Substantial, never padded.` },
    short: { name: "Short thread (3-5)", body:
`FORMAT: a SHORT THREAD of 3-5 tweets. Tweet 1 = standalone hook (<=25 words) + a forward cue ("Here's what you need to know:" or "👇"). Tweets 2-4 = one idea each, lead with the point. Final tweet = one-line takeaway + engagement CTA. Number tweets 1/, 2/, ...` },
    long: { name: "Long thread (6-10)", body:
`FORMAT: a LONG THREAD of 6-10 tweets. T1 = hook (<=25 words, promise the payoff). T2 = context/stakes (why it matters now). T3-8 = body, one point per tweet, add a mid-thread mini-cliffhanger. Penultimate = the key insight or prediction. Final = recap + "Bookmark this" / follow CTA. Number tweets 1/, 2/, ...` },
    quote: { name: "Quote-tweet", body:
`FORMAT: a QUOTE-TWEET commenting on the story, 150-270 chars. Add a unique angle, data point, or sharp take (never empty praise). Stake a position or ask a question to drive replies.` },
  },
  voices: {
    breaking: { name: "Breaking-news wire", body:
`VOICE: neutral, authoritative breaking-news wire. Open "BREAKING:" or "NEW:" + the single most important fact ([Company] just [did what], <=15 words). Then 2-4 ultra-scannable lines (who / what / key number / when). Report, don't editorialize. No hype adjectives.` },
    hottake: { name: "Hot take / opinion", body:
`VOICE: bold, defensible hot take. Open with a contrarian or pattern-interrupting claim most will instinctively debate. Back it with ONE crisp fact from the source. End "Change my mind." / "Am I wrong?". Provocative but substantive, never insulting.` },
    educational: { name: "Educational explainer", body:
`VOICE: clear educator. Hook = name the development + promise clarity ("Here's what it actually means:"). Explain plainly: what it is, why it matters, what changes for the reader. Short sentences, simple analogies. End with a takeaway + "Bookmark this" or a question.` },
    casual: { name: "Casual / relatable", body:
`VOICE: casual, like texting a smart friend. Hook with a relatable reaction ("Okay this is actually wild."). Tie it to everyday life. End with an open question ("anyone else seeing this?").` },
    analytical: { name: "Analytical deep-dive", body:
`VOICE: respected analyst. Hook with the non-obvious implication ("The real story isn't X — it's Y."). Bring rigor: specific models/numbers, prior context, second-order effects. End "What I'll be watching:" + a question. Separate fact from interpretation.` },
    hype: { name: "Hype / excitement", body:
`VOICE: genuine high-energy excitement. Hook with awe ("This changes everything."). Emphasize the most jaw-dropping capability/number from the source. 1-3 purposeful emojis (🤯🔥⚡). End "what would you build with this?". Stay truthful — no overstating.` },
    skeptical: { name: "Skeptical / critical", body:
`VOICE: credible skeptic cutting through hype. Hook by puncturing it with a specific, evidence-based reservation ("Everyone's hyping X. Here's what they're missing:"). Raise a concrete limitation grounded in the source. Incisive but fair. End with a debate question.` },
    storytelling: { name: "Storytelling", body:
`VOICE: master storyteller. Hook with a moment/tension ("In 2023 this was impossible. Last night it shipped."). Build setup -> turning point -> payoff using the source's facts. Vivid, concrete, human. End with the meaning + an invitation to reflect.` },
  },
  hooks: {
    auto: { name: "Auto (let the style decide)", body: "" },
    curiosity: { name: "Curiosity gap", body:
`HOOK OVERRIDE: open with a curiosity gap — hint at something surprising WITHOUT revealing it (<=18 words). Don't reveal the payoff until the next line/tweet.` },
    bold: { name: "Bold claim", body:
`HOOK OVERRIDE: open with ONE bold declarative claim most readers will want to challenge or affirm, defensible from the source (<=15 words).` },
    stat: { name: "Stat / number", body:
`HOOK OVERRIDE: open with the most striking specific number from the source, stated plainly (<=15 words). Never fabricate or round misleadingly.` },
    question: { name: "Question", body:
`HOOK OVERRIDE: open with a sharp question the news provokes — avoid yes/no, favor opinion-inviting (<=15 words).` },
    contrarian: { name: "Contrarian", body:
`HOOK OVERRIDE: open by challenging the consensus ("Everyone thinks X. They're wrong — here's the data."), backed by the source, constructive (<=18 words).` },
    breaking: { name: "Breaking", body:
`HOOK OVERRIDE: open with "BREAKING:" (or "🚨 BREAKING:") + the single most important fact: [Company] just [did what] (<=15 words). One urgency emoji max. Use only if genuinely fresh.` },
  },
};

window.buildXPrompt = function (o) {
  const L = window.XLIB;
  const fmt = (L.formats[o.format] || L.formats.single).body;
  const voice = (L.voices[o.voice] || L.voices.breaking).body;
  const hook = (L.hooks[o.hook] || L.hooks.auto).body;
  const lang = o.lang === "ur"
    ? "Write in simple Roman Urdu with light English."
    : "Write in clear, simple English for a global worldwide audience.";
  return [
    "You are an expert X (Twitter) writer specializing in AI news that earns maximum impressions and engagement (replies, bookmarks, reposts — not just likes).",
    lang, "",
    fmt, "", voice, (hook ? hook + "\n" : ""),
    L.universal, "",
    "STORY TITLE: " + (o.title || ""),
    (o.summary ? "SUMMARY: " + o.summary : ""),
    (o.url ? "LINK TO PLACE AT THE END: " + o.url : ""),
    "",
    'Return ONLY a JSON array of strings — one string per tweet (a single post = an array of length 1). End the LAST tweet with the link on its own final line, prefixed with 🔗. No text outside the JSON array.',
  ].filter(x => x !== "").join("\n");
};


/* ===== LinkedIn editorial contract — the shared rules every LinkedIn draft obeys.
   Kept separate from HUMAN_VOICE (that one is X-native: no links, lowercase energy).
   The point of these rules: one useful post for one real audience, built only from
   facts we actually supplied — never from a link the AI cannot open. ===== */
window.LINKEDIN_CONTRACT = [
"EVIDENCE RULES — these come first, before style:",
"- FIRST, if you have web browsing or any retrieval tool: OPEN the source link below and read the article. Write from what you actually read, and say in [[REVIEW]] that you retrieved it.",
"- If you have no browsing tool, or the fetch fails, or the page is paywalled or empty: say so plainly in [[REVIEW]] and work only from the facts supplied below. Never describe a page you did not actually read — a headline is not an article, and a guess dressed as a summary is the one thing you must not produce.",
"- Never invent numbers, quotes, dates, prices, features, benchmarks, study results, client names or outcomes.",
"- A company's own claim stays attributed to them (\"OpenAI says…\", \"according to the announcement\"). A vendor claim is not independent proof.",
"- Check timing separately from when the story was collected. If the supplied material does not establish WHEN this happened, do not write new, breaking, today, just launched or latest. An older piece can still be worth discussing — as a dated argument, not fresh news.",
"- NEVER ask the operator for anything. Do not request the article text, the audience, or an angle: you have a link, so read it. Always come back with a post.",
"- If you truly could not read the source and no facts were supplied, still write — but only what the HEADLINE itself supports: keep it short, attribute it to the headline (\"the headline says…\"), build the value out of the professional question it raises rather than invented detail, and note the limitation in [[REVIEW]]. Thin and honest beats confident and made up.",
"- The one case for [[STATUS]] skip: the story genuinely has nothing useful for this audience. Give a one-line reason. That is a judgement call, not a request for more input.",
"- Do not turn an unsupported fact into an opinion to make it publishable. \"I think X\" does not fix missing evidence for X.",
"",
"PERSONAL VOICE:",
"- Write in first person, as the operator, in plain English.",
"- Firsthand claims (\"I tested\", \"my client\", \"we cut costs\") are allowed ONLY when a personal note is supplied below. With no note, write as someone who reads this space and thinks carefully about it — attributed explanation and honest interpretation.",
"- A new opinion is fine, but flag it in [[REVIEW]] as needing approval before posting.",
"- Never reuse another creator's wording, structure, story or distinctive thesis.",
"",
"WRITING:",
"- ONE idea per post, aimed squarely at the audience below.",
"- Open with something specific: a decision, a consequence, a concrete fact. Never \"In a major development\", never a generic reaction, never fake urgency.",
"- Natural paragraphs, varied sentence length. No rigid template, no repeated skeleton.",
"- 120-220 words is the default range — write less for a smaller idea. This is an editorial preference, not a platform limit.",
"- NO forced call to action. No \"follow me\", no \"repost ♻️\", no \"comment YES\", no \"agree?\", no \"tag someone\", no engagement bait of any kind. A real question at the end is optional, and only when you genuinely want the answer.",
"- Hashtags optional, 0-3 maximum. Emojis 0-2, only where they add meaning.",
"- Keep the source visible enough that a reader can verify the claim. No \"link in comments\" rule, no website detour required.",
"- Plain text only. No markdown, no bold markers, no headers.",
"- BANNED phrases: game changer, game-changer, revolutionise/revolutionize, unlock the power, unlock value, next big thing, cutting-edge, seamless, transformative, in today's world, the future is here, AI is changing everything, this will disrupt every industry, leverage, harness, robust, paradigm shift, landscape, delve, dive in, deep dive, supercharge, elevate, testament, underscore.",
"- BANNED AI sentence patterns: \"It's not just X, it's Y\"; \"The real X isn't Y, it's Z\"; \"Here's the thing\"; rule-of-three lists; throat-clearing openers; summary closers (\"At the end of the day\", \"Ultimately\")."
].join("\n");

/* ---- The canonical LinkedIn writer: ONE selected story -> ONE useful LinkedIn draft.
   Two modes, same writer:
     insight   — one supported development/argument + what it means for the audience
     practical — one supported action, decision checklist, tradeoff or evaluation question
   Output stays in this project's [[MARKER]] format so the studio can split post text
   from the private review notes. ---- */
window.buildLinkedInPrompt = function (o) {
  o = o || {};
  var mode = o.mode === "practical" ? "practical" : "insight";
  var modeBlock = mode === "practical" ? [
'MODE: PRACTICAL TAKEAWAY.',
'Give the reader ONE useful thing they can act on: a decision checklist, an evaluation question, a tradeoff to weigh, or a concrete step — but ONLY if the supplied facts actually support it.',
'Numbered steps are optional, never required. Product instructions, pricing, free-access claims, eligibility and deadlines need direct support in the material below.',
'If the material cannot support a how-to, use a decision question, an evaluation checklist or a tradeoff instead — there is always one of those available. Never manufacture a tutorial to fill this mode, and never hand the job back to the operator.'
  ] : [
'MODE: NEWS INSIGHT.',
'Explain ONE specific professional implication of what happened — the consequence, the decision it forces, or the thing most people reading the headline will miss.',
'Give just enough context for the implication to land. This is not a neutral news bulletin and not a 700-word article.',
'Include one honest limitation, caveat or open question. End when the idea is complete, not with a manufactured flourish.'
  ];
  return [
'You are helping a real person write one LinkedIn post. You are an editorial assistant, not an autonomous publisher.',
'',
window.LINKEDIN_CONTRACT,
'',
modeBlock.join('\n'),
'',
'AUDIENCE: ' + (o.audience || 'not specified — write for working professionals who care about practical AI. Do not ask who the audience is; just write.'),
'',
'STORY: ' + (o.title || '(none supplied)'),
(o.source ? 'SOURCE LINK — open this and read the article before writing: ' + o.source : ''),
'',
'SOURCE FACTS SUPPLIED' + (o.excerpt ? ':' : ' — none pasted, so open the link above and read the article yourself.'),
(o.excerpt || ''),
'',
(o.note ? 'APPROVED PERSONAL NOTE (real, owner-supplied — firsthand language is allowed only for what this covers):\n' + o.note
        : 'APPROVED PERSONAL NOTE: none supplied. Do NOT write any firsthand experience claim.'),
'',
(o.recent ? 'RECENTLY POSTED (do not repeat these angles or openings):\n' + o.recent + '\n' : ''),
'OUTPUT EXACTLY in this format. Every [[MARKER]] on its own line, nothing before [[STATUS]] and nothing after [[END]].',
'',
'[[STATUS]]',
'(one word: draft, or skip only when the story is genuinely not worth a post)',
'',
'[[POST]]',
'(the LinkedIn post exactly as it would be published — nothing else, no notes, no labels. Leave empty only for skip.)',
'',
'[[SOURCES]]',
'(the attribution line(s) a reader can check: source name and the link supplied above. Leave empty if none was supplied.)',
'',
'[[REVIEW]]',
'(private notes for the operator, never part of the post: which sentence rests on which supplied fact; anything that is your interpretation rather than a reported fact; any opinion needing approval before posting; any claim you deliberately left out and why.)',
'',
'[[MISSING]]',
'(leave this empty — it exists only so an older parser does not choke.)',
(o.visual === false ? null :
'\n[[VISUAL]]\n' +
'(A ready-to-paste image-generation prompt for a picture to go WITH the post above. Skip this — leave it empty — if the post is pure commentary that a graphic would only decorate. Build it ONLY from what the post actually says: never put a number, name, step or claim on the image that is not in the post.\n' +
'Choose whichever suits the post:\n' +
'  A) INFOGRAPHIC (4:5) when the post carries steps, a comparison, a checklist, a decision or several named things — pick ONE format from the library below.\n' +
'  B) HEADLINE POSTER (4:5) when the post is about a single development and the point is the statement itself.\n' +
'\n' + window.INFOGRAPHIC_FORMATS + '\n' +
'\nFor a HEADLINE POSTER instead: a realistic photo-based scene (office, lab, desk, stage — natural light, real textures, no sci-fi glow, no robots, no glowing circuits), with the post\'s core line rendered on it word for word, spelled exactly, in clean modern editorial type, one accent colour.\n' +
'Either way: every word that appears on the image must be spelled exactly as written here — a misspelling ruins the graphic. No logos, no watermarks. One small quiet "@aixahmad" mark in a bottom corner as attribution — never a follow/like/share line.)'),
'',
'[[END]]',
  ].filter(function (x) { return x !== null && x !== undefined; }).join('\n');
};

window.buildPostRepurposePrompt = function (o) {
  return [
    "You are an intelligent social-media strategist for Ahmad / @aixahmad (an AI-news + AI-builder brand). You turn good posts Ahmad SEES on X or LinkedIn into ORIGINAL content for his own brand — without copying, sounding robotic, or wasting time.",
    "",
    "MAIN GOAL: Do not just rewrite the post. Think first. Understand the post. Decide the smartest move. Then write.",
    "",
    "SOURCE POST:",
    "PLATFORM: " + (o.platform || ""),
    "AUTHOR: " + (o.author_name || "") + " " + (o.author_handle || ""),
    'POST: "' + (o.post_text || "") + '"',
    "",
    "STEP 1 — CLASSIFY the post (post_type): question / news / hot_take / personal_story / personal_win / joke_or_meme / technical_tip / launch_announcement / controversy / advice / generic / unclear.",
    "",
    "STEP 2 — DECIDE the best_action: rewrite_as_own_post / create_comment_reply / ask_question / answer_question / add_hot_take / add_builder_angle / create_linkedin_version / create_x_version / skip_post.",
    "",
    "DECISION RULES:",
    "- If the post asks a question, answer it directly first.",
    "- If the post is news, add Ahmad's angle: why it matters, who it affects, what changes next.",
    "- If the post is a hot take, agree or disagree with a clear reason.",
    "- If the post is a personal win, do NOT copy it as your own — make a supportive comment or a general lesson inspired by it.",
    "- If the post is someone's personal story, do NOT steal the story — make a respectful comment or extract a general lesson WITHOUT pretending it happened to Ahmad.",
    "- If the post is technical, create a practical builder angle.",
    "- If the post is generic, improve it with specificity or skip it.",
    "- If the post has no useful insight, set best_action = skip_post and should_repurpose = false.",
    "- Only ask a question when asking is the smartest action.",
    "- NEVER plagiarize, never copy the structure too closely, never pretend Ahmad experienced something he didn't, never invent facts, numbers, quotes, results, or personal stories.",
    "",
    window.HUMAN_VOICE,
    "",
    "X RULES: short, sharp, social-native; one strong hook; 2-5 short lines; a question if useful; usually no hashtags; max 1 emoji.",
    "LINKEDIN RULES: strong first 2 lines; clear insight; short paragraphs; professional but human; end with a thoughtful question; 2-4 hashtags max; no fake authority.",
    "COMMENT/REPLY RULES: question -> answer directly; hot take -> agree/challenge with a reason; win -> be supportive; technical -> add a useful practical angle; keep it natural and short.",
    "",
    "Produce all 6 outputs (x_post, linkedin_post, comment_reply, question_post, hot_take, builder_angle), then choose the single BEST one for THIS post.",
    "",
    "Return ONLY a JSON object, no text outside it, in EXACTLY this shape:",
    "{",
    '  "post_type": "question | news | hot_take | personal_story | personal_win | joke_or_meme | technical_tip | launch_announcement | controversy | advice | generic | unclear",',
    '  "best_action": "rewrite_as_own_post | create_comment_reply | ask_question | answer_question | add_hot_take | add_builder_angle | create_linkedin_version | create_x_version | skip_post",',
    '  "should_repurpose": true,',
    '  "analysis": "1-2 simple sentences: what this post is and what Ahmad should do with it",',
    '  "recommend_why": "one short reason why this action is best",',
    '  "best_output_type": "x_post | linkedin_post | comment_reply | question_post | hot_take | builder_angle | skip",',
    '  "best_output": "the strongest ready-to-use output (the matching output text, word-for-word)",',
    '  "outputs": [',
    '    {"type":"x_post","text":"...","score":8,"reason":"why this works on X"},',
    '    {"type":"linkedin_post","text":"...","score":8,"reason":"why this works on LinkedIn"},',
    '    {"type":"comment_reply","text":"...","score":8,"reason":"why this reply fits the source post"},',
    '    {"type":"question_post","text":"...","score":8,"reason":"why this question creates engagement"},',
    '    {"type":"hot_take","text":"...","score":8,"reason":"why this opinion starts discussion"},',
    '    {"type":"builder_angle","text":"...","score":8,"reason":"why this fits Ahmad\'s AI builder brand"}',
    "  ]",
    "}",
    "Score = 1-10. If best_action is skip_post, set should_repurpose=false, best_output_type=\"skip\", and keep outputs brief.",
  ].join("\n");
};

/* ---- Anthropic Write Engine: short text-only X posts that grow an AI account ---- */
/* [category, slug, display, short desc, prompt behavior, example] */
window.XMINI_PRESETS = [
  ["question", "ask-real-question", "❓ Ask a Real Question", "Get genuine replies", "Turn the idea into a simple question people actually want to answer. Avoid fake engagement bait. The question should reveal how people work, think, or choose tools.", "What AI tool do you actually use every day — not the one you hype?"],
  ["question", "vibe-coder-question", "👾 Vibe Coder Question", "Casual questions for builders", "Write casual, community-style questions for people who code/build. Feel like Ahmad talking to builders, not marketing.", "Vibe coders, what's one AI tool you paid for and instantly knew was worth it?"],
  ["community", "community-callout", "👋 Community Callout", "Invite people to say hi", "Write a warm, casual, easy-to-reply post inviting AI/startup/coding/design/automation people to introduce themselves.", "X gets 100x better when your timeline is full of people building cool things. Into AI, startups, coding, design or automation? Say hi 👋"],
  ["funny", "funny-ai-thought", "😅 Funny AI Thought", "Dry, relatable AI joke", "Write a dry, relatable AI joke. No forced punchlines, no meme-speak overload.", "AI agents are amazing until you realize you're basically managing a very confident intern 😅"],
  ["fact", "interesting-ai-fact", "📌 Interesting AI Fact", "A simple AI truth", "Write a short fact-style post. If the claim isn't verified, make it a general observation, not a hard fact.", "Most people still use AI like a search box. The real shift starts when they use it like a worker."],
  ["hot_take", "hot-take", "🔥 Hot Take", "Bold but defensible", "Write a bold but defensible take. Not toxic, not insulting. Should invite disagreement.", "Hot take: most people don't need more AI tools. They need one workflow they'll actually repeat."],
  ["builder", "builder-thought", "🛠 Builder Thought", "Practical builder note", "Write a practical builder observation. Focus on workflow, systems, loops, tools, shipping.", "The model isn't the product. The workflow around the model is where the real value starts."],
  ["relatable", "relatable-ai-pain", "🤝 Relatable AI Pain", "Everyday AI struggle", "Write something people instantly recognize from their own workflow.", "Opening 6 AI tools for one task is the new version of having 47 browser tabs open."],
  ["shower_thought", "ai-shower-thought", "🚿 AI Shower Thought", "Thoughtful simple post", "Write a short, slightly philosophical AI/work/future thought.", "The future of work might just be humans learning how to explain things better to machines."],
  ["comparison", "tool-comparison", "⚔️ Tool Comparison", "Compare by real use", "Compare tools by real use case, not generic ranking. Make people pick a side.", "ChatGPT feels like a generalist. Claude feels like a thinking partner. Cursor feels like a teammate inside the repo."],
  ["truth", "one-line-truth", "✨ One-Line Truth", "Punchy standalone line", "Write one strong sentence that feels obvious after reading.", "Good prompting is just clear thinking with less hiding."],
  ["debate", "debate-starter", "⚖️ Debate Starter", "Force a choice, get comments", "Ask a question with two or three sides. Force a real choice.", "For coding in 2026, what matters more: the smartest model or the best workflow?"],
  ["personal", "beginner-confession", "🌱 Beginner Confession", "Honest learning journey", "Write an honest post about learning AI/agents/coding/automation. Do NOT invent fake wins or numbers.", "I'm realizing agentic AI is less about fancy prompts and more about designing clean loops."],
  ["build_in_public", "build-in-public", "🚧 Build In Public Mini", "Short project update", "Write a short update about what Ahmad is building or learning. Ask for feedback only when natural.", "Today I added one small feature to Radar Studio: selected text → Anthropic → instant X post ideas. Tiny, but it saves a lot of thinking time."],
  ["skeptical", "anti-hype-check", "🧊 Anti-Hype Check", "Grounded, smart skepticism", "Challenge hype without being negative.", "Everyone's talking about AI agents replacing work. The real question: can they handle boring edge cases without babysitting?"]
];
/* style profiles: [name, description] */
window.XMINI_STYLES = [
  ["Ahmad Natural", "Simple, casual, curious, AI-builder energy"],
  ["Builder Twitter", "Direct, practical, workflow-focused"],
  ["Funny Dev", "Dry, witty, slightly chaotic, not cringe"],
  ["AI News Analyst", "Simple insight about what a news event means"],
  ["Indie Hacker", "Shipping, building, learning, small wins, real struggles"],
  ["Community Growth", "Warm, inviting, asks people to say hi or share"],
  ["Sharp Hot Take", "Opinionated but respectful"]
];
/* ---- "Me" posters: Ahmad personally presents a news announcement (anchor style) ---- */
/* ---- Optional adaptations of an APPROVED LinkedIn post. Neither of these is
   part of the default flow: LinkedIn is the product, these are opt-in extras you
   run on a post you already decided to publish. They adapt the same research -
   they never start a second one, and they never add a claim the post lacks. ---- */
window.buildAdaptPrompt = function (o) {
  o = o || {};
  var common = [
"THE APPROVED POST (this is the research; do not add anything it does not already say):",
(o.post || ""),
"",
(o.source ? "SOURCE FOR ATTRIBUTION: " + o.source : ""),
"",
"Keep every qualification the post makes. If a claim is attributed there, it stays attributed here.",
"Never invent a number, date, feature or firsthand experience to make it fit the format.",
  ];
  if (o.platform === "reddit") {
    return [
"You are checking whether an idea is worth contributing to a specific subreddit - not distributing a post.",
"",
"Reddit is a place to answer a real question, not a channel to cross-post to. Blanket promotion gets removed and earns a ban, and every community has its own rules.",
"",
    ].concat(common).concat([
"",
"SUBREDDIT AND ITS CURRENT RULES: " + (o.community || "(not supplied)"),
"",
"DECIDE, in this order:",
"1. If the subreddit or its current rules were not supplied, return status review_rules and say which rules you need to read first. Do not guess a community's norms.",
"2. If the content is off-topic there, or the rules prohibit this kind of post, return status skip with the reason.",
"3. If there is a genuine discussion or question this idea actually answers, write it as a contribution: a plain descriptive title and a comment that helps a reader, in your own words.",
"",
"HARD RULES: no promotional link, no 'check out my post', no upvote or engagement ask, no pretending to be a customer or a neutral bystander. Disclose any relevant affiliation plainly. Reddit punishes selling; it rewards being useful.",
"",
"OUTPUT EXACTLY:",
"[[STATUS]]",
"(draft, review_rules, or skip)",
"[[TITLE]]",
"(descriptive, specific, not clickbait - empty unless status is draft)",
"[[BODY]]",
"(the contribution itself - empty unless status is draft)",
"[[REVIEW]]",
"(private: which rule you checked it against, and anything the operator should confirm before posting)",
"[[END]]",
    ]).join("\n");
  }
  return [
"Adapt one approved LinkedIn post into ONE standalone X post. This is a deliberate extra, not an automatic cross-post.",
"",
  ].concat(common).concat([
"",
"X SPECIFICS:",
"- ONE post that stands on its own. No thread, no numbered parts, no 'a 🧵 below'.",
"- Shorter and more direct than LinkedIn, but the meaning must survive the cut. If the idea cannot fit truthfully - if fitting it means dropping a caveat that changes what it claims - return status skip instead.",
"- Plain language, no corporate register, no hype.",
"- No engagement bait: no 'follow me', no 'RT if you agree', no fake urgency, no manufactured controversy.",
"- Do not assume any rule about links being suppressed; put the source where it reads naturally, or leave it out and let the post stand alone.",
"",
"OUTPUT EXACTLY:",
"[[STATUS]]",
"(draft or skip)",
"[[POST]]",
"(the X post - empty if skip)",
"[[REVIEW]]",
"(private: what you compressed or dropped, and anything that needs the operator's approval)",
"[[END]]",
  ]).join("\n");
};

/* ---- Visual prompts for a finished post. These are OPTIONAL: a LinkedIn post
   stands on its own, and no image is ever required before you can publish. Run
   one only when a picture genuinely carries the idea better than the words.
      kind "infographic" -> one 4:5 graphic that holds the whole point
      kind "poster"      -> a news-style photo/headline card (13 formats, 20 designers)
   Both build from the APPROVED post text, so a visual can never claim more than
   the post itself already says. ---- */
window.INFOGRAPHIC_FORMATS = [
"STEP A — pick ONE format from this library, the one whose SHAPE fits the content best. HARD RULE: never the format you would pick by default, and never the same format twice in a row — rotate through the whole library over time so no two graphics look alike:",
"1. HUB & SPOKE — one central circle (topic icon) with arrows out to 4-6 bordered cards; each card = bold name + \"Purpose:\" one line + \"Key features:\" 2-3 ticked bullets + \"Top uses:\" 2-3 bullets + a bordered \"Pro Tip:\" strip at the card bottom with one quoted example. White background, thin black arrows, cards outlined in ONE accent color. Best for: tools/apps/modes overview.",
"2. JOURNEY MAP — a numbered winding dotted path (1 → N) of rounded step cards on cream paper, light hand-drawn doodle style with one small illustrated character walking the path; each card = STEP NAME in caps + a short \"DO THIS:\" paragraph + a tiny highlighted \"WHY IT WORKS:\" footnote. Best for: multi-step systems, habit guides, 8-14 tips.",
"3. COMPARISON TABLE — a real table: 3-4 columns with header cells (name + small colored icon, each column a different accent), left criteria column in caps (PURPOSE / STRENGTHS / HOW IT WORKS / BEST FOR / LIMITATIONS), alternating dark row shading, dark charcoal background. Best for: X vs Y vs Z verdicts.",
"4. VS ROWS — bold statement poster: huge condensed title at top with ONE word in accent color, then 4-6 stacked pill rows each \"[myth/bad thing] VS [truth/good thing]\" with small icons both sides, dark editorial background. Best for: myth-busting, mindset shifts, contrarian takes.",
"5. THEN → TODAY LADDER — two labeled columns (\"Yesterday\" / \"Today\" or \"Old way\" / \"New way\") with an arrow between each word pair, 8-10 rows, big playful title, one bold quote line at the bottom, paper-texture background. Best for: vocabulary shifts, behavior changes, evolution of a workflow.",
"6. NUMBERED TIP GRID — 2-3 column grid of clean numbered cards, each card = number badge + 5-8 word tip + one support line, small flat icon per card, white/cream background, 1 accent color. Best for: 6-10 independent tips.",
"7. MIND MAP — dark rounded title box on the left, colored branch lines to 4-6 topic boxes on the right, each branch box with 2-3 short example bullets, flat design. Best for: \"types of X\" and topic breakdowns.",
"8. PROMPT CARD — one huge quoted prompt block center-stage in a bordered card (typewriter-style font), numbered heading above it (\"1/ [what it does]\"), minimal cream background, a \"swipe →\" or \"save this ⤵\" hint in the footer corners. Best for: sharing 1-3 copyable prompts.",
"9. CHECKLIST SHEET — clipboard/checklist style: title band at top, 6-9 rows each with a big ✓ box + short item + one-line why, one row highlighted as \"most people skip this\", subtle grid paper background. Best for: steal-my-system checklists.",
"10. DECISION TREE — \"START HERE:\" question box at top, yes/no arrows branching down to 4-6 outcome boxes each naming the answer + one line of reason, clean flat flowchart, white background. Best for: \"which X should you pick\" content.",
"STEP B — vary the LOOK between posts: rotate background theme (white / cream paper / dark charcoal) and rotate the single accent color (electric blue / red / amber / green) to match the mood. Never reuse the previous post's theme+accent combo.",
"STEP C — write the final prompt in full detail: the chosen format and layout placement, every text element word for word (spell EXACTLY, the graphic dies if a word is misspelled), the [[GRAPHIC_TITLE]] as the heading, background theme, accent color, and typography (clean modern editorial, generous spacing, short legible text). Style guard: must look like a human designer made it in Canva/Figma — NO AI-gloss, NO sci-fi glow, NO glowing circuits, NO robots, NO logos/watermarks. Add ONE small, quiet handle mark in a bottom corner (\"@aixahmad\") — attribution, not a call to action. No follow/like/share line on the image."
].join("\n");

window.buildVisualPrompt = function (o) {
  o = o || {};
  if (o.kind === "poster") {
    return [
"Create ONE image for a LinkedIn post. Use ONLY what the post below actually says - never add a number, name, claim or detail that is not in it.",
"",
"THE POST:",
(o.post || ""),
"",
"HEADLINE TO RENDER ON THE IMAGE (word for word, spelled exactly): " + (o.title || ""),
"",
window.HUMAN_IMAGE
    ].join("\n");
  }
  return [
"Turn the LinkedIn post below into ONE infographic that carries its whole point in a single image.",
"Use ONLY what the post says. Never invent a step, number, feature, price or claim to fill a slot in the layout - if a section would need something the post does not support, pick a format that fits what you actually have.",
"",
"THE POST:",
(o.post || ""),
"",
"HEADING FOR THE GRAPHIC (max 10 words, benefit-first): " + (o.title || "write one from the post"),
"",
window.INFOGRAPHIC_FORMATS,
"",
"Output ONLY the finished image-generation prompt, ready to paste into an image AI. No preamble."
  ].join("\n");
};

window.buildMePosterPrompt = function (o) {
  o = o || {};
  return [
window.designStudio(),
"",
"Create ONE vertical 4:5 news-announcement poster where AHMAD (creator of @aixahmad) personally PRESENTS this news — like the face of a top Instagram news page. Design it through your assigned designer's eyes.",
"",
"USE THE ATTACHED PHOTO OF AHMAD. Keep his face EXACTLY as provided — never regenerate or alter it. You may adapt only his pose, expression angle, outfit and the scene around him.",
"",
"THE NEWS: " + (o.story || o.headline || ""),
'HEADLINE TO RENDER on the poster, word for word: "' + (o.headline || "") + '"',
"",
"PICK AHMAD'S REACTION POSE to match the story's mood (vary it between posters — never the same pose twice in a row):",
"- shocked, hands to head (drama / leak / unbelievable update)",
"- excited, pointing at the headline (launch / new model / big update)",
"- confident, arms crossed (analysis / my-take)",
"- thumbs up, smiling (free stuff / good news / opportunity)",
"- hand on chin, thinking (question / debate)",
"- mind-blown gesture (crazy stats / records)",
"",
"LAYOUT: Ahmad cut out chest-up on one side (~35% of the width) with a clean cutout edge, over a dark, softly blurred scene relevant to the story; 1-2 CIRCLE inset images of the subject (the product / company / person in the news) on the other side; big ALL-CAPS condensed headline across the lower half — white with the 2-3 key words in ONE accent color (red = drama, yellow = money/free, blue = tech, green = growth); a small name tag 'AHMAD · @aixahmad' near him; small footer line 'Follow @aixahmad for more'.",
"",
"STYLE: like a real designer composed it in Photoshop — realistic photography, natural light, crisp modern editorial typography, generous contrast, phone-legible. NO sci-fi glow, NO logos, NO watermarks, NO extra text. Spell every word EXACTLY.",
  ].join("\n");
};

/* ---- Inspire tab: proven, USEFUL content-idea bank. [category, title, why it works, ready seed] ---- */
window.INSPIRE_IDEAS = [
  ["interactive", "Write the prompt for this pic", "People love guessing — huge comment driver", "Post a striking AI image and ask: 'Write the prompt you think made this. Closest one wins a follow.' Then reveal the real prompt in comments."],
  ["interactive", "AI or real photo?", "Everyone wants to test themselves", "Post 2 images side by side: 'One is AI, one is real. Which is which?' Reveal the answer after 24h in comments."],
  ["interactive", "Guess the tool", "Curiosity + tool discovery in one", "Show a result (image/video/site) and ask 'Which AI tool made this in under 2 minutes?' Reveal + mini how-to in comments."],
  ["interactive", "What should I automate next?", "Gets ideas AND engagement", "Tell people one thing you automated with AI this week (real), then ask: 'What's one boring task in your day I should try to automate next?'"],
  ["list", "20 things you didn't know AI can do", "Save-magnet carousel — shock + usefulness", "Carousel: 20 surprising, REAL things AI can do today (translate a call live, restore old photos, read handwriting, plan meals from a fridge photo...). One per slide, no hype, each must be actually doable."],
  ["list", "5 free AI tools that replace paid ones", "Money saved = instant share", "List 5 genuinely free AI tools that do what people pay for (writing, design, transcription, coding, research). One line each: tool + what it replaces."],
  ["list", "AI tool tier list", "Rankings force disagreement = comments", "S/A/B/C tier list of the AI tools everyone uses (Claude, ChatGPT, Gemini, Cursor, Midjourney...). Your honest ranking + one-line reasons. Ask 'what did I get wrong?'"],
  ["list", "Learn AI in this order", "Beginners are the biggest audience", "'If you only have 10 minutes a day, learn AI in this order:' 5-step path from zero (use a chatbot daily -> prompts -> one image tool -> one automation -> build something tiny)."],
  ["update", "Unbelievable AI update of the week", "Shock value with receipts", "Pick THE most jaw-dropping real AI development this week. One post: what it is, proof it's real, and the one-line 'this means...' takeaway. No exaggeration — the real thing is wild enough."],
  ["update", "New model dropped — what you can DO with it", "Everyone posts the news; nobody posts the uses", "When a model launches: skip the specs. '5 things you can actually do with <model> today' — each a real, tryable use case with the simplest instructions."],
  ["update", "This week in AI in 60 seconds", "Busy people share summaries", "5 bullets max: the only AI news that actually matters this week, each with a 'why you care' half-line. Same day/time every week so people expect it."],
  ["update", "AI news explained for your parents", "Simplicity is a superpower", "Take today's biggest AI story and explain it so a 60-year-old gets it in 3 sentences. No jargon at all. End: 'Did I explain it simply enough?'"],
  ["prompts", "Prompt of the day", "Copy-paste value, daily habit", "One killer prompt people can copy today, with a before/after showing the difference it makes. Keep the prompt short enough to retype."],
  ["prompts", "3 prompts that make ChatGPT/Claude 10x better", "Directly actionable, huge saves", "3 short prompts (or prompt patterns) with what each fixes: better answers, honest criticism, step-by-step teaching. Show one example output."],
  ["prompts", "The prompt behind this image", "Transparency builds followers", "Post your best AI-generated poster/image and share the EXACT prompt that made it. Creators save these instantly."],
  ["tools", "I tested it so you don't have to", "Honest reviews beat hype", "Pick one hyped AI tool. Use it for a real task for 30 minutes. One-line verdict + who should actually use it + who shouldn't. Honesty is the hook."],
  ["tools", "Underrated feature nobody uses", "Insider knowledge feel", "One feature inside a popular AI tool that most users never touch (projects, memory, custom instructions, voice...). Show a real use in 3 steps."],
  ["tools", "My AI stack in one screenshot", "Stack posts always travel", "Share the 4-6 AI tools you ACTUALLY use daily and the one job each does. Ask people to share theirs. (Works as a clean infographic.)"],
  ["money", "AI side-hustle of the week", "Money angle = widest audience", "One realistic way people are earning with AI right now (no get-rich hype): what it is, what you need, honest earnings range, first step today."],
  ["money", "Free this week — grab it before it's gone", "Deadlines drive action", "Round up genuinely free AI offers right now (student offers, credits, trials). Who qualifies + how to claim in 2 steps + the deadline."],
  ["education", "One-minute explainer with an analogy", "Confusion is your content goldmine", "Pick one confusing AI term (RAG, agent, MCP, tokens) and explain it with a household analogy: 'LLM = brain. RAG = brain + books. Agent = brain + hands.'"],
  ["education", "Myth vs fact", "Correcting wrong beliefs earns trust", "One common AI belief that's wrong ('AI will take all jobs', 'AI can't be creative') vs what's actually true, in plain words with one concrete example."],
  ["education", "Before/after: with AI vs without", "Time saved is the universal hook", "Show one real task done the old way vs with AI: time taken, steps, result. Real numbers from your own attempt only."],
  ["education", "Beginner mistakes (I made all of them)", "Vulnerability + usefulness", "5 mistakes beginners make with AI (vague prompts, trusting outputs blindly, tool-hopping...) — admit which ones you made, and the fix for each."],
  ["personal", "Build in public: what I shipped this week", "Journey content compounds", "Share one small real thing you built/learned/automated this week with AI — with a screenshot. End with what you're trying next."],
  ["personal", "What I'd learn first if starting today", "Beginner magnet from experience", "'If I was starting with AI from zero in 2026, here's exactly what I'd do in week 1' — 4-5 concrete steps, no fluff, from your real path."]
];

/* starter ideas you can tap to seed a post (paraphrased X-native patterns) */
window.XMINI_IDEAS = {
  question: ["What AI tool do you actually use every day — not the one you talk about most?", "If you could keep only one AI product for work, which survives?", "For coding right now: Claude, ChatGPT, or Cursor?", "Are you using AI more like Google or more like an employee?", "What AI workflow saved you the most time this week?", "What's one thing AI still does annoyingly badly in your workflow?"],
  funny: ["AI agents are amazing until the job becomes managing them like very confident interns.", "Opening six AI tools for one task is the new version of 47 browser tabs.", "A lot of 'AI automation' is just manual work with better branding.", "The AI demo was magic. The actual workflow needed adult supervision.", "AI is making us all more productive and somehow worse at naming files."],
  fact: ["Most people still use AI like a smarter search box. The jump starts when it becomes part of a workflow.", "The model by itself usually isn't the product. The usable system around it is.", "Better prompts matter, but better routines matter more for most people.", "A workflow that saves 30 seconds every day beats one that saves 10 minutes once."],
  hot_take: ["Most people don't need more AI tools. They need one workflow they'll actually repeat.", "The workflow layer is becoming more important than the chat layer.", "'Agent' is doing a lot of PR work for products that still need babysitting.", "The most useful AI software will feel boring before it feels revolutionary."],
  builder: ["The model isn't the moat. The workflow around it is where the product starts.", "The difference between demo AI and product AI is state, guardrails, and retries.", "Good AI features disappear into the task instead of demanding a new habit.", "The better question for builders is 'what happens after the answer?'"],
  relatable: ["Nobody wants 10 AI tabs open just to finish one thing.", "The worst part of AI workflows is forgetting which prompt actually worked.", "The real flex is one AI workflow that still works when you're tired.", "The hard part isn't generating outputs anymore. It's deciding which one is worth using."],
  shower_thought: ["Work might slowly become the skill of explaining things clearly to machines.", "Good prompting is often just structured thinking with less hiding.", "AI is turning clarity into a real economic advantage.", "AI might not replace thinking. It might punish lazy thinking faster."],
  comparison: ["ChatGPT feels like a generalist. Claude feels like a thinking partner.", "Some AI tools are better at retrieval. Others are better at judgment. People mix those up.", "The better comparison isn't model vs model. It's workflow vs workflow.", "The best AI tool is usually the one that asks the least from your memory."]
};
window.buildXMiniPrompt = function (o) {
  o = o || {};
  var preset = o.preset || null;            // [cat, slug, name, desc, pattern]
  var seed = (o.seed || "").trim();
  var head = [
    "You are a sharp, X-native writer for Ahmad / @aixahmad (an AI builder + AI-news brand). You write SHORT, original, text-only X posts that grow an AI account — the kind people actually repost: a real question, a dry funny truth, a surprising fact, a sharp hot take, a builder note, a relatable line, a clean shower thought, or a tool comparison.",
    "",
    "THINK FIRST, THEN WRITE. Decide which ONE format best fits this idea, then write the strongest version.",
    "",
    seed ? ('IDEA / TEXT TO WORK FROM:\n"' + seed + '"') : "No seed given — invent ONE fresh, specific, non-obvious AI observation worth posting.",
    preset ? ("REQUESTED STYLE: " + preset[2] + " — " + preset[3] + ' (e.g. "' + preset[4] + '")') : "STYLE: choose whichever of the 8 categories fits best.",
    "",
    "STYLE RULES (X-native):",
    "- Casual, sharp, simple, human. ONE strong idea only.",
    "- No corporate buzzwords, no LinkedIn tone, no hashtag stuffing, no links.",
    "- Use emojis where they fit and add energy, emotion, or clarity (often 1-3) — natural and tasteful, never forced or spammy.",
    "- Under 280 characters. Prefer 1-3 short lines.",
    "- A question must be a REAL question about how people actually work — not engagement bait.",
    "- Funny = dry/observational, never forced.",
    "- If a fact is uncertain, generalize it or frame it as opinion. NEVER invent numbers, names, quotes, or results.",
    "- Never copy the source wording — make it Ahmad's own.",
    ""
  ];
  if (o.brief) {
    return head.concat([
      "Write only the single BEST post and ONE backup (a meaningfully different angle). Make both excellent.",
      "",
      "Return ONLY this JSON, nothing else:",
      "{",
      '  "analysis": "one sentence: what this idea is and the smartest format",',
      '  "best_category": "question | funny | fact | hot_take | builder | relatable | shower_thought | comparison",',
      '  "best_post": "the single strongest post, ready to paste",',
      '  "backup_posts": ["one backup, a different angle"]',
      "}",
      "Both texts MUST be under 280 characters."
    ]).join("\n");
  }
  return head.concat([
    "Write the single best post, 2 backups (meaningfully different), and one option for EACH of the 8 categories.",
    "",
    "Return ONLY this JSON, nothing else:",
    "{",
    '  "analysis": "one sentence: what this idea is and the smartest format",',
    '  "best_category": "question | funny | fact | hot_take | builder | relatable | shower_thought | comparison",',
    '  "best_post": "the single strongest post, ready to paste",',
    '  "backup_posts": ["second option", "third option"],',
    '  "all_options": [',
    '    {"category":"question","text":"...","score":8,"why":"..."},',
    '    {"category":"funny","text":"...","score":8,"why":"..."},',
    '    {"category":"fact","text":"...","score":8,"why":"..."},',
    '    {"category":"hot_take","text":"...","score":8,"why":"..."},',
    '    {"category":"builder","text":"...","score":8,"why":"..."},',
    '    {"category":"relatable","text":"...","score":8,"why":"..."},',
    '    {"category":"shower_thought","text":"...","score":8,"why":"..."},',
    '    {"category":"comparison","text":"...","score":8,"why":"..."}',
    "  ]",
    "}",
    "Every text MUST be under 280 characters. score 1-10 = how likely it is to earn replies/reposts.",
  ]).join("\n");
};

/* ---- Anthropic Write Engine: the intelligent creator brain ---- */
window.buildAnthropicWritePrompt = function (o) {
  o = o || {};
  var preset = o.preset || null;   // [cat, slug, name, desc, behavior, example]
  var style = o.style || null;     // [name, desc]
  var seed = (o.seed || "").trim();
  var refine = (o.refine || "").trim();
  var head = [
    "You are an intelligent CREATOR BRAIN for Ahmad / @aixahmad — an AI / startup / builder voice on X. You write SHORT, original, text-only posts that grow the account. You are NOT a plain rewriter: think first, understand the input, decide the smartest content move, then write.",
    ""
  ];
  if (refine) {
    head.push('REFINE MODE — take the post below and: ' + refine + '. Keep it original, true, and X-native. Do not invent facts.');
    head.push('POST TO REFINE:\n"' + seed + '"');
  } else {
    head.push(seed ? ('INPUT (selected text or idea to work from):\n"' + seed + '"') : "No input given — invent ONE fresh, specific, non-obvious AI/startup/builder observation worth posting.");
  }
  if (preset) head.push("PRESET: " + preset[2] + " — " + preset[4] + ' (example feel: "' + preset[5] + '")');
  if (style) head.push("STYLE PROFILE: " + style[0] + " — " + style[1] + ". Write in this voice.");
  head.push("");
  head.push("DECIDE THE BEST MOVE: is this best as a question, funny line, fact, hot take, builder thought, community callout, comparison, relatable line, shower thought, debate, personal note, or skeptical check? Is it too weak (improve it)? Does it risk copying someone too closely (rewrite the idea, not the wording)? Is it someone else's personal story (do NOT retell it as Ahmad's experience — generalize the lesson)?");
  head.push("");
  head.push(window.HUMAN_VOICE);
  head.push("");
  head.push("OUTPUT RULES:");
  head.push("- Text only. Under 280 characters. 1-3 short lines preferred.");
  head.push("- No copied phrasing or structure from another creator. Never invent facts, numbers, quotes, or personal experience.");
  head.push("- If a factual claim is uncertain, rewrite it as opinion or a general observation.");
  head.push("- If the input is weak, IMPROVE the idea instead of copying it.");
  head.push('- When it fits within the 280 limit, end with a short follow CTA ("follow @aixahmad for more"); drop it only if it would push the post over the limit or kill a one-liner\'s punch.');
  head.push("- copy_risk = how close it is to copying a source; factuality_risk = how likely it states an unverified claim as fact. Keep both low.");
  head.push("");
  head.push("Produce the single BEST post, 2 backups (meaningfully different), and up to 5 all_options across different categories.");
  head.push("");
  head.push("Return ONLY valid JSON, nothing outside it:");
  return head.concat([
    "{",
    '  "analysis": "1-2 short sentences explaining the content move",',
    '  "input_type": "question | fact | opinion | joke | personal | news | generic | unclear",',
    '  "best_category": "question | funny | fact | hot_take | builder | relatable | shower_thought | comparison | community | personal | debate | skeptical | truth | build_in_public",',
    '  "style_profile": "Ahmad Natural | Builder Twitter | Funny Dev | AI News Analyst | Indie Hacker | Community Growth | Sharp Hot Take",',
    '  "copy_risk": "low | medium | high",',
    '  "factuality_risk": "low | medium | high",',
    '  "best_output": "single best ready-to-post text",',
    '  "backup_outputs": ["backup option 1", "backup option 2"],',
    '  "all_options": [',
    '    {"category":"question","text":"...","score":8,"why":"..."},',
    '    {"category":"funny","text":"...","score":8,"why":"..."},',
    '    {"category":"hot_take","text":"...","score":8,"why":"..."},',
    '    {"category":"builder","text":"...","score":8,"why":"..."},',
    '    {"category":"community","text":"...","score":8,"why":"..."}',
    "  ],",
    '  "post_quality_score": 8,',
    '  "improvement_tip": "one short suggestion"',
    "}",
    "Every text MUST be under 280 characters. score / post_quality_score = 1-10.",
  ]).join("\n");
};
