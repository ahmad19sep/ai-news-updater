/* AI x Ahmad - prompt templates.
   Placeholders in {curly braces} are filled by the tool from story data.
   Refine the wording here anytime - the site reloads it automatically.
   Kept separate so a future Cloudflare Worker can reuse the same file. */

/* Template GALLERY (Buffer "Create > Templates" style).
   Famous creator formats. {topic} is filled by the tool.
   The output language (Roman Urdu / English) is chosen with the toggle. */
window.GALLERY = [
  { cat: "Trending", emoji: "🧪", name: "I tested it so you don't have to",
    desc: "Try a tool/feature, share honest results. Builds trust fast.",
    body: "Write a post/short script: 'Maine {topic} khud test kiya' — my 3 honest findings (good, bad, surprising), one practical tip, end with a question to the audience." },
  { cat: "Trending", emoji: "⚡", name: "Myth vs Reality",
    desc: "Break one popular myth about the topic. High share rate.",
    body: "Write a post/short script busting ONE common myth about {topic}. Structure: the myth people believe -> the reality with a simple proof/example -> what to do instead." },
  { cat: "Tip", emoji: "💡", name: "Hook + 3 quick tips",
    desc: "Scroll-stopping hook, three practical tips, save-worthy.",
    body: "Write a post/short script: strong hook about {topic}, then exactly 3 numbered practical tips a beginner can use today, end with 'save this post'." },
  { cat: "List", emoji: "📋", name: "Top 5 list",
    desc: "Classic listicle. Easy to film, easy to share.",
    body: "Write a 'Top 5 {topic}' post/short script. One line per item with a concrete benefit. Rank them, tease #1 in the hook." },
  { cat: "How-to", emoji: "🛠", name: "Mini tutorial",
    desc: "Step-by-step in under a minute. Tutorial = trust.",
    body: "Write a mini step-by-step tutorial about {topic}: hook (the result they will get), 3-5 numbered steps, one warning/mistake to avoid, CTA." },
  { cat: "Question", emoji: "❓", name: "Strategic audience question",
    desc: "Real questions invite real conversation (Buffer favorite).",
    body: "Write a short post asking the audience ONE strategic question about {topic}. Include my own one-line answer first, then invite theirs. No empty bait." },
  { cat: "Opinion", emoji: "🔥", name: "Niche hot take",
    desc: "The opinions you're nervous to post build authority.",
    body: "Write a confident hot-take post about {topic}: my contrarian-but-defensible stance, 2 reasons, invite disagreement respectfully." },
  { cat: "Story", emoji: "📖", name: "Personal lesson story",
    desc: "Story arc: struggle, turn, lesson. Most human format.",
    body: "Write a first-person mini story about {topic}: the moment it clicked for me, what went wrong first, the lesson, how the viewer can skip my mistake." },
  { cat: "Case Study", emoji: "📊", name: "Before / After case study",
    desc: "Show a transformation with numbers — proof sells.",
    body: "Write a before/after case-study post about {topic}: starting point, what changed (steps), the result with a number, one takeaway." },
  { cat: "Behind the Scenes", emoji: "🎬", name: "Behind the scenes",
    desc: "Show the messy middle. People follow people.",
    body: "Write a behind-the-scenes post about {topic} (my process, tools, time it took, what nobody sees), casual tone, one honest struggle." },
  { cat: "Authority", emoji: "👋", name: "Reintroduce yourself",
    desc: "New people find you daily — tell them who you are.",
    body: "Write a reintroduction post for AI x Ahmad: who I am, why I talk about {topic}, what followers get from me weekly, one fun personal detail." },
  { cat: "Authority", emoji: "📚", name: "2-line takeaway from a read",
    desc: "Your interpretation is the value.",
    body: "Write a short post sharing my 2-line takeaway about {topic} (as if from an article I read), why it matters for Pakistan/India, link placeholder." },
  { cat: "X engagement", emoji: "🎁", name: "X: Prompt share",
    desc: "Useful prompt + 'show your result' — bookmarks + replies.",
    body: "Write ONE X post (under 280 chars) sharing a genuinely useful AI prompt about {topic}, the exact prompt in quotes, end: 'apna result comment mein dikhao'." },
  { cat: "X engagement", emoji: "⚔️", name: "X: Test & tell",
    desc: "Claude vs ChatGPT challenge — fun comparisons.",
    body: "Write ONE X post (under 280 chars): I made Claude vs ChatGPT do {topic}, my one-line verdict, challenge readers to try and reply with theirs." },
  { cat: "X engagement", emoji: "🗣", name: "X: Local debate",
    desc: "Jobs/AI question for PK/IN — your stance first.",
    body: "Write ONE X post (under 280 chars): sharp debate question about {topic} tied to daily life in Pakistan/India, MY clear stance first, then ask theirs." },
  { cat: "X engagement", emoji: "✏️", name: "X: Fill the blank",
    desc: "Easy replies + feature loop to YouTube.",
    body: "Write ONE X post (under 280 chars): fill-in-the-blank about {topic}, end with 'best answer agli video mein feature hoga'." },
];

/* Plug-and-play caption templates for the post composer (Buffer-style).
   Edit freely - {topic} stays as a placeholder you replace while writing. */
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

window.TEMPLATES = {

shortScript: `You are writing a short vertical video script for "AI x Ahmad" — AI explained in simple Roman Urdu for viewers in Pakistan and India. Audience: everyday people (students, freelancers, shopkeepers, parents), NOT tech experts. No jargon, no English-heavy lines. Friendly tone, like a friend explaining.

Story: {title}
Summary: {summary}
Link: {url}

FIRST: open and read the link above.

Write a {duration}-second script with EXACTLY this structure:
1. HOOK (0–3 sec): one scroll-stopping line about how this affects the viewer's life.
2. BODY: explain the story simply, one idea per sentence, with one concrete example or demo idea.
3. LOCAL ANGLE: "Pakistan/India ke liye iska matlab kya hai" — jobs, paisa, daily life.
4. CTA: follow @aixahmad, naya video har hafte.

Output in Roman Urdu. Add [B-ROLL] suggestions in brackets. Total spoken length must fit {duration} seconds.`,

longScript: `You are writing a YouTube main-video script for "AI x Ahmad" — AI explained in simple Roman Urdu for viewers in Pakistan and India. Audience: everyday people (students, freelancers, shopkeepers, parents), NOT tech experts. No jargon. Friendly tone, like a friend explaining.

Story: {title}
Key point: {summary}
Link: {url}

FIRST: open and read the link above.

STEP 1 — Classify this story as ONE of: news explainer (4–6 min) / tutorial (8–15 min) / comparison / opinion. Say which one you picked and why in one line.

STEP 2 — Write the full script using the matching structure:
- INTRO HOOK (first 20 sec): why the viewer must stay — connect to their life immediately.
- BODY in sections with [timestamp] markers and [B-ROLL] suggestions. One idea per section. Concrete examples for everyday people.
- LOCAL ANGLE section: "Pakistan/India ke liye iska matlab" — jobs, income, daily tools.
- RECAP: 3 key points in 3 lines.
- OUTRO + CTA: subscribe + join WhatsApp Channel "AI x Ahmad".

Output in Roman Urdu with light English where natural.`,

postPack: `For the video below, generate platform posts for "AI x Ahmad" (@aixahmad), simple Roman Urdu + light English mix:
Video topic: {title} — key point: {summary}

1. YOUTUBE: 3 title options (under 60 chars, curiosity-driven, no clickbait lies) + 2-paragraph description + 15 tags.
2. TIKTOK caption + 5 hashtags.
3. INSTAGRAM caption + 8 hashtags (mix Urdu/English/desi-tech tags).
4. FACEBOOK caption + 4 hashtags.
5. X: one post under 280 chars that invites replies (question or hot take with my stance).
6. WHATSAPP CHANNEL: 2-line announcement with the video link placeholder.
7. LINKEDIN: 4–6 line professional-tone post.`,

xFormats: {

promptShare: `Write an X post for @aixahmad ("AI x Ahmad" — AI in simple Roman Urdu for Pakistan/India).

Format: PROMPT-SHARE. Share ONE genuinely useful ChatGPT/Claude prompt about: {topic}.
- The prompt must be practical — something a student, freelancer or shopkeeper would actually use today.
- Show the exact prompt text in the post (short enough to copy).
- End with: "apna result comment mein dikhao 👇"
- Roman Urdu + light English. Under 280 characters. No empty hype.`,

testAndTell: `Write an X post for @aixahmad ("AI x Ahmad" — AI in simple Roman Urdu for Pakistan/India).

Format: TEST-AND-TELL challenge about: {topic}.
- Structure: "Maine Claude vs ChatGPT se ___ karwaya — aap try karo, kaunsa better hai?"
- Pick a concrete, fun, useful task related to the topic.
- Include my one-line result/observation so the post has real value.
- Invite people to reply with their result. Roman Urdu + light English. Under 280 characters.`,

debateLocal: `Write an X post for @aixahmad ("AI x Ahmad" — AI in simple Roman Urdu for Pakistan/India).

Format: LOCAL DEBATE question about: {topic}.
- A sharp question tied to daily life / jobs / income in Pakistan and India.
- IMPORTANT: the post must include MY OWN clear answer/stance first (one line), then ask readers theirs.
- No empty engagement bait — the stance must carry real insight.
- Roman Urdu + light English. Under 280 characters.`,

fillBlank: `Write an X post for @aixahmad ("AI x Ahmad" — AI in simple Roman Urdu for Pakistan/India).

Format: FILL-IN-THE-BLANK about: {topic}.
- Structure like: "ChatGPT se sabse useful kaam jo maine kiya: ___"
- Adapt the blank to the topic so answers are specific and interesting.
- End with: "Best answer ko apni agli video mein feature karunga 🎥" (connects X to YouTube).
- Roman Urdu + light English. Under 280 characters.`
}
};
