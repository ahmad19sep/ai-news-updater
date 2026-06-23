# AI Radar → Caira integration note

**Give this file to Caira (its repo / its AI assistant).** It describes the two
small endpoints Caira needs so **AI Radar Studio** can auto-create work tasks in
Caira, load-balanced across the team.

AI Radar is a separate app (a news command center). When a fresh AI story scores
high enough — or the owner taps "Send to Caira" — AI Radar will create **one card
("video") in a chosen Caira workspace**, assigned to the teammate who currently has
the **fewest open tasks**, carrying a ready-to-use "master prompt" the worker pastes
into their own GPT/Claude. AI Radar never touches your accounts, social posting, or
Supabase directly — it only calls the two HTTPS endpoints below.

Caira already runs on **Vercel serverless functions (`api/`) + Supabase**, so this is
a natural fit: add `api/tasks.ts` and `api/pending-counts.ts`.

---

## 1. One-time setup in Caira (owner)

1. Create a workspace for this, e.g. **"AI Radar"**, and invite the two workers to it.
2. Note that workspace's **id** and each worker's **member id** (or email) — those
   ids are what AI Radar will use as `assignee` values.
3. Add these Vercel env vars (server-side):
   - `RADAR_INGEST_TOKEN` — a long random secret. AI Radar must send the same token.
   - `RADAR_WORKSPACE_ID` — the "AI Radar" workspace id tasks should land in.
   - (reuse existing) `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
4. Run the small migration in section 4 (adds prompt/source/score/dedup columns).

---

## 2. Endpoint A — create a task

```
POST  https://videoflow-sigma.vercel.app/api/tasks
Header: Authorization: Bearer <RADAR_INGEST_TOKEN>
Content-Type: application/json
```

Request body (exactly these fields — this is what AI Radar sends):

```json
{
  "external_id": "a1b2c3d4e5f6a7b8",      // stable id; ignore if already imported (dedup)
  "title":   "OpenAI launches GPT-5.5",
  "url":     "https://techcrunch.com/...", // original source link
  "source":  "TechCrunch",
  "summary": "",
  "category":"New Tools & Models",
  "score":   14,
  "assignee":"<member id or email>",        // already load-balanced by AI Radar
  "status":  "assigned",
  "prompt":  "You are a world-class journalist... [[HEADLINE]] ... [[RISK_LEVEL]]"
}
```

What Caira should do:
- Verify the `Authorization` bearer token equals `RADAR_INGEST_TOKEN` (else `401`).
- If a card with this `external_id` already exists → return `200 {"status":"duplicate"}` (don't create twice).
- Insert a new `videos` row in `RADAR_WORKSPACE_ID`:
  - `title` = `title`
  - `stage` = the first stage (e.g. `"Idea"`) — it's an inbox item the worker pulls in
  - `assignee` = `assignee`
  - `platform` = e.g. `"All"` (these are written posts, not a single platform)
  - `master_prompt` = `prompt`  ← the worker copies this
  - `source_url` = `url`, `news_score` = `score`, `radar_external_id` = `external_id`
  - production notes = a short header: `source • category • score` + `summary`
- Return any `2xx` on success.

In the Caira card UI, the worker should see the title + source link, a **Copy prompt**
button for `master_prompt`, and (your existing) paste-output / submit flow.

## 3. Endpoint B — pending counts (for load balancing)

```
GET   https://videoflow-sigma.vercel.app/api/pending-counts
Header: Authorization: Bearer <RADAR_INGEST_TOKEN>
```

Return how many **open** tasks each worker has in the AI Radar workspace, so AI Radar
can assign new work to the freer person:

```json
{ "<member id or email>": 3, "<member id or email>": 5 }
```

"Open" = cards in `RADAR_WORKSPACE_ID` not yet finished (e.g. `stage <> 'Publishing'`,
or however Caira marks "done"). Key the object by the **same id you expect back as
`assignee`** in endpoint A.

---

## 4. Suggested Supabase migration (`stage7.sql`)

```sql
alter table public.videos
  add column if not exists master_prompt    text,
  add column if not exists source_url       text,
  add column if not exists news_score       int,
  add column if not exists radar_external_id text;

create unique index if not exists videos_radar_external_id_key
  on public.videos (radar_external_id) where radar_external_id is not null;
```

## 5. Sample Vercel functions (TypeScript, using the service role key)

```ts
// api/_radar.ts  (shared helper)
import { createClient } from '@supabase/supabase-js'
export const admin = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!)
export function authed(req: Request) {
  const t = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '')
  return !!process.env.RADAR_INGEST_TOKEN && t === process.env.RADAR_INGEST_TOKEN
}
```

```ts
// api/tasks.ts
import { admin, authed } from './_radar'
export const config = { runtime: 'edge' }   // or node — your choice
export default async function handler(req: Request) {
  if (req.method !== 'POST') return new Response('Method not allowed', { status: 405 })
  if (!authed(req)) return new Response('Unauthorized', { status: 401 })
  const b = await req.json()
  const ws = process.env.RADAR_WORKSPACE_ID!
  // dedup
  const { data: dup } = await admin.from('videos')
    .select('id').eq('radar_external_id', b.external_id).maybeSingle()
  if (dup) return Response.json({ status: 'duplicate' })
  const { error } = await admin.from('videos').insert({
    workspace_id: ws,
    title: b.title,
    stage: 'Idea',
    assignee: b.assignee || null,
    platform: 'All',
    priority: (b.score >= 14 ? 'High' : 'Medium'),
    notes: `${b.source} • ${b.category} • score ${b.score}\n${b.summary || ''}`,
    master_prompt: b.prompt,
    source_url: b.url,
    news_score: b.score,
    radar_external_id: b.external_id,
  })
  if (error) return new Response(error.message, { status: 500 })
  return Response.json({ status: 'created' })
}
```

```ts
// api/pending-counts.ts
import { admin, authed } from './_radar'
export const config = { runtime: 'edge' }
export default async function handler(req: Request) {
  if (!authed(req)) return new Response('Unauthorized', { status: 401 })
  const ws = process.env.RADAR_WORKSPACE_ID!
  const { data, error } = await admin.from('videos')
    .select('assignee').eq('workspace_id', ws).neq('stage', 'Publishing')
  if (error) return new Response(error.message, { status: 500 })
  const counts: Record<string, number> = {}
  for (const r of data || []) if (r.assignee) counts[r.assignee] = (counts[r.assignee] || 0) + 1
  return Response.json(counts)
}
```

(Adjust column/stage names to Caira's real schema — only these two files change.)

---

## 6. What AI Radar needs back from you

Give Ahmad these three so he can flip it on in AI Radar:

1. **`CAIRA_API_URL`** = `https://videoflow-sigma.vercel.app/api`
2. **`CAIRA_API_KEY`** = the `RADAR_INGEST_TOKEN` value (kept as a GitHub secret).
3. **Editor ids** = the two workers' `assignee` ids/emails (the same keys returned by
   `/api/pending-counts`).

That's it. AI Radar handles scoring, choosing the freer worker, building the prompt,
and not sending the same story twice. Caira just receives the card and runs its
normal pipeline.

## 7. Notes
- Auth header is `Authorization: Bearer <token>`. If Caira prefers a different header
  (e.g. `X-API-Key`), tell Ahmad — it's a one-line change on the AI Radar side.
- Keep `RADAR_INGEST_TOKEN` and the service-role key in Vercel env only, never in code.
- These tasks are written content (article + X/LinkedIn/IG/YouTube/image prompt), so a
  single Caira card with `platform: All` is the natural fit; the worker produces all
  outputs from the one master prompt.
