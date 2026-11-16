"""publish_api.py — posting ke Threads via Threads API resmi (graph.threads.net).

Fase 2: menggantikan Playwright + cookie.
Token dibaca dari ~/.threads_poster/threads_token.env (mode 600).
File ini TIDAK PERNAH mencetak token.

Alur Threads API (v1.0):
  1. POST /me/threads (media_type=TEXT, text=...) -> container id
  2. Tunggu status container FINISHED (poll GET /{id}?fields=status)
  3. POST /me/threads_publish (creation_id=...) -> post id
  4. GET /{post_id}?fields=permalink -> URL publik (verifikasi)

Balasan (self-reply berisi link): container dengan reply_to_id=<id post 1>.
Reply bermedia: publish_media_reply(text, reply_to, image_url=... /
video_url=...) — container IMAGE/VIDEO + reply_to_id (cek API 16 Nov 2026).

Penggunaan:
  python tools/publish_api.py --text "..." [--reply-to <id>]
  python tools/publish_api.py --text "..." --dry-run   # cek panjang saja
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://graph.threads.net/v1.0"
TOKEN_PATH = Path("~/.threads_poster/threads_token.env").expanduser()
USERNAME = "shopee_harian"


def load_token(path: Path = TOKEN_PATH) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Token tidak ditemukan: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("THREADS_ACCESS_TOKEN="):
            tok = line.split("=", 1)[1].strip()
            if tok:
                return tok
    raise ValueError(f"THREADS_ACCESS_TOKEN kosong di {path}")


def _post(path: str, params: dict) -> dict:
    body = dict(params)
    body["access_token"] = load_token()
    req = urllib.request.Request(
        BASE + path,
        data=urllib.parse.urlencode(body).encode(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(
            f"Threads API {e.code} POST {path}: {detail[:300]}") from e


def _get(path: str, params: dict) -> dict:
    body = dict(params)
    body["access_token"] = load_token()
    url = BASE + path + "?" + urllib.parse.urlencode(body)
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(
            f"Threads API {e.code} GET {path}: {detail[:300]}") from e


def _publish_container(cid: str, wait_s: int) -> dict:
    """Poll container sampai FINISHED lalu publish. Kembalikan
    {'id', 'permalink', 'permalink_verified'}.

    Sprint 2: permalink TIDAK PERNAH difabrikasi. Bila GET permalink gagal
    (2x percobaan), kembalikan permalink=None + verified=False — pencatat
    di run_slot.py yang memutuskan statusnya (bukan 'posted').
    """
    deadline = time.time() + wait_s
    while True:
        st = _get(f"/{cid}", {"fields": "status"})
        status = st.get("status", "")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"Container {cid} ERROR: {st}")
        if time.time() > deadline:
            raise RuntimeError(
                f"Container {cid} belum FINISHED setelah {wait_s} dtk: {st}")
        time.sleep(2)
    pub = _post("/me/threads_publish", {"creation_id": cid})
    pid = pub["id"]
    permalink = None
    verified = False
    for attempt in range(2):
        try:
            permalink = _get(f"/{pid}", {"fields": "permalink"}).get("permalink")
            if permalink:
                verified = True
                break
        except Exception:
            if attempt == 0:
                time.sleep(2)
    return {"id": pid, "permalink": permalink, "permalink_verified": verified}


def get_media(media_id: str) -> dict:
    """Baca satu media via API (read-only, untuk verifikasi manual).
    Kembalikan {'id', 'permalink', 'timestamp'} bila ada; raise bila
    media tidak ditemukan / tidak bisa diakses (mis. sudah dihapus).
    """
    return _get(f"/{media_id}", {"fields": "id,permalink,timestamp"})


def publish_text(text: str, reply_to: str | None = None,
                 wait_s: int = 30) -> dict:
    """Posting satu teks. Kembalikan {'id', 'permalink',
    'permalink_verified'} — permalink bisa None bila GET verifikasi
    gagal (lihat _publish_container); JANGAN anggap terbit bila id
    tidak ada (fungsi ini raise bila publish gagal)."""
    if len(text) > 500:
        raise ValueError(f"Teks {len(text)} karakter (maks 500).")
    params: dict = {"media_type": "TEXT", "text": text}
    if reply_to:
        params["reply_to_id"] = reply_to
    container = _post("/me/threads", params)
    return _publish_container(container["id"], wait_s)


def publish_media_reply(text: str, reply_to: str,
                        image_url: str | None = None,
                        video_url: str | None = None,
                        wait_s: int = 60) -> dict:
    """Reply bermedia via Threads API: container media_type=IMAGE
    (+image_url) atau VIDEO (+video_url) + reply_to_id, lalu poll FINISHED
    dan publish. Media HARUS di URL publik https:// (Meta mengambil
    langsung saat container dibuat). image_url dan video_url saling
    eksklusif — isi tepat satu.

    Dasar: model container Threads API menerima reply_to_id bersama
    media_type IMAGE/VIDEO (bukan hanya TEXT). BELUM pernah diuji live
    untuk app 'TemuanHarian Threads API' — uji live pertama wajib
    --dry-run dulu + approval Kyan.
    """
    if bool(image_url) == bool(video_url):
        raise ValueError("Isi tepat satu: image_url ATAU video_url.")
    if len(text) > 500:
        raise ValueError(f"Teks {len(text)} karakter (maks 500).")
    if image_url:
        params: dict = {"media_type": "IMAGE", "image_url": image_url,
                        "text": text}
    else:
        params = {"media_type": "VIDEO", "video_url": video_url,
                  "text": text}
    params["reply_to_id"] = reply_to
    container = _post("/me/threads", params)
    return _publish_container(container["id"], wait_s)


def main() -> int:
    ap = argparse.ArgumentParser(description="Posting via Threads API")
    ap.add_argument("--text", required=True)
    ap.add_argument("--reply-to", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if len(args.text) > 500:
        print(f"❌ Teks {len(args.text)} karakter (maks 500).")
        return 1
    if args.dry_run:
        print(f"✅ DRY RUN OK ({len(args.text)} karakter, tidak posting).")
        return 0
    res = publish_text(args.text, reply_to=args.reply_to)
    print(f"✅ Terkirim: {res['permalink'] or '(permalink belum terverifikasi, id=' + res['id'] + ')'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
