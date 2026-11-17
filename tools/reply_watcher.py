#!/usr/bin/env python3
"""reply_watcher.py — pantau balasan di postingan kita; balas yang nanya link.

Fase 2b. DUA mode:
- API (@shopee_harian, default): baca /me/threads + /{id}/replies via token
  (pola verify_video_post.py), balas via publish_api.publish_text(reply_to=...).
- Playwright (akun sekunder, --account <handle>): baca postingan terbaru
  dari profil + balasan via DOM (heuristik — baca probe_replies.py),
  balas top-level dengan @mention via comment_playwright.py --profile.
  CATATAN: ekstraksi balasan Playwright TERVERIFIKASI 18 Nov ~00:0x WIB
  (keyword-first, post pilot putrikiian: 2 entri ditemukan — caption post
  + balasan link sendiri, keduanya benar teratribusi ke putrikiian).

Aturan (berlaku dua mode):
- Deteksi: teks balasan mengandung kata kunci minta link/harga
  (link, spill, beli, harga, berapa, checkout, order, "di mana", "dimana").
- JANGAN balas balasan dari akun sendiri, dan JANGAN balas 2x ke komentator
  yang sama di postingan yang sama (seen store data/reply_watch.json).
- Balasan = "Linknya di sini kak 👇 <link>" (API, reply_to langsung ke
  komentarnya) atau "@user Linknya di sini kak 👇 <link>" (Playwright,
  top-level karena comment_playwright tidak mendukung nested reply).
  Link = link affiliate postingan itu (dari post_history.json); bila tidak
  ada link di history, SKIP.
- Cap: maks --max-replies balasan/hari/akun (default 5).
- Default DRY-RUN: hanya laporkan kandidat. --live baru membalas.
  LIVE butuh approval Kyan (pertama kali) — jangan diaktifkan dari cron
  sebelum ia menyetujui template + hasil dry-run.

Penggunaan:
  reply_watcher.py --self-test            # uji deteksi (tanpa network)
  reply_watcher.py --dry-run              # API @shopee_harian, baca saja
  reply_watcher.py --account putrikiian --dry-run
  reply_watcher.py --live                 # (butuh approval Kyan dulu)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "vendor" / "threads-affiliate"))

HISTORY_PATH = ROOT / "data" / "post_history.json"
WATCH_PATH = ROOT / "data" / "reply_watch.json"
MAIN_ACCOUNT = "shopee_harian"
ACCOUNTS = (MAIN_ACCOUNT, "putrikiian", "randomaffil", "iwantu142",
            "iniputriiii2626")
KEYWORDS = ("link", "spill", "beli", "harga", "berapa", "checkout",
            "order", "di mana", "dimana")
UI_JUNK = ("insights", "views", "profile visits", "follows", "see all")

# Keyword-first: node teks berisi kata kunci -> ancestor terkecil yang
# mengandung teks itu + >=1 link handle telanjang. Diuji di post pilot
# putrikiian: menemukan 2 entri (caption post + balasan link sendiri).
EXTRACT_JS = """
() => {
  const KEYWORDS = ['link','spill','beli','harga','berapa','checkout','order','di mana','dimana'];
  const out = [];
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const t = (node.textContent || '').trim();
    if (t.length < 20 || t.length > 500) continue;
    const parent = node.parentElement;
    if (!parent || ['SCRIPT','STYLE'].includes(parent.tagName)) continue;
    const low = t.toLowerCase();
    if (!KEYWORDS.some(k => low.includes(k))) continue;
    let el = parent;
    for (let i = 0; i < 8 && el; i++) {
      const links = [...el.querySelectorAll('a[href^="/@"]')]
        .map(a => a.getAttribute('href'))
        .filter(h => /^\\/@[^/?#]+$/.test(h || ''));
      const txt = (el.innerText || '');
      if (links.length >= 1 && txt.length < 1000 && txt.includes(t.slice(0, 30))) {
        const m = links[0].match(/^\\/@([^/?#]+)$/);
        if (m) {
          const key = m[1] + '|' + t.slice(0, 60);
          if (!seen.has(key)) { seen.add(key); out.push({username: m[1], text: t}); }
          break;
        }
      }
      el = el.parentElement;
    }
  }
  return out;
}
"""


def wants_link(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in KEYWORDS)


def load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    return json.loads(HISTORY_PATH.read_text()).get("posts", [])


def load_watch() -> dict:
    if not WATCH_PATH.exists():
        return {"replied": []}
    try:
        return json.loads(WATCH_PATH.read_text())
    except Exception:
        return {"replied": []}


def save_watch(data: dict) -> None:
    WATCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    WATCH_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def clean_link(link: str) -> str:
    return (link or "").rstrip("-")


# --- API (shopee_harian) ---------------------------------------------------

def load_token() -> str | None:
    p = Path(os.path.expanduser("~/.threads_poster/threads_token.env"))
    if not p.exists():
        return None
    for line in p.read_text().splitlines():
        line = line.strip()
        if line.startswith("THREADS_ACCESS_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def api_get(tok: str, path: str, params: dict | None = None) -> dict:
    url = "https://graph.threads.net/v1.0/" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def scan_api(tok: str, limit_posts: int, max_age_days: int) -> list[dict]:
    """Kembalikan kandidat: [{post, comment}]."""
    cands: list[dict] = []
    me = api_get(tok, "me/threads", {
        "fields": "id,permalink,timestamp,text,shortcode,media_type",
        "limit": limit_posts})
    cutoff = datetime.now() - timedelta(days=max_age_days)
    for post in me.get("data", []):
        ts = post.get("timestamp") or ""
        try:
            posted = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if posted.replace(tzinfo=None) < cutoff:
                continue
        except Exception:
            pass
        try:
            reps = api_get(tok, post["id"] + "/replies",
                           {"fields": "id,text,timestamp,username"})
        except Exception as e:
            print(f"  ! gagal baca balasan {post.get('id')}: {e}")
            continue
        for c in reps.get("data", []):
            if (c.get("username") or "").lower() == MAIN_ACCOUNT:
                continue
            if wants_link(c.get("text") or ""):
                cands.append({"post": post, "comment": c})
    return cands


# --- Playwright (akun sekunder) --------------------------------------------

def extract_replies_pw(page) -> list[dict]:
    """Keyword-first (terverifikasi 18 Nov 00:0x di post pilot putrikiian):
    cari node teks berisi kata kunci, lalu naik ke ancestor terkecil yang
    mengandung teks itu + >=1 link handle telanjang (/ @handle, bukan
    /@handle/post/...). Mengembalikan [{username, text}] — termasuk
    postingan utama + balasan kita (pemanggil yang menyaring)."""
    return page.evaluate(EXTRACT_JS)


def scan_pw(account: str, limit_posts: int) -> list[dict]:
    """Kembalikan kandidat + URL postingan tiap kandidat."""
    from playwright.sync_api import sync_playwright
    import profile_context
    cands: list[dict] = []
    with sync_playwright() as p:
        ctx = profile_context.launch_profile_context(p, account)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://www.threads.com/@{account}",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        urls: list[str] = []
        for a in page.locator('a[href*="/post/"]').all():
            href = a.get_attribute("href") or ""
            if "/post/" in href:
                full = href if href.startswith("http") else \
                    "https://www.threads.com" + href
                if full not in urls:
                    urls.append(full)
            if len(urls) >= limit_posts:
                break
        for url in urls[:limit_posts]:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            extracted = extract_replies_pw(page)
            print(f"  . {url}: {len(extracted)} balasan terekstrak", flush=True)
            for r in extracted:
                if r["username"].lower() == account.lower():
                    continue
                if wants_link(r["text"]):
                    cands.append({"post_url": url, "comment": r})
        ctx.close()
    return cands


# --- main ------------------------------------------------------------------

def self_test() -> int:
    cases = [
        ("kak linknya dong", True),
        ("spill linknya kak", True),
        ("beli di mana kak?", True),
        ("harganya berapa", True),
        ("mau checkout tapi bingung", True),
        ("bagus banget videonya", False),
        ("wkwk lucu", False),
        ("ini affiliate ya?", False),
        ("LINK PLEASE", True),
        ("", False),
    ]
    bad = 0
    for text, expected in cases:
        got = wants_link(text)
        mark = "OK " if got == expected else "GAGAL"
        if got != expected:
            bad += 1
        print(f"{mark} {text!r:35} -> {got} (harap {expected})")
    print(f"SELF-TEST: {len(cases) - bad}/{len(cases)} lolos")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Watcher balasan minta link")
    ap.add_argument("--account", default=MAIN_ACCOUNT, choices=list(ACCOUNTS))
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-replies", type=int, default=5)
    ap.add_argument("--limit-posts", type=int, default=5)
    ap.add_argument("--max-age-days", type=int, default=7)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    live = args.live and not args.dry_run
    account = args.account
    history = load_history()
    watch = load_watch()
    today = datetime.now().date().isoformat()
    replied_today = sum(
        1 for r in watch.get("replied", [])
        if r.get("account") == account and str(r.get("date", ""))[:10] == today)
    print(f"[{account}] mode={'LIVE' if live else 'DRY-RUN'} "
          f"(sudah balas hari ini: {replied_today}/{args.max_replies})")

    # Kumpulkan kandidat
    if account == MAIN_ACCOUNT:
        tok = load_token()
        if not tok:
            print("token API tidak ditemukan")
            return 2
        raw = scan_api(tok, args.limit_posts, args.max_age_days)
        cands = []
        by_media = {e.get("media_id"): e for e in history if e.get("media_id")}
        for item in raw:
            post, c = item["post"], item["comment"]
            entry = by_media.get(post.get("id"))
            cands.append({
                "key": f"api:{post.get('id')}:{c.get('id')}",
                "post_url": post.get("permalink"),
                "username": c.get("username"),
                "text": c.get("text"),
                "comment_id": c.get("id"),
                "link": clean_link(entry.get("affiliate_link")) if entry else "",
                "reply_text": "",
            })
    else:
        raw = scan_pw(account, args.limit_posts)
        by_url = {e.get("permalink"): e for e in history if e.get("permalink")}
        cands = []
        for item in raw:
            entry = by_url.get(item["post_url"])
            cands.append({
                "key": "pw:" + item["post_url"] + ":" + item["comment"]["username"]
                       + ":" + hashlib.md5(
                           item["comment"]["text"][:80].encode()).hexdigest()[:8],
                "post_url": item["post_url"],
                "username": item["comment"]["username"],
                "text": item["comment"]["text"][:200],
                "comment_id": None,
                "link": clean_link(entry.get("affiliate_link")) if entry else "",
                "reply_text": "",
            })

    # Saring: sudah dibalas / tanpa link / cap harian
    fresh = []
    seen_keys = {r.get("key") for r in watch.get("replied", [])}
    for c in cands:
        if c["key"] in seen_keys:
            print(f"  - skip (sudah dibalas): @{c['username']} di {c['post_url']}")
            continue
        if not c["link"]:
            print(f"  - skip (post tanpa link di history): {c['post_url']}")
            continue
        if account == MAIN_ACCOUNT:
            c["reply_text"] = f"Linknya di sini kak 👇 {c['link']}"
        else:
            c["reply_text"] = f"@{c['username']} Linknya di sini kak 👇 {c['link']}"
        fresh.append(c)
    print(f"Kandidat baru: {len(fresh)}")
    for c in fresh:
        print(f"  - @{c['username']}: {c['text'][:80]!r} -> {c['post_url']}")

    if not live:
        print("DRY-RUN: tidak ada balasan dikirim.")
        return 0
    if replied_today >= args.max_replies:
        print("Cap harian tercapai, tidak membalas.")
        return 0

    # LIVE: balas satu per satu
    from publish_api import publish_text  # noqa: E402 (hanya dipakai live)
    sent = 0
    for c in fresh:
        if replied_today + sent >= args.max_replies:
            break
        ok, rid = False, None
        if account == MAIN_ACCOUNT:
            try:
                r = publish_text(c["reply_text"], reply_to=c["comment_id"])
                ok, rid = bool(r.get("id")), r.get("id")
            except Exception as e:
                print(f"  ! gagal balas @{c['username']}: {e}")
        else:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "comment_playwright.py"),
                 "--url", c["post_url"], "--text", c["reply_text"],
                 "--live", "--allow-link", "--profile", account],
                capture_output=True, text=True, timeout=600)
            ok = r.returncode in (0, 7)
            print(r.stdout[-400:])
        if ok:
            watch.setdefault("replied", []).append({
                "key": c["key"], "account": account, "date": today,
                "username": c["username"], "post_url": c["post_url"],
                "reply_id": rid, "reply_text": c["reply_text"][:120],
            })
            sent += 1
            print(f"  + terkirim ke @{c['username']} (reply_id={rid})")
    save_watch(watch)
    print(f"LIVE: {sent} balasan terkirim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
