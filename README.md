# Sistem Affiliate Shopee → Threads (v1)

**Akun:** @temuanhariann.id · **Niche awal:** home living / kos-kosan
**Status:** LIVE 16 Nov 2026 — posting via Threads API resmi 3x/hari (09:00 dapur / 12:30 organizer / 19:30 kebersihan, systemd timer di PC). Post pertama 17:51 Kikkoman, terverifikasi via API. Pinterest: modul siap, token belum ada (dry-run saja).

Sistem full-auto gratis: link Shopee dari database manual → draf dicek
guardrails → posting otomatis 3x/hari (09:00 / 12:30 / 19:30 WIB) via
Threads API resmi (`graph.threads.net`, `tools/run_slot.py --api`).
Playwright + cookie kini jalur cadangan saja. Pinterest: 1 Pin/hari via
Pinterest API v5 (`tools/run_pinterest.py`, timer DISABLED — lihat bawah).

## Arsitektur v1

```
config.yaml                  kriteria produk, jadwal, format post
data/affiliate_links.md      database link (Markdown, diisi manual)
templates/                   template v1 — gaya "intip produk" (ditulis ulang)
tools/run_slot.py            satu slot posting: ambil link → generate →
                             cek guardrails → cek dedup → posting → tandai USED
tools/check_draft.py         checker guardrails (bisa dipakai terpisah)
vendor/threads-affiliate/    kode basis (d4ncboz, MIT) + 1 perbaikan Linux
ops/crontab.txt              jadwal cron WIB untuk PC
```

Alur tiap slot (dijalankan `tools/run_slot.py --slot HH:MM`):

1. Ambil link UNUSED berikutnya dari database (kategori sesuai slot).
2. Generate rantai **2 post**: post 1 = hook (tanpa link, tanpa nama
   produk), post 2 = isi "intip produk" fokus review + CTA TANPA kata-kata
   terlarang (aturan Kyan 16 Nov 2026 18:50); link ditempel
   poster di post 2 (= self-reply pertama, BUKAN post utama).
3. `check_draft.py` memeriksa: tanpa klaim "review", tanpa bahasa garansi,
   disclosure ada, ≤500 karakter/post, link `s.shopee.co.id`. Gagal → batal.
4. Dedup: link tidak boleh dipakai ulang; gaya hook tidak boleh sama dengan
   2 post terakhir; kemiripan hook ≤60% dengan 5 post terakhir.
5. Posting via Threads API resmi. Sukses → catat history + tandai link
   USED. Gagal → exit code non-nol, log. (Jalur Playwright + cookie
   masih tersedia sebagai cadangan: jalankan tanpa `--api`.)

## Kenapa v1 tidak pakai API resmi

**Shopee Affiliate Open API — TERTAHAN.** Dicek langsung di dashboard
16 Nov 2026 (akun 'pratama', login Google berhasil): menu Open API ADA,
tapi AppID/Secret kosong (`--`), tombol Apply nonaktif, halaman bilang
hubungi Shopee untuk minta akses. Link "contact us"-nya malah nyasar ke
artikel Help Center soal pelanggaran & penalti — bukan form pengajuan.
Satu-satunya jalur: hubungi CS Shopee via live chat. Sampai akses disetujui,
produk HANYA bisa masuk lewat database link manual (model repo teman).

**Threads API resmi — LIVE 16 Nov 2026.** App Meta 'TemuanHarian Threads
API' (tester diterima Kyan 17:18), token tersimpan aman di
`~/.threads_poster/threads_token.env` (mode 600) + Secure Vault
(custom.threads-api). Posting via `tools/publish_api.py` /
`tools/run_slot.py --api`, systemd timer aktif. Playwright + cookie
kini jalur cadangan saja (sesi Threads di Brave PC mati; SSO IG hanya
bisa login sebagai @kyankiian — AKUN SALAH, jangan posting via itu).

## Instalasi di PC (bukan VM ini)

```bash
# 1. Clone/copy folder ini ke PC, mis. ~/threads-affiliate-system
# 2. Python 3.10+ + venv + dependensi + browser Playwright
python3 -m venv .venv
.venv/bin/pip install -r requirements-v1.txt
.venv/bin/playwright install chromium

# 3. Ekstrak cookie sesi dari Chrome PC (Chrome harus login IG/Threads).
#    Modul vendor dipanggil dengan PYTHONPATH (foldernya bernama
#    threads-affiliate, pakai strip — jadi bukan nama paket Python).
export PYTHONPATH="$PWD/vendor/threads-affiliate"
.venv/bin/python -m threads_poster.cli setup --extract-cookies
.venv/bin/python -m threads_poster.cli setup --validate-cookies

# 4. Isi database link (lihat docs/isi-link-db.md) — target 50-100 link
# 5. Uji satu slot tanpa posting:
.venv/bin/python tools/run_slot.py --slot 09:00 --dry-run --api

# 6. Uji satu post beneran via API:
.venv/bin/python tools/run_slot.py --slot 09:00 --api
#    (cek di Threads, lalu putuskan lanjut timer atau tidak)

# 7. Pasang timer systemd (sudah aktif untuk Threads):
systemctl --user list-timers | grep threads-affiliate

# 8. Pinterest (dry-run dulu, token belum ada):
.venv/bin/python tools/run_pinterest.py --dry-run
#    (lihat docs/pinterest.md — butuh Pinterest Business app + token +
#     board_id + kolom Image URL di database sebelum bisa live)
```

> ℹ️ `tools/run_slot.py` sudah mengatur `sys.path` sendiri, jadi cukup
> `python tools/run_slot.py ...` dari root repo. Perintah vendor
> (`-m threads_poster.cli ...`) butuh `PYTHONPATH` seperti di langkah 3.

## Yang masih dibutuhkan dari Kyan

1. **Pinterest app + token + board** — buat Pinterest Business app di
   developers.pinterest.com (scope boards/pins read+write), simpan token
   di `~/.pinterest_poster/pinterest_token.env` (mode 600), isi
   `board_id` di `config.yaml`, lalu ajukan Standard access (video demo)
   supaya Pin terlihat publik. Lihat `docs/pinterest.md`.
2. **Kolom Image URL di database** — URL gambar produk dari listing
   Shopee per produk (klik kanan gambar → 'Copy image address').
   Tanpa ini Pinterest BATAL (tidak scraping gambar).
   Cookie = kunci login penuh; jangan pernah dikirim ke siapa pun.
2. **Database link terisi** — 50–100 produk sesuai kriteria
   (rating ≥4,8, terjual ≥1 rb, Rp20–100 rb, Star/Mall + XTRA).
   Lihat `docs/isi-link-db.md`.
3. **Terima undangan tester** app Meta 'TemuanHarian Threads API'
   (untuk fase 2 — API resmi).
4. **Minta akses Open API ke CS Shopee** via live chat (untuk fase 2 —
   API resmi Shopee). Tidak ada form pengajuan di halaman Open API.
5. **Satu post uji manual** sebelum cron diaktifkan (langkah 6 di atas).

## Fase 2 (rencana, belum dibangun)

| Item | Syarat | Perubahan |
|---|---|---|
| Shopee Open API | Akses disetujui CS Shopee | `productOfferV2` (sortir komisi) + `generateShortLink` gantikan isi manual DB |
| Threads API resmi | ✅ LIVE 16 Nov 2026 | Playwright jadi cadangan; `run_slot.py --api` + systemd timer aktif |
| AI drafting | Provider gratis 9Router | Ganti template statis → draf LLM + checker tetap jalan |
| Landing page | — | Etalase ala jagonya.my.id (Next.js) sebagai tujuan link |

## Pinterest (modul baru, 16 Nov 2026 — token belum ada)

Akun Pinterest Yozo (@dirtoflegend) sudah terhubung ke Shopee Affiliate
'pratama'. Modul ini membuat maks 1 Pin/hari dari database link yang sama:

```bash
.venv/bin/python tools/run_pinterest.py --dry-run   # bangun Pin + cek, tanpa API
.venv/bin/python tools/run_pinterest.py             # posting beneran (butuh token)
```

- Gambar WAJIB (kolom `Image URL` di database) — tanpa itu BATAL, tidak scraping.
- Deskripsi Pin diawali `#ad ` + kalimat komisi (tanpa kata "affiliate").
- Tagging produk native dilakukan MANUAL di aplikasi Pinterest (maks 5/Pin);
  API v5 tidak bisa tagging.
- Timer systemd `pinterest-1000` (10:00 WIB) sudah dibuat tapi DISABLED —
  aktifkan hanya setelah token + dry-run lolos + board_id terisi
  (`systemctl --user enable --now pinterest-1000.timer`).
- Trial API: Pin hanya terlihat pembuatnya sampai Standard access disetujui.

## Aturan (guardrails.md — ringkas)

- Link HANYA di post ke-2 (self-reply pertama), tidak pernah di post utama.
- Dilarang klaim "review"/pemakaian pribadi — formatnya "ilustrasi AI /
  intip produk".
- Dilarang bahasa garansi ("dijamin", "pasti ampuh", "termurah", ...).
- Disclosure komisi wajib di tiap thread — TANPA kata "affiliate"
  (aturan Kyan 16 Nov 2026). Pinterest: `#ad` di awal deskripsi.
- Maks 3 post/hari. Satu link tidak pernah dipakai dua kali.
- `--force` tidak ada di sistem ini. Checker menolak = perbaiki drafnya.

## Dokumen lain

- `AUDIT.md` — hasil audit kode repo teman (temuan + risiko).
- `VENDOR-NOTES.md` — apa yang di-vendor, apa yang diubah.
- `guardrails.md` — aturan lengkap yang ditegakkan checker.
- `docs/isi-link-db.md` — cara isi database link dari dashboard Shopee.
- `docs/pinterest.md` — modul Pinterest (API v5, token, board, timer).
- `vendor/threads-affiliate/docs/` — dokumentasi asli repo (akun, cookie,
  troubleshooting, etika/ToS).
