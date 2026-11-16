"""pinterest_api.py — posting Pin ke Pinterest via Pinterest API v5.

Token dibaca dari ~/.pinterest_poster/pinterest_token.env (mode 600).
File ini TIDAK PERNAH mencetak token.

Alur Pinterest API v5:
  1. POST /v5/pins (board_id, title, description, link,
     media_source={source_type: image_url, url: image_url}) -> pin id
  2. GET /v5/pins/{id} -> verifikasi link + judul

Catatan penting (riset GitHub 16 Nov 2026):
  - Akun Trial: Pin HANYA terlihat oleh pembuatnya (sandbox) sampai
    Standard access disetujui (butuh video demo OAuth flow).
  - Tagging produk native Shopee TIDAK bisa lewat API — tagging dilakukan
    manual di aplikasi Pinterest (kemitraan resmi Shopee x Pinterest).
  - Pinterest melarang Pin afiliasi "repetitif atau dalam jumlah besar" —
    modul ini dibatasi maks 1 Pin/hari (lihat tools/run_pinterest.py).

Penggunaan:
  python tools/pinterest_api.py --board-id <id> --title "..." \
      --description "..." --link "https://s.shopee.co.id/..." \
      --image-url "https://cf.shopee.co.id/file/..." [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.pinterest.com/v5"
TOKEN_PATH = Path("~/.pinterest_poster/pinterest_token.env").expanduser()


def load_token(path: Path = TOKEN_PATH) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Token Pinterest tidak ditemukan: {path} — buat Pinterest "
            f"Business app + Trial access dulu (lihat docs/pinterest.md)."
        )
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("PINTEREST_ACCESS_TOKEN="):
            tok = line.split("=", 1)[1].strip()
            if tok:
                return tok
    raise ValueError(f"PINTEREST_ACCESS_TOKEN kosong di {path}")


def _request(method: str, path: str, payload: dict | None = None) -> dict:
    token = load_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(
            f"Pinterest API {e.code} {method} {path}: {detail[:300]}"
        ) from e


def create_pin(board_id: str, title: str, description: str,
               link: str, image_url: str) -> dict:
    """Buat satu Pin. Kembalikan {'id', 'link', 'title'} (terverifikasi)."""
    if len(title) > 100:
        raise ValueError(f"Judul {len(title)} karakter (maks 100).")

    payload = {
        "board_id": board_id,
        "title": title,
        "description": description,
        "link": link,
        "media_source": {"source_type": "image_url", "url": image_url},
    }
    created = _request("POST", "/pins", payload)
    pid = created["id"]
    verified = _request("GET", f"/pins/{pid}")
    return {
        "id": pid,
        "link": verified.get("link", link),
        "title": verified.get("title", title),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Buat Pin via Pinterest API v5")
    ap.add_argument("--board-id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--link", required=True)
    ap.add_argument("--image-url", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if len(args.title) > 100:
        print(f"Judul {len(args.title)} karakter (maks 100).")

        return 1
    if args.dry_run:
        print("DRY RUN OK — payload valid, tidak memanggil API:")
        print(f"  board: {args.board_id}")
        print(f"  judul ({len(args.title)} karakter): {args.title}")
        print(f"  deskripsi ({len(args.description)} karakter):")
        print(f"  {args.description}")
        print(f"  link: {args.link}")
        print(f"  image: {args.image_url}")
        return 0
    res = create_pin(args.board_id, args.title, args.description,
                     args.link, args.image_url)
    print(f"Terkirim: Pin {res['id']} | {res['link']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
