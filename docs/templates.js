/* AI x Ahmad - prompt templates.
   Placeholders in {curly braces} are filled by the tool from story data.
   Refine the wording here anytime - the site reloads it automatically.
   Kept separate so a future Cloudflare Worker can reuse the same file. */

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
