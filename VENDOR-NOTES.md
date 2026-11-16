# Vendor Notes — d4ncboz/threads-affiliate

## Yang di-vendor

- **Repo:** https://github.com/d4ncboz/threads-affiliate
- **Commit:** `93eb866` ("feat: AI agent optimization")
- **Lisensi:** MIT (salinan di `LICENSE` root + asli di
  `vendor/threads-affiliate/LICENSE`). Atribusi dipertahankan.
- **Isi:** seluruh repo (kode, templates, tests, examples, docs, schemas)
  KECUALI folder `.git`.
- **Lokasi:** `vendor/threads-affiliate/`
- **Tanggal vendor:** 16 Nov 2026.

## Yang DIUBAH dari upstream (2 perubahan)

### 1. Perbaikan paste di Linux — `threads_poster/poster.py::_paste_text`

- **Masalah:** upstream memakai `page.keyboard.press("Meta+v")`
  (paste macOS) secara hardcode. Di Linux, paste adalah `Control+v`.
- **Dampak tanpa perbaikan:** link affiliate gagal ditempel di PC Kyan
  (Linux/Omarchy) → tiap posting gagal di "Affiliate link not inserted
  after retries".
- **Perbaikan:** deteksi platform — `Meta+v` hanya di macOS
  (`platform.system() == "Darwin"`), `Control+v` di Linux/Windows.
- **Bukti:** 6/6 asersi `tests/test_core.py` (direplikasi manual karena
  pytest tidak tersedia di VM audit) lolos terhadap kode hasil patch.

### 2. Kategori home living — `threads_poster/content_generator.py::CATEGORIES` + `threads_poster/database.py::_init_empty`

- **Alasan:** niche v1 diganti dari beauty ke home living / kos-kosan
  (riset 16 Nov 2026, disetujui Kyan); template aktif kini
  dapur/organizer/kebersihan (Workflow E di `AGENTS.md` vendor).
- **Perubahan:** `CATEGORIES = ["dapur", "organizer", "kebersihan"]`
  (dulu skincare/parfum/haircare/makeup); scaffold DB kosong
  `_init_empty` ikut diganti ke 3 seksi yang sama, supaya DB yang
  terhapus tidak sengaja terlahir kembali dengan seksi beauty.
  `cli.py` tidak perlu diubah — sudah memakai `choices=CATEGORIES`.
- **Bukti:** `tools/run_slot.py --slot 09:00 --dry-run` menerima slot baru
  dan lanjut ke tahap DB (gagal lanjut hanya karena DB masih kosong,
  exit 4 — ekspektasi); `ContentGenerator.generate_chain` kategori
  `dapur` + `check_draft.py` lolos tanpa error (2.916 kombinasi
  hook × post2 × CTA diuji, 0 ERROR — lihat laporan template 16 Nov).

## Yang TIDAK diubah di vendor

- Semua logika lain (poster, content_generator, dedup, database,
  cookie_manager, cli) dibiarkan apa adanya — supaya gampang
  dibandingkan dengan upstream saat update.
- Template upstream (`vendor/.../templates/`) dibiarkan apa adanya
  sebagai REFERENSI — tetapi TIDAK dipakai v1, karena berisi klaim
  review palsu (lihat AUDIT.md temuan #2). Template aktif v1 ada di
  `templates/` (root) dan sudah ditulis ulang.

## Aturan update vendor

1. Jangan edit file di `vendor/` kecuali perbaikan bug yang
   didokumentasikan di sini (tambah entri baru di bawah).
2. Bila upstream merilis versi baru: bandingkan diff, terapkan ulang
   perbaikan paste, jalankan ulang replikasi `test_core.py`, catat
   commit baru di sini.
3. Semua penyesuaian perilaku v1 (guardrails, format 2-post, Sub-ID,
   validasi cookie sebelum posting) tinggal di `tools/` + `templates/`
   + `config.yaml` — BUKAN di vendor.
