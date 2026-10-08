"""Pipeline tests with a fake Claude: no network, no key, no cost.

  python -m unittest tests.test_pipeline
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import config  # noqa: E402
from agents import angle, enrich, sources, store as storemod, triage, verify, writer  # noqa: E402
from agents.llm import LLM  # noqa: E402

ARTICLE = """<html><head><title>x</title><script>var a=1;</script></head><body>
<nav>Home Subscribe Sign in</nav>
<article>
<p>Acme Health said on Tuesday that its new triage assistant cut average waiting time by 32% across 4 clinics in Lahore.</p>
<p>"We did not automate the doctor, we automated the paperwork," said Dr. Sara Khan, the program lead.</p>
<p>The pilot ran for 6 months and covered 12,400 patient visits. Acme says the tool costs about $40 per clinician per month.</p>
<p>Critics note the study was not independently reviewed.</p>
</article>
<footer>Copyright</footer></body></html>"""


class FakeClient:
    """Mimics the two SDK call shapes the LLM wrapper uses and answers per role."""

    def __init__(self, answers):
        self.answers = answers          # role -> dict or callable(user_text) -> dict
        self.calls = []
        self.messages = SimpleNamespace(create=self._create)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        model = kw["model"]
        # three roles share one model, so the role is recognised from its system prompt
        sys_text = kw["system"][0]["text"]
        role = ("triage" if "triage editor" in sys_text else "angle" if "angle editor" in sys_text
                else "verify" if "fact-checker" in sys_text else "writer")
        assert role in self.answers, f"unexpected role {role}"
        user = kw["messages"][0]["content"]
        self.calls.append((role, kw))
        ans = self.answers[role]
        data = ans(user) if callable(ans) else ans
        return SimpleNamespace(
            stop_reason="end_turn", model=model,
            content=[SimpleNamespace(type="text", text=json.dumps(data))],
            usage=SimpleNamespace(input_tokens=1000, output_tokens=300,
                                  cache_read_input_tokens=0, cache_creation_input_tokens=0))


def triage_answer(user):
    ids = [line.split("]")[0][1:] for line in user.splitlines() if line.startswith("[")]
    items = []
    for n, i in enumerate(ids):
        items.append({"id": i, "score": 9 - n, "topic": "health", "urgency": "this_week",
                      "reason": "useful", "angle_hint": "paperwork not doctors"})
    return {"items": items}


GOOD_POST = ("A clinic group in Lahore cut waiting time by 32%. The AI never touched a diagnosis.\n\n"
             "Acme Health says its triage assistant handled intake paperwork across 4 clinics for 6 months, "
             "covering 12,400 visits. The doctors still made every call.\n\n"
             "The lead, Dr. Sara Khan, put it plainly: they automated the paperwork, not the doctor.\n\n"
             "I think that is the pattern worth copying. Before you look for an AI that replaces an expert, "
             "look for the hour of typing around the expert. Acme quotes about $40 per clinician per month, "
             "which is cheaper than the time it saves if the numbers hold.\n\n"
             "One caveat the coverage mentions: the study was not independently reviewed. Worth watching, not "
             "worth copying blindly.")

ANSWERS = {
    "triage": triage_answer,
    "angle": {"angles": [{"angle": "Automate paperwork around the expert, not the expert", "hook": "A clinic cut waiting time by 32%. The AI never touched a diagnosis.",
                          "format": "text", "mode": "insight", "why": "outcome reported", "supported_by": ["32% across 4 clinics"]}],
              "recommended": 0, "skip": False, "skip_reason": ""},
    "writer": {"post": GOOD_POST, "first_comment": "Source: Acme Health announcement - https://example.com/acme",
               "hashtags": ["#ai", "#healthcare"],
               "claims": [{"claim": "32% cut", "support": "cut average waiting time by 32%", "kind": "reported_fact"}],
               "review_notes": "the 'pattern worth copying' paragraph is my interpretation", "status": "draft"},
    "verify": {"unsupported_claims": [], "misattributed": [], "ai_smell": 2, "specificity": 4, "fixes": [], "summary": "ok"},
}


def make_db(path, n=3):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT, url TEXT UNIQUE, links TEXT DEFAULT '[]',
          source TEXT, pillar INTEGER, published TEXT, fetched TEXT, notified INTEGER DEFAULT 0,
          done INTEGER DEFAULT 0, upvotes INTEGER DEFAULT 0, comments INTEGER DEFAULT 0, summary TEXT DEFAULT '');
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
    """)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    titles = ["Lahore clinics cut waiting time with AI triage assistant",
              "OpenAI drops price of its smallest model for API users",
              "New study: farmers using AI irrigation timing saved water"]
    for k in range(n):
        conn.execute("INSERT INTO items (title,url,source,pillar,published,fetched,summary) VALUES (?,?,?,?,?,?,?)",
                     (titles[k % 3], f"https://example.com/acme{k}", "Acme News", 8, now, now,
                      "Acme Health says waiting time fell 32%."))
    conn.commit()
    conn.close()


class StoreTests(unittest.TestCase):
    def test_local_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "pipeline.json")
            s = storemod.Store(backend="local", local_path=path, key="k")
            s.put("candidates", "a1", {"title": "t", "status": "new"})
            s.patch("candidates", "a1", status="shortlisted")
            self.assertEqual(s.flush(), 1)
            s2 = storemod.Store(backend="local", local_path=path, key="k")
            self.assertEqual(s2.get("candidates", "a1")["status"], "shortlisted")
            self.assertIn("updated", s2.get("candidates", "a1"))

    def test_published_history_from_drafts(self):
        with tempfile.TemporaryDirectory() as d:
            s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
            s.put("drafts", "x", {"title": "Old post", "url": "u", "status": "published", "post": "Hook line\nbody"})
            s.put("drafts", "y", {"title": "Draft", "url": "u2", "status": "draft", "post": "no"})
            h = s.published_history()
            self.assertEqual([x["title"] for x in h], ["Old post"])
            self.assertEqual(h[0]["hook"], "Hook line")


class EnrichTests(unittest.TestCase):
    def test_extract_text_prefers_article_and_drops_chrome(self):
        text = enrich.extract_text(ARTICLE)
        self.assertIn("32% across 4 clinics", text)
        self.assertNotIn("Subscribe", text)
        self.assertNotIn("var a=1", text)
        self.assertNotIn("Copyright", text)

    def test_numbers_and_quotes(self):
        text = enrich.extract_text(ARTICLE)
        nums = enrich.numbers_in(text)
        self.assertIn("32%", nums)
        self.assertIn("12400", nums)
        self.assertIn("40", nums)
        self.assertTrue(any("automated the paperwork" in q for q in enrich.quotes_in(text)))

    def test_resolve_url_passes_normal_links_and_decodes_google_news(self):
        self.assertEqual(enrich.resolve_url("https://example.com/a"), "https://example.com/a")

        class FakeResp:
            def __init__(self, text): self.text = text

        class FakeRequests:
            def get(self, url, **kw):
                assert "news.google.com/articles/ABC" in url
                return FakeResp('<c-wiz data-n-a-ts="3" data-n-a-sg="SIG"></c-wiz>')

            def post(self, url, data=None, **kw):
                assert "batchexecute" in url and "ABC" in data and "SIG" in data
                return FakeResp(")]}'\n\n" + json.dumps([["wrb.fr", "Fbv4je", json.dumps(["garturlres", "https://pub.example/story"])]]))

        real = enrich.requests
        enrich.requests = FakeRequests()
        try:
            self.assertEqual(enrich.resolve_url("https://news.google.com/rss/articles/ABC?oc=5"), "https://pub.example/story")
        finally:
            enrich.requests = real

    def test_run_tries_alternate_links_and_records_resolved_url(self):
        with tempfile.TemporaryDirectory() as d:
            s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
            s.put("candidates", "c1", {"title": "T", "url": "https://news.google.com/rss/articles/X", "source": "s",
                                       "links": ["https://alt.example/full"]})
            long_article = ARTICLE.replace("</article>", "<p>" + "More reported detail from the alternate source. " * 12 + "</p></article>")
            pages = {"https://pub.example/empty": "<html><body><p>short</p></body></html>", "https://alt.example/full": long_article}
            r = enrich.run(s, ["c1"], log=lambda *a: None, fetcher=lambda u: pages[u],
                           resolver=lambda u: "https://pub.example/empty" if "google" in u else u)
            self.assertEqual(r["thin"], 0)
            pack = s.get("sources", "c1")
            self.assertEqual(pack["url"], "https://alt.example/full")
            self.assertEqual(pack["original_url"], "https://news.google.com/rss/articles/X")
            self.assertEqual(pack["source"], "s")
            self.assertEqual(s.get("candidates", "c1")["resolved_url"], "https://alt.example/full")

    def test_run_uses_database_alternate_objects_after_primary_failure(self):
        import database

        with tempfile.TemporaryDirectory() as d:
            db_path = os.path.join(d, "news.db")
            make_db(db_path, n=1)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
            try:
                database.add_link_to_item(conn, 1, "https://alt.example/blocked", "Blocked News")
                database.add_link_to_item(conn, 1, "https://alt.example/full", "Alternate News")
                candidate = sources.new_stories(conn, s)[0]
            finally:
                conn.close()
            self.assertEqual(candidate["links"][0], {
                "url": "https://alt.example/blocked", "source": "Blocked News",
            })
            s.put("candidates", candidate["id"], candidate)
            attempted = []
            long_article = ARTICLE.replace("</article>", "<p>" +
                                           "More reported detail from the alternate source. " * 12 +
                                           "</p></article>")

            def fetch_page(url):
                attempted.append(url)
                if url != "https://alt.example/full":
                    raise RuntimeError("source unavailable")
                return long_article

            result = enrich.run(s, [candidate["id"]], log=lambda *a: None,
                                fetcher=fetch_page, resolver=lambda url: url)
            self.assertEqual(attempted, [candidate["url"], "https://alt.example/blocked",
                                         "https://alt.example/full"])
            self.assertEqual(result, {"enriched": 1, "thin": 0})
            pack = s.get("sources", candidate["id"])
            self.assertEqual(pack["url"], "https://alt.example/full")
            self.assertEqual(pack["original_url"], candidate["url"])
            self.assertEqual(pack["source"], "Alternate News")
            self.assertEqual(s.get("candidates", candidate["id"])["source"], "Acme News")
            self.assertIn("source unavailable", pack["note"])
            self.assertEqual(s.get("candidates", candidate["id"])["resolved_url"], pack["url"])

    def test_run_skips_invalid_and_duplicate_links_and_keeps_primary_on_failure(self):
        with tempfile.TemporaryDirectory() as d:
            s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
            primary = "https://example.com/original"
            s.put("candidates", "c1", {"title": "T", "url": primary, "source": "Original News", "links": [
                {"url": primary, "source": "Repeated"}, {"source": "Missing URL"},
                {"url": None}, 42, " ", "https://alt.example/one",
                {"url": " https://alt.example/one ", "source": "Duplicate"},
                {"url": "https://alt.example/two", "source": "Two"},
                "https://alt.example/three", {"url": "https://alt.example/four"},
            ]})
            attempted = []

            def fail_page(url):
                attempted.append(url)
                raise RuntimeError("source unavailable")

            result = enrich.run(s, ["c1"], log=lambda *a: None,
                                fetcher=fail_page, resolver=lambda url: url + "/resolved")
            self.assertEqual(attempted, [primary + "/resolved"] + [
                "https://alt.example/" + name + "/resolved" for name in ("one", "two", "three")
            ])
            self.assertEqual(result, {"enriched": 1, "thin": 1})
            self.assertEqual(s.get("sources", "c1")["url"], primary)
            self.assertEqual(s.get("sources", "c1")["original_url"], primary)
            self.assertEqual(s.get("sources", "c1")["source"], "Original News")
            self.assertEqual(s.get("candidates", "c1")["resolved_url"], primary)

    def test_run_keeps_primary_publisher_when_primary_article_succeeds(self):
        with tempfile.TemporaryDirectory() as d:
            s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
            primary = "https://example.com/original"
            s.put("candidates", "c1", {
                "title": "T", "url": primary, "source": "Original News",
                "links": [{"url": primary, "source": "Duplicate label"},
                          {"url": "https://alt.example/full", "source": "Alternate News"}],
            })
            long_article = "<article><p>" + "Details from the original publisher. " * 30 + "</p></article>"
            attempted = []

            def fetch_page(url):
                attempted.append(url)
                return long_article

            enrich.run(s, ["c1"], log=lambda *a: None,
                       fetcher=fetch_page, resolver=lambda url: url)
            self.assertEqual(attempted, [primary])
            self.assertEqual(s.get("sources", "c1")["source"], "Original News")
            self.assertEqual(s.get("sources", "c1")["url"], primary)

    def test_pack_marks_thin(self):
        cand = {"title": "T", "url": "u", "source": "s", "summary": "sum"}
        self.assertTrue(enrich.build_pack(cand, "")["thin"])
        self.assertFalse(enrich.build_pack(cand, "x" * 800)["thin"])


class VerifyChecksTests(unittest.TestCase):
    def setUp(self):
        self.pack = enrich.build_pack({"title": "Acme cuts waiting time", "url": "u", "source": "Acme"},
                                      enrich.extract_text(ARTICLE))

    def test_good_post_passes(self):
        r = verify.checks(GOOD_POST, self.pack, hashtags=["#ai", "#healthcare"])
        self.assertEqual(r["verdict"], "pass", r["issues"])
        self.assertLess(r["hook_len"], verify.HOOK_MOBILE)

    def test_invented_number_fails(self):
        r = verify.checks(GOOD_POST.replace("32%", "57%"), self.pack)
        self.assertEqual(r["verdict"], "fail")
        self.assertTrue(any(i["code"] == "number" and "57%" in i["msg"] for i in r["issues"]))

    def test_banned_phrase_and_bait(self):
        r = verify.checks(GOOD_POST + "\n\nThis is a game changer. Link in comments!", self.pack)
        codes = {i["code"] for i in r["issues"]}
        self.assertIn("banned", codes)
        self.assertIn("pattern", codes)
        self.assertEqual(r["verdict"], "fail")

    def test_long_hook_warns_then_fails(self):
        hook = "x" * 150
        r = verify.checks(hook + "\n\n" + GOOD_POST, self.pack)
        self.assertTrue(any(i["code"] == "hook" and i["level"] == "warn" for i in r["issues"]))
        r = verify.checks("x" * 230 + "\n\n" + GOOD_POST, self.pack)
        self.assertTrue(any(i["code"] == "hook" and i["level"] == "fail" for i in r["issues"]))

    def test_markdown_and_hashtags(self):
        r = verify.checks("**Bold** hook\n\n" + GOOD_POST, self.pack, hashtags=["#a", "#b", "#c", "#d"])
        codes = {i["code"] for i in r["issues"]}
        self.assertIn("markdown", codes)
        self.assertIn("hashtags", codes)

    def test_judge_findings_change_verdict(self):
        llm = LLM(client=FakeClient({"verify": {"unsupported_claims": ["'cut costs in half'"], "misattributed": [],
                                                "ai_smell": 4, "specificity": 3, "fixes": ["remove cost claim"], "summary": ""}}))
        r = verify.run(llm, {"post": GOOD_POST, "angle": {}}, self.pack, log=lambda *_: None)
        self.assertEqual(r["verdict"], "fail")
        self.assertIn("remove cost claim", verify.fix_list(r))
        self.assertTrue(any(i["code"] == "ai_smell" for i in r["issues"]))


class LLMWrapperTests(unittest.TestCase):
    def test_cost_ledger_and_budget(self):
        llm = LLM(budget_usd=0.01, client=FakeClient({"triage": {"items": []}, "writer": {"post": ""}}))
        llm.json("triage", "s", "u", {"type": "object"})
        self.assertEqual(llm.calls[0]["model"], "claude-haiku-4-5")
        self.assertAlmostEqual(llm.calls[0]["usd"], 1000 * 1.0 / 1e6 + 300 * 5.0 / 1e6, places=6)
        llm.spent = 0.02
        from agents.llm import BudgetExceeded
        with self.assertRaises(BudgetExceeded):
            llm.json("writer", "s", "u", {"type": "object"})

    def test_opus_call_uses_beta_with_fallback_and_effort(self):
        fake = FakeClient({"writer": {"post": "x"}})
        LLM(client=fake).json("writer", "sys", "u", {"type": "object"}, cache_system=True)
        role, kw = fake.calls[0]
        self.assertEqual(kw["fallbacks"], "default")
        self.assertIn("server-side-fallback-2026-07-01", kw["betas"])
        self.assertEqual(kw["output_config"]["effort"], config.PIPELINE_EFFORT["writer"])
        self.assertEqual(kw["system"][0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("thinking", kw)


class EndToEndTests(unittest.TestCase):
    def test_full_run_with_fake_claude(self):
        import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "news.db")
            make_db(db, n=3)
            old_db = config.DB_FILE
            config.DB_FILE = db
            try:
                s = storemod.Store(backend="local", local_path=os.path.join(d, "pipeline.json"), key="k")
                fake = FakeClient(ANSWERS)
                llm = LLM(client=fake)
                quiet = lambda *a, **k: None  # noqa: E731
                run_pipeline.log = quiet
                t = run_pipeline.stage_triage(llm, s, mode="api")
                self.assertEqual(t["scored"], 3)
                self.assertEqual(t["kept"], 3)
                # second triage sees nothing new
                self.assertEqual(run_pipeline.stage_triage(llm, s, mode="api")["scored"], 0)
                # deterministic fetch instead of the network
                enrich_run = enrich.run
                enrich.run = lambda store, ids, log=print: enrich_run(store, ids, log=log, fetcher=lambda u: ARTICLE)
                try:
                    r = run_pipeline.stage_draft(llm, s, limit=2)
                finally:
                    enrich.run = enrich_run
                self.assertEqual(r["drafts"], 2)
                drafts = list(s.all("drafts").values())
                self.assertEqual(drafts[0]["status"], "draft")
                self.assertEqual(drafts[0]["verify"]["verdict"], "pass", drafts[0]["verify"]["issues"])
                self.assertIn("https://example.com/acme", drafts[0]["first_comment"])
                self.assertEqual(s.get("candidates", drafts[0]["candidate_id"])["status"], "drafted")
                # store persisted to disk
                with open(os.path.join(d, "pipeline.json"), encoding="utf-8") as f:
                    on_disk = json.load(f)
                self.assertEqual(len(on_disk["drafts"]), 2)
                # the writer system prompt carries the voice + rules, and is cached
                wcall = next(kw for role, kw in fake.calls if role == "writer")
                self.assertIn("Ahmad", wcall["system"][0]["text"])
                self.assertIn("Hook first", wcall["system"][0]["text"])
                # the remaining candidate is picked next time; drafted ones are not
                self.assertEqual(len(run_pipeline.pick_candidates(s, 5)), 1)
            finally:
                config.DB_FILE = old_db

    def test_writer_rewrites_once_on_failed_verify(self):
        bad = GOOD_POST.replace("32%", "57%")
        calls = {"n": 0}

        def writer_answer(user):
            calls["n"] += 1
            post = bad if calls["n"] == 1 else GOOD_POST
            return dict(ANSWERS["writer"], post=post)

        with tempfile.TemporaryDirectory() as d:
            s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
            s.put("candidates", "c1", {"title": "Acme cuts waiting time", "url": "https://example.com/acme",
                                       "source": "Acme", "score": 9, "status": "new", "topic": "health"})
            s.put("sources", "c1", dict(enrich.build_pack(s.get("candidates", "c1"), enrich.extract_text(ARTICLE)), fetched_at="now"))
            fake = FakeClient(dict(ANSWERS, writer=writer_answer))
            import run_pipeline
            run_pipeline.log = lambda *a, **k: None
            r = run_pipeline.stage_draft(LLM(client=fake), s, limit=1)
            self.assertEqual(r["drafts"], 1)
            self.assertEqual(calls["n"], 2)
            second_user = [kw for role, kw in fake.calls if role == "writer"][1]["messages"][0]["content"]
            self.assertIn("FAILED VERIFICATION", second_user)
            self.assertIn("57%", second_user)
            self.assertEqual(s.get("drafts", "c1")["verify"]["verdict"], "pass")


class RulesTriageTests(unittest.TestCase):
    def _story(self, title, **kw):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        base = {"id": storemod.doc_id(title), "title": title, "url": "https://e.com/" + storemod.doc_id(title), "source": "Some Blog",
                "category": "AI General News", "published": now, "fetched": now, "summary": "", "links": []}
        base.update(kw)
        return base

    def test_scores_reward_signals_and_stay_in_range(self):
        weak = self._story("An opinion about the future of thinking machines", published="2020-01-01T00:00:00+00:00", fetched="2020-01-01T00:00:00+00:00")
        strong = self._story("OpenAI launches free voice feature for everyone", source="OpenAI Blog", links=["a", "b"], summary="x" * 200)
        s_weak = triage.rules_score(weak, [])[0]
        s_strong, topic, urgency, reason = triage.rules_score(strong, [])
        self.assertLess(s_weak, config.PIPELINE_TRIAGE_MIN_SCORE)
        self.assertGreaterEqual(s_strong, 8)
        self.assertLessEqual(s_strong, 10)
        self.assertEqual(urgency, "today")
        self.assertIn("official announcement", reason)
        self.assertEqual(topic, "tools")

    def test_topic_keywords_and_category_fallback(self):
        self.assertEqual(triage.rules_score(self._story("Hospital uses AI to triage patients"), [])[1], "health")
        self.assertEqual(triage.rules_score(self._story("EU regulators draft a law on chatbots"), [])[1], "politics_policy")
        self.assertEqual(triage.rules_score(self._story("Quiet week", category="AI in Coding"), [])[1], "coding")

    def test_run_rules_stores_dedupes_and_drops_noise(self):
        with tempfile.TemporaryDirectory() as d:
            s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
            stories = [self._story("OpenAI unveils Dots always-on personal AI agents powered by GPT-6", source="OpenAI Blog", links=["x"]),
                       self._story("OpenAI introduces Dots: autonomous AI agents powered by GPT-6", source="OpenAI Blog", links=["x"]),
                       self._story("A benchmark paper on tokenizer quantization", published="2020-01-01T00:00:00+00:00", fetched="2020-01-01T00:00:00+00:00")]
            r = triage.run_rules(s, stories, [], log=lambda *a: None)
            self.assertEqual(r["scored"], 3)
            self.assertEqual(r["duplicates"], 1)
            self.assertEqual(r["dismissed"], 1)
            self.assertEqual(sorted(c["status"] for c in s.all("candidates").values()), ["duplicate", "new"])
            self.assertTrue(all(c["engine"] == "rules" for c in s.all("candidates").values()))

    def test_prune_keeps_acted_on_candidates(self):
        import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
            s.put("candidates", "old", {"status": "low", "created": "2020-01-01T00:00:00+00:00"})
            s.put("candidates", "kept", {"status": "shortlisted", "created": "2020-01-01T00:00:00+00:00"})
            s.put("candidates", "fresh", {"status": "new", "created": storemod.now_iso()})
            s.put("sources", "old", {"excerpt": "x"})
            s.put("sources", "orphan", {"excerpt": "x"})
            self.assertEqual(run_pipeline.prune(s), 1)
            self.assertEqual(sorted(s.all("candidates")), ["fresh", "kept"])
            self.assertEqual(list(s.all("sources")), [])

    def test_free_mode_prepares_sources_without_llm(self):
        import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "news.db")
            make_db(db, n=2)
            old = config.DB_FILE
            config.DB_FILE = db
            try:
                s = storemod.Store(backend="local", local_path=os.path.join(d, "p.json"), key="k")
                run_pipeline.log = lambda *a, **k: None
                t = run_pipeline.stage_triage(None, s, mode="free")
                self.assertEqual(t["scored"], 2)
                enrich_run = enrich.run
                enrich.run = lambda store, ids, log=print: enrich_run(store, ids, log=log, fetcher=lambda u: ARTICLE)
                try:
                    r = run_pipeline.stage_prepare(s, 5)
                finally:
                    enrich.run = enrich_run
                open_c = [c for c in s.all("candidates").values() if c["status"] in ("new", "shortlisted")]
                self.assertEqual(r["prepared"], len(open_c))
                self.assertTrue(all(p["fetched_at"] for p in s.all("sources").values()))
                self.assertEqual(s.all("drafts"), {})
            finally:
                config.DB_FILE = old


if __name__ == "__main__":
    unittest.main()
