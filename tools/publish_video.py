"""publish_video.py — publish video hasil Google Flow ke Threads via API resmi.

Alur:
  1. Validasi file video lokal (mp4/mov, <= 1 GB, durasi <= 5 menit via ffprobe).
  2. QC manusia WAJIB: --qc-ok + --qc-file (JSON checklist 4 item, semua true).
     Tanpa keduanya skrip MENOLAK jalan — QC tidak bisa di-skip.
  3. Bangun caption dari template hook v5.1 via ContentGenerator (sama seperti
     run_slot.py): post 1 = hook (teks di video), post 2 = isi + CTA + link
     (self-reply pertama). Validasi via check_draft.py — gagal = batal.
  4. Publish video via Threads API: container media_type=VIDEO.
     PENTING: Threads API TIDAK menerima upload file langsung — video harus
     sudah di-host di URL publik (--video-url). File lokal hanya dipakai
     untuk QC + cek durasi/ukuran. Tanpa --video-url, mode live DITOLAK.

Default = --dry-run: tampilkan caption + guardrail + payload, TIDAK kirim
apa pun, TIDAK panggil API. Mode live HANYA dengan flag --live.

Log: data/video_publish_log.json (TIDAK di-commit — lihat .gitignore).

Penggunaan:
  python tools/publish_video.py --video out/rak-piring.mp4 --video-url https://.../rak-piring.mp4 --product "Rak Piring" --category dapur --link https://s.shopee.co.id/xxxx --qc-file data/qc-rak-piring.json --qc-ok --dry-run
  python tools/publish_video.py ... --live   # kirim beneran (butuh approval Kyan)

Format --qc-file (JSON, semua harus true):
  {"produk_sama_persis": true, "label_tidak_ngaco": true,
   "suara_nyambung": true, "tanpa_kata_terlarang": true}
  Artinya manusia sudah MENONTON videonya dan memastikan:
  - produk di video sama persis seperti di foto (kemasan/warna/bentuk/label)
  - teks label tidak ngaco (kesalahan umum video AI)
  - suara/voiceover nyambung dengan gambar
  - caption tidak mengandung kata terlarang (dicek ulang otomatis juga)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor" / "threads-affiliate"
sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(ROOT / "tools"))

from check_draft import check_chain  # noqa: E402
from threads_poster.content_generator import ContentGenerator  # noqa: E402

MAX_SIZE_BYTES = 1_000_000_000  # 1 GB — batas video Threads
MAX_DURATION_S = 5 * 60         # 5 menit — batas video Threads
ALLOWED_EXTS = {".mp4", ".mov"}
LOG_PATH = ROOT / "data" / "video_publish_log.json"
QC_KEYS = ("produk_sama_persis", "label_tidak_ngaco",
           "suara_nyambung", "tanpa_kata_terlarang")


# --- Validasi video ---------------------------------------------------------

def probe_video(path: Path) -> dict:
    """Cek file video: ada, ekstensi, ukuran, durasi (ffprobe bila ada)."""
    if not path.exists():
        raise FileNotFoundError(f"File video tidak ditemukan: {path}")
    if path.suffix.lower() not in ALLOWED_EXTS:
        raise ValueError(
            f"Ekstensi {path.suffix} tidak didukung — pakai .mp4 / .mov.")
    size = path.stat().st_size
    if size > MAX_SIZE_BYTES:
        raise ValueError(
            f"Ukuran {size / 1e6:.1f} MB melebihi batas Threads 1 GB.")
    info: dict = {"size_bytes": size, "duration_s": None}
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(path)],
            capture_output=True, text=True, timeout=30, check=True)
        fmt = json.loads(out.stdout).get("format", {})
        dur = fmt.get("duration")
        if dur is not None:
            info["duration_s"] = float(dur)
            if info["duration_s"] > MAX_DURATION_S:
                raise ValueError(
                    f"Durasi {info['duration_s']:.1f} dtk melebihi batas "
                    f"Threads 5 menit.")
    except FileNotFoundError:
        print("⚠️  ffprobe tidak ditemukan — durasi tidak dicek, "
              "hanya ukuran file.")
    return info


# --- QC manusia -------------------------------------------------------------

def load_qc(path: Path) -> dict:
    """Baca checklist QC. Semua item HARUS true, kalau tidak = gagal."""
    if not path.exists():
        raise FileNotFoundError(f"File checklist QC tidak ditemukan: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in QC_KEYS if k not in data]
    if missing:
        raise ValueError(f"Checklist QC kurang item: {', '.join(missing)}.")
    failed = [k for k in QC_KEYS if data[k] is not True]
    if failed:
        raise ValueError(
            f"QC TIDAK LOLOS — item belum dicentang: {', '.join(failed)}. "
            f"Tonton ulang videonya, jangan dipaksakan.")
    return data


# --- Caption ----------------------------------------------------------------

def build_caption(product: str, category: str, link: str,
                  templates_dir: Path, attempts: int = 5) -> tuple[str, str]:
    """Bangun rantai 2 post dari template v5.1 (pola run_slot.py --api).

    Post 1 = hook (teks di post video). Post 2 = isi + CTA + link
    (self-reply pertama). Ulangi sampai keduanya muat 500 karakter.
    """
    gen = ContentGenerator(templates_dir)
    last: tuple[str, str] | None = None
    for attempt in range(attempts):
        chain = gen.generate_chain(
            product=product, affiliate_link=link, category=category,
            num_posts=2)
        body = gen.generate_post2(product, category)
        post_1 = chain["post_1"]
        post_2 = f"{body}\n\n{chain['post_2']}\n{link}"
        last = (post_1, post_2)
        if len(post_1) <= 500 and len(post_2) <= 500:
            return post_1, post_2
        print(f"⚠️  Percobaan {attempt + 1}: rantai "
              f"{len(post_1)}/{len(post_2)} karakter — coba varian lain.")
    raise ValueError(
        f"Tidak ada varian rantai yang muat 500 karakter setelah {attempts}x "
        f"(terakhir {len(last[0])}/{len(last[1])}).")


# --- Publish video via Threads API ------------------------------------------

def publish_video(video_url: str, caption: str, wait_s: int = 120) -> dict:
    """Publish satu video. Kembalikan {'id', 'permalink'}.

    Threads API: container media_type=VIDEO dengan video_url publik,
    poll status sampai FINISHED, lalu /me/threads_publish.
    Fungsi ini TIDAK PERNAH mencetak token (lihat publish_api.py).
    """
    import publish_api

    container = publish_api._post("/me/threads", {
        "media_type": "VIDEO", "video_url": video_url, "text": caption,
    })
    cid = container["id"]
    deadline = time.time() + wait_s
    while True:
        st = publish_api._get(f"/{cid}", {"fields": "status"})
        status = st.get("status", "")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"Container video {cid} ERROR: {st}")
        if time.time() > deadline:
            raise RuntimeError(
                f"Container video {cid} belum FINISHED setelah {wait_s} dtk: "
                f"{st}")
        time.sleep(5)
    pub = publish_api._post("/me/threads_publish", {"creation_id": cid})
    pid = pub["id"]
    try:
        permalink = publish_api._get(
            f"/{pid}", {"fields": "permalink"}).get("permalink")
    except Exception:
        permalink = None
    return {"id": pid,
            "permalink": permalink or f"https://www.threads.com/@{publish_api.USERNAME}/post/{pid}"}


# --- Log --------------------------------------------------------------------

def append_log(entry: dict, path: Path = LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if path.exists():
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append(entry)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2),
                    encoding="utf-8")


# --- Main -------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Publish video Flow ke Threads")
    ap.add_argument("--video", type=Path, required=True,
                    help="File video lokal (.mp4/.mov) hasil Google Flow")
    ap.add_argument("--video-url", default=None,
                    help="URL PUBLIK video (wajib untuk --live; Threads API "
                         "tidak menerima upload file langsung)")
    ap.add_argument("--product", required=True,
                    help="Nama pendek produk (sesuai DB)")
    ap.add_argument("--category", required=True,
                    choices=["dapur", "organizer", "kebersihan"])
    ap.add_argument("--link", required=True,
                    help="Link affiliate s.shopee.co.id (ditempel di post 2)")
    ap.add_argument("--qc-file", type=Path, required=True,
                    help="File JSON checklist QC (4 item, semua true)")
    ap.add_argument("--qc-ok", action="store_true",
                    help="Pernyataan manusia: video SUDAH ditonton dan QC lolos")
    ap.add_argument("--templates", type=Path,
                    default=ROOT / "templates")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="Hanya tampilkan caption + guardrail + payload "
                         "(default aman)")
    ap.add_argument("--live", action="store_true",
                    help="KIRIM beneran (wajib eksplisit + approval Kyan)")
    args = ap.parse_args()
    live = args.live
    now = datetime.now().isoformat(timespec="seconds")

    # 1. Validasi file video
    try:
        info = probe_video(args.video)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        return 1
    dur = info["duration_s"]
    print(f"🎬 Video: {args.video.name} — {info['size_bytes'] / 1e6:.2f} MB" +
          (f", {dur:.1f} dtk" if dur is not None else ", durasi tak dicek"))

    # 2. QC manusia — TIDAK BISA di-skip, di dry-run sekalipun
    if not args.qc_ok:
        print("❌ BATAL: tambahkan flag --qc-ok — artinya kamu SUDAH "
              "menonton videonya dan QC lolos. Tanpa ini skrip tidak jalan.")
        return 1
    try:
        load_qc(args.qc_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ QC gagal: {e}")
        return 1
    print("✅ QC checklist lolos (4/4 item dicentang manusia).")

    # 3. Bangun caption + guardrail
    try:
        post_1, post_2 = build_caption(args.product, args.category,
                                       args.link, args.templates)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        return 1
    problems = check_chain([post_1, post_2], args.link)
    errors = [p for p in problems if p["level"] == "ERROR"]
    for p in problems:
        mark = "❌" if p["level"] == "ERROR" else "⚠️"
        print(f"{mark} [{p['rule']}] {p['detail']}")
    if errors:
        print("❌ BATAL: caption ditolak guardrails.")
        return 1
    print(f"\n--- post 1 / video ({len(post_1)} karakter) ---\n{post_1}")
    print(f"\n--- post 2 / reply ({len(post_2)} karakter) ---\n{post_2}")

    # 4. Payload video (container Threads API)
    if not live:
        payload = {"media_type": "VIDEO",
                   "video_url": args.video_url or "<BELUM ADA — isi --video-url>",
                   "text": post_1}
        print("\n--- payload container (DRY-RUN, tidak dikirim) ---")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if not args.video_url:
            print("\n⚠️  Mode live butuh --video-url: video harus di-host di "
                  "URL publik dulu (Threads API tidak menerima file lokal).")
        print("\n✅ DRY RUN LOLOS (tidak posting, tidak panggil API).")
        append_log({"date": now, "status": "dry-run",
                    "product": args.product, "category": args.category,
                    "video": str(args.video), "video_url": args.video_url,
                    "post_1": post_1, "post_2": post_2})
        return 0

    # 5. Live — wajib ada URL publik
    if not args.video_url:
        print("❌ BATAL: --live butuh --video-url (URL publik video). "
              "Upload dulu videonya ke hosting publik, lalu ulangi.")
        return 1
    try:
        import publish_api
        res = publish_video(args.video_url, post_1)
        res2 = publish_api.publish_text(post_2, reply_to=res["id"])
    except Exception as e:  # noqa: BLE001 — catat & laporkan
        print(f"❌ Publish video gagal: {e}")
        append_log({"date": now, "status": "failed",
                    "product": args.product, "category": args.category,
                    "video": str(args.video), "video_url": args.video_url,
                    "error": str(e)[:300]})
        return 5
    print(f"\n✅ Video terkirim: {res['permalink']}")
    print(f"✅ Reply terkirim: {res2['permalink']}")
    append_log({"date": now, "status": "posted",
                "product": args.product, "category": args.category,
                "video": str(args.video), "video_url": args.video_url,
                "post_url": res["permalink"],
                "reply_url": res2["permalink"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
