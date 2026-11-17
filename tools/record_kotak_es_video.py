#!/usr/bin/env python3
"""Record Kotak Es video post (17 Nov 2026 10:15 WIB) into PC history + DB.
Receipt verified 3 ways: web fetch permalink, GET /me/threads, GET /{id}/replies.
Media IDs from API: video 18141707743629193, reply 18073477226790519.
Run on PC in ~/threads-affiliate-system. Backups are made by the caller.
Structure: post_history.json is {"posts": [...]}; DB Stats recomputed from rows.
"""
import json
import re

hp = 'data/post_history.json'
h = json.load(open(hp))
posts = h['posts']
print('entri lama:', len(posts))

entry = {
    "date": "2026-11-17T10:15:24",
    "hook_category": "controversy",
    "hook_text": "Mitos: alat dapur harus mahal biar awet. Ulasan bilang beda.",
    "product": "Kotak Penyimpanan Es Portabel",
    "affiliate_link": "https://s.shopee.co.id/an_redir?origin_link=https%3A%2F%2Fshopee.co.id%2Fproduct%2F1223910013%2F28725037276?&affiliate_id=11369851901&sub_id=threadsdapurkotakes20261117----",
    "num_posts": 2,
    "category": "dapur",
    "status": "posted",
    "platform": "threads",
    "product_id": "P-1223910013-28725037276",
    "content_id": "kotak-es-threads-20261117",
    "sub_id": "threadsdapurkotakes20261117",
    "published_at": "2026-11-17T10:15:24",
    "media_id": "18141707743629193",
    "permalink": "https://www.threads.com/@shopee_harian/post/Df08R7ggYRL",
    "media_id_reply": "18073477226790519",
    "permalink_reply": "https://www.threads.com/@shopee_harian/post/Df08cc1k9-V",
    "media_type": "VIDEO",
    "video_file": "data/videos/kotak-es-ugc/kotak-es-ugc-v2.mp4",
    "source": "device browser (Threads web UI)",
    "receipt_verified_via": ["web fetch permalink", "GET /me/threads", "GET /{id}/replies"],
}
assert not any(e.get("sub_id") == entry["sub_id"] and e.get("status") == "posted" for e in posts), "duplikat!"
posts.append(entry)
json.dump(h, open(hp, "w"), indent=2, ensure_ascii=False)
print('history kini:', len(posts), 'entri; Kotak Es tercatat posted')

db = 'data/affiliate_links.md'
txt = open(db).read()
lines = txt.splitlines()
for i, line in enumerate(lines):
    if line.startswith('| 4 | Kotak Penyimpanan Es Portabel |'):
        parts = [p for p in line.split('|')]
        # split('|') -> ['', ' 4 ', ' Kotak... ', ' `link` ', ' status ', ' last used ', ' sub_id ', '']
        assert 'UNUSED' in parts[4], f'status bukan UNUSED: {parts[4]}'
        parts[4] = ' ✅ USED (2026-11-17) — video UGC Flow via browser '
        parts[5] = ' 2026-11-17 '
        lines[i] = '|'.join(parts)
        break
else:
    raise AssertionError('baris Kotak Es tidak ketemu')
txt = '\n'.join(lines) + '\n'
# Stats dihitung ulang dari baris (header lama basi: ECOCO sudah USED tapi header masih 2)
used = len(re.findall(r'\| ✅ USED', txt))
total = len(re.findall(r'^\| \d+ \|', txt, re.M))
txt = re.sub(r'- \*\*Used:\*\* \d+', f'- **Used:** {used}', txt)
txt = re.sub(r'- \*\*Available:\*\* \d+', f'- **Available:** {total - used}', txt)
txt = re.sub(r'- \*\*Total Links:\*\* \d+', f'- **Total Links:** {total}', txt)
open(db, 'w').write(txt)
print(f'DB: Kotak Es USED; Stats dihitung ulang: Total {total}, Used {used}, Available {total - used}')
print('OK')
