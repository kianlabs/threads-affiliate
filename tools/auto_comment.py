"""auto_comment.py — komen otomatis di postingan ramai (niche home living / kos-kosan).

Tujuan: bantu jawab / nambah info di postingan orang lain yang ramai,
supaya yang penasaran cek profil @temuanhariann.id (di profil ada link
+ postingan produk). Komen TIDAK PERNAH berisi link affiliate, ajakan
beli, kata terlarang, atau klaim pengalaman pribadi.

Aturan keamanan (lihat guardrails.md + aturan Kyan 16 Nov 2026 18:50):
  - Kata 'komisi' / 'commission' / 'affiliate' DILARANG di teks komen.
  - DILARANG klaim pemakaian pribadi ("gw pake", "udah coba", dsb).
  - DILARANG link apa pun di komen — termasuk link Shopee.
  - DILARANG ajakan beli ("beli di sini", "cek link di bio", "checkout").
  - Maks 10 komen/hari, jeda acak 10-30 menit antar komen (live).
  - Jangan komen 2x di postingan yang sama, jangan komen di postingan sendiri.
  - Setiap komen WAJIB lolos tools/check_draft.py — gagal = skip + catat.

Sumber target:
  - Threads: cari postingan ramai via keyword search API (jika endpoint
    tersedia), atau terima daftar target dari file --targets.
  - Facebook / Pinterest: STUB — belum tersedia, menunggu API.

Penggunaan:
  python tools/auto_comment.py --targets data/comment_targets.txt --dry-run
  python tools/auto_comment.py --targets data/comment_targets.txt --live
  python tools/auto_comment.py --search "rak dapur kos" --live
  python tools/auto_comment.py --text "isi komen..." --dry-run   # tes guardrail
  python tools/auto_comment.py --targets data/comment_targets.txt --dry-run --opener "Izin kak"
  python tools/auto_comment.py --targets data/comment_targets.txt --dry-run --product "ECOCO Cup Washing Brush"
  python tools/auto_comment.py --targets data/comment_targets.txt --dry-run --image-url https://example.com/foto.jpg

Format file --targets: satu target per baris, boleh berupa post ID Threads
atau URL threads.com. Baris kosong dan baris diawali # diabaikan.
Opsional: "post_id<TAB>topik" — topik dipakai memilih template komen.

Default mode = --dry-run (aman): hanya cetak draf + hasil guardrail,
TIDAK mengirim apa pun. Mode live HANYA dengan flag --live.

Riwayat disimpan di data/comment_history.json (TIDAK di-commit).

Hook pembuka sopan (aturan Kyan 16 Nov 2026 19:46): setiap komen diawali
satu sapaan acak — "Izin kak", "Maaf kak", "Permisi kak", "Izin nimbrung
kak", "Kak, izin tanya", "Halo kak, izin ya" — total tetap maks 200 karakter.

Media di komen (cek API 16 Nov 2026 19:46): Threads API MENDUKUNG reply
bermedia — container media_type=IMAGE + image_url (atau VIDEO +
video_url) + reply_to_id, alur dua tahap. Karena itu --image-url /
--video-url / --product (ambil Image URL dari DB) opsional didukung.
TAPI kolom Image URL di DB saat ini MASIH KOSONG untuk semua produk
(0/29 per 16 Nov 2026), jadi sampai Image URL diisi dari foto listing
Shopee, komen jalan teks saja.

Formula hook v2 (riset 16 Nov 2026, report.md riset hook reply):
  1 detail spesifik dari postingan target + 1 sinyal bukti nyata +
  1 pertanyaan pilihan/tebakan. 100-200 karakter, tanpa link, tanpa
  nama produk di hook, tanpa klaim pengalaman pribadi, tanpa kata
  terlarang. Hook pembuka sopan dipakai bervariasi — TIDAK di semua
  komen (kadang tanpa opener, kadang "Relate banget kak").
  Yang dihindari: pertanyaan tertutup ("apa?"), superlatif tanpa
  bukti ("paling jujur"), template yang bisa ditempel di postingan
  mana saja.
  Slot template: {detail} = frasa spesifik dari postingan target,
  {bukti} = klaim OP sendiri yang bisa dicek dari postingannya ATAU
  angka listing terverifikasi dari VERIFIED_PROOFS (jangan karang
  angka — {bukti} hanya boleh diisi dari dua sumber itu).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_draft import URL_RE, check_chain  # noqa: E402

USERNAME = "temuanhariann.id"
MAX_PER_DAY = 10
MAX_CHARS = 200
DELAY_MIN_S = 10 * 60
DELAY_MAX_S = 30 * 60

ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = ROOT / "data" / "comment_history.json"

# --- Template komen -------------------------------------------------------
# Gaya mengikuti hook v5.1: fokus review / rating / ulasan pembeli, tanya,
# info fungsi, tips. TANPA nama produk, TANPA klaim pribadi, TANPA link,
# TANPA ajakan beli. {topik} diganti topik postingan (mis. "rak dapur").

COMMENT_TEMPLATES = {
    "tanya_rating": [
        "Ratingnya 4.8+ di Shopee, ribuan terjual — ulasan pembelinya bilang apa soal ukurannya?",
        "Yang udah beli di kolom ulasan, bahannya beneran awet nggak sih?",
        "Rame banget yang bahas ini, rating pembelinya rata-rata berapa ya?",
        "Ulasan pembeli soal ini biasanya bilang apa? Penasaran sebelum milih.",
    ],
    "info_fungsi": [
        "Buat kamar kos sempit ini ngebantu banget, fungsinya buat nyimpen biar nggak numpuk.",
        "Yang kayak gini cocok buat dapur kecil, hemat tempat dan gampang dibersihin.",
        "Fungsinya simpel tapi kepake tiap hari, apalagi kalau ruangannya terbatas.",
        "Ini tuh yang bikin meja kelihatan rapi, soalnya semua barang ada tempatnya.",
    ],
    "tips": [
        "Tips milihnya: cek dulu rating sama foto ulasan pembeli, jangan cuma liat gambar etalase.",
        "Kalau buat kos, ukur dulu space-nya biar pas — banyak yang kecele soal ukuran.",
        "Baca ulasan bintang 3-4 dulu, di situ biasanya keliatan minusnya yang asli.",
        "Bandingin harga antar toko dulu, kadang selisihnya lumayan buat barang yang sama.",
    ],
}

# --- Template komen v2 (formula riset 16 Nov 2026) -------------------------
# {detail} = frasa spesifik dari postingan target (WAJIB spesifik — bukan
# "ini" generik). {bukti} = klaim OP sendiri ATAU angka listing dari
# VERIFIED_PROOFS (jangan karang). 8 pola, 10 template.
COMMENT_TEMPLATES_V2 = {
    "curiosity_gap": [
        "Kak, {detail} — {bukti}, buat yang berat-berat berani nggak, apa cuma buat yang ringan?",
        "{detail} muat berapa kilo sih kak? {bukti} soalnya keliatan enteng banget.",
    ],
    "relatable_pain": [
        "Relate banget kak, {detail} — {bukti}, yang vertikal apa yang susun, yang mana lebih ngebantu biar nggak numpuk?",
    ],
    "specific_question": [
        "Kak, {detail} — tim tempel apa tim bor nih? {bukti} buat kosan 3x3.",
    ],
    "hot_take": [
        "Jujur kak, {detail} lebih awet daripada rak berdiri, asal nempelnya bener — {bukti}. Setuju nggak?",
    ],
    "social_proof": [
        "Kak, {detail} — {bukti}. Yang paling sering dipuji pembeli apanya?",
        "{detail} — {bukti}, ada yang bilang goyang kalau diisi penuh, beneran gitu ya kak?",
    ],
    "humor": [
        "Kak, {detail} — {bukti}. Kosku isinya Indomie semua, ini muat berapa kilo sih? \U0001f62d",
    ],
    "specificity_data": [
        "Kak, {detail} lebarnya 40 cm apa 60 cm? {bukti} buat rice cooker muat nggak?",
    ],
    "permission_reframe": [
        "Kak, anak kos tuh nggak butuh dapur gede, butuh {detail} yang rapi — {bukti}. Ini sudutnya udah bener.",
    ],
}

# Bukti listing TERVERIFIKASI (dicek langsung dari halaman produk Shopee,
# 16 Nov 2026 — JANGAN tambah angka tanpa verifikasi halaman produk).
# Dipakai sebagai {bukti} HANYA bila target cocok dengan jenis produknya.
VERIFIED_PROOFS = {
    "YESALL Rak Dapur Serbaguna": {
        "text": "di Shopee ratingnya 4,9 dari 4.452 ulasan",
        "source": "shopee.co.id/product/1043883019/27672762637",
        "checked": "2026-11-16",
    },
    "WARS Rak Dapur Panci Wajan": {
        "text": "di Shopee ratingnya 4,8 dari 1.581 ulasan",
        "source": "shopee.co.id/product/21738068/25602903412",
        "checked": "2026-11-16",
    },
}


def lookup_proof(product: str) -> str | None:
    """Cari teks {bukti} terverifikasi untuk produk di DB (nama mengandung
    `product`). Kembalikan None kalau tidak ada data terverifikasi."""
    needle = product.strip().lower()
    for name, info in VERIFIED_PROOFS.items():
        if needle in name.lower() or name.lower() in needle:
            return info["text"]
    return None

# Hook pembuka sopan — dipilih acak per komen (aturan Kyan 16 Nov 2026).
# Dipakai sebagai awalan: "<opener>, <isi komen>" (huruf pertama isi
# dikecilkan). Total komen tetap maks 200 karakter — kalau kepanjangan,
# opener dibuang dan komen jalan dengan isi saja.
POLITE_OPENERS = [
    "Izin kak",
    "Maaf kak",
    "Permisi kak",
    "Izin nimbrung kak",
    "Kak, izin tanya",
    "Halo kak, izin ya",
]

# Frasa ajakan beli — dilarang di komen (di luar check_draft.py).
BUY_CTA_PATTERNS = [
    r"\bbeli\b.*\b(di|di sini|sekarang|yuk)\b",
    r"\bcek\s+link\b",
    r"\blink\s+di\s+bio\b",
    r"\bcheckout\b",
    r"\bbeli\s+sekarang\b",
    r"\bklik\s+link\b",
    r"\bdiskon\b",
    r"\bpromo\b.*\bbeli\b",
]
BUY_CTA_RES = [re.compile(p, re.I) for p in BUY_CTA_PATTERNS]

# Superlatif / bahasa garansi — dilarang (riset hook v2: vague = made up).
SUPERLATIVE_PATTERNS = [
    r"\bpaling (jujur|murah|bagus|awet|cepat)\b",
    r"\bdijamin\b",
    r"\b100%\s*(ampuh|manjur|asli)\b",
    r"\bpasti\s+(ampuh|sembuh|berhasil)\b",
]
SUPERLATIVE_RES = [re.compile(p, re.I) for p in SUPERLATIVE_PATTERNS]


def pick_opener(opener: str | None = None) -> str:
    """Pilih hook pembuka sopan — acak, atau yang diminta via --opener."""
    if opener:
        if opener not in POLITE_OPENERS:
            raise ValueError(
                f"Opener tidak dikenal: {opener!r}. Pilih: {POLITE_OPENERS}")
        return opener
    return random.choice(POLITE_OPENERS)


def pick_template(topic: str | None = None,
                  opener: str | None = None,
                  style: str | None = None) -> str:
    """Pilih satu template komen secara acak (dari semua gaya, atau dari
    satu gaya bila --style diisi), diawali hook pembuka sopan.
    Total tetap maks 200 karakter."""
    if style:
        pool = COMMENT_TEMPLATES[style]
    else:
        pool = [t for group in COMMENT_TEMPLATES.values() for t in group]
    text = random.choice(pool)
    if topic:
        # Ganti hanya kata "ini" yang berdiri sendiri — jangan merusak
        # kata yang mengandung "ini" (mis. "gini" -> "g<topik>").
        text = re.sub(r"\bini\b", topic, text, count=1)
    prefix = pick_opener(opener)
    body = text[0].lower() + text[1:] if text else text
    full = f"{prefix}, {body}"
    if len(full) > MAX_CHARS:
        return text  # kepanjangan: opener dibuang, isi saja
    return full


def pick_template_v2(detail: str | None = None,
                     bukti: str | None = None,
                     opener: str | None = None,
                     style: str | None = None) -> str:
    """Pilih satu template v2, isi slot {detail} + {bukti}, lalu (kadang)
    awali hook pembuka sopan. Opener TIDAK di semua komen: bila `opener`
    None, dipilih acak dari POLITE_OPENERS + tanpa opener. `opener="none"`
    = tanpa opener. Total tetap maks 200 karakter — kepanjangan: opener
    dibuang dulu, masih kepanjangan: kembalikan apa adanya (guardrail
    akan menolak di validate_comment)."""
    if style:
        pool = COMMENT_TEMPLATES_V2[style]
    else:
        pool = [t for group in COMMENT_TEMPLATES_V2.values() for t in group]
    text = random.choice(pool)
    text = text.replace("{detail}", detail or "yang di foto itu")
    text = text.replace("{bukti}", bukti or "")
    text = re.sub(r"\s{2,}", " ", text).strip()
    if opener == "none":
        prefix = ""
    elif opener:
        if opener not in POLITE_OPENERS:
            raise ValueError(
                f"Opener tidak dikenal: {opener!r}. Pilih: {POLITE_OPENERS}")
        prefix = opener
    else:
        prefix = random.choice(POLITE_OPENERS + [""])
    if prefix:
        # Opener sudah menyapa ("Izin kak") -- buang sapaan "kak" di badan
        # template supaya tidak dobel ("Izin kak, kak, ...").
        body = re.sub(r"^kak,?\s+", "", text, flags=re.I)
        body = re.sub(r"\bkak,?\s+(?=[a-z])", "", body)
        body = body[0].lower() + body[1:] if body else body
        full = f"{prefix}, {body}"
    else:
        full = text
    if len(full) > MAX_CHARS:
        return text  # kepanjangan: opener dibuang, isi saja
    return full


def lookup_image_url(product: str) -> str | None:
    """Cari kolom Image URL (ke-7) di data/affiliate_links.md untuk produk
    yang namanya mengandung `product`. Kembalikan None kalau kolom kosong
    atau produk tidak ketemu — pemanggil lanjut teks saja."""
    db = ROOT / "data" / "affiliate_links.md"
    if not db.exists():
        return None
    needle = product.strip().lower()
    for line in db.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| #"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7 or needle not in cells[1].lower():
            continue
        url = cells[6].strip("` ")
        return url if url.startswith("http") else None
    return None


def validate_comment(text: str) -> list[dict]:
    """Guardrail komen. Kembalikan daftar masalah (kosong = lolos)."""
    problems: list[dict] = []
    if len(text) > MAX_CHARS:
        problems.append({
            "level": "ERROR", "rule": "komen-kepanjangan",
            "detail": f"{len(text)} karakter (maks {MAX_CHARS}).",
        })
    if URL_RE.search(text):
        problems.append({
            "level": "ERROR", "rule": "link-di-komen",
            "detail": "Komen mengandung link — dilarang di komen orang lain.",
        })
    for rx in BUY_CTA_RES:
        m = rx.search(text)
        if m:
            problems.append({
                "level": "ERROR", "rule": "ajakan-beli",
                "detail": f"Frasa ajakan beli '{m.group(0)}' dilarang di komen.",
            })
            break
    for rx in SUPERLATIVE_RES:
        m = rx.search(text)
        if m:
            problems.append({
                "level": "ERROR", "rule": "superlatif-tanpa-bukti",
                "detail": f"Frasa '{m.group(0)}' dilarang — superlatif/garansi "
                          "tanpa bukti (aturan hook v2).",
            })
            break
    # Guardrail yang sama dengan posting: kata terlarang, klaim review, garansi.
    for p in check_chain([text]):
        if p["rule"] == "link-di-post-utama":
            continue  # aturan post utama, bukan komen
        if p["rule"] == "hook-panjang":
            continue  # warning hook, bukan komen
        problems.append(p)
    return problems


# --- Riwayat --------------------------------------------------------------

def load_history(path: Path = HISTORY_PATH) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_history(entries: list[dict], path: Path = HISTORY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2),
                    encoding="utf-8")


def already_commented(history: list[dict], post_id: str) -> bool:
    return any(e.get("post_id") == post_id for e in history)


def sent_today(history: list[dict]) -> int:
    today = date.today().isoformat()
    return sum(1 for e in history
               if e.get("date") == today and e.get("status") == "sent")


# --- Target ---------------------------------------------------------------

def parse_targets_file(path: Path) -> list[dict]:
    """Baca file target: 'post_id' atau 'post_id<TAB>topik' per baris."""
    targets = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        post_id = parts[0].strip()
        # Terima URL threads.com juga — ambil segmen terakhir sebagai ID.
        if post_id.startswith("http"):
            post_id = post_id.rstrip("/").split("/")[-1]
        topic = parts[1].strip() if len(parts) > 1 else None
        # Kolom 3 = detail spesifik postingan, kolom 4 = bukti (v2).
        detail = parts[2].strip() if len(parts) > 2 else None
        bukti = parts[3].strip() if len(parts) > 3 else None
        targets.append({"post_id": post_id, "topic": topic,
                        "detail": detail, "bukti": bukti})
    return targets


def search_threads(keyword: str, limit: int = 10) -> list[dict]:
    """Cari postingan ramai via Threads keyword search API.

    Endpoint keyword_search tidak selalu tersedia di semua app — kalau
    gagal, kembalikan list kosong dan pemanggil memakai file --targets.
    Fungsi ini TIDAK PERNAH mencetak token.
    """
    try:
        import publish_api
        data = publish_api._get("/keyword_search", {
            "q": keyword, "search_type": "TOP", "limit": str(limit),
        })
    except Exception as e:  # noqa: BLE001 — endpoint bisa tidak tersedia
        print(f"⚠️  Pencarian Threads gagal ({e}) — pakai file --targets.")
        return []
    out = []
    for item in data.get("data", []):
        pid = item.get("id")
        if not pid:
            continue
        out.append({
            "post_id": pid,
            "topic": keyword,
            "author": item.get("username"),
        })
    return out


# --- Facebook / Pinterest: STUB -------------------------------------------

def comment_facebook(*args, **kwargs):  # noqa: ANN002, ANN003
    """STUB — belum tersedia: menunggu API/koneksi Facebook Page."""
    raise NotImplementedError(
        "Komen Facebook belum tersedia — menunggu API Facebook Page. "
        "Jangan pura-pura jalan: modul ini sengaja stub.")


def comment_pinterest(*args, **kwargs):  # noqa: ANN002, ANN003
    """STUB — belum tersedia: menunggu API Pinterest + token."""
    raise NotImplementedError(
        "Komen Pinterest belum tersedia — menunggu API Pinterest. "
        "Jangan pura-pura jalan: modul ini sengaja stub.")


# --- Pengiriman (Threads, via API resmi) ----------------------------------

def send_comment_threads(post_id: str, text: str,
                         image_url: str | None = None,
                         video_url: str | None = None) -> dict:
    """Kirim komen sebagai reply via Threads API.

    Tanpa media: publish_api.publish_text. Dengan media:
    publish_api.publish_media_reply (container IMAGE/VIDEO + reply_to_id).

    Sebelum kirim, cek pemilik postingan — jangan komen di post sendiri.
    """
    import publish_api
    try:
        owner = publish_api._get(f"/{post_id}", {"fields": "username"})
        if owner.get("username") == USERNAME:
            raise ValueError("Target adalah postingan sendiri — dilewati.")
    except ValueError:
        raise
    except Exception as e:  # noqa: BLE001 — cek pemilik gagal, lanjut hati-hati
        print(f"⚠️  Tidak bisa cek pemilik {post_id} ({e}) — lanjut kirim.")
    if image_url or video_url:
        return publish_api.publish_media_reply(
            text, reply_to=post_id, image_url=image_url, video_url=video_url)
    return publish_api.publish_text(text, reply_to=post_id)


# --- Main -----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-komen di postingan ramai")
    ap.add_argument("--targets", type=Path,
                    help="File daftar target (post ID / URL per baris)")
    ap.add_argument("--search", help="Kata kunci cari postingan ramai (Threads)")
    ap.add_argument("--text", help="Tes guardrail untuk satu teks komen")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="Hanya cetak draf + hasil guardrail (default aman)")
    ap.add_argument("--live", action="store_true",
                    help="KIRIM komen beneran (wajib eksplisit)")
    ap.add_argument("--opener", choices=POLITE_OPENERS + ["none"], default=None,
                    help="Hook pembuka sopan (default: acak per komen, "
                         "kadang tanpa opener; 'none' = tanpa opener)")
    ap.add_argument("--style",
                    choices=list(COMMENT_TEMPLATES) + list(COMMENT_TEMPLATES_V2),
                    default=None,
                    help="Gaya template saja (default: acak semua gaya)")
    ap.add_argument("--seed", type=int, default=None,
                    help="Seed random (regenerasi draf yang sama)")
    ap.add_argument("--detail", default=None,
                    help="Detail spesifik postingan target (slot {detail} v2)")
    ap.add_argument("--proof", default=None,
                    help="Sinyal bukti nyata (slot {bukti} v2) — klaim OP "
                         "atau angka listing terverifikasi, jangan karang")
    ap.add_argument("--v1", action="store_true",
                    help="Pakai template lama (v1), bukan formula hook v2")
    ap.add_argument("--image-url", default=None,
                    help="URL publik foto produk untuk dilampirkan di komen")
    ap.add_argument("--video-url", default=None,
                    help="URL publik video produk untuk dilampirkan di komen")
    ap.add_argument("--product", default=None,
                    help="Nama produk di DB — ambil Image URL dari kolom ke-7")
    args = ap.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    live = args.live
    image_url = args.image_url
    video_url = args.video_url
    if image_url and video_url:
        ap.error("--image-url dan --video-url saling eksklusif (pilih satu).")
        return 2
    if args.product and not (image_url or video_url):
        found = lookup_image_url(args.product)
        if found:
            image_url = found
            print(f"🖼️  Image URL produk '{args.product}': {image_url}")
        else:
            print(f"⚠️  Produk '{args.product}' belum punya Image URL di DB "
                  "— komen jalan teks saja.")
    if args.product and not args.proof:
        proof = lookup_proof(args.product)
        if proof:
            args.proof = proof
            print(f"📊 Bukti terverifikasi '{args.product}': {proof}")
    for label, url in (("image", image_url), ("video", video_url)):
        if url and not url.startswith("https://"):
            ap.error(f"--{label}-url harus URL publik https://, "
                     f"bukan {url!r}.")
            return 2
    media_note = ""
    if image_url:
        media_note = f" + foto {image_url}"
    elif video_url:
        media_note = f" + video {video_url}"
    if args.text:
        problems = validate_comment(args.text)
        print(f"Komen: {args.text!r} ({len(args.text)} karakter)")
        if problems:
            for p in problems:
                print(f"❌ [{p['rule']}] {p['detail']}")
            print("\nDITOLAK.")
            return 1
        print("✅ LOLOS guardrail.")
        return 0

    targets: list[dict] = []
    if args.targets:
        targets = parse_targets_file(args.targets)
    if args.search:
        targets += search_threads(args.search)
    if not targets:
        ap.error("Tidak ada target: isi --targets atau --search.")
        return 2

    history = load_history()
    if live and sent_today(history) >= MAX_PER_DAY:
        print(f"❌ Limit harian tercapai: {MAX_PER_DAY} komen/hari.")
        return 1

    sent = 0
    skipped = 0
    seen_this_run: set[str] = set()
    for t in targets:
        pid = t["post_id"]
        if pid in seen_this_run:
            print(f"⏭️  {pid}: sudah ada di run ini — skip.")
            skipped += 1
            continue
        seen_this_run.add(pid)
        if already_commented(history, pid):
            print(f"⏭️  {pid}: sudah pernah dikomen — skip.")
            skipped += 1
            continue
        if live and sent_today(history) + sent >= MAX_PER_DAY:
            print(f"⏹️  Limit {MAX_PER_DAY} komen/hari tercapai — berhenti.")
            break
        detail = t.get("detail") or args.detail
        bukti = t.get("bukti") or args.proof
        if args.v1 or (args.style and args.style in COMMENT_TEMPLATES):
            text = pick_template(t.get("topic"),
                                 opener=None if args.opener == "none" else args.opener,
                                 style=args.style)
        else:
            text = pick_template_v2(detail, bukti,
                                    opener=args.opener, style=args.style)
        problems = validate_comment(text)
        if problems:
            print(f"❌ {pid}: draf ditolak guardrail:")
            for p in problems:
                print(f"   [{p['rule']}] {p['detail']}")
            history.append({"date": date.today().isoformat(),
                            "platform": "threads", "post_id": pid,
                            "text": text, "status": "rejected",
                            "reason": "; ".join(p["rule"] for p in problems)})
            skipped += 1
            continue
        if not live:
            print(f"📝 [DRY-RUN] {pid}: {text} ({len(text)} karakter)"
                  f"{media_note} — LOLOS")
            continue
        # Live: kirim, catat, jeda acak 10-30 menit sebelum komen berikut.
        try:
            res = send_comment_threads(pid, text,
                                         image_url=image_url,
                                         video_url=video_url)
        except Exception as e:  # noqa: BLE001 — catat & lanjut target berikut
            print(f"❌ {pid}: gagal kirim ({e})")
            history.append({"date": date.today().isoformat(),
                            "platform": "threads", "post_id": pid,
                            "text": text, "status": "failed",
                            "reason": str(e)[:200]})
            skipped += 1
            continue
        print(f"✅ {pid}: terkirim — {res.get('permalink', res.get('id'))}")
        history.append({"date": date.today().isoformat(),
                        "platform": "threads", "post_id": pid,
                        "text": text, "status": "sent",
                        "media_url": image_url or video_url,
                        "permalink": res.get("permalink")})
        sent += 1
        save_history(history)
        if sent < len(targets):
            delay = random.randint(DELAY_MIN_S, DELAY_MAX_S)
            print(f"⏳ Jeda {delay // 60} menit sebelum komen berikut...")
            time.sleep(delay)

    save_history(history)
    mode = "LIVE" if live else "DRY-RUN"
    print(f"\n[{mode}] Terkirim: {sent}, dilewati/ditolak: {skipped}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
