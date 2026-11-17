#!/usr/bin/env python3
"""Verifikasi pasca-posting video via Threads API (read-only) + opsi
perbaiki receipt post_history.json bila permalink yang dicatat salah.

Dipakai cron posting video: insiden ZuoShu 17 Nov 2026 - script video
mencatat permalink postingan lama (profil belum refresh) sehingga balasan
link nyasar ke postingan lain. Tool ini mencari postingan BENAR via API
(/me/threads, cocokkan caption persis), lalu cek apakah balasan link sudah
ada di postingan benar itu.

Penggunaan:
  verify_video_post.py --caption "..." --reply-probe "..."
      [--content-id ... --fix-receipt]
Keluaran: satu baris JSON.
"""
import argparse, json, os, sys, urllib.request, urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HISTORY_PATH = BASE / "data" / "post_history.json"

ap = argparse.ArgumentParser()
ap.add_argument("--caption", required=True)
ap.add_argument("--reply-probe", required=True)
ap.add_argument("--content-id", default="")
ap.add_argument("--fix-receipt", action="store_true")
a = ap.parse_args()

tok = None
for line in open(os.path.expanduser("~/.threads_poster/threads_token.env")):
    line = line.strip()
    if line.startswith("THREADS_ACCESS_TOKEN="):
        tok = line.split("=", 1)[1].strip().strip('"').strip("'")
        break
if not tok:
    print(json.dumps({"ok": False, "error": "token tidak ditemukan"}, ensure_ascii=False))
    sys.exit(2)

def get(path, params=None):
    url = "https://graph.threads.net/v1.0/" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

out = {"ok": True, "post_url": None, "media_id": None,
       "reply_found": False, "reply_id": None, "receipt_fixed": False}
try:
    me = get("me/threads", {"fields": "id,permalink,timestamp,text,shortcode,media_type", "limit": 10})
    for t in me.get("data", []):
        if (t.get("text") or "").strip() == a.caption.strip():
            out["post_url"] = t.get("permalink")
            out["media_id"] = t.get("id")
            break
    if out["media_id"]:
        reps = get(out["media_id"] + "/replies", {"fields": "id,text,timestamp,username"})
        for x in reps.get("data", []):
            if a.reply_probe in (x.get("text") or ""):
                out["reply_found"] = True
                out["reply_id"] = x.get("id")
                break
    if a.fix_receipt and a.content_id and out["post_url"] and HISTORY_PATH.exists():
        history = json.loads(HISTORY_PATH.read_text())
        for e in history.get("posts", []):
            if e.get("content_id") == a.content_id:
                if e.get("permalink") != out["post_url"]:
                    e["permalink"] = out["post_url"]
                    e["media_id"] = out["media_id"]
                    e["correction_note"] = ("Permalink awal salah (script video ambil URL "
                        "postingan lama dari profil); diperbaiki otomatis via API "
                        "verify_video_post.py.")
                    out["receipt_fixed"] = True
                break
        if out["receipt_fixed"]:
            HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2))
except Exception as e:
    out = {"ok": False, "error": str(e)}
print(json.dumps(out, ensure_ascii=False))
