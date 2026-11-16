# Sistem Affiliate Shopee → Threads (v1)

**Akun:** @temuanhariann.id · **Niche awal:** beauty (skincare / parfum / haircare / makeup)
**Status:** scaffold v1 — SIAP diinstal di PC, BELUM posting apa pun.

Sistem full-auto gratis: link Shopee dari database manual → draf dicek
guardrails → posting otomatis 3x/hari (08:00 / 13:00 / 20:00 WIB) via
Playwright. Tanpa API resmi (keduanya belum tersedia — lihat bawah).

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
2. Generate rantai **2 post**: post 1 = hook (tanpa link), post 2 = isi
   "intip produk" + CTA + disclosure `#affiliate`; link ditempel poster
   di post 2 (= self-reply pertama, BUKAN post utama).
3. `check_draft.py` memeriksa: tanpa klaim "review", tanpa bahasa garansi,
   disclosure ada, ≤500 karakter/post, link `s.shopee.co.id`. Gagal → batal.
4. Dedup: link tidak boleh dipakai ulang; gaya hook tidak boleh sama dengan
   2 post terakhir; kemiripan hook ≤60% dengan 5 post terakhir.
5. Posting via Playwright + cookie sesi (headless Chromium). Sukses →
   catat history + tandai link USED. Gagal → exit code non-nol, log.

## Kenapa v1 tidak pakai API resmi

**Shopee Affiliate Open API — TERTAHAN.** Dicek langsung di dashboard
16 Nov 2026 (akun 'pratama', login Google berhasil): menu Open API ADA,
tapi AppID/Secret kosong (`--`), tombol Apply nonaktif, halaman bilang
hubungi Shopee untuk minta akses. Link "contact us"-nya malah nyasar ke
artikel Help Center soal pelanggaran & penalti — bukan form pengajuan.
Satu-satunya jalur: hubungi CS Shopee via live chat. Sampai akses disetujui,
produk HANYA bisa masuk lewat database link manual (model repo teman).

**Threads API resmi — BELUM SIAP.** App Meta 'TemuanHarian Threads API'
menunggu Kyan menerima undangan tester; App Review untuk
`threads_content_publish` belum diajukan. Maka v1 posting via Playwright +
cookie sesi (cara repo teman, sudah terbukti jalan). Ini grey-area menurut
dokumen repo sendiri: meniru aksi manusia, bukan API resmi. Risiko: akun
bisa dibatasi/diblokir Meta sewaktu-waktu. Mitigasi: maks 3 post/hari,
rotasi kategori + hook, dedup, tanpa auto-follow/DM/like.

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
.venv/bin/python tools/run_slot.py --slot 08:00 --dry-run

# 6. Uji satu post beneran, browser terlihat:
.venv/bin/python tools/run_slot.py --slot 08:00 --headed
#    (cek di Threads, lalu putuskan lanjut cron atau tidak)

# 7. Pasang cron (ops/crontab.txt)
crontab -e
```

> ℹ️ `tools/run_slot.py` sudah mengatur `sys.path` sendiri, jadi cukup
> `python tools/run_slot.py ...` dari root repo. Perintah vendor
> (`-m threads_poster.cli ...`) butuh `PYTHONPATH` seperti di langkah 3.

## Yang masih dibutuhkan dari Kyan

1. **Cookie sesi Threads** — diekstrak di PC-nya sendiri
   (`setup --extract-cookies`, Chrome PC harus login IG/Threads).
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
| Threads API resmi | Tester diterima + App Review lolos | Ganti Playwright → `graph.threads.net` (POST + reply) |
| AI drafting | Provider gratis 9Router | Ganti template statis → draf LLM + checker tetap jalan |
| Landing page | — | Etalase ala jagonya.my.id (Next.js) sebagai tujuan link |

## Aturan (guardrails.md — ringkas)

- Link HANYA di post ke-2 (self-reply pertama), tidak pernah di post utama.
- Dilarang klaim "review"/pemakaian pribadi — formatnya "ilustrasi AI /
  intip produk".
- Dilarang bahasa garansi ("dijamin", "pasti ampuh", "termurah", ...).
- Disclosure `#affiliate` wajib di tiap thread.
- Maks 3 post/hari. Satu link tidak pernah dipakai dua kali.
- `--force` tidak ada di sistem ini. Checker menolak = perbaiki drafnya.

## Dokumen lain

- `AUDIT.md` — hasil audit kode repo teman (temuan + risiko).
- `VENDOR-NOTES.md` — apa yang di-vendor, apa yang diubah.
- `guardrails.md` — aturan lengkap yang ditegakkan checker.
- `docs/isi-link-db.md` — cara isi database link dari dashboard Shopee.
- `vendor/threads-affiliate/docs/` — dokumentasi asli repo (akun, cookie,
  troubleshooting, etika/ToS).
