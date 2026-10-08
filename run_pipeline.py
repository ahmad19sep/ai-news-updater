"""AI x Ahmad content pipeline - runs the small agents in order.

  python run_pipeline.py              FREE mode (default): rules triage + fetch articles for the
                                      top candidates; you write in the Studio with your own
                                      Claude/ChatGPT subscription. No API key, no cost.
  python run_pipeline.py --mode api   the Claude agents triage, draft and verify (costs ~$0.30)
  python run_pipeline.py --triage     only score new stories into candidates
  python run_pipeline.py --draft      only write drafts for the best undrafted candidates (api mode)
  python run_pipeline.py --draft --ids abc123,def456   draft these candidates (Studio shortlist)
  python run_pipeline.py --limit 3    how many drafts this run (default config.PIPELINE_DRAFTS_PER_RUN)
  python run_pipeline.py --dry-run    show what would run, no model calls, no writes
  python run_pipeline.py --status     print what is in the store
  python run_pipeline.py --notify     push "N drafts ready" to your phone at the end

Nothing here posts anything. Drafts land in the Studio for you to edit and post.
API mode needs ANTHROPIC_API_KEY (or anthropic_key.txt); free mode needs nothing.
"""

import argparse
import sys
import time

import config
import scoring
from agents import angle, enrich, sources, triage, verify, writer
from agents.llm import LLM, BudgetExceeded
from agents.store import Store, now_iso

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def log(msg=""):
    print(msg, flush=True)


# ---------------------------------------------------------------- stages
def stage_triage(llm, store, dry_run=False, mode="free"):
    conn = sources.open_db()
    stories = sources.new_stories(conn, store)
    hot = scoring.rising_terms(scoring.compute_trends(conn))[:15] if stories else []
    conn.close()
    log(f"\n[1/5] TRIAGE ({mode})  {len(stories)} new stories (last {config.PIPELINE_TRIAGE_LOOKBACK_HOURS}h)")
    if not stories:
        return {"scored": 0, "kept": 0, "dismissed": 0, "duplicates": 0}
    if dry_run:
        for s in stories[:15]:
            log(f"   - {s['title'][:80]}  ({s['source']})")
        if len(stories) > 15:
            log(f"   ... and {len(stories) - 15} more")
        return {"scored": 0, "kept": 0, "dismissed": 0, "duplicates": 0, "dry_run": len(stories)}
    r = (triage.run_rules(store, stories, hot, log=log) if mode == "free"
         else triage.run(llm, store, stories, log=log))
    sources.remember_triaged(store, r.pop("ids", []))
    store.flush()
    log(f"      scored {r['scored']}  ->  {r['kept']} kept, {r['dismissed']} dismissed, {r['duplicates']} duplicates")
    return r


def stage_prepare(store, limit, dry_run=False):
    """Free mode: fetch the article for the best candidates so the Studio's
    prompt carries real source text instead of a headline."""
    cands = store.all("candidates")
    pool = [c for c in cands.values() if c.get("status") in ("new", "shortlisted")
            and not (store.get("sources", c["id"]) or {}).get("fetched_at")]
    pool.sort(key=lambda c: (c.get("status") != "shortlisted", -int(c.get("score", 0))))
    picked = [c["id"] for c in pool[:limit]]
    log(f"\n[2/2] PREPARE  fetching articles for {len(picked)} candidates")
    if not picked or dry_run:
        return {"prepared": 0}
    r = enrich.run(store, picked, log=log)
    store.flush()
    return {"prepared": r["enriched"], "thin": r["thin"]}


def pick_candidates(store, limit, ids=None):
    """Shortlisted by you first, then highest score; never something already drafted."""
    cands = store.all("candidates")
    drafted = {d.get("candidate_id") for d in store.all("drafts").values()}
    if ids:
        return [i for i in ids if i in cands and i not in drafted]
    pool = [c for c in cands.values()
            if c.get("status") in ("new", "shortlisted") and c["id"] not in drafted
            and not c.get("skip")]
    pool.sort(key=lambda c: (c.get("status") != "shortlisted", -int(c.get("score", 0)),
                             c.get("published") or ""), reverse=False)
    return [c["id"] for c in pool[:limit]]


def stage_draft(llm, store, limit, ids=None, dry_run=False, use_judge=True):
    picked = pick_candidates(store, limit, ids)
    log(f"\n[2/5] SELECT  {len(picked)} candidates to draft")
    for i in picked:
        c = store.get("candidates", i)
        log(f"   {c.get('score', 0):>2}  {c.get('topic', ''):<16} {c['title'][:70]}")
    if not picked or dry_run:
        return {"picked": len(picked), "drafts": 0, "skipped": 0, "failed": 0}

    log("\n[3/5] ENRICH  fetching articles")
    need = [i for i in picked if not (store.get("sources", i) or {}).get("fetched_at")]
    enrich.run(store, need, log=log)
    store.flush()

    recent = store.published_history()
    settings = store.get("settings", "profile") or {}
    made = skipped = failed = 0
    for i in picked:
        c = store.get("candidates", i)
        pack = store.get("sources", i) or {}
        log(f"\n[4/5] ANGLE+WRITE  {c['title'][:70]}")
        try:
            a = angle.run(llm, store, i, log=log)
            if a.get("skip"):
                store.patch("candidates", i, status="skipped")
                skipped += 1
                continue
            d = writer.run(llm, store, i, note=settings.get("personal_note", ""), recent=recent, log=log)
            if d.get("status") == "skip" or not d.get("post"):
                store.patch("candidates", i, status="skipped", skip_reason=d.get("review_notes", ""))
                skipped += 1
                continue
            log("[5/5] VERIFY")
            v = verify.run(llm, d, pack, log=log, use_llm=use_judge)
            if v["verdict"] == "fail":
                fixes = verify.fix_list(v)
                log("      rewriting once: " + "; ".join(fixes)[:160])
                d2 = writer.run(llm, store, i, note=settings.get("personal_note", ""), recent=recent,
                                log=log, fix_issues=fixes, previous=d["post"])
                if d2.get("post"):
                    v2 = verify.run(llm, d2, pack, log=log, use_llm=use_judge)
                    if v2["verdict"] != "fail" or len(v2["issues"]) <= len(v["issues"]):
                        d, v = d2, v2
            store.put("drafts", i, {
                "candidate_id": i, "title": c["title"], "url": pack.get("url") or c["url"], "source": c["source"],
                "topic": c.get("topic"), "score": c.get("score"),
                "angle": d.get("angle"), "format": (d.get("angle") or {}).get("format", "text"),
                "post": d.get("post", ""), "first_comment": d.get("first_comment", ""),
                "hashtags": d.get("hashtags", []), "claims": d.get("claims", []),
                "review_notes": d.get("review_notes", ""),
                "verify": {"verdict": v["verdict"], "issues": v["issues"], "hook_len": v.get("hook_len"),
                           "chars": v.get("chars"), "judge": v.get("judge")},
                "status": "draft", "created": now_iso(), "channel": "linkedin",
                "thin_source": bool(pack.get("thin")),
            })
            store.patch("candidates", i, status="drafted")
            made += 1
        except BudgetExceeded as e:
            log(f"  [!] {e} — stopping")
            break
        except Exception as e:
            log(f"  [!] failed: {type(e).__name__}: {str(e)[:200]}")
            failed += 1
        finally:
            store.flush()
    return {"picked": len(picked), "drafts": made, "skipped": skipped, "failed": failed}


def prune(store, days=21):
    """Keep the store small: drop stale candidates nobody acted on."""
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    keep = {"shortlisted", "drafted", "published"}
    gone = [c["id"] for c in store.all("candidates").values()
            if c.get("status") not in keep and (c.get("created") or c.get("updated") or "") < cutoff]
    for i in gone:
        store.delete("candidates", i)
        if i in store.all("sources") and i not in store.all("drafts"):
            store.delete("sources", i)
    for i in [i for i in store.all("sources") if i not in store.all("candidates") and i not in store.all("drafts")]:
        store.delete("sources", i)
    return len(gone)


def print_status(store):
    cands = store.all("candidates").values()
    drafts = store.all("drafts").values()
    by = {}
    for c in cands:
        by[c.get("status", "?")] = by.get(c.get("status", "?"), 0) + 1
    log(f"store: {store.backend}  key: {store.key[:8]}…")
    log(f"candidates: {len(list(cands))}  " + "  ".join(f"{k}={v}" for k, v in sorted(by.items())))
    dby = {}
    for d in drafts:
        dby[d.get("status", "?")] = dby.get(d.get("status", "?"), 0) + 1
    log(f"drafts: {len(list(drafts))}  " + "  ".join(f"{k}={v}" for k, v in sorted(dby.items())))
    runs = sorted(store.all("runs").values(), key=lambda r: r.get("ts", ""))[-5:]
    for r in runs:
        log(f"  run {r.get('ts', '')[:16]}  ${r.get('cost', {}).get('usd', 0):.3f}  {r.get('summary', '')}")


def notify(n_drafts):
    if n_drafts <= 0 or not config.NTFY_TOPIC:
        return
    import notifier
    notifier.send("AI x Ahmad - drafts ready",
                  f"{n_drafts} LinkedIn draft{'s' if n_drafts != 1 else ''} waiting for your review.",
                  click=config.DASHBOARD_URL, tags="memo")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--triage", action="store_true")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--ids", default="", help="comma-separated candidate ids to draft")
    p.add_argument("--limit", type=int, default=config.PIPELINE_DRAFTS_PER_RUN)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-judge", action="store_true", help="skip the LLM fact-check judge (checks still run)")
    p.add_argument("--status", action="store_true")
    p.add_argument("--notify", action="store_true")
    p.add_argument("--budget", type=float, default=None, help="USD cap for this run")
    p.add_argument("--mode", choices=["free", "api"], default=config.PIPELINE_MODE)
    p.add_argument("--store", choices=["local", "firebase"], default=None,
                   help="Explicit state backend; local matches studio_server.py even with legacy Firebase configured")
    args = p.parse_args(argv)

    store = Store(backend=args.store)
    if args.status:
        print_status(store)
        return 0
    do_triage = args.triage or not args.draft
    do_draft = args.draft or not args.triage

    llm = LLM(budget_usd=args.budget)
    t0 = time.time()
    log(f"AI x Ahmad pipeline  |  mode: {args.mode}  |  store: {store.backend}"
        + (f"  |  budget ${llm.budget:.2f}" if args.mode == "api" else "  |  no API cost")
        + ("  |  DRY RUN" if args.dry_run else ""))
    summary = {}
    if do_triage:
        summary["triage"] = stage_triage(llm, store, dry_run=args.dry_run, mode=args.mode)
    if args.mode == "free":
        if args.draft:
            log("\n[!] --draft needs --mode api (free mode: write in the Studio with your subscription)")
        elif do_draft:
            summary["draft"] = stage_prepare(store, max(args.limit, config.PIPELINE_FREE_ENRICH),
                                             dry_run=args.dry_run)
    elif do_draft:
        ids = [x.strip() for x in args.ids.split(",") if x.strip()] or None
        summary["draft"] = stage_draft(llm, store, args.limit, ids=ids, dry_run=args.dry_run,
                                       use_judge=not args.no_judge)

    if not args.dry_run:
        pruned = prune(store)
        if pruned:
            log(f"\npruned {pruned} stale candidates")
    cost = llm.summary()
    parts = {**summary.get("triage", {}), **summary.get("draft", {})}
    line = "  ".join(f"{k}:{v}" for k, v in parts.items() if k != "ids") or "nothing new"
    if not args.dry_run:
        store.add_run({"summary": line, "cost": cost, "triage": summary.get("triage"),
                       "draft": summary.get("draft"), "seconds": round(time.time() - t0)})
        store.flush()
    log(f"\ndone in {time.time() - t0:.0f}s  |  cost ${cost['usd']:.4f} over {cost['calls']} calls"
        + "".join(f"\n   {r:<7} {v['calls']:>2} calls  {v['tokens_in']:>7} in  {v['tokens_out']:>6} out  ${v['usd']:.4f}"
                  for r, v in cost["by_role"].items()))
    n = summary.get("draft", {}).get("drafts", 0)
    if n:
        log(f"\n{n} draft(s) ready in the Studio -> {config.DASHBOARD_URL}")
    elif args.mode == "free" and summary.get("triage", {}).get("kept"):
        log(f"\n{summary['triage']['kept']} new ideas in the Studio -> {config.DASHBOARD_URL}  (Ideas -> Write)")
    if args.notify:
        notify(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
