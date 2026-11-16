# Laporan Sprint 2 — Publishing Reliability + Verifikasi Final Sprint 1

**Tanggal:** 17 Nov 2026, ~01:00 WIB
**Repo:** kianlabs/threads-affiliate (PC = live, VM = mirror)
**Status Tahap 1 (verifikasi Sprint 1): COMPLETE — 7/7 PASS**
**Status Tahap 2 (Sprint 2): COMPLETE**

---

## TAHAP 1 — Final Verification Sprint 1

### Check 1 — Checksum PC vs VM: PASS
md5sum identik untuk ke-6 file Sprint 1 di kedua sisi:

| File | md5 |
|---|---|
| data/affiliate_links.md | 4b35b6d434adb023a9a52ac7c5ba86fe |
| data/subid_mapping.md | f3be76a24b9450813781e96ccf336f06 |
| data/performance.csv | 14aa0d48d33e4ebea303b9ca2306f2e6 |
| tools/calc_performance.py | a0a5af1b7601fbb52d26ea9b489653e5 |
| docs/skema-id-dan-subid.md | f3f4b41fa4e1b569f2c06ccaf65fac61 |
| docs/isi-performance-manual.md | e7c3bee95d58946f29d6c95f577a01d9 |

Satu celah sync ditemukan & diperbaiki: VM belum punya backup
`data/affiliate_links.md.bak-20261117-0024` — sudah disalin dari PC
(md5 715611b8eb5b828fa803b44f5900e058, cocok).

### Check 2 — performance.csv tanpa fixture: PASS
File berisi tepat 3 baris: header + 2 baris post terbit (Kikkoman,
BONBOX). Semua 8 kolom metrik di kedua baris KOSONG. Fixture pengujian
Sprint 1 hanya pernah ada di `/tmp/sprint1/fixture_performance.csv`,
tidak pernah masuk `data/`. `calc_performance.py` hanya membaca file
CSV yang diberikan sebagai argumen (default `data/performance.csv`).

### Check 3 — 2 link USED + Sub-ID historis tidak berubah: PASS
Baris Kikkoman dan BONBOX di DB saat ini byte-identik dengan backup
`affiliate_links.md.bak-20261117-0024` (verifikasi programatis,
`verify_checks34.py`). Token sub_id di `post_history.json` cocok
dengan kolom Sub-ID DB untuk keduanya.

### Check 4 — 27 Sub-ID baru unik + product_id benar: PASS
Verifikasi programatis (29/29):
- 29 nilai Sub-ID di kolom DB semuanya unik; 27 Sub-ID baru unik.
- `sub_id_baru` di `data/subid_mapping.md` == kolom Sub-ID DB.
- `product_id` == `P-<shop>-<item>` dari `origin_link` di URL tiap baris.
- Token slot-1 di URL (`sub_id=TOKEN----`) == kolom Sub-ID.
- Format Sub-ID huruf+angka saja (tanpa hubung).
- Produk USED (2) == produk yang tidak diubah di mapping (2).

(Catatan: skrip verifikasi awal sempat FAIL palsu karena `"USED" in
"❌ UNUSED"` — substring. Diperbaiki dengan cek `startswith("✅")`.)

### Check 5 — Kalkulasi UNKNOWN tidak tercampur simulasi: PASS
`calc_performance.py` atas `performance.csv` asli: semua total dan
metrik = UNKNOWN, tanpa crash. Fixture hanya di `/tmp` (lihat Check 2).

### Check 6 — Batas karakter caption 470 (operasional) / 500 (absolut): PASS
Diimplementasikan di `tools/check_draft.py`:
- `MAX_POST_CHARS = 500` (absolut, ERROR `panjang-post` bila lewat).
- `OPERATIONAL_MAX_CHARS = 470` — 471–500 karakter = WARN
  `panjang-operasional`, post tetap boleh terbit.
- Retry 5x di `run_slot.py` tetap memakai batas absolut 500 (tidak diubah).

Uji batas (per post): 469 → lolos; 470 → lolos; 471 → WARN;
500 → WARN; 501 → ERROR. `check_draft.py --db` atas DB baru: LOLOS.
Aturan didokumentasikan di `docs/skema-id-dan-subid.md` §5.

### Check 7 — Tanggal Sub-ID vs tanggal publikasi: PASS (keputusan didokumentasikan)
Temuan jujur: 27 Sub-ID baru memakai tanggal regenerasi `20261117`,
sementara produknya baru dipublikasikan di tanggal berikutnya.
**Keputusan (ditulis di `docs/skema-id-dan-subid.md` §2): tanggal di
Sub-ID = tanggal link dibuat** (identitas link yang stabil).
Tanggal publikasi aktual tercatat di `performance.csv` kolom `date`,
`post_history.json` kolom `date`, dan `content_id`. 27 link TIDAK
diregenerasi ulang — regenerasi hanya demi menyamakan tanggal akan
merusak kestabilan tracking. Batch link berikutnya memakai tanggal
pembuatannya sendiri.

---

## TAHAP 2 — Sprint 2: Publishing Reliability

### A. Audit BONBOX: TERBUKTI — receipt lengkap
Permalink https://www.threads.com/@shopee_harian/post/DfzXk9En8B-
diverifikasi 3 cara independen (17 Nov 2026):
1. Fetch web: post oleh SHOPEE HARIAN (@shopee_harian), isi = hook
   transformasi BONBOX ("Bau apek dulu nempel di kos...").
2. Threads API `GET /me/threads`: id `18134500336833170`,
   timestamp `2026-11-16T12:35:19+0000` (= 19:35:19 WIB — cocok dengan
   `post_history` 19:35:44, selisih 25 detik = waktu publish→catat).
3. Threads API `GET /18134500336833170/replies`: reply post 2 =
   id `18133074499692005`, permalink `.../post/DfzXm5vn2dA`, teks
   "Intip BONBOX Mop Stick Set BCT3505 dari listingnya..." (berisi link).

Receipt BONBOX di `data/post_history.json` sudah dilengkapi
(media_id, permalink, media_id_reply, permalink_reply, published_at,
product_id, content_id, sub_id, platform, receipt_verified_via).
Anomali "handle @shopee_harian" di audit SUDAH terjawab: itu memang
akun yang sama (diganti nama sebelum post itu). Baris "Terkirim"
duplikat di `cron.log` belum diketahui pasti penyebabnya — hipotesis:
systemd menulis stdout ke log yang sama dengan append manual script
(belum diverifikasi); TIDAK ada double-post (hanya 1 post BONBOX di API).

**Temuan baru (di luar BONBOX, wajib dibaca Kyan): repost Kikkoman v4
(DfzOch6n5SE, media_id 18135902441497212) TIDAK LAGI BISA DIAKSES.**
Tiga sinyal independen: API `GET /18135902441497212` → HTTP 400
(2x, dengan field yang sama seperti kontrol BONBOX + Kikkoman lama
yang berhasil); tidak ada di `GET /me/threads` (seharusnya ada di
antara 12:35 dan 10:51 UTC); fetch web gagal ("no public post data").
Kemungkinan: post dihapus/disembunyikan — penyebab belum diketahui.
Status di `post_history.json` DIPERTAHANKAN 'posted' (tidak diubah
tanpa keputusan Kyan) + ditambah `verification_note` berisi temuan ini.
Perlu keputusan Kyan: periksa dari HP / abaikan / catat sebagai hilang.

### B. Perbaiki publication receipt
`tools/publish_api.py`:
- `_publish_container` TIDAK LAGI memfabrikasi permalink
  (`https://www.threads.com/@{USERNAME}/post/{pid}` dihapus). GET
  permalink dicoba 2x; bila tetap gagal → `permalink=None`,
  `permalink_verified=False`.
- `publish_text` kini mengembalikan `{'id', 'permalink',
  'permalink_verified'}`.
- Baru: `get_media(media_id)` — baca media via API untuk verifikasi manual.

`tools/run_slot.py`:
- Setiap publikasi kini menyimpan: media_id, permalink, media_id_reply,
  permalink_reply, product_id, content_id, sub_id, published_at,
  platform, status (+ kolom lama dipertahankan).
- Tanpa media_id → status TIDAK BOLEH 'posted'. Bila media_id hilang →
  catat `publish_interrupted` + error jelas, link TIDAK ditandai USED.
- Bila media_id ada tapi permalink belum terverifikasi → status
  `posted_receipt_incomplete` (post TERBUKTI terbit, receipt belum
  lengkap) + link ditandai USED + peringatan log berisi media_id.
- Jalur Playwright (fallback): tidak ada media_id → status paling
  tinggi `posted_receipt_incomplete` bila post_url ada; bila post_url
  kosong → `publish_interrupted`.
- Batas harian kini menghitung `posted` + `posted_receipt_incomplete`.

### C. Perbaiki retry + deduplication
- **Kunci idempotency baru: (content_id, sub_id)** — dicek SEBELUM
  publish (`find_existing_publication`), dalam status APAPUN
  (posted / posted_receipt_incomplete / publish_interrupted).
  Cocok → BATAL exit 3, tanpa publish ulang.
- Entri lama (tanpa kolom content_id/sub_id) tetap terdeteksi lewat
  parse Sub-ID dari `affiliate_link`-nya.
- **Tidak ada blind retry:** bila publish gagal SETELAH post 1 terbit,
  post 1 dicatat `publish_interrupted` (dengan media_id + error) dan
  retry otomatis DILARANG — verifikasi manual dulu. Entri
  `publish_interrupted` juga memblokir percobaan ulang via kunci
  idempotency di atas.
- Error yang disimpan di history/log hanya berisi: jenis error, kode
  HTTP API, container/media id, langkah yang gagal — TIDAK PERNAH
  berisi token (token hanya ada di body request, tidak pernah dicetak
  atau masuk pesan error).

### D. Pengujian (tanpa live posting) — 19/19 PASS
Harness: `/tmp/sprint2-verify/test_sprint2.py` (transport API dimock;
tidak ada request ke graph.threads.net).
- D1 batas karakter 469/470/471/500/501 → sesuai spesifikasi.
- D2 publish sukses (simulasi) → id + permalink_verified True.
- D3 timeout (URLError via transport asli) → raise, tidak disembunyikan.
- D4 HTTP 500 (via transport asli) → RuntimeError berisi kode, tanpa token.
- D5 container ERROR → RuntimeError.
- D6 permalink GET gagal → verified False → `posted_receipt_incomplete`.
- D7 deduplication: content_id sama / sub_id sama / entri legacy → ditolak;
  produk lain → lolos.
- D8 receipt tidak lengkap → `receipt_failed`; entri interrupted
  menyimpan media_id post 1 + error; interrupted memblokir retry.
- D9 `build_history_entry`: semua 10 kolom receipt wajib ada.
- Tambahan di PC (setelah deploy): `py_compile` 3 file OK;
  `check_draft.py --db` LOLOS; `run_slot.py --category dapur --dry-run
  --api` LOLOS (tidak posting, DB tidak diubah).

### File yang diubah (PC = live, VM = mirror)
- `tools/check_draft.py` — aturan 470/500 (Check 6).
- `tools/publish_api.py` — permalink tidak difabrikasi + `get_media`.
- `tools/run_slot.py` — receipt lengkap, idempotency, anti blind-retry.
- `docs/skema-id-dan-subid.md` — §2 keputusan tanggal Sub-ID + §5 batas caption.
- `data/post_history.json` (gitignored) — receipt BONBOX lengkap +
  kolom receipt baru di kedua entri + verification_note repost Kikkoman.
- `docs/laporan-sprint2-verifikasi.md` (baru) — dokumen ini.
- Backup: `data/post_history.json.bak-20261117-<jam>` di PC sebelum
  perubahan (gitignored). Tools yang diubah ter-commit (git sebagai backup).
- Commit: `d4d8791` (`d4d879117e7a3034baf1be0b0841905bb845a666`) — remote HEAD terverifikasi 17 Nov 2026 ~01:05 WIB.

### Masalah yang belum selesai
1. Repost Kikkoman v4 (DfzOch6n5SE) tidak lagi bisa diakses via API —
   perlu keputusan Kyan (lihat §A).
2. Penyebab duplikasi baris "Terkirim" di `cron.log` belum diverifikasi
   (hipotesis: double-write stdout + append; tidak ada double-post).
3. Receipt post 2 (reply) untuk repost Kikkoman tidak bisa dilengkapi
   karena media induknya tidak resolve (id reply DfzOdSwn0ne tidak
   diketahui).
4. Pengujian end-to-end live (satu slot sungguhan) BELUM dilakukan —
   butuh persetujuan Kyan + slot jadwal berikutnya; semua uji di atas
   simulasi/dry-run.

### Risiko
- Aturan baru lebih ketat: bila GET permalink API sedang bermasalah,
  post yang sebenarnya terbit akan tercatat `posted_receipt_incomplete`
  (bukan `posted`) sampai diverifikasi manual — disengaja, demi
  kejujuran receipt.
- `publish_interrupted` memblokir link dari percobaan ulang otomatis
  (via idempotency) — bila ini terjadi, WAJIB ada intervensi manual
  (cek media_id → lengkapi reply manual / hapus entri interrupted
  setelah verifikasi) sebelum link itu bisa dipakai lagi.
- `tools/check_draft.py` di VM sebelumnya masih v4 (mewajibkan
  disclosure komisi — sudah dibatalkan Kyan); dalam sprint ini VM
  disinkronkan ke versi PC v5 + aturan 470. Sinkronisasi penuh VM↔PC
  tetap tugas Sprint 6.

### Status
- Tahap 1 (verifikasi Sprint 1): **COMPLETE** — 7/7 PASS.
- Tahap 2 (Sprint 2): **COMPLETE** — receipt + deduplication teruji
  (simulasi + dry-run; uji live end-to-end menunggu persetujuan Kyan).
