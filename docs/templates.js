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

/* ===== Shared REALISTIC IMAGE rules — designer-made editorial graphic, not an AI poster. ===== */
window.HUMAN_IMAGE = "Make it look like a real designer edited it in Photoshop/Figma — a premium social-news graphic, NOT an AI poster. Use a realistic PHOTO-BASED scene relevant to the story (founder working late, AI lab, startup office, laptop showing a dashboard, newsroom desk, data centre, investor meeting, developer workspace). Natural lighting, realistic shadows, real textures, believable human detail. NO glossy sci-fi look, NO random glowing symbols, NO fake-futuristic nonsense, NO logos, NO watermark, NO random text. Vertical 4:5. Top ~70% is the photo; bottom ~30% is a clean darker band for the headline. Clean editorial typography — large, readable, modern, well-spaced. Render ONLY the exact headline provided, word for word; highlight ONE key word or phrase with a subtle blue or white contrast.";

/* WIZ = the Create wizard library. Each template:
     type:  "short" | "long" | "post"
     plats: ["*"] = fits all platforms, or specific keys
            (post: x, ig, fb, li, wa | short: yt, tiktok, ig, fb | long: yt, fb)
     body:  instructions sent to Claude (the tool adds topic, language,
            platform format rules and duration around it). */

window.WIZ = [

/* ---------- SHORT VIDEO templates ---------- */
{ type:"short", plats:["*"], emoji:"⚡", name:"Hook → 3 facts → CTA",
  desc:"The classic. Scroll-stopping hook, three punchy facts, strong close.",
  body:"Structure the script as: one scroll-stopping HOOK line, then exactly 3 short punchy facts/points about the topic (one line each), then a strong closing line + CTA." },
{ type:"short", plats:["*"], emoji:"🛠", name:"Mini tutorial",
  desc:"Teach one thing in under a minute. Tutorials build trust.",
  body:"Make it a mini step-by-step tutorial: hook = the result the viewer will get, then 3-4 numbered steps (simple words), one mistake to avoid, CTA." },
{ type:"short", plats:["*"], emoji:"🚫", name:"Myth bust",
  desc:"'People think X… reality is Y.' High retention format.",
  body:"Format: state the popular myth about the topic dramatically, then bust it with the reality + one simple proof or example, end with the correct takeaway." },
{ type:"short", plats:["*"], emoji:"🗞", name:"News reaction",
  desc:"'Did you hear what just happened?' — urgency + explanation.",
  body:"Format as breaking-news reaction: urgent hook (what just happened), explain it simply in 3-4 lines, why it matters for normal people in Pakistan/India, CTA." },
{ type:"short", plats:["*"], emoji:"📊", name:"Before / After demo",
  desc:"Show the transformation. Demos beat descriptions.",
  body:"Format: show the BEFORE state (the old/slow/manual way), then the AFTER with the topic (fast/easy), include a concrete demo idea I can film on screen, end with how viewers can try it today." },
{ type:"short", plats:["*"], emoji:"🎙", name:"Storyteller (any real story)",
  desc:"Mini documentary of any true story — success, lawsuit, shocking. Tone adapts.",
  body:"Narrate the REAL story behind the topic like a mini documentary. FIRST detect the story type and match the tone: success/inspiring -> energetic; tragedy/lawsuit -> respectful and serious, no graphic details; shocking/funny -> playful but never mocking real pain. Skeleton: HOOK = most dramatic true moment, who the person is, the journey in short tension-building lines, the turning point, where it stands today, one closing takeaway for the viewer ('aap ke liye sabaq'). STRICT: only facts from the source — never invent details, numbers, or quotes." },
{ type:"short", plats:["tiktok","ig"], emoji:"🎭", name:"POV / Storytime",
  desc:"TikTok-native storytelling. Personal, casual, relatable.",
  body:"Format as POV/storytime: first-person casual story related to the topic ('POV: you...' or 'ek din maine...'), with a turn and a payoff lesson at the end. Native, unpolished tone." },
{ type:"short", plats:["yt"], emoji:"🔁", name:"Loop hook (Shorts)",
  desc:"Last line connects to the first — YouTube Shorts loop trick.",
  body:"Write so the LAST line connects naturally back to the FIRST line (loop effect for replays on YouTube Shorts). Keep the hook a question that the loop re-triggers." },

/* ---------- LONG VIDEO templates ---------- */
{ type:"long", plats:["*"], emoji:"🗞", name:"News explainer",
  desc:"What happened, why it matters, what it means for the viewer.",
  body:"Structure: hook (the news in one dramatic line), what exactly happened, background in simple words, why it matters for everyday people in Pakistan/India, what happens next, my opinion section (placeholder), recap." },
{ type:"long", plats:["*"], emoji:"🛠", name:"Step-by-step tutorial",
  desc:"Full how-to with steps on screen. The subscriber machine.",
  body:"Structure: hook = the final result, what you need, numbered steps with [SCREEN: what to show] notes, common mistakes section, pro tip, recap of steps." },
{ type:"long", plats:["*"], emoji:"⚔️", name:"VS comparison",
  desc:"Tool A vs Tool B — people love a verdict.",
  body:"Structure: hook (the battle), quick intro of both sides, compare on 4-5 criteria that matter to normal users (price, ease, Urdu support, speed, results) with a winner per criterion, final verdict + who should pick which." },
{ type:"long", plats:["*"], emoji:"🔥", name:"Opinion / analysis",
  desc:"Your stance on a hot topic. Authority builder.",
  body:"Structure: hook = my hot take in one line, the common view, why I see it differently (3 arguments with examples), the strongest counter-argument handled honestly, what I'd advise viewers to do." },
{ type:"long", plats:["*"], emoji:"🧪", name:"I tried it for 7 days",
  desc:"Experiment format — story + proof + verdict.",
  body:"Structure: hook = the experiment promise, day-by-day highlights (3-4 key moments, wins and fails), the numbers/results, honest verdict, who should and should not try it." },
{ type:"long", plats:["*"], emoji:"📋", name:"Top 5 countdown",
  desc:"Countdown keeps people watching till #1.",
  body:"Structure: hook teasing #1 without revealing, countdown 5→1 with one concrete use/benefit each, save the best for last, recap list at the end." },

/* ---------- POST templates: general (work everywhere) ---------- */
{ type:"post", plats:["*"], emoji:"🎙", name:"Storyteller (any real story)",
  desc:"Narrate any TRUE story — success, lawsuit, shocking, funny. Tone adapts.",
  body:"Tell the REAL story behind the topic as a gripping third-person narration. FIRST detect the story type and match the tone: success/inspiring -> energetic and motivating; tragedy/lawsuit -> respectful and serious, no graphic details; shocking/funny -> playful but never mocking real pain. SAME skeleton always: (1) HOOK = the single most dramatic or surprising true moment, (2) who this person is in one line, (3) the journey step by step in short tension-building lines, (4) the turning point, (5) where it stands today (money figure / case status / result), (6) ONE closing takeaway: 'aap ke liye sabaq' — what an ordinary person in Pakistan/India should learn or be careful about. STRICT: only facts from the source — never invent details, numbers, or quotes." },
{ type:"post", plats:["*"], emoji:"❓", name:"Strategic question",
  desc:"Real questions invite real conversation.",
  body:"Write a post asking ONE strategic question about the topic. Include my own one-line answer/stance FIRST, then invite theirs. No empty engagement bait." },
{ type:"post", plats:["*"], emoji:"🚨", name:"Announcement",
  desc:"New video / news drop with curiosity gap.",
  body:"Write an announcement post about the topic: curiosity-driven opening line, 2-3 lines of what it is and why it matters, link placeholder, CTA." },
{ type:"post", plats:["*"], emoji:"🔥", name:"Hot take",
  desc:"The opinions you're nervous to post build authority.",
  body:"Write a confident hot-take post: my contrarian-but-defensible stance on the topic, 2 short reasons, invite disagreement respectfully." },
{ type:"post", plats:["*"], emoji:"📖", name:"Mini story",
  desc:"Struggle → turn → lesson. Most human format.",
  body:"Write a first-person mini story about the topic: the moment it clicked, what went wrong first, the lesson, how the reader can skip my mistake." },
{ type:"post", plats:["*"], emoji:"📋", name:"Listicle",
  desc:"'5 things…' — easy to read, easy to save.",
  body:"Write a listicle post: hook line, then 5 short numbered points about the topic (each with a concrete benefit), end with 'save this'." },
{ type:"post", plats:["*"], emoji:"⚡", name:"Myth vs Reality",
  desc:"Bust one myth. High share rate.",
  body:"Write a post busting ONE common myth about the topic: the myth -> the reality with simple proof -> what to do instead." },
{ type:"post", plats:["*"], emoji:"🚫", name:"Mistake Warning",
  desc:"'Stop doing X' / 'mistakes killing your Y.' Loss aversion — the strongest scroll-stopper in 2026 data.",
  body:"Write a \"mistake warning\" post about: {topic} (the common mistake people make and what to do instead — ask me if unclear).\nStructure:\n1. HOOK (line 1): \"Stop [common behavior].\" OR \"[X] mistakes that are killing your [result].\" Must trigger loss aversion — the reader should feel they might be losing something RIGHT NOW.\n2. Briefly validate why everyone does it (so the reader doesn't feel stupid).\n3. Reveal the real cost of the mistake with one concrete example or number.\n4. Give the correct approach in 2-4 short, actionable lines.\n5. End with: \"Which of these are you doing?\" or similar self-audit question.\nRules: short lines, white space between thoughts, no lecture tone — write like a friend pulling someone aside. The advice MUST genuinely deliver; never clickbait without payoff." },
{ type:"post", plats:["*"], emoji:"📊", name:"Before → After",
  desc:"Quantified transformation. The gap between two numbers forces the click.",
  body:"Write a before/after transformation post about: {topic} (what changed, the starting number, the ending number, and what made the difference — ask me if numbers are missing).\nStructure:\n1. HOOK: state BEFORE number and AFTER number in the first 1-2 lines with the timeframe. Example shape: \"[Bad number] in [month]. [Good number] today. Here's the ONE thing that changed.\"\n2. Briefly paint the 'before' pain (2-3 lines, specific and honest).\n3. The turning point — what was actually changed. Be concrete, not vague (\"I changed my hook structure\", not \"I worked harder\").\n4. The after state + one lesson the reader can apply today.\n5. Optional soft CTA: \"Save this if you're still in the 'before' stage.\"\nRules: the numbers must be real (ask me if I haven't provided them — never invent metrics). Short paragraphs. No humble-bragging tone — frame it as a repeatable lesson, not a flex." },
{ type:"post", plats:["*"], emoji:"🎯", name:"Identity Call-out",
  desc:"'If you're a [freelancer / parent / dev]...' — names the reader, filters the feed.",
  body:"Write an identity call-out post about: {topic} (who exactly this is for, and the specific insight/advice for them).\nStructure:\n1. HOOK (line 1): \"If you're a [specific identity], [stop scrolling / this is for you / read this twice].\" The identity must be SPECIFIC (\"freelance devs sending 20 proposals a week\", not just \"freelancers\").\n2. Prove you understand their exact situation in 2-3 lines — describe a detail only an insider would know. This builds instant trust.\n3. Deliver the insight/advice: 3-5 tight lines.\n4. Close with belonging: \"If this is you, you're not behind — you're early.\" or a question to the named group.\nRules: never water down the identity to widen the audience — specificity IS the mechanism. Warm, direct, peer-to-peer tone." },
{ type:"post", plats:["*"], emoji:"🧪", name:"I Tested It",
  desc:"Did the work so they don't have to. Save-magnet + instant credibility.",
  body:"Write an \"I tested it so you don't have to\" post about: {topic} (what was tested, how long / how many, and the verdict — ask me if missing).\nStructure:\n1. HOOK: \"[I tested N things / I did X for N days] so you don't have to. [Teaser of surprising verdict].\" Numbers in the first line are mandatory.\n2. One line on the method (enough to be credible, not boring): what exactly was done.\n3. The results — ranked or grouped: winners, losers, surprise finding. Each gets ONE specific reason, not generic praise.\n4. The single biggest takeaway in one bold line.\n5. CTA: \"Save this — you'll need it when [trigger moment].\"\nRules: verdicts must be opinionated (a clear winner and a clear loser). The \"surprise finding\" is what makes it shareable — always include one counterintuitive result. Honest > promotional." },
{ type:"post", plats:["*"], emoji:"📋", name:"Steal My System",
  desc:"Exact checklist / stack / workflow — built for saves & shares, the rising metrics.",
  body:"Write a \"steal my system\" post about: {topic} (the system/checklist/stack/workflow being shared and what result it produces).\nStructure:\n1. HOOK: \"My exact [system] that [specific result]. Steal it.\" — the word \"exact\" and a real result are mandatory.\n2. The system itself: numbered steps or a labeled stack. Every item = WHAT + one line of WHY/HOW. No vague items like \"be consistent.\"\n3. One pro-tip or common failure point (\"Most people skip step 3 — that's why it doesn't work for them\").\n4. CTA: \"Save this. Future you will thank you.\" or \"Send this to someone who needs it.\"\nRules: the system must be COMPLETE — the reader should be able to execute it without anything else. 5-9 items max. Formatting must be scannable (numbers/short lines)." },
{ type:"post", plats:["*"], emoji:"🔄", name:"Open Loop (Part 1/2)",
  desc:"Cliffhanger format. Trains followers to come back.",
  body:"Write PART 1 of a two-part open-loop story about: {topic} (the full story including the ending, so Part 1 can be cut at the right moment).\nStructure for Part 1:\n1. HOOK: start in the middle of the action or at the moment of highest tension — never at the chronological beginning.\n2. Build the story with concrete details (names changed, real stakes, real numbers).\n3. Escalate to the decisive moment... then CUT exactly before the resolution.\n4. Final line: \"Part 2 tomorrow.\" + one teaser line about what the resolution involves (\"What happened next cost me $400 — and taught me more than any course.\").\nThen also write PART 2:\n1. One-line recap hook for new readers.\n2. The resolution + the unexpected twist.\n3. The lesson, stated plainly.\n4. CTA: \"Follow so you don't miss the next story.\"\nRules: the cut point of Part 1 must land mid-tension. Part 2 must fully deliver — an open loop that under-delivers burns trust permanently." },

/* ---------- POST templates: X specific ---------- */
{ type:"post", plats:["x"], emoji:"🧵", name:"X thread (5-7 posts)",
  desc:"The authority format on X. Hook tweet + value chain.",
  body:"Write an X THREAD of 5-7 posts: post 1 = strong hook with the promise, posts 2-6 = one idea each (short lines, no fluff), last post = recap + follow CTA @aixahmad. Number them." },
{ type:"post", plats:["x"], emoji:"🎁", name:"Prompt share",
  desc:"Useful prompt + 'show your result' — bookmarks + replies.",
  body:"ONE X post under 280 chars sharing a genuinely useful AI prompt about the topic, exact prompt in quotes, end: 'apna result comment mein dikhao'." },
{ type:"post", plats:["x"], emoji:"✏️", name:"Fill the blank",
  desc:"One-tap replies — the lowest-friction engagement format on X. Feeds the algorithm.",
  body:"ONE X post under 280 chars: fill-in-the-blank about the topic, end with an invitation to drop their answer in the replies." },
{ type:"post", plats:["x"], emoji:"⚔️", name:"VS Battle",
  desc:"Pit two tools, methods, or approaches against each other — comparison bait that fills the replies.",
  body:"Write an X post that pits two things against each other for: {topic} (the two things being compared and for what use case — ask me if unclear).\nStructure:\n1. Line 1: name the battle directly — \"X vs Y for [use case]. I tested both.\"\n2. Give a 2-3 line verdict with ONE specific, surprising detail from real use.\n3. Declare a winner BUT concede one thing the loser does better (this fuels disagreement in replies).\n4. End with a question that forces readers to pick a side.\nRules: under 280 characters if possible, no hashtags, no emojis unless one fits naturally, conversational tone, sound like a real person who actually used both — not a review site." },
{ type:"post", plats:["x"], emoji:"🔧", name:"Build in Public",
  desc:"Real numbers + what you learned. X's native trust format — never goes out of style.",
  body:"Write a build-in-public X post about: {topic} (the project, the real numbers/progress this period, and one lesson or struggle).\nStructure:\n1. HOOK: the headline number or milestone, raw and unpolished. \"Month 2 of freelancing: $0 → $340.\"\n2. 2-4 short lines: what was tried, what worked, what flopped. At least ONE honest failure — that's what makes it credible.\n3. The lesson in one line.\n4. What's next (one line) — this creates a follow-the-journey loop.\nRules: real numbers only (ask me if missing — never invent). No motivational fluff. Vulnerability + specificity = the whole format." },

/* ---------- POST templates: Instagram specific ---------- */
{ type:"post", plats:["ig"], emoji:"🎠", name:"Carousel (8 slides)",
  desc:"IG's best save-format. Slide-by-slide text.",
  body:"Write an Instagram CAROUSEL: slide 1 = bold hook title, slides 2-7 = one idea per slide (max 20 words each), slide 8 = recap + follow CTA. Then the caption + max 5 hashtags (Instagram 2026 limit)." },
{ type:"post", plats:["ig"], emoji:"📱", name:"Story Q&A set",
  desc:"3-4 story frames: poll, quiz, question sticker.",
  body:"Write an Instagram STORY SET about the topic: frame 1 = poll question (2 options), frame 2 = quiz with 3 choices (mark correct), frame 3 = open question sticker prompt, frame 4 = result/answer + CTA. Short text per frame." },
{ type:"post", plats:["ig"], emoji:"💬", name:"Quote card caption",
  desc:"One strong quote image + caption that adds context.",
  body:"Give ONE strong quotable line about the topic (for the image card, max 12 words), then a caption that adds the context/story behind it + 3-5 hashtags (IG max is 5)." },
{ type:"post", plats:["ig"], emoji:"🎬", name:"Reel Script",
  desc:"3-second hook + shot beats + caption. Reels drive ~2x the reach of static posts.",
  body:"Write a complete Instagram Reel script about: {topic}.\nOutput 3 parts:\nPART A — SPOKEN SCRIPT (30-45 seconds when read aloud):\n1. HOOK (first 3 seconds / max 12 words): pattern interrupt — bold claim, contrarian line, or curiosity gap. Write 3 hook options, mark the strongest.\n2. BODY: 3-4 beats, each one idea, each a short punchy sentence. No filler words.\n3. PAYOFF: the promised value, delivered clearly.\n4. CTA (one line): follow / save / comment trigger.\nPART B — ON-SCREEN TEXT: the text overlay for each beat (max 8 words per overlay).\nPART C — CAPTION: first line = a second hook (it shows before \"...more\"), then 2-3 value lines, then 3-5 niche hashtags.\nRules: write for spoken delivery — contractions, rhythm, no formal sentences. The hook must NOT summarize the video; it must open a gap the video closes." },

/* ---------- POST templates: LinkedIn specific ---------- */
{ type:"post", plats:["li"], emoji:"💼", name:"Professional insight",
  desc:"Industry observation + so-what. LinkedIn's native format.",
  body:"Write a LinkedIn post: one sharp industry observation about the topic, 3-4 short lines of analysis, what it means for professionals in Pakistan/India, one question at the end. Professional but warm. 3-5 hashtags in PascalCase (#ArtificialIntelligence style)." },
{ type:"post", plats:["li"], emoji:"📖", name:"Lesson-learned story",
  desc:"Career/skill story with a takeaway. High reach format.",
  body:"Write a LinkedIn story post: short personal experience related to the topic (first lines must hook), the mistake or surprise, the professional lesson, takeaway for readers. Line breaks between thoughts." },
{ type:"post", plats:["li"], emoji:"📑", name:"Document Carousel (PDF)",
  desc:"Hook slide + 6-8 value slides + CTA. LinkedIn's #1 engagement format (~7% ER — beats video).",
  body:"Write a LinkedIn document carousel (PDF) about: {topic}. Output slide-by-slide text I can design into a PDF.\nStructure (9-10 slides):\n- SLIDE 1 (HOOK): max 10 words + a sub-line. Must create a curiosity gap or promise a specific outcome (\"7 proposal mistakes costing you clients — #4 is the silent killer\"). Write 3 hook options, mark the strongest.\n- SLIDE 2 (STAKES): why this matters / the cost of not knowing. One stat or sharp claim.\n- SLIDES 3-8 (VALUE): one idea per slide. Format each as: bold 5-8 word headline + 2-3 supporting lines. Each slide must stand alone if screenshotted.\n- SLIDE 9 (SUMMARY): recap all points as a scannable checklist — this is the \"save trigger\" slide.\n- SLIDE 10 (CTA): one clear ask — follow for more / comment a keyword / repost to help someone.\nALSO write the post caption: first 2 lines = hook (visible before \"...see more\"), then 2-3 context lines, then \"Repost if useful\" style CTA (with recycle emoji). 3-5 hashtags max.\nRules: professional but human tone — no corporate jargon. Slide text must be SHORT; it's a billboard, not a paragraph." },
{ type:"post", plats:["li"], emoji:"📈", name:"Case Study (with numbers)",
  desc:"Client problem -> what you did -> measurable result. Proof beats opinion on LinkedIn.",
  body:"Write a LinkedIn case study post about: {topic} (the client/project, the problem, what was done, and the measurable result — anonymize the client if needed).\nStructure:\n1. HOOK: lead with the RESULT, not the story. \"We took [metric] from [before] to [after] in [timeframe]. Here's exactly how.\"\n2. THE PROBLEM: 2-3 lines, specific and recognizable — the reader should think \"we have this exact problem.\"\n3. THE APPROACH: 3-4 numbered steps of what was actually done. Concrete actions, not buzzwords.\n4. THE RESULT: restate numbers + one unexpected secondary benefit.\n5. THE LESSON: one transferable principle the reader can apply.\n6. Soft CTA: \"Dealing with something similar? My DMs are open.\" (only if I say I want leads — otherwise end on the lesson).\nRules: real numbers only — ask me, never invent. No client-confidential details. Confident but not boastful: the framework is the hero, not me." },

/* ---------- POST templates: Facebook specific ---------- */
{ type:"post", plats:["fb"], emoji:"🗣", name:"Discussion starter",
  desc:"FB loves comments — ask the family-audience question.",
  body:"Write a Facebook post: relatable everyday angle on the topic (very simple words, family audience), short context, then a discussion question people will WANT to answer. 1-3 hashtags max." },
{ type:"post", plats:["fb"], emoji:"🆚", name:"This or That",
  desc:"Zero-effort comment bait. FB's algorithm feeds on reply threads.",
  body:"Write a Facebook \"this or that\" post about: {topic} (the two options and the audience).\nStructure:\n1. Set the scene in 1-2 warm, relatable lines (Facebook = family/friends tone).\n2. Present the two options clearly: \"Team A or Team B?\"\n3. Add one playful provocation that makes people defend their side (\"And yes, there IS a wrong answer\" + laughing emoji).\n4. Ask them to comment their pick AND tag someone who'd pick the opposite.\nRules: the two options must be something EVERYONE has an instant opinion on — no expertise required to answer. Light, fun, zero selling." },
{ type:"post", plats:["fb"], emoji:"😅", name:"Relatable Confession",
  desc:"'Am I the only one who...' — everyday struggle + nostalgia, FB's comment goldmine.",
  body:"Write a Facebook \"relatable confession\" post about: {topic} (the everyday habit, struggle, or guilty pleasure to confess).\nStructure:\n1. HOOK: \"Am I the only one who [specific, slightly embarrassing but universal thing]?\" or \"Confession: [thing].\"\n2. Describe the moment with 2-3 vivid, specific details — specificity is what makes people say \"this is literally me.\"\n3. A self-aware punchline or shrug (\"No regrets. Okay, some regrets.\").\n4. CTA: \"Tell me I'm not alone\" + sweat-smile emoji or \"What's yours?\"\nRules: keep it light and universal — never an actual heavy confession. Family-friendly. The more specific the detail, the more relatable it lands." },

/* ---------- POST templates: WhatsApp specific ---------- */
{ type:"post", plats:["wa"], emoji:"📢", name:"Channel announcement",
  desc:"2-3 lines, personal tone, link. WhatsApp = your inner circle.",
  body:"Write a WhatsApp Channel message: 2-3 lines max, personal tone (like messaging friends), one emoji per line max, the value in line 1, link placeholder at the end." },
{ type:"post", plats:["wa"], emoji:"💡", name:"Quick tip drop",
  desc:"One instantly-usable tip. Keeps the channel alive daily.",
  body:"Write a WhatsApp Channel message: ONE practical tip about the topic people can use in the next 5 minutes, 2-3 lines, friendly, no links needed." },
{ type:"post", plats:["wa"], emoji:"📊", name:"Poll of the Day",
  desc:"One-tap question using native channel polls — the lowest-friction engagement that exists.",
  body:"Write a WhatsApp channel poll post about: {topic}.\nOutput:\n1. SETUP LINE (1-2 lines, personal inner-circle tone): why I'm asking, with a hint of my own opinion to provoke responses.\n2. THE POLL QUESTION: one short, clear question.\n3. POLL OPTIONS: 2-4 options, each max 5 words, mutually exclusive, at least one slightly spicy/funny option.\n4. FOLLOW-UP TEASER: \"Results + my take tomorrow\" + eyes emoji (creates a return loop).\nRules: WhatsApp = inner circle, so write like texting friends, not broadcasting. One emoji max per line. The question must be answerable in under 2 seconds of thought." },
];

/* Plug-and-play caption templates for the post composer quick-fill. */
window.POST_TEMPLATES = [
  { name: "Video announcement",
    text: "🚨 Nayi video aa gayi!\n\n{topic} — sab kuch simple Urdu mein samjhaya hai.\n\nLink bio mein 🔗\n#AI #AIxAhmad" },
  { name: "Hook question",
    text: "Kya aap jaante hain {topic}?\n\n90% log ye nahi jaante... maine video mein sab bataya hai 👇" },
  { name: "Prompt share",
    text: "Ye prompt copy karo aur khud try karo 🎁\n\n\"{topic}\"\n\nApna result comment mein dikhao 👇\n#AI #AIPrompts" },
  { name: "Behind the scenes",
    text: "Aaj ki video ke peeche ki kahani 🎬\n\n{topic}\n\nKal video aa rahi hai — follow karke rakho!" },
  { name: "Debate / poll",
    text: "Sawal: {topic}?\n\nMera jawab: [apni stance likho]\n\nAap kya sochte hain? Comment mein batao 👇" },
  { name: "Weekly recap",
    text: "Is hafte AI duniya mein kya hua 🌍\n\n1. {topic}\n2. ...\n3. ...\n\nPoori detail YouTube pe — link bio mein!" },
];

/* ===================================================================
   X (Twitter) engagement-optimized library — 2026 playbook.
   Format (A) + Voice (B) + Hook (C) mix-and-match, plus universal rules.
   The app builds the full prompt from these and the Worker just relays it,
   so you can tune wording here anytime with no Worker re-paste.
   =================================================================== */
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

/* ---- Social pack: engaging, platform-tailored posts (YouTube / Facebook /
   WhatsApp / Instagram). Default language English (global audience). ---- */
window.SOCIAL = {
  youtube: {
    label: "YouTube",
    rules: "Platform: YouTube (community post / Short caption). Open with a strong curiosity or bold hook in the FIRST line. Then 2-4 short lines on why this matters to a normal person. End with a clear CTA to watch and subscribe to @aixahmad. 1-2 emojis max. Put the link at the end. 2-3 relevant hashtags.",
  },
  facebook: {
    label: "Facebook",
    rules: "Platform: Facebook page post. Start with a scroll-stopping hook line. Then 3-5 short, simple, engaging lines with a relatable angle for a global audience. Ask ONE question at the end to spark comments. Put the link on its own line at the end. 2-3 hashtags. A few natural emojis.",
  },
  whatsapp: {
    label: "WhatsApp Channel",
    rules: "Platform: WhatsApp Channel broadcast. Very punchy and skimmable. A strong 1-line hook with one emoji. Then 2-3 short lines of the key point. End with the link and a soft line like 'Follow for daily AI updates'. Avoid hashtags (they don't help on WhatsApp).",
  },
  instagram: {
    label: "Instagram",
    rules: "Platform: Instagram caption. Bold hook as the first line. Short engaging lines with line breaks and tasteful emojis. Strong CTA to follow @aixahmad. Instagram captions can't have clickable links, so write 'Full story — link in bio' instead of pasting the URL. End with 6-10 relevant hashtags.",
  },
};

/* ---- Global Newsroom: ONE prompt -> article + 2 image prompts + all platform
   posts. Output uses [[MARKERS]] so the studio can split it into sections. ---- */
window.buildNewsroomPrompt = function (o) {
  return [
'You are a world-class senior journalist and platform-native social media strategist for AI/news content.',
'Think like Reuters, BBC, AP, The New York Times, FT, and The Washington Post for accuracy.',
'Think like a top creator/editor on X, LinkedIn, Instagram, Facebook, Reddit, WhatsApp, and YouTube for distribution.',
'',
'Your job:',
'1) Read and understand the source story carefully.',
'2) Privately analyze the story before writing.',
'3) Decide the strongest angle for each platform.',
'4) Produce professional journalism plus engaging platform-ready posts.',
'',
'SOURCE STORY: ' + (o.title || ''),
(o.source ? 'SOURCE LINK: ' + o.source + '\nFIRST open and read the source carefully.' : ''),
'',
'IMPORTANT RULES:',
'Use ONLY facts from the source story/source link.',
'Never invent quotes, numbers, names, dates, events, motives, or claims.',
'If the source does not say something, do not add it.',
'Attribute facts clearly.',
'Accuracy first. Engagement second.',
'No clickbait. No fake urgency. No sensationalism.',
'Do not sound robotic or like a press release.',
'Plain text only. No markdown.',
'',
'PRIVATE ANALYSIS STEP — do this silently before writing, but DO NOT output it:',
'Identify the strongest verified news peg.',
'Identify what makes the story interesting: money, power, product change, AI impact, risk, controversy, surprise, human impact, business impact, or future implication.',
'Identify the best audience angle for each platform.',
'Choose the best hook style for each platform: hard fact, contrast, tension, consequence, sharp question, curiosity gap, or practical implication.',
'Make sure every platform post feels different, not copy-pasted.',
'',
'GLOBAL SOCIAL WRITING RULES:',
'Every social post must quickly answer: what happened, why it matters, and why people should click/read.',
'Use strong first lines.',
'Front-load the most interesting fact or consequence.',
'Use short paragraphs and whitespace.',
'Make the copy skimmable on mobile.',
'Write like a smart human, not a corporate brand. Vary sentence length (mix short punchy lines with one longer line) so it does not read as AI-generated.',
'Avoid boring openings like: "In a major development", "According to reports", "The article discusses", "This is a game-changer", "In today’s fast-paced world".',
'BANNED phrases (sound like AI): game changer, revolutionising the future, unlock the power, next big thing, cutting-edge, seamless, transformative, "the future is here", "AI is changing everything", "this will disrupt every industry", leverage, harness, robust, paradigm shift, delve, dive in. Also avoid "It\'s not just X, it\'s Y" and rule-of-three lists.',
'Where natural, add a light human angle/opinion (my take / the part people ignore / for builders this means).',
'Use natural CTAs, not engagement bait.',
'Wherever the article link belongs, write the literal token [ARTICLE LINK].',
'',
'OUTPUT EXACTLY in the format below.',
'Keep every [[MARKER]] on its own line, in this order.',
'Write nothing before [[HEADLINE]] and nothing after [[END]].',
'',
'[[HEADLINE]]',
'(Write a compelling, professional headline. Make it specific, clear, and newsworthy. Use strong verbs. Avoid vague hype.)',
'',
'[[SUBHEAD]]',
'(Write one sentence summarizing the story and its significance. Do not simply repeat the headline.)',
'',
'[[ARTICLE]]',
'(Write a 500-700 word professional article. Use a strong lede, short paragraphs, clear attribution, context, and significance. Keep the tone neutral, credible, and global. Use only source facts.)',
'',
'[[SOURCES]]',
'(List the original source title and source link provided.)',
'',
'[[IMAGE1]]',
'(Write a ready-to-paste image-generation prompt for the headline graphic. ' + window.HUMAN_IMAGE + ' Render the EXACT headline from [[HEADLINE]] in the bottom band, word for word, nothing else.)',
'',
'[[IMAGE2]]',
'(Write a DIFFERENT image-generation prompt with NO text — a clean realistic hero photo showing another angle, wider context, or the human/business impact of the story. Real photo-based scene (startup office, AI lab, data centre, developer desk, investor meeting, newsroom), natural lighting, realistic shadows and textures, believable human detail. NO sci-fi glow, NO glossy AI look, NO logos, NO watermark, NO text. 16:9.)',
'',
'[[LINKEDIN]]',
'(English. Write a professional but engaging LinkedIn post for smart professionals. Do not make it boring. Structure: 1) Strong first line based on the biggest implication, tension, or business impact. 2) Short context explaining what happened. 3) Explain why it matters for business, AI, tech, policy, creators, startups, workers, or consumers depending on the story. 4) Add one thoughtful discussion question. Use short paragraphs and whitespace. Tone: credible, human, sharp, not corporate. Length: 120-220 words. End exactly with: Read the full story:\n[ARTICLE LINK])',
'',
'[[X]]',
'(English. Write a strong X/Twitter news post designed for attention and link clicks. Do NOT write a tiny one-line tweet. Structure it like this: Line 1 = scroll-stopping hook using the strongest verified fact, number, surprise, conflict, risk, product change, AI implication, or consequence from the story. Lines 2-6 = short punchy lines explaining what happened, who is involved, and why it matters. Use whitespace. Lines 7-8 = the bigger implication, risk, opportunity, or question people should think about. Then add one natural CTA line such as "Read the full story below", "Here’s what you need to know", "This is worth watching", "Bookmark this", or a sharp question. Final line must be only: [ARTICLE LINK]. Tone: smart, human, slightly dramatic but not clickbait. Avoid fake hype. Avoid corporate language. Use 0-1 hashtag only if genuinely useful. Target length: 700-1,200 characters.)',
'',
'[[REDDIT]]',
'(English. First line must be a Reddit-style title: descriptive, neutral, specific, not clickbait. Then write a neutral summary of the story in 2-4 short paragraphs. Add one genuine discussion question at the end. Do not ask for upvotes, shares, or engagement. End with [ARTICLE LINK])',
'',
'[[FACEBOOK]]',
'(English. Write an engaging Facebook post for a general audience. Start with a relatable or surprising hook. Explain the story in simple language with 2-4 short paragraphs. Use light emojis only if natural. Make it easy to understand and easy to comment on. Avoid engagement bait like "comment YES" or "tag someone". End exactly with: Read the full story:\n[ARTICLE LINK])',
'',
'[[INSTAGRAM]]',
'(English. Write an Instagram caption. Start with a scroll-stopping first sentence. Then explain the key facts in a concise, visual, caption-friendly way. Use natural keywords people might search for. Use light emojis only if they fit the story. Add 3-6 relevant hashtags max. Avoid hashtag stuffing. End exactly with: Read the full story:\n[ARTICLE LINK])',
'',
'[[WHATSAPP]]',
'(English. Write a very concise WhatsApp/Channel update. Biggest fact first. Mobile-friendly. Short lines. Clear and useful. Minimal emojis only if natural. End exactly with: Read the full story:\n[ARTICLE LINK])',
'',
'[[YOUTUBE]]',
'(English. Write a YouTube Community post. Create curiosity in the first line. Explain the key development and why viewers should care. Ask one clear question to encourage discussion. Keep it short, direct, and community-friendly. End exactly with: Read the full story:\n[ARTICLE LINK])',
'',
'[[END]]',
  ].filter(x => x !== null && x !== undefined).join('\n');
};

window.buildSocialPrompt = function (o) {
  const cfg = window.SOCIAL[o.platform] || window.SOCIAL.facebook;
  const lang = o.lang === "ur"
    ? "Write in simple Roman Urdu (Urdu written in English letters) with light English."
    : "Write in clear, simple English for a global worldwide audience.";
  const wantLink = o.platform !== "instagram" && o.link;
  return [
    'You write social-media posts for "AI x Ahmad" (@aixahmad), a global AI-news brand.',
    lang, "",
    cfg.rules, "",
    window.HUMAN_VOICE, "",
    "Make it genuinely ENGAGING — a real hook that stops the scroll, not a press release. Simple words, one idea per line.",
    "Base everything ONLY on the story below — never invent facts, numbers, or quotes.", "",
    "STORY: " + (o.title || ""),
    (o.body ? "DETAILS: " + String(o.body).replace(/\s+/g, " ").slice(0, 500) : ""),
    (wantLink ? "LINK (put at the end): " + o.link : ""),
    "",
    "Return ONLY the final post text, ready to copy-paste — no options, no notes, no markdown.",
  ].filter(x => x !== "").join("\n");
};

/* ---- X Reply Engine: 7 reply styles for a captured post ---- */
window.XREPLY_STYLES = [
  ["smart",      "💡 Smart",          "an insightful reply that adds real value / a non-obvious angle and shows expertise"],
  ["short",      "⚡ Short viral",     "a punchy one-liner with viral energy, under ~120 characters"],
  ["question",   "❓ Question",        "a sharp, genuine question that invites the author + others to reply"],
  ["relatable",  "😅 Relatable",       "a relatable, casual human reaction that makes people feel 'same'"],
  ["builder",    "🛠 Builder",         "a builder/technical angle — concrete, practical, what you'd actually do"],
  ["opinion",    "🔥 Strong opinion",  "a bold, slightly contrarian but defensible take (respectful, never insulting)"],
  ["supportive", "🤝 Supportive",      "a warm, encouraging, genuinely supportive reply"],
];
window.buildXReplyPrompt = function (o) {
  o = o || {};
  if (o.brief) {
    return [
      "You are writing an X/Twitter reply for @aixahmad — a smart, human voice (never a brand or an AI assistant).",
      "",
      "Reply to THIS X post:",
      "AUTHOR: " + (o.author_name || "") + " " + (o.author_handle || ""),
      'POST: "' + (o.post_text || "") + '"',
      "",
      "THINK FIRST, then write — decide what THIS post actually needs, then write the 2 strongest replies:",
      "- If it asks a question, ANSWER it directly (do not ask another question back).",
      "- News -> add a smart angle or implication. Hot take -> agree or disagree with a clear reason.",
      "- Joke/meme -> witty or relatable. Personal win -> genuinely supportive. Technical -> a practical builder angle.",
      "- Only ask a question when that is genuinely the smartest reply.",
      "",
      window.HUMAN_VOICE,
      "REPLY SPECIFICS: sound like a sharp friend replying under the post. No fake praise ('Great insight!', 'This is huge'). No @mention needed. Text only. Under 280 characters.",
      "",
      "Give the BEST reply and ONE BACKUP (a meaningfully different angle or style).",
      "",
      "Return ONLY this JSON, nothing else:",
      "{",
      '  "post_type": "question | news | hot_take | joke_or_meme | personal_update | launch_or_announcement | technical | debate | advice | unclear",',
      '  "best_action": "answer_directly | add_insight | ask_followup | agree_and_expand | respectfully_challenge | make_it_relatable | add_builder_angle | be_supportive | be_witty | clarify",',
      '  "analysis": "1 casual sentence: what this post is and what reply will work",',
      '  "recommend": "smart | short | question | relatable | builder | opinion | supportive",',
      '  "recommend_why": "one short line on why the best reply fits",',
      '  "best_reply": "the single strongest reply, ready to paste",',
      '  "backup_reply": "the second reply, a different angle",',
      '  "replies": [',
      '    {"style":"<style of best>","text":"<best_reply, word for word>","score":9},',
      '    {"style":"<style of backup>","text":"<backup_reply, word for word>","score":8}',
      "  ]",
      "}",
      "Both replies MUST be under 280 characters and copied word-for-word into the replies list.",
    ].join("\n");
  }
  const styles = window.XREPLY_STYLES
    .map((s, i) => (i + 1) + ") " + s[0] + " — " + s[2])
    .join("\n");

  return [
    "You are writing X/Twitter replies for @aixahmad.",
    "",
    "MAIN GOAL:",
    "Do NOT just generate random engagement replies.",
    "Think like an intelligent human first.",
    "Before writing, decide what the post needs:",
    "- If the post asks a question, ANSWER the question directly.",
    "- If the post shares news, add a smart angle or implication.",
    "- If the post is a hot take, agree/disagree with a reason.",
    "- If the post is a joke/meme, reply casually or witty.",
    "- If the post is a personal win, be supportive and human.",
    "- If the post is technical, add a builder/practical angle.",
    "- If the post is unclear, ask a simple clarifying question.",
    "- Only ask a question when a question is the smartest reply.",
    "",
    window.HUMAN_VOICE,
    "- Write like a smart friend replying under a post. No fake praise (Great insight, Amazing update, This is huge) unless it truly fits.",
    "- Across the 7 replies, only 2-4 should use an emoji (max 1 each) — not every reply.",
    "",
    "Reply to THIS X post:",
    "AUTHOR: " + (o.author_name || "") + " " + (o.author_handle || ""),
    'POST: "' + (o.post_text || "") + '"',
    "",
    "STEP 1 — CLASSIFY THE POST:",
    "Choose the post_type:",
    "- question",
    "- news",
    "- hot_take",
    "- joke_or_meme",
    "- personal_update",
    "- launch_or_announcement",
    "- technical",
    "- debate",
    "- advice",
    "- unclear",
    "",
    "STEP 2 — DECIDE THE BEST REPLY MOVE:",
    "Choose the best_action:",
    "- answer_directly",
    "- add_insight",
    "- ask_followup",
    "- agree_and_expand",
    "- respectfully_challenge",
    "- make_it_relatable",
    "- add_builder_angle",
    "- be_supportive",
    "- be_witty",
    "- clarify",
    "",
    "Decision rules:",
    "- For question posts: best_action should usually be answer_directly, not ask_followup.",
    "- For news posts: best_action should usually be add_insight or add_builder_angle.",
    "- For hot takes: best_action should usually be agree_and_expand or respectfully_challenge.",
    "- For jokes/memes: best_action should usually be be_witty or make_it_relatable.",
    "- For personal wins: best_action should usually be be_supportive.",
    "- For technical posts: best_action should usually be add_builder_angle.",
    "- Do not force debate if the post needs a normal answer.",
    "- Do not force a question if the post already asked one.",
    "",
    "STEP 3 — WRITE EXACTLY 7 REPLIES:",
    styles,
    "",
    "REPLY QUALITY RULES:",
    "- Every reply must match the post_type and best_action.",
    "- Every reply must be specific to the actual post.",
    "- If the original post asks a question, at least 4 of the replies must answer it directly.",
    "- If the original post is news, at least 4 replies must add insight or implication.",
    "- If the original post is a hot take, at least 3 replies should have a clear opinion.",
    "- If the original post is a joke/meme, replies can be lighter and more casual.",
    "- Keep replies under 280 characters.",
    "- Most replies should be 1 sentence. Some can be 2 short lines.",
    "- No @mention needed because this is already a reply.",
    "- Usually no hashtags.",
    "- Do not repeat the same idea across replies.",
    "- Do not over-explain.",
    "- Do not invent facts, numbers, names, or claims.",
    "- Do not insult anyone.",
    "- Do not sound desperate for engagement.",
    "",
    "GOOD BEHAVIOR EXAMPLES:",
    "If post asks: 'Is Claude better than ChatGPT for coding?'",
    "Bad: 'Interesting question, what do you think?'",
    "Good: 'For long coding sessions, Claude feels stronger to me. For quick fixes and debugging, ChatGPT still feels faster.'",
    "",
    "If post says: 'AI agents will replace SaaS dashboards.'",
    "Bad: 'Great insight!'",
    "Good: 'Maybe not replace all dashboards, but agents will definitely make a lot of dashboards feel outdated.'",
    "",
    "If post says: 'OpenAI launched a new coding agent.'",
    "Bad: 'This is a game-changer for the AI landscape.'",
    "Good: 'The real shift is not better autocomplete. It’s AI moving closer to doing full engineering tasks end-to-end.'",
    "",
    "Pick the BEST reply and a BACKUP reply (second-best, ideally a DIFFERENT style).",
    "",
    "Return ONLY a JSON object, no text outside it, in EXACTLY this shape:",
    "{",
    '  "post_type": "<question | news | hot_take | joke_or_meme | personal_update | launch_or_announcement | technical | debate | advice | unclear>",',
    '  "best_action": "<answer_directly | add_insight | ask_followup | agree_and_expand | respectfully_challenge | make_it_relatable | add_builder_angle | be_supportive | be_witty | clarify>",',
    '  "analysis": "1-2 casual sentences explaining what this post is and what kind of reply will work best",',
    '  "best_reply": "the single strongest reply for THIS post (copy word-for-word from the replies list)",',
    '  "backup_reply": "the second-best reply, preferably a DIFFERENT style (copy word-for-word from the replies list)",',
    '  "recommend": "<one of: smart, short, question, relatable, builder, opinion, supportive>",',
    '  "recommend_why": "one short casual line explaining why this style should perform best",',
    '  "replies": [',
    '    {"style":"smart","text":"...","score":8},',
    '    {"style":"short","text":"...","score":8},',
    '    {"style":"question","text":"...","score":8},',
    '    {"style":"relatable","text":"...","score":8},',
    '    {"style":"builder","text":"...","score":8},',
    '    {"style":"opinion","text":"...","score":8},',
    '    {"style":"supportive","text":"...","score":8}',
    "  ]",
    "}",
    "",
    "Score = 1-10 based on how likely the reply is to get likes, replies, or profile clicks.",
    "best_reply = the strongest reply for this specific post (if the post asks a question, it should usually answer directly). backup_reply = the next best, ideally a different style. Both MUST be copied word-for-word from the replies list.",
  ].join("\n");
};

/* ---- Post Repurpose Engine: turn a post you saw into ORIGINAL content ---- */
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
