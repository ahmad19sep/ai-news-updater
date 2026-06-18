/* AI x Ahmad - template library.
   Edit wording freely - the site reloads it automatically.

   WIZ = the Create wizard library. Each template:
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
   WhatsApp / Instagram). Default language Roman Urdu (Pakistan/India audience). ---- */
window.SOCIAL = {
  youtube: {
    label: "YouTube",
    rules: "Platform: YouTube (community post / Short caption). Open with a strong curiosity or bold hook in the FIRST line. Then 2-4 short lines on why this matters to a normal person. End with a clear CTA to watch and subscribe to @aixahmad. 1-2 emojis max. Put the link at the end. 2-3 relevant hashtags.",
  },
  facebook: {
    label: "Facebook",
    rules: "Platform: Facebook page post. Start with a scroll-stopping hook line. Then 3-5 short, simple, engaging lines with a relatable angle for a Pakistani/Indian audience. Ask ONE question at the end to spark comments. Put the link on its own line at the end. 2-3 hashtags. A few natural emojis.",
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
'You are a world-class senior journalist (Reuters, BBC, The New York Times, AP, FT, The Washington Post). Analyze the source news and produce professional journalism for a global audience, then platform-ready social posts.',
'',
'SOURCE STORY: ' + (o.title || ''),
(o.source ? 'SOURCE LINK: ' + o.source + '\nFIRST open and read the source carefully.' : ''),
'',
'Rules: accuracy, neutrality, credibility. Use ONLY facts from the source — never invent quotes, numbers, names, or events. Attribute facts. No sensationalism. Plain text (no markdown).',
'',
'Output EXACTLY in the format below. Keep every [[MARKER]] on its own line, in this order, with nothing before [[HEADLINE]] or after [[END]]. In every social post, wherever the article link belongs, write the literal token [ARTICLE LINK] (I will replace it).',
'',
'[[HEADLINE]]',
'(compelling, professional headline)',
'[[SUBHEAD]]',
'(one-sentence summary)',
'[[ARTICLE]]',
'(500-700 word article: strong lede, short paragraphs, context, significance, attribution)',
'[[SOURCES]]',
'(the original source(s))',
'[[IMAGE1]]',
'(A ready-to-paste AI IMAGE-GENERATION PROMPT for a vertical 4:5 social news poster with the headline beautifully written ON the image: a photorealistic, cinematic subject relevant to the story (real person / product / scene), professional dramatic lighting, sharp focus, on a dark moody background that fades darker toward the bottom to leave room for text. In the lower area render the EXACT headline above in bold, modern, eye-catching typography — large, clean, high-contrast and perfectly legible, tastefully styled (you may emphasize one key word or number with a colored accent). Spell the headline EXACTLY, word for word — only the headline words appear, no gibberish. NO logos, NO watermarks, NO social icons.)',
'[[IMAGE2]]',
'(A DIFFERENT 16:9 image-generation prompt — a CLEAN alternate with NO text: another angle/consequence/wider context, photorealistic editorial photography, dramatic lighting, ultra-detailed, no text/logos/watermarks. Use this when you want a plain hero image instead of the headline poster.)',
'[[LINKEDIN]]',
'(English. Professional LinkedIn post: strong hook, key insight + implications, encourage discussion. End with "Read the full story:\\n[ARTICLE LINK]")',
'[[X]]',
'(English. A SUBSTANTIAL single X post — do NOT cap at 280 chars. Open with a scroll-stopping hook (front-load the key fact/number), then 3-5 short lines giving the key points AND why it matters (one idea per line, lots of whitespace), then one engagement line (a sharp question or "Bookmark this"). ~6-9 lines, skimmable, zero fluff, 0-1 hashtag. End with the link on its own final line: [ARTICLE LINK])',
'[[REDDIT]]',
'(English. First line = a Reddit-style title, then a neutral summary + one discussion question. End with [ARTICLE LINK])',
'[[FACEBOOK]]',
'(Roman Urdu. Engaging hook, easy paragraphs, emojis, encourage comments. End with "Puri khabar parhein:\\n[ARTICLE LINK]")',
'[[INSTAGRAM]]',
'(Roman Urdu. Caption style: hook, key facts, emojis, hashtags. End with "Puri khabar parhein:\\n[ARTICLE LINK]")',
'[[WHATSAPP]]',
'(Roman Urdu. Very concise, most important facts first, mobile-friendly, few emojis. End with "Puri khabar parhein:\\n[ARTICLE LINK]")',
'[[YOUTUBE]]',
'(Roman Urdu. Community post: create curiosity, highlight the key development, ask a question. End with "Puri khabar parhein:\\n[ARTICLE LINK]")',
'[[END]]',
  ].filter(x => x !== null && x !== undefined).join('\n');
};

window.buildSocialPrompt = function (o) {
  const cfg = window.SOCIAL[o.platform] || window.SOCIAL.facebook;
  const lang = o.lang === "en"
    ? "Write in clear, simple English."
    : "Write in simple Roman Urdu (Urdu written in English letters) with light English — the audience is Pakistan/India.";
  const wantLink = o.platform !== "instagram" && o.link;
  return [
    'You write social-media posts for "AI x Ahmad" (@aixahmad), an AI-education brand for Pakistan & India.',
    lang, "",
    cfg.rules, "",
    "Make it genuinely ENGAGING — a real hook that stops the scroll, not a press release. Simple words, one idea per line.",
    "Base everything ONLY on the story below — never invent facts, numbers, or quotes.", "",
    "STORY: " + (o.title || ""),
    (o.body ? "DETAILS: " + String(o.body).replace(/\s+/g, " ").slice(0, 500) : ""),
    (wantLink ? "LINK (put at the end): " + o.link : ""),
    "",
    "Return ONLY the final post text, ready to copy-paste — no options, no notes, no markdown.",
  ].filter(x => x !== "").join("\n");
};
