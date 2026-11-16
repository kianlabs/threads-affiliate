# Audit — d4ncboz/threads-affiliate (basis v1)

- **Repo:** https://github.com/d4ncboz/threads-affiliate
- **Versi:** 0.1.0 · **Lisensi:** MIT · **Commit terakhir saat audit:**
  `93eb866` ("feat: AI agent optimization")
- **Tanggal audit:** 16 Nov 2026 · **Ruang lingkup:** seluruh kode
  (`threads_poster/*.py`, 1.328 baris), templates, tests, examples, docs.
- **Metode:** baca kode + uji parser DB + replikasi 6/6 asersi
  `tests/test_core.py` (pytest tidak tersedia di VM audit; asersi
  dijalankan manual, semua lolos).

## Cara kerja posting (poster.py, 400 baris)

1. Muat cookie IG + Threads dari `~/.threads_poster/cookies/session.json`.
2. Playwright: buka headless Chromium, injeksikan cookie ke
   `.instagram.com`, `.threads.com`, `.threads.net`.
3. `instagram.com` (warming) → `threads.com/login` → klik
   "Continue with Instagram" (Meta SSO) → feed `threads.com` → klik
   "New thread" → cari editor `contenteditable`.
4. Ketik post 1 (hook, 30 ms/karakter), klik "Add to thread" untuk
   post 2/3, tempel link affiliate via clipboard di post terakhir.
5. Verifikasi link ada di editor terakhir (retry paste 1x), lampirkan
   gambar bila ada, klik Post/Kirim, tidur 10 dtk.
6. "Verifikasi" ke halaman profil: sukses dinyatakan bila 30 karakter
   pertama hook ATAU 20 karakter pertama nama produk muncul di HTML
   profil. URL yang dikembalikan hanya URL profil — **bukan URL post**.

## Cookie / sesi (cookie_manager.py, 153 baris)

- Diekstrak dari profil Chrome via `browser_cookie3` (membaca SQLite
  `Cookies` milik Chrome). Wajib ada `sessionid`, `csrftoken`,
  `ds_user_id` dari Instagram (akun Threads terikat IG).
- Disimpan ke `~/.threads_poster/cookies/session.json` dengan `chmod 600`.
- Validasi via endpoint Instagram `web_profile_info` dengan
  `X-IG-App-ID` hardcode.
- Cron menyarankan refresh tiap 6 jam dari Chrome (Chrome harus tetap
  login di mesin yang sama).
- **Risiko:** file cookie = sesi login penuh (bocor = akun diambil alih);
  sesi bisa kedaluwarsa/berputar sewaktu-waktu; Meta bisa menandai sesi
  sebagai otomatis → pembatasan/pemblokiran akun. Repo sendiri
  (docs/ethics-and-tos.md) menyebut metode ini **grey-area**, bukan API
  resmi.

## Anti-spam yang ada (dedup.py, 104 baris)

- Link tidak pernah dipakai ulang (dicek terhadap history).
- Gaya hook tidak boleh sama dengan 2 post terakhir.
- Kemiripan kata hook ≤60% terhadap 5 post terakhir.
- History disimpan 100 entri terakhir (`data/post_history.json`).
- Ketik 30 ms/karakter, paste via clipboard, jeda antar langkah,
  maks 3 post/hari (dokumen), tidak ada burst.
- **Celahlah:** tidak ada jitter/acak waktu antar eksekusi (cron jam
  tetap), tidak ada pengecekan kesehatan akun sebelum posting.

## Temuan — harus diperbaiki / diwaspadai

### 🔴 Kritis

1. **Bug paste di Linux (`poster.py::_paste_text`).** Kode memakai
   `Meta+v` (paste macOS) secara hardcode. Di Linux (PC Kyan =
   Omarchy) paste adalah `Control+v`; `Meta+v` tidak melakukan apa-apa
   di Chromium Linux → link affiliate GAGAL ditempel → error
   "Affiliate link not inserted after retries". Komentar di kode
   mengakui ini ("On Linux/Win, switch to Control+v") tapi kode tidak
   melakukannya. **SUDAH DIPERBAIKI di vendor v1** (deteksi platform;
   lihat VENDOR-NOTES.md).
2. **Template berisi klaim review palsu.** `post2_templates.json`
   ("setelah 2 minggu rutin pake, tekstur kulit berubah",
   "rambut rontok berkurang 70% setelah 1 bulan rutin pake",
   "Gw test: semprot jam 7 pagi...") dan sebagian hook
   ("Gw review {product} secara jujur", "Tekstur kulit gw sebelum &
   sesudah pake {product}", "Pas live IG, gw pake {product}",
   "Gw udah coba keduanya") mengklaim pemakaian pribadi atas produk
   yang tidak pernah dipegang. Ini melanggar aturan Kyan, S&K Shopee
   (fake reviews), dan berisiko UU ITE. **Template v1 ditulis ulang
   penuh** (`templates/`); template upstream hanya tersimpan di
   `vendor/` sebagai referensi dan TIDAK dipakai.

### 🟡 Penting

3. **Tidak ada disclosure otomatis.** Generator tidak menambahkan
   `#affiliate`/`#ShopeeAffiliate` ke konten apa pun. Dokumen etika
   hanya menyarankan di bio / minimal 1 post seminggu — tidak cukup
   untuk aturan Kyan (wajib tiap thread). **Diperbaiki di v1:**
   template CTA selalu memuat disclosure + `check_draft.py`
   menolak thread tanpa disclosure.
4. **Tidak ada batas 500 karakter.** Threads membatasi 500 karakter
   per post; tidak ada validasi di mana pun. Nama produk panjang +
   template bisa melampaui batas. **Diperbaiki di v1:** checker
   menolak post >500 karakter.
5. **Verifikasi posting lemah.** "Sukses" dinyatakan meski pengecekan
   profil gagal (hanya `post_url` yang kosong); pencocokan substring
   bisa false-positive; URL post asli tidak pernah diambil.
6. **Kegagalan login tidak terdeteksi.** Bila SSO gagal / sesi mati,
   alur tetap jalan dan baru gagal di "Editor element not found" —
   pesan yang menyesatkan. CLI juga tidak memanggil
   `validate_cookies()` sebelum posting (padahal AGENTS.md
   menyarankannya). **Diperbaiki di v1:** `run_slot.py` memvalidasi
   cookie dulu (exit 2 bila tidak valid).
7. **Aturan rotasi kategori adalah dead code.** `dedup.py` Rule 4
   hanya berisi `pass` (komentar "warning only, not blocking") —
   rotasi sebenarnya hanya ditegakkan oleh contoh cron
   (kategori berbeda per slot). v1 mengandalkan slot cron yang sama.
8. **Parser database rapuh.** Baris tanpa link ber-backtick dilewati
   diam-diam (`_parse_rows`); tidak ada validasi format host link;
   tidak ada dukungan Sub-ID. **Diperbaiki di v1:** kolom Sub-ID
   ke-6 sudah dites (parse + `mark_used` tetap jalan);
   `check_draft.py --db` memvalidasi host + duplikat.
9. **Selektor rapuh.** Klik berbasis teks eksak ("New thread", "Buat",
   "Create" — "Create" bisa mengenai elemen lain), deteksi editor via
   `contenteditable`. Perubahan UI Threads bisa merusak semuanya tanpa
   pesan yang jelas. Tidak ada retry di level CLI.
10. **Tidak ada retry / backoff.** Post gagal = exit 1, cron tidak
    mencoba lagi. v1 mempertahankan perilaku ini (gagal = log + lewati
    slot) — retry otomatis berisiko double-post.

### ⚪ Minor / stale

11. **Dependensi mati:** `Pillow`, `click`, `python-dotenv` ada di
    `requirements.txt` tapi tidak dipakai di mana pun (CLI memakai
    `argparse`).
12. **Env var terdokumentasi tapi tidak dibaca:** AGENTS.md mendaftarkan
    `THREADS_COOKIES_PATH`, `THREADS_DB_PATH`, dll. — tidak ada satu
    pun yang dibaca kode (`cli.py` hanya memakai argumen/default).
13. **Klaim "battle-tested, 1000+ posts"** di README tidak dapat
    diverifikasi dari repo (3 commit, v0.1.0, tanpa bukti).
14. **Hardcode `X-IG-App-ID`** di validasi cookie — bisa rusak bila
    Meta menggantinya.
15. **Tidak ada `scheduler.py`** (tidak seperti yang diperkirakan):
    penjadwalan dilakukan via contoh cron + `batch_schedule.py` +
    helper `cli schedule`.

## Yang masih bagus / dipertahankan

- Struktur kode bersih dan kecil (1.328 baris), mudah diaudit.
- Dedup inti (aturan 1–3) benar dan teruji.
- Database Markdown mudah diisi manusia; `mark_used`/`reset_all` jalan.
- Dokumen etika/ToS jujur soal grey-area + risiko ban + kewajiban pajak
  dan UU PDP/ITE — dipakai sebagai referensi `guardrails.md`.
- AGENTS.md upstream ditaati v1: tidak commit cookie/data, maks 3
  post/hari (di bawah batas 5 repo), selalu dedup sebelum posting,
  selalu tandai USED setelah sukses, log ke `logs/cron.log`.
