# Creator Studio implementation checkpoint

Updated 8 October 2026 (Asia/Karachi). Branch: `feat/creator-studio-foundation`; baseline: `888242a`. This checkpoint follows the supplied blueprint's Phase 0, then the first safe LinkedIn-focused Phase 1 slice. No deployment, production database migration, paid provider calls or social posting is authorized by this checkpoint.

## Phase status

| Phase | Status | Gate / next dependency |
| --- | --- | --- |
| 0: inventory and baseline | Complete | [BASELINE.md](BASELINE.md) contains code/data map, capability targets, risks, passing existing test baseline and migration/rollback baseline. [ADR-001.md](ADR-001.md) records the local-first dependency decision. |
| 1: private state and contracts | Partial; first local slice implemented and tested | Local contracts, private file/revisions, migration/backup and authenticated loopback editing pass focused tests and generated-Studio integration. The combined backend, all six Node suites, generated build and real-browser manual flow pass locally. Offline CI is configured; hosted CI results are recorded separately when available. Deployed owner UID authentication/rules, live migration and legacy browser-cache reconciliation remain outside the proven gate. |
| 2–7 | Not started | Follow the recorded sequence after Phase 1 acceptance. No public or legacy redesign in the foundation slice. |

## Current / proposed / implemented capabilities

| Capability | Existing behavior | Target | Implementation checkpoint |
| --- | --- | --- | --- |
| Shared factual core | Candidate and selected legacy source excerpt | Versioned source, story, evidence and content variant contracts | Typed schema-v1 source/document revision/span/claim/evidence/story/variant/approval contracts pass 21 tests; the runtime pipeline is not fully migrated |
| Local private state | `docs/pipeline.json` fallback | Ignored private path, atomic writes, revisions and backups | Private repository/migration implemented and focused tests pass; file locks and conditional writes merge independent records, stale edits retained, deleted-ID revisions cannot be reused |
| Local browser editing | Direct Firebase REST or public JSON with browser overrides | Authenticated same-origin private API, visible conflicts | Loopback Flask bridge and separate transport implemented; offline/conflict/recovery states and session-expiry DOM clearing tested; deployed Firebase behavior unchanged |
| Owner authorization | Passcode screen gate/derived path | Denied unauthorized private reads/writes | Local session/CSRF/Host/Origin boundary passes 21 API tests; owner UID/Firebase rules and hosted service remain unverified |
| State migration | No versioned migration | Dry run, count/integrity report, stable ID map, backup and rollback | File-only dry run/apply/backups/count verification implemented; malformed/conflicting imports abort; tombstones preserve local deletion; no live data touched |
| Manual prompting/export | Copy writer/check/image prompt, paste answer, edit/copy post/comment | Preserve throughout rollout, then shared strict prompt import policy | Existing workflow retained; prompt parity remains Phase 4 |
| Approval and publishing | General status mutation, manual post and owner mark | Backend revision-bound review/approval, explicit confirmation origin | Local API guards transitions and owner-manual approval/current-content hash, invalidates material edits/source associations, and records owner-manual confirmation. Checks remain the limited deterministic screen; stronger factual verification and durable delivery are incomplete. Static legacy behavior remains unchanged. |
| Evidence checking | Numeric presence and optional LLM review | Supported context/units/time/entity, caveats, claim-to-span traceability | Remains Phase 3/4 work |
| Image assets | Prompt export | No-image/import/template/provenance and revision-bound asset review | Remains Phase 5 work; prompt is not an image |
| Scheduling | Browser/device timezone and manual slots | Explicit IANA timezone, reminders, durable jobs if authorized | Local approval/future-offset checks and locked slot collision prevention are tested. IANA timezone preferences, reminders and durable jobs remain Phase 6 work; no exact-time delivery promise |
| Paid integrations/budgets | Optional API mode and per-run counter | Server secrets and durable reservations/reconciliation | No provider activation; daily cap remains unresolved |
| Future platforms | Product plans | Capability registry and isolated contract-tested alternate adapter | A nonproduction `test_caption` adapter consumes `StoryBrief`; Urdu/Roman Urdu workflows and active account/publishing capabilities remain unconfigured/unverified |

## Changed files

| Boundary | Files / purpose |
| --- | --- |
| Shared contracts | `creator/__init__.py`, `creator/contracts.py`, `tests/test_creator_contracts.py`: strict versioned codecs, evidence provenance, content fingerprints and additive legacy preview |
| Private repository and CLI | `agents/store.py`, `migrate_studio_state.py`, `run_pipeline.py`, `tests/test_private_store.py`, `tests/test_pipeline_cli.py`: private path/revisions/locks/tombstones, explicit migration and backend selection |
| Local authenticated server | `studio_server.py`, `tests/test_studio_server.py`: loopback session/CSRF/API, conditional editing and owner-manual transition guards |
| Studio integration | `studio/private-state.js`, `studio/app.js`, `studio/app.css`, `studio/index.html`, `generate_studio.py`, regenerated `docs/studio.html`, `private_studio_test.js`, `private_ui_test.js`: private transport, lock/logout/recovery/conflict UI and source build |
| Configuration/automation | `.env.example`, `.gitignore`, `README.md`, `.github/workflows/test.yml`, `fetch.yml`, `pipeline.yml`, `ui_test.js`: safe setup notes, ignored state, offline CI and public-artifact safeguards / compatible legacy test fixture |
| Architecture checkpoint | `documentation/creator-studio/BASELINE.md`, `ADR-001.md`, `PROGRESS.md`: baseline, accepted boundary and precise phased status |

Public/legacy generator source is preserved. Ignored `.tmp-studio-preview/` integration fixtures/reports use synthetic data and are not application artifacts.

## Validation record

| Stage | Command / check | Outcome |
| --- | --- | --- |
| Existing Python baseline | `python -m unittest tests.test_pipeline tests.test_fetcher test_agent_ai_radar test_agent_discovery` | 64 passed, reported by root agent |
| Existing Studio UI baseline | `node studio_test.js` | Exit 0, all checks passed, reported by root agent |
| Existing public UI baseline | `node public_test.js` | Exit 0, all checks passed, reported by root agent |
| Contract tests | `python -m unittest tests.test_creator_contracts` | 21 passed, reported by contract agent; combined contracts + legacy pipeline: 46 passed |
| Private repository/migration tests | `python -m unittest tests.test_private_store` | 40 run: 39 passed, 1 skipped (Windows account lacks symlink privileges); reported by repository agent. Source edits/deletions, late-created dependent drafts, stale source reads, changed source associations, merged slot validation and shared configured paths are covered. |
| Local API tests | `python -m unittest tests.test_studio_server` | 21 passed; includes expired signed sessions, manual creation, source deletion, repeat publication confirmation and explicit deleted-ID reconciliation |
| Private browser transport tests | `node private_studio_test.js` | 19 passed; built-in Node VM, no provider/network, including locked debounce capture and deleted-ID reconciliation |
| Private generated-Studio integration | `node private_ui_test.js` | 20 checks passed, zero browser exceptions; all endpoint traffic mocked, including newer keystrokes after earlier acknowledgements and expiry before debounce |
| Combined backend | `python -m unittest discover` | 147 run: 146 passed, 1 Windows symlink privilege skip |
| Existing Node regressions | `node public_test.js`, `node smoke_test.js`, `node ui_test.js`, `node studio_test.js` | All pass; CI wrapper suppresses external DOM resources |
| Real browser | Edge, synthetic private server, 1440/390/320px | Login/edit/approval/schedule/invalidation/logout pass at each width; 9 screenshots, no horizontal overflow or runtime exceptions. Ignored artifacts: `.tmp-studio-preview/private-shots/` |
| Automation | Offline CI YAML/Bash and staging guard checks | Python Ubuntu/Windows matrix plus all six Node suites configured; public state exclusion verified using a temporary Git repository |
| Generator/build diffs | `python generate_studio.py`, `git diff --check` | Studio rebuilt from source; public/legacy generated pages and `news.db` have no changes; whitespace checks pass |

Live Firebase rules/authentication, social publishing, provider charges and live account permissions are deliberately untested. No production certification is claimed. The private DOM smoke check verifies login, all eight routes, manual source prompt/post copying, private Settings, pending edit export, blocked sign-out with unsynced edits, confirmed logout and expiry clearing. The separate real-browser run establishes reflow for the three sampled screens/widths; full contrast/accessibility certification and future evidence/asset/publishing workflows remain unproven.

## Local development interface

Configure `STUDIO_LOCAL_PASSCODE` (at least eight characters) in the process environment (the existing local `SITE_PASSCODE`/secret-file fallback is also supported), then run:

```text
python studio_server.py --port 8765
```

The server binds only to `127.0.0.1`; open `http://127.0.0.1:8765`. `STUDIO_STATE_PATH` is shared by the local repository, server and migration defaults; destinations under public `docs/` are rejected. `STUDIO_SESSION_SECRET` is optional and must have at least 32 characters when configured; otherwise restarting the server resets sessions through a fresh random secret. Session lifetime is configured to eight hours. Do not copy a passcode or session secret into tracked configuration or generated HTML.

Use an explicit local backend for the pipeline, even when an existing Firebase configuration is present:

```text
python run_pipeline.py --store local --status
```

Private-mode copied pipeline commands include `--store local`. The CLI also accepts `--store firebase`; omitting the option retains legacy automatic selection. These options choose state storage, not provider activation or publishing authorization. `--status` is read-only and makes no provider or Firebase request when local storage is selected.

| Endpoint | Request / result |
| --- | --- |
| `GET /api/session` | Reports authentication; returns a CSRF token only when signed in |
| `POST /api/session` | `{ "passcode": "…" }` creates the owner session |
| `DELETE /api/session` | Requires `X-Studio-CSRF`; signs out |
| `GET /api/state` | Authenticated private state snapshot |
| `PATCH /api/records/<collection>/<id>` | `{ "expected_revision": 0, "fields": { } }` plus `X-Studio-CSRF`; stale writes conflict |

This is the local editing boundary. The deployed static site's legacy Firebase configuration/rules have not been migrated or verified. The revised private local fallback is not exposed as a static site artifact.

## Workflow safeguards

`.github/workflows/test.yml` adds offline Python checks on Ubuntu/Windows and all five existing/new DOM/transport suites with source builds. This workflow has been checked locally; no hosted GitHub Actions run is claimed.

The API-draft workflow no longer commits private state, uses read-only repository permission and requires its existing legacy Firebase destination before paid drafting. This is compatibility plumbing, not owner-authenticated Firebase deployment. The hourly workflow rejects tracked/generated/staged `docs/pipeline.json` and excludes it in staging/rebase handling. No workflow was activated and no paid calls were made during implementation.

## Explicit local migration

The file-only CLI is dry-run by default. Replace the example source path with an existing legacy state export; no source file is fabricated or downloaded from Firebase:

```text
python migrate_studio_state.py --source .\legacy-export.json
python migrate_studio_state.py --source .\legacy-export.json --apply
```

`--target` selects an explicit private destination. The report provides the input hash, per-collection counts, preserved-ID result, backup paths and rollback instructions without printing draft contents. Conflicting target records abort; unrelated records remain. Repeat imports must not overwrite newer edits or resurrect IDs deleted in private state. Schema-v1 `_deleted_revisions` records deletion counters outside the five content collections.

`--apply` creates private source/target backups beside the target before a change. The source stays in place unless `--remove-source` is supplied with `--apply`; source removal follows integrity verification. If the source is a public artifact, separately resolve its existing exposure/history—moving a file does not revoke prior access or remove repository history. No tracked `docs/pipeline.json` existed at this baseline.

For rollback, stop the local Studio/writers and follow the report's exact backup-to-target instructions; if the target was newly created, remove only that target after verifying its absolute path. Apply failures after backups also return the backup paths and rollback instructions. Preserve source exports and backups until counts/links/owner work are reconciled. There is no automatic deployed migration or rollback subcommand.

`creator.contracts.convert_legacy_state` is a separate pure additive preview: it retains exact legacy JSON, creates source/evidence/story/variant objects plus an ID map, and sets inherited evidence to `not_checked`. It does not write files or upgrade the live collector/writer into a verified evidence pipeline. The authoritative compatibility store retains its five collections for this slice.

## Resume and rollback

1. Preserve this tested local checkpoint and monitor the new offline CI. No live state migration, paid calls, social posting or deployment occurred.
2. Complete Phase 1 by evaluating owner-scoped Firebase auth/rules and one authenticated hosting boundary; use emulators/mocks before any separately authorized live migration. Add explicit legacy browser cache import/reconciliation and concurrent-device tests. New private-cache logout/recovery behavior is tested; the old cache is preserved and not silently imported. Production credentials must be configured securely outside chat/repository.
3. Begin Phase 2 UI tokens/components after that gate; source evidence/retrieval and prompt/verification work follows in Phases 3–4.

Preserve local source exports and ignored private backups. A code rollback must use a compatible private schema reader; it must not restore unsafe public-draft writes or delete owner caches.
