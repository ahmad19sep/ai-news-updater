"""
AI News Radar - Re-sort the whole archive into categories

Run this after changing CATEGORIES or CATEGORY_RULES in config.py:
    python reclassify.py

Every stored story is re-classified by its title using the current
rules. Locked feeds (leaders, podcasts, papers) keep their category.
"""

import config
import database
import filters

# source name -> (default category, locked)
SOURCE_MAP = {f["name"]: (f["category"], f.get("lock", False)) for f in config.FEEDS}
SOURCE_MAP["HF Trending Papers"] = (9, True)


def run():
    conn = database.connect()
    rows = conn.execute("SELECT id, title, source, pillar FROM items").fetchall()
    changed = 0
    counts = {}
    for r in rows:
        default_cat, locked = SOURCE_MAP.get(r["source"], (10, False))
        new_cat = default_cat if locked else filters.classify(r["title"], default_cat)
        counts[new_cat] = counts.get(new_cat, 0) + 1
        if new_cat != r["pillar"]:
            conn.execute("UPDATE items SET pillar = ? WHERE id = ?", (new_cat, r["id"]))
            changed += 1
    conn.commit()

    print(f"{len(rows)} stories checked, {changed} moved to a new category.\n")
    for num, name in config.CATEGORIES.items():
        print(f"  {name}: {counts.get(num, 0)}")
    conn.close()


if __name__ == "__main__":
    run()
