import json, sys
sys.path.insert(0, "vendor/threads-affiliate")
sys.path.insert(0, "tools")
from threads_poster.database import AffiliateDatabase
from check_draft import check_chain

db = AffiliateDatabase("data/affiliate_links.md")
rows = db._parse_rows(db._read())
post2 = json.load(open("templates/post2_templates.json"))
cta = json.load(open("templates/post3_cta_templates.json"))
hooks = {c: json.load(open("templates/hooks_%s.json" % c))
         for c in ("dapur", "organizer", "kebersihan")}
for cat in ("dapur", "organizer", "kebersihan"):
    unused = [r for r in rows
              if r["category"].lower() == cat
              and "UNUSED" in r.get("status", "").upper()]
    prod, link = unused[0]["product"], unused[0]["link"]
    bodies = [t.format(product=prod) for t in post2.get(cat, post2["default"])]
    ctas = [t.format(product=prod) for t in cta["templates"]]
    ok = sum(1 for b in bodies for t in ctas
             if len("%s\n\n%s\n%s" % (b, t, link)) <= 500)
    total = len(bodies) * len(ctas)
    print("%s: %d/%d combo post2 lolos (<=500 dgn link) = %.0f%%; "
          "5x retry gagal ~= %.4f%%"
          % (cat, ok, total, 100.0 * ok / total,
             100.0 * (1 - ok / total) ** 5))
    v5hook = hooks[cat]["hooks"]["edukasi"][0]
    worst = "%s\n\n%s\n%s" % (max(bodies, key=len), max(ctas, key=len), link)
    errs = [p for p in check_chain([v5hook, worst], link)
            if p["level"] == "ERROR"]
    if errs:
        print("   hook v5 %r worst-case: GAGAL %s"
              % (v5hook[:40], errs[0]["detail"]))
    else:
        print("   hook v5 %r worst-case: lolos" % v5hook[:40])
