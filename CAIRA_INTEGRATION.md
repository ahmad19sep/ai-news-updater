# AI Radar ⇄ Caira integration note

**Give this file to Caira (its repo / its AI assistant).** It is the full spec for
connecting **AI Radar Studio** (Ahmad's private news command center) to **Caira**
(the worker production app). It is a **two-way** link:

1. **AI Radar → Caira:** high-scoring (or manually chosen) news stories are pushed to
   Caira as **tasks**, auto-assigned to the worker with the fewest open tasks.
2. **Caira → AI Radar:** when a worker finishes and the owner approves, the parsed
   result flows **back** to AI Radar's "Ready to Post" screen, where Ahmad copies
   each platform's post and publishes from his own accounts.

AI Radar never touches your accounts, social posting, or Supabase directly — it only
calls the three HTTPS endpoints below. Caira already runs on **Vercel functions
(`api/`) + Supabase**, so add `api/tasks.ts`, `api/pending-counts.ts`, `api/ready.ts`.

---

## 0. Important: add a "post" content type in Caira

Caira today is video-centric (Idea → … → Publishing). These AI Radar tasks are
**news posts**, not videos. So:

- Add a **content type / kind** field to cards: `"video"` (existing) and **`"post"`** (new).
- Tasks coming from AI Radar are `kind = "post"`.
- A **post** card's worker view shows: the headline + source link, a **Copy master
  prompt** button, a **Paste AI output** box, the auto-created **Drive folder** link,
  a checklist, and **Submit**. (Same board/stages/assignees/Drive you already have —
  just a card type that's a writing task instead of a video shoot.)

---

## 1. One-time setup in Caira (owner)

1. Create a workspace, e.g. **"AI Radar"**, and invite the two workers (as you already
   invite by email).
2. Note that workspace's **id** and each worker's **member id** (or email) — those are
   the `assignee` values AI Radar uses.
3. Add Vercel env vars (server-side): `RADAR_INGEST_TOKEN` (a long random secret AI
   Radar must send), `RADAR_WORKSPACE_ID` (the AI Radar workspace), and reuse existing
   `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
4. Run the migration in section 6.

---

## 2. Endpoint A — create a task   `POST /api/tasks`

```
POST  https://videoflow-sigma.vercel.app/api/tasks
Header: Authorization: Bearer <RADAR_INGEST_TOKEN>
Content-Type: application/json
```
Body AI Radar sends:
```json
{
  "external_id": "a1b2c3d4e5f6a7b8",   // dedup key: ignore if already imported
  "title":    "OpenAI launches GPT-5.5",
  "url":      "https://techcrunch.com/...",
  "source":   "TechCrunch",
  "summary":  "",
  "category": "New Tools & Models",
  "score":    14,
  "assignee": "<member id/email>",      // may be "" -> Caira/Radar picks the free worker
  "status":   "assigned",
  "prompt":   "...full master prompt (the [[MARKER]] format in section 5)..."
}
```
Caira: verify the bearer token; if `external_id` already imported return `200
{"status":"duplicate"}`; else insert a card in `RADAR_WORKSPACE_ID` with
`kind="post"`, `stage="Idea"`, `assignee`, `master_prompt=prompt`, `source_url=url`,
`news_score=score`, `radar_external_id=external_id`, notes = `source • category •
score` + summary. Return any `2xx`.

> **Fully automatic assignment (important).** AI Radar usually sends `assignee = ""`
> (blank). When it's blank, **Caira must auto-assign the task to whichever current
> workspace member has the FEWEST open tasks** — and just honor a non-empty `assignee`
> when one is given. This way it scales to **any number of workers** with zero config
> on AI Radar's side: add or remove workers in the workspace and balancing keeps
> working automatically. (If `/api/pending-counts` returns every member with a count,
> AI Radar will balance too — but Caira owning the assignment is what makes "however
> many I add" just work.)

## 3. Endpoint B — pending counts   `GET /api/pending-counts`

```
GET  https://videoflow-sigma.vercel.app/api/pending-counts
Header: Authorization: Bearer <RADAR_INGEST_TOKEN>
```
Return open-task count per worker in the AI Radar workspace, so AI Radar gives new
work to the freer person (keys = the same ids returned as `assignee`):
```json
{ "boy1": 3, "boy2": 5 }
```
"Open" = cards in `RADAR_WORKSPACE_ID` not finished (e.g. `stage <> 'Publishing'`).

## 4. Endpoint C — approved work back to Radar   `GET /api/ready`  ← the return path

After a worker pastes the AI output and the **owner approves** it in Caira, expose it
here so AI Radar can pull it into "Ready to Post". Return a JSON **list** of approved,
not-yet-delivered tasks. AI Radar de-dupes by `id`, so you can keep returning approved
items (or drop them after they've been pulled — your choice).

```
GET  https://videoflow-sigma.vercel.app/api/ready
Header: Authorization: Bearer <RADAR_INGEST_TOKEN>
```
```json
[
  {
    "id": "task-123",
    "title": "...", "headline": "...",
    "source": "TechCrunch", "source_url": "https://...",
    "assignee": "boy1", "risk_level": "low",
    "drive_url": "https://drive.google.com/...",
    "article": "...full article...",
    "x_post": "...", "linkedin_post": "...", "facebook_post": "...",
    "instagram_caption": "...", "whatsapp_post": "...",
    "youtube_short_script": "...", "image_prompt": "..."
  }
]
```
These fields come straight from **parsing the worker's pasted AI output** (the
`[[MARKER]]` blocks in section 5) — Caira already plans to parse on submit. Include
the `drive_url` (the card's Drive folder) and `risk_level` so Ahmad can see caution
notes before posting. Any field you can't fill, just omit.

**What AI Radar does with it:** every approved task shows up in Studio's **"Ready to
Post"** tab as a card with a **Copy** button for each platform that has content
(X, LinkedIn, Facebook, Instagram, WhatsApp, YouTube, Article, Image prompt) plus
**Open Drive**, **Open source**, and **✓ Posted**. Adding a platform later = just one
more field name; nothing else changes.

---

## 5. Master-prompt output format (what the worker's AI must return)

The `prompt` AI Radar sends forces GPT/Claude to output exactly this, so Caira can
parse it into the fields above. (English, global audience, facts only.)

```
[[HEADLINE]]            final headline
[[ARTICLE]]             500-700 word article
[[X_POST]]              substantial single X post, link on the last line
[[LINKEDIN_POST]]       professional post, ends "Read more: [ARTICLE LINK]"
[[FACEBOOK_POST]]       engaging post + a question, ends "[ARTICLE LINK]"
[[INSTAGRAM_CAPTION]]   caption + "Full story — link in bio" + hashtags
[[WHATSAPP_POST]]       very concise, ends "[ARTICLE LINK]"
[[YOUTUBE_SHORT_SCRIPT]] 45-60 sec script
[[IMAGE_PROMPT]]        vertical 4:5 news-poster image prompt (headline on the image)
[[FACT_CHECK_NOTES]]    source facts + cautions
[[RISK_LEVEL]]          low / medium / high
```
Map markers → fields: `X_POST→x_post`, `LINKEDIN_POST→linkedin_post`,
`FACEBOOK_POST→facebook_post`, `INSTAGRAM_CAPTION→instagram_caption`,
`WHATSAPP_POST→whatsapp_post`, `YOUTUBE_SHORT_SCRIPT→youtube_short_script`,
`IMAGE_PROMPT→image_prompt`, `FACT_CHECK_NOTES→fact_check_notes`, etc.

---

## 6. Suggested Supabase migration (`stage7.sql`)

```sql
alter table public.videos
  add column if not exists kind              text default 'video',  -- 'video' | 'post'
  add column if not exists master_prompt     text,
  add column if not exists source_url        text,
  add column if not exists news_score        int,
  add column if not exists radar_external_id text,
  -- parsed worker output (filled on submit/approve):
  add column if not exists headline          text,
  add column if not exists article           text,
  add column if not exists x_post            text,
  add column if not exists linkedin_post     text,
  add column if not exists facebook_post     text,
  add column if not exists instagram_caption text,
  add column if not exists whatsapp_post     text,
  add column if not exists youtube_short_script text,
  add column if not exists image_prompt      text,
  add column if not exists fact_check_notes  text,
  add column if not exists risk_level        text,
  add column if not exists radar_delivered   boolean default false; -- set true after /api/ready returns it

create unique index if not exists videos_radar_external_id_key
  on public.videos (radar_external_id) where radar_external_id is not null;
```

## 7. Sample Vercel functions

```ts
// api/_radar.ts
import { createClient } from '@supabase/supabase-js'
export const admin = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!)
export const WS = process.env.RADAR_WORKSPACE_ID!
export function authed(req: Request) {
  const t = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '')
  return !!process.env.RADAR_INGEST_TOKEN && t === process.env.RADAR_INGEST_TOKEN
}
```
```ts
// api/tasks.ts
import { admin, WS, authed } from './_radar'
export default async function handler(req: Request) {
  if (req.method !== 'POST') return new Response('No', { status: 405 })
  if (!authed(req)) return new Response('Unauthorized', { status: 401 })
  const b = await req.json()
  const { data: dup } = await admin.from('videos').select('id').eq('radar_external_id', b.external_id).maybeSingle()
  if (dup) return Response.json({ status: 'duplicate' })
  // FULLY AUTO: if no assignee given, give it to the member with the fewest open tasks.
  let assignee = b.assignee || null
  if (!assignee) {
    const { data: members } = await admin.from('workspace_members').select('user_id,email').eq('workspace_id', WS)
    const { data: open } = await admin.from('videos').select('assignee').eq('workspace_id', WS).neq('stage', 'Publishing')
    const load: Record<string, number> = {}
    for (const m of members || []) load[m.email || m.user_id] = 0
    for (const o of open || []) if (o.assignee) load[o.assignee] = (load[o.assignee] || 0) + 1
    assignee = Object.keys(load).sort((a, c) => load[a] - load[c])[0] || null   // freest member
  }
  const { error } = await admin.from('videos').insert({
    workspace_id: WS, kind: 'post', title: b.title, stage: 'Idea',
    assignee, platform: 'All',
    priority: b.score >= 14 ? 'High' : 'Medium',
    notes: `${b.source} • ${b.category} • score ${b.score}\n${b.summary || ''}`,
    master_prompt: b.prompt, source_url: b.url, news_score: b.score,
    radar_external_id: b.external_id,
  })
  return error ? new Response(error.message, { status: 500 }) : Response.json({ status: 'created' })
}
```
```ts
// api/pending-counts.ts
import { admin, WS, authed } from './_radar'
export default async function handler(req: Request) {
  if (!authed(req)) return new Response('Unauthorized', { status: 401 })
  const { data, error } = await admin.from('videos').select('assignee').eq('workspace_id', WS).neq('stage', 'Publishing')
  if (error) return new Response(error.message, { status: 500 })
  const c: Record<string, number> = {}
  for (const r of data || []) if (r.assignee) c[r.assignee] = (c[r.assignee] || 0) + 1
  return Response.json(c)
}
```
```ts
// api/ready.ts  -> approved tasks back to Radar
import { admin, WS, authed } from './_radar'
const FIELDS = ['id','title','headline','article','x_post','linkedin_post','facebook_post',
  'instagram_caption','whatsapp_post','youtube_short_script','image_prompt','fact_check_notes',
  'risk_level','assignee','source','source_url','drive_url']
export default async function handler(req: Request) {
  if (!authed(req)) return new Response('Unauthorized', { status: 401 })
  // "approved" = however Caira marks owner-approved (e.g. stage 'Review'/'Approved' or an approved flag)
  const { data, error } = await admin.from('videos')
    .select(FIELDS.join(',')).eq('workspace_id', WS).eq('kind', 'post')
    .eq('approved', true).eq('radar_delivered', false)
  if (error) return new Response(error.message, { status: 500 })
  // optional: mark delivered so they aren't returned again (Radar also de-dupes by id)
  const ids = (data || []).map((r: any) => r.id)
  if (ids.length) await admin.from('videos').update({ radar_delivered: true }).in('id', ids)
  return Response.json(data || [])
}
```
(Adjust column/stage/approved names to Caira's real schema — only these files change.)

---

## 8. The full round-trip (what the worker actually does)

1. AI Radar pushes a `post` task → Caira card appears for the free worker.
2. Worker opens it → **Copy master prompt** → runs it in his own GPT/Claude.
3. Worker **pastes the full output** back → Caira parses the `[[MARKER]]` blocks →
   attaches the generated image + the Drive folder → **Submit**.
4. Owner **reviews & approves** in Caira.
5. `GET /api/ready` exposes it → AI Radar stages it → it appears in Studio **Ready to
   Post** with a copy button per platform → Ahmad posts manually from his accounts.

## 9. What AI Radar needs back from you
1. `CAIRA_API_URL` = `https://videoflow-sigma.vercel.app/api`
2. `CAIRA_API_KEY` = the `RADAR_INGEST_TOKEN` value (Ahmad stores it as a GitHub secret)
3. The two workers' **assignee ids/emails** (the keys `/api/pending-counts` returns)

## 10. Notes
- Auth = `Authorization: Bearer <token>` on all three endpoints. Different header? tell Ahmad (one-line change).
- Keep `RADAR_INGEST_TOKEN` + service-role key in Vercel env only, never in code.
- Posting stays 100% manual on Ahmad's side — no social APIs anywhere in this flow.
