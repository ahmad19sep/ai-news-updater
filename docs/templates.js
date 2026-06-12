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

/* ---------- POST templates: X specific ---------- */
{ type:"post", plats:["x"], emoji:"🧵", name:"X thread (5-7 posts)",
  desc:"The authority format on X. Hook tweet + value chain.",
  body:"Write an X THREAD of 5-7 posts: post 1 = strong hook with the promise, posts 2-6 = one idea each (short lines, no fluff), last post = recap + follow CTA @aixahmad. Number them." },
{ type:"post", plats:["x"], emoji:"🎁", name:"Prompt share",
  desc:"Useful prompt + 'show your result' — bookmarks + replies.",
  body:"ONE X post under 280 chars sharing a genuinely useful AI prompt about the topic, exact prompt in quotes, end: 'apna result comment mein dikhao'." },
{ type:"post", plats:["x"], emoji:"✏️", name:"Fill the blank",
  desc:"Easy replies + feature loop to YouTube.",
  body:"ONE X post under 280 chars: fill-in-the-blank about the topic, end with 'best answer agli video mein feature hoga'." },
{ type:"post", plats:["x"], emoji:"⚔️", name:"Test & tell",
  desc:"Claude vs ChatGPT challenge — fun comparison bait.",
  body:"ONE X post under 280 chars: I made Claude vs ChatGPT do something with the topic, my one-line verdict, challenge readers to try and reply with theirs." },

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

/* ---------- POST templates: LinkedIn specific ---------- */
{ type:"post", plats:["li"], emoji:"💼", name:"Professional insight",
  desc:"Industry observation + so-what. LinkedIn's native format.",
  body:"Write a LinkedIn post: one sharp industry observation about the topic, 3-4 short lines of analysis, what it means for professionals in Pakistan/India, one question at the end. Professional but warm. 3-5 hashtags in PascalCase (#ArtificialIntelligence style)." },
{ type:"post", plats:["li"], emoji:"📖", name:"Lesson-learned story",
  desc:"Career/skill story with a takeaway. High reach format.",
  body:"Write a LinkedIn story post: short personal experience related to the topic (first lines must hook), the mistake or surprise, the professional lesson, takeaway for readers. Line breaks between thoughts." },

/* ---------- POST templates: Facebook specific ---------- */
{ type:"post", plats:["fb"], emoji:"🗣", name:"Discussion starter",
  desc:"FB loves comments — ask the family-audience question.",
  body:"Write a Facebook post: relatable everyday angle on the topic (very simple words, family audience), short context, then a discussion question people will WANT to answer. 1-3 hashtags max." },

/* ---------- POST templates: WhatsApp specific ---------- */
{ type:"post", plats:["wa"], emoji:"📢", name:"Channel announcement",
  desc:"2-3 lines, personal tone, link. WhatsApp = your inner circle.",
  body:"Write a WhatsApp Channel message: 2-3 lines max, personal tone (like messaging friends), one emoji per line max, the value in line 1, link placeholder at the end." },
{ type:"post", plats:["wa"], emoji:"💡", name:"Quick tip drop",
  desc:"One instantly-usable tip. Keeps the channel alive daily.",
  body:"Write a WhatsApp Channel message: ONE practical tip about the topic people can use in the next 5 minutes, 2-3 lines, friendly, no links needed." },
];

/* Plug-and-play caption templates for the post composer quick-fill. */
window.POST_TEMPLATES = [
  { name: "Video announcement",
    text: "🚨 Nayi video aa gayi!\n\n{topic} — sab kuch simple Urdu mein samjhaya hai.\n\nLink bio mein 🔗\n#AI #AIxAhmad" },
  { name: "Hook question",
    text: "Kya aap jaante hain {topic}?\n\n90% log ye nahi jaante... maine video mein sab bataya hai 👇" },
  { name: "Prompt share",
    text: "Ye prompt copy karo aur khud try karo 🎁\n\n\"{topic}\"\n\nApna result comment mein dikhao 👇\n#ChatGPT #AI" },
  { name: "Behind the scenes",
    text: "Aaj ki video ke peeche ki kahani 🎬\n\n{topic}\n\nKal video aa rahi hai — follow karke rakho!" },
  { name: "Debate / poll",
    text: "Sawal: {topic}?\n\nMera jawab: [apni stance likho]\n\nAap kya sochte hain? Comment mein batao 👇" },
  { name: "Weekly recap",
    text: "Is hafte AI duniya mein kya hua 🌍\n\n1. {topic}\n2. ...\n3. ...\n\nPoori detail YouTube pe — link bio mein!" },
];
