# Rancangan Kill Switch & Operational Safety — Sprint 3 (Tahap A + B, REVISI FINAL Tahap 1)

**Tanggal:** 17 Nov 2026, ~01:15–01:45 WIB (draf awal) · **Revisi final Tahap 1: 17 Nov 2026 ~02:00 WIB** · **Revisi final Tahap 2 (dokumen ini): 17 Nov 2026 ~02:30 WIB — D9 DISETUJUI + 4 koreksi K1-1 s.d. K1-4** · **Revisi final tambahan: 17 Nov 2026 ~02:45 WIB — 6 koreksi K2-1 s.d. K2-6** · **Revisi terakhir: 17 Nov 2026 ~08:05 WIB — 3 koreksi P0-1, P1-1, P1-2**
**Status:** DOKUMEN FINAL TAHAP 2 — REVISI TERAKHIR (desain + rencana implementasi) — Keputusan D1–D9 **DISETUJUI Kyan** (D1–D8: 17 Nov 2026 01:22 WIB; D9: 17 Nov 2026 01:34 WIB); koreksi K2-1 s.d. K2-6 ditambahkan 17 Nov 2026 ~02:45 WIB; koreksi P0-1, P1-1, P1-2 ditambahkan 17 Nov 2026 ~08:05 WIB. Belum ada file sistem yang diubah, belum ada commit. Implementasi MENUNGGU persetujuan terpisah Kyan atas dokumen ini.
**Ruang lingkup:** repo `kianlabs/threads-affiliate`; PC `~/threads-affiliate-system` (mesin posting LIVE) + VM `~/workspace/threads-affiliate-system` (mirror).
**Konteks:** Sprint 1 COMPLETE (7/7 PASS, commit `1ae75aa`). Sprint 2 COMPLETE (commit `d4d8791` + `6c6eb1a`, 19/19 uji simulasi + dry-run). Live end-to-end test BELUM dilakukan. Akun Threads `@shopee_harian` (ID API 29489356290657436).

> Aturan audit ini: semua temuan di bawah dibaca langsung dari file + systemd + cron pada 17 Nov 2026 ~01:30 WIB. Tidak ada file yang diubah selama audit.

---

## Keputusan final Kyan (D1–D8) — DISETUJUI 17 Nov 2026 01:22 WIB

| # | Keputusan | Isi yang disetujui |
|---|---|---|
| D1 | Sumber kebenaran kill switch | **Flag file** `data/publishing_disabled*` (§B2). Bukan kunci `config.yaml`. |
| D2 | Auto-comment | **Wajib mengikuti kill switch Threads.** Komen adalah publikasi Threads (melewati `_post()` yang sama). |
| D3 | Re-enable | **Hanya Kyan** yang boleh mengaktifkan kembali publishing. Agent hanya boleh membaca + memverifikasi status. Tidak ada perintah re-enable untuk agent; re-enable = Kyan menghapus flag file secara manual (SSH) lalu verifikasi `publish_guard.py status` → `ALLOWED`. |
| D4 | `publish_video.py` | **Diperbaiki dalam Sprint 3:** hapus permalink fabrikasi; permalink hanya bila terverifikasi; receipt terintegrasi ke `post_history.json`; terapkan idempotency (cek `(content_id, sub_id)` sebelum publish). |
| D5 | Pinterest | **Wajib `--live` eksplisit.** Tanpa flag itu tidak boleh ada publikasi. Berlaku untuk `run_pinterest.py` DAN `pinterest_api.py` CLI (keduanya default-live hari ini). Timer Pinterest memanggil tanpa flag apa pun hari ini — wajib diubah memanggil `--live` eksplisit (atau tetap tanpa publikasi; timer saat ini disabled). (+ K2-5: tanpa `--live` = dry-run + banner DRY-RUN; `--dry-run --live` = konflik, ditolak.) |
| D6 | Vendor CLI | **Wajib melewati guardrail + mekanisme keamanan yang sama.** `cli.py cmd_post`/`cmd_post_auto` + `poster.post()` harus melewati `check_chain`, kill switch, lock, dan idempotency. Tidak boleh ada bypass via pemanggilan langsung. |
| D7 | VM | **Tetap BUKAN publisher** sampai Sprint 6 selesai + persetujuan terpisah. |
| D8 | Duplikasi log | **Satu penulis saja:** `log()` print-only, systemd append ke `cron.log` (opsi 1 §B4-C4). |
| D9 | `delete_media()` ikut kill switch Threads? | ✅ **DISETUJUI — YA (17 Nov 2026 01:34 WIB).** Saat Threads OFF, SEMUA tindakan DELETE diblokir, termasuk pemanggilan langsung. Penghapusan hanya boleh dilakukan melalui alur yang telah melewati seluruh pemeriksaan keamanan (gate kill switch + lock + intent record DELETE terpisah, §B3, §B4-C2, §B5 urutan 8). |

## Koreksi wajib (mengikat — dari Kyan 17 Nov 2026 01:22 WIB)

| # | Koreksi | Dampak ke desain (di mana diterapkan) |
|---|---|---|
| K0-1 | Intent record `publish_started` harus ditulis secara **ATOMIK** dan dipastikan tersimpan (**fsync**) SEBELUM request publikasi dikirim. | §B4-C2: tulis ke file sementara + `os.replace` + `fsync` file + `fsync` direktori, baru kirim request. Tanpa ini intent record tidak menutup celah A3-a (crash persis setelah tulis tapi sebelum flush = tidak ada jejak). |
| K0-2 | **SATU mekanisme flock bersama** untuk semua publisher di PC: `run_slot`, `publish_video`, `auto_comment`, Pinterest, vendor CLI. | §B4-C1: satu file lock `data/.publisher.lock`, satu helper `acquire_publisher_lock()` di `publish_guard.py`, dipakai semua jalur. Lock TIDAK per-jalur (lock per-jalur masih membiarkan `run_slot` + `publish_video` berjalan bersamaan). |
| K0-3 | Kill switch diperiksa **TEPAT SEBELUM request irreversible**. Jangan mengunci hanya entry point. | §B3: cek berlapis — entry point (gagal cepat) + cek ulang sebelum publish + choke point terdalam (`_post` / `poster.post` / `create_pin` / `delete_media`). |
| K0-4 | Kegagalan API / HTTP 400 **TIDAK BOLEH** dianggap bukti post tidak terbit. | §B4-C2/C3: status ambigu (`publish_started` tanpa receipt, timeout, HTTP 400 saat verifikasi) = **blokir + verifikasi manual**, bukan `abandoned`, bukan publish ulang. Preseden: repost Kikkoman v4 — media_id tidak resolve via API (HTTP 400) tapi post itu PERNAH terbit (16 Nov 18:18, terverifikasi saat itu). |
| K0-5 | `reconcile.py` **default READ-ONLY**. Status menjadi `abandoned` HANYA dengan bukti kuat post tidak pernah terbit. Bila ambigu, tetap blokir + minta keputusan manusia. | §B4-C3: mode default `--check` (laporan saja); perubahan status butuh `--apply` + bukti (GET media 404 konsisten + tidak ada di `/me/threads` + fetch web gagal) + operator manusia; ambiguitas apa pun → tetap `publish_started`/`publish_interrupted` + eskalasi. |
| K0-6 | Semua publisher yang **belum terintegrasi default-DENY**. Tidak adanya kill switch bukan izin otomatis untuk fitur yang belum disetujui. | §B3 + §B5: jalur baru / jalur yang belum melewati gate = DITOLAK. Daftar jalur yang diizinkan bersifat eksplisit (allowlist), bukan denylist. `repost_product.py` dan `pinterest_api.py` CLI masuk daftar integrasi wajib Tahap 2 (lihat §A7). |
| K0-7 | Jangan hapus/timpa riwayat publikasi. Recovery bersifat **append / audit-preserving**. | §B4-C3 + §B5: `update_history` di `repost_product.py` hari ini MENIMPA entri lama (`entry.update(...)`) — **dilarang**, wajib diubah menjadi append entri baru + catatan `supersedes`. Semua perubahan status menambah catatan, tidak menimpa. |
| K0-8 | **Jangan live posting selama Sprint 3.** | Berlaku untuk Tahap 1, 2, dan 3 (pengujian hanya mock/fixture/dry-run). |

## Koreksi wajib revisi final (K1-1 s.d. K1-4) — mengikat, dari Kyan 17 Nov 2026 01:34 WIB

| # | Koreksi | Dampak ke desain (di mana diterapkan) |
|---|---|---|
| K1-1 | **Cegah nested flock.** Satu pemilik lock per proses. Publisher terdalam tetap WAJIB memeriksa kill switch, tetapi TIDAK BOLEH mengambil lock kedua bila proses pemanggil sudah memilikinya. Pemanggilan langsung tetap harus memperoleh lock. | §B3 + §B4-C1: `acquire_publisher_lock()` idempotent dalam satu proses (state `_lock_fd`/`_lock_pid`/`_lock_depth` di `publish_guard.py`); pemanggilan kedua dari proses yang sama langsung sukses tanpa `flock()` kedua. Cek kill switch tetap dilakukan di setiap lapis tanpa kecuali. Uji: RV-1, RV-2 (§B7). |
| K1-2 | **Durable intent record + idempotency di SELURUH jalur publikasi:** `run_slot`, `publish_video`, `auto_comment`, Pinterest, vendor CLI, `repost_product`. **Tindakan DELETE dicatat TERPISAH dari publikasi** (intent record + history DELETE sendiri, jangan dicampur ke publication receipt). | §B4-C2 + §B5: satu helper `write_intent()` bersama untuk semua jalur; file baru `data/delete_history.json` (gitignored) untuk intent + history DELETE (`delete_started` → `deleted` / `delete_failed` / `delete_ambiguous`). Uji: RV-3, RV-4, matriks DELETE §B7. |
| K1-3 | **Signal handler HANYA menandai proses sedang dihentikan** (flag in-memory). Penulisan status `interrupted` dilakukan melalui cleanup yang aman (bukan di dalam handler). Intent record atomik + fsync tetap perlindungan utama terhadap crash. | §B4-C2: handler hanya menyetel `_SHUTTING_DOWN = True`; loop utama/`finally` memeriksa flag lalu menulis `publish_interrupted` lewat jalur tulis atomik biasa. Uji: RV-5, RV-6 (§B7). |
| K1-4 | **`config.yaml` BUKAN sumber kebenaran kill switch. Hilangnya `config.yaml` TIDAK mengubah status flag. Direktori data hilang atau flag tidak dapat diperiksa → BLOCKED (fail closed).** | §B2 + §B3: `is_publishing_allowed()` TIDAK membaca `config.yaml` sama sekali (hanya pointer direktori, fallback `"data"`); `data/` hilang/tidak terbaca → `False` + alasan "tidak dapat diperiksa". Uji: RV-7, RV-8 (§B7). |

## Koreksi wajib revisi final tambahan (K2-1 s.d. K2-6) — mengikat, dari Kyan 17 Nov 2026 01:42 WIB

| # | Koreksi | Dampak ke desain (di mana diterapkan) |
|---|---|---|
| K2-1 | **Fork safety untuk flock.** Periksa PID pemilik lock terhadap PID proses saat ini. Proses hasil fork TIDAK BOLEH mewarisi hak kepemilikan lock parent; proses anak wajib memperoleh lock sendiri. | §B4-C1: `acquire_publisher_lock()` memvalidasi `_lock_pid == os.getpid()` di setiap pemanggilan; bila PID berbeda (proses hasil fork) → state warisan dibuang (fd warisan ditutup, depth direset) lalu acquire baru via `flock()`; `release_publisher_lock()` no-op bila PID berbeda. Uji: RV2-1, RV2-2 (§B7). |
| K2-2 | **Atomic history + concurrent writes.** Semua operasi read-modify-write pada history dilindungi lock yang sama; intent punya ID operasi unik; `write_intent()` MENOLAK duplikasi idempotency key, termasuk status `publish_started`; update receipt berdasarkan ID intent; kegagalan menulis intent WAJIB membatalkan request; DELETE punya ID operasi tersendiri. | §B4-C2: `op_id` unik per intent; penolakan duplikat atomik di bawah lock; receipt update by `intent_id`; gagal tulis intent = batalkan request (fail closed). Uji: RV2-3, RV2-4, RV2-5 (§B7). |
| K2-3 | **Idempotency key per jenis operasi.** Post affiliate/video: `content_id + sub_id + channel`. Auto-comment: `comment_id + target_media_id + channel`. Pinterest: `content_id + sub_id + pinterest`. DELETE: `delete_operation_id + media_id`. Key antarjenis tidak boleh bertabrakan. | §B4-C2: skema kunci dengan prefix namespace per jenis (`pub:` / `cmt:` / `pin:` / `del:`); diterapkan di semua jalur §B5 urutan 3–10. Uji: RV2-6 (§B7). |
| K2-4 | **Pemisahan publish dan DELETE pada repost.** Publish baru dan DELETE lama adalah dua operasi independen. DELETE gagal/ambigu TIDAK BOLEH memicu retry otomatis. Tidak boleh menghapus history lama. Relasi `supersedes`/`replaces` harus eksplisit. Tidak ada rollback otomatis dengan menghapus post baru. | §B3 [3d], §B4-C3, §B5 urutan 8: dua intent terpisah (op ID + kunci sendiri); DELETE gagal → status akhir tercatat (post baru live + post lama tetap ada), tanpa retry/rollback otomatis. Uji: RV2-7, RV2-8 (§B7). |
| K2-5 | **Perilaku CLI Pinterest.** Tanpa `--live`: tidak ada mutasi + tampilkan DRY-RUN. Dengan `--live`: wajib melewati semua pemeriksaan keamanan. `--dry-run` dan `--live` bersamaan HARUS ditolak sebagai konflik. Konsisten di `run_pinterest.py` dan `pinterest_api.py`. | §B5 urutan 9–10: default = dry-run (tanpa mutasi, banner DRY-RUN); kombinasi `--dry-run --live` = error konflik (exit 2), 0 mutasi. Uji: RV2-9 (§B7). |
| K2-6 | **Pisahkan status kill switch dan kesehatan sistem.** CLI `publish_guard.py status` menampilkan 5 baris terpisah: Kill switch ALLOWED/BLOCKED; Data directory HEALTHY/ERROR; Lock FREE/HELD; Publisher integration COMPLETE/INCOMPLETE; Live publishing authorization NOT AUTHORIZED selama Sprint 3. | §B3 (subsection status CLI): arti + sumber tiap baris; status kill switch tidak dicampur dengan kesehatan sistem. Uji: RV2-10 (§B7). |

**Pemeriksaan kontradiksi (K2 vs D1–D9, K0-1 s.d. K0-8, K1-1 s.d. K1-4) — tidak ada kontradiksi; empat ketegangan diperiksa dan diselesaikan:**
- **K2-1 vs K1-1 (nested flock):** bukan kontradiksi — K1-1 mengatur pemanggilan berulang *dalam satu proses yang sama* (idempotent, boleh lanjut); K2-1 mengatur *proses hasil fork* (PID berbeda = proses berbeda = wajib lock sendiri). Pembeda formalnya adalah PID pemilik lock: `_lock_pid == os.getpid()` → nested (lanjut); `_lock_pid != os.getpid()` → warisan fork (buang state, acquire baru). Keduanya ditegakkan oleh pemeriksaan PID yang sama di `acquire_publisher_lock()`.
- **K2-2 vs K0-7 (append-only) dan vs Sprint 2:** penolakan duplikat tidak menghapus apa pun — intent yang ditolak tidak ditulis, intent lama tetap ada. Transisi status dalam SATU entri intent (`publish_started` → `posted`) adalah siklus hidup satu operasi, bukan penimpaan riwayat; entri `post_history.json` lama tetap tidak pernah ditimpa. Pengecualian retry yang sah: setelah `reconcile.py --apply` manusia menyelesaikan intent lama ke status terminal (`abandoned` / `posted` / `posted_receipt_incomplete` / `deleted` / `delete_failed`), intent BARU dengan `op_id` baru boleh ditulis untuk kunci yang sama — intent lama tetap tersimpan sebagai `abandoned`. Status non-terminal (`publish_started`, `publish_interrupted`, `delete_started`, `delete_ambiguous`) selalu memblokir intent baru untuk kunci yang sama.
- **K2-3 vs kunci Sprint 2 `(content_id, sub_id)`:** perluasan, bukan perubahan — komponen tengah kunci tetap sama; K2-3 hanya menambah prefix namespace jenis operasi + channel. Kunci lama dapat dipetakan secara mekanis ke kunci baru (`pub:threads:<content_id>:<sub_id>`).
- **K2-5 vs D5:** perluasan — D5 sudah mewajibkan `--live` eksplisit; K2-5 menambahkan perilaku default (dry-run + banner) dan penolakan konflik `--dry-run --live`. Tidak ada keputusan D5 yang diubah.

## Koreksi wajib revisi terakhir (P0-1, P1-1, P1-2) — mengikat, dari Kyan 17 Nov 2026 ~08:05 WIB

| # | Koreksi | Dampak ke desain (di mana diterapkan) |
|---|---|---|
| P0-1 | **Hard gate otorisasi live selama Sprint 3.** Status "Live publishing authorization: NOT AUTHORIZED" TIDAK BOLEH hanya berupa informasi CLI — ia harus berupa **hard gate yang ditegakkan pada SETIAP choke point mutasi**. Selama Sprint 3, SEMUA request mutasi live WAJIB ditolak, sekalipun kill switch berstatus ALLOWED. Berlaku untuk: Threads API `_post()`, Playwright `poster.post()`, Pinterest `create_pin()`, auto-comment, vendor CLI, repost, dan DELETE. Dry-run dan operasi read-only tetap diperbolehkan. Otorisasi live TIDAK BOLEH aktif otomatis setelah seluruh tes lulus atau setelah kill switch ALLOWED — ia hanya bisa diaktifkan oleh keputusan manusia terpisah SETELAH Sprint 3 selesai. | §B1 (prinsip 8, baru), §B2 (flag dihapus ≠ otorisasi), §B3 (hard gate sebagai lapis [0] di semua choke point + subsection baru), §B4-C2/C3 (intent/reconcile tidak melewati hard gate — lihat pengecualian yang dinyatakan), §B5 urutan 1 (hard gate bagian dari guard, sebelum jalur lain dibuka) + §B5b C-S3-1, §B6 R24–R27, §B7 (dampak terhadap pengujian + matriks choke point × gate + RV3-1 s.d. RV3-11), §B9. Uji: RV3-1 s.d. RV3-5 (§B7). |
| P1-1 | **Shared lock untuk reconcile.** `reconcile.py --apply` WAJIB memperoleh shared publisher lock yang sama (`data/.publisher.lock` via `acquire_publisher_lock()`). Jika lock gagal diperoleh, batalkan SELURUH perubahan. Operasi recovery tidak boleh menimpa atau berkompetisi dengan history yang sedang diperbarui publisher. Default `--check` tetap read-only. | §B4-C1 (lock dipakai reconcile), §B4-C3 (prosedur `--apply`: lock + baca ulang di bawah lock + tulis atomik; `--check` tetap tanpa lock dengan penanganan torn-read), §B5 urutan 11, §B5b C-S3-9, §B6 R25, §B7 RV3-6 s.d. RV3-8, §B9. Uji: RV3-6, RV3-7, RV3-8 (§B7). |
| P1-2 | **Default-deny Pinterest direct import.** `create_pin()` harus menegakkan otorisasi live di titik mutasi TERDALAM. Persyaratan `--live` tidak cukup hanya diperiksa pada CLI. Pemanggilan fungsi langsung dari Python TIDAK BOLEH melewati otorisasi live, kill switch, shared lock, intent record, dan idempotency. | §B3 [3c] (gate di dalam `create_pin()`), §B5 urutan 10, §B5b C-S3-8, §B6 R26, §B7 (matriks choke point × gate + RV3-9 s.d. RV3-11), §B9. Uji: RV3-9, RV3-10, RV3-11 (§B7). |

**Pemeriksaan kontradiksi (P0-1, P1-1, P1-2 vs D1–D9, K0–K2, §B5, §B5b, §B7, §B8, §B9) — diperiksa satu per satu; tidak ada kontradiksi yang tidak terselesaikan:**
- **P0-1 vs T2 / matriks per publisher (kolom "ON → jalan (mock)") / D-1 / D-4 / D-6 / K3 / RV-3 / RV-4 / RV-5 / RV2-7 / RV2-8 (§B7):** KETEGANGAN NYATA, diselesaikan dengan re-scope eksplisit (bukan dengan mengubah P0-1). Semua ekspektasi "mock publish sukses" di §B7 ditulis SEBELUM hard gate ada, saat "ON" masih berarti "boleh publish". Selama Sprint 3, "ON" (kill switch ALLOWED) TIDAK PERNAH berarti "boleh publish" — hard gate menolak semua mutasi. Karena itu: (a) T2, kolom ON matriks per publisher, D-1, D-4, D-6, dan bagian K3 yang mensyaratkan request terkirim di-re-scope menjadi uji penolakan hard gate (0 mutasi) — lihat subsection baru "Dampak P0-1 terhadap rencana pengujian" di §B7; (b) jalur sukses penuh (gate → lock → intent → HTTP mock → receipt) diuji pada level komponen secara terisolasi (fungsi guard, lock, `write_intent()`, pemeriksa idempotency — tanpa melewati choke point live) dan sebagai uji end-to-end TERTUNDA (T2-live, D-1-live, D-6-live, K3-live — lihat §B7) yang HANYA dijalankan setelah keputusan manusia terpisah mengaktifkan otorisasi live pasca-Sprint 3. Tidak ada satu pun uji sukses yang dijalankan selama Sprint 3. Tidak ada keputusan D/K yang diubah — hanya ekspektasi uji yang diselaraskan dengan hard gate.
- **P0-1 vs B1 prinsip 4 (dry-run tidak pernah diblokir) dan prinsip 6 (pembacaan tidak diblokir):** bukan kontradiksi — hard gate hanya dipasang pada choke point MUTASI. Dry-run tidak melewati choke point mutasi, dan `_get()`/`get_media()` (read-only) tidak dicek. RV3-4 membuktikannya.
- **P0-1 vs D3 (re-enable hanya Kyan):** bukan kontradiksi — P0-1 justru memperkuat D3. Menghapus flag file (re-enable kill switch) TIDAK memberikan otorisasi live. Keduanya adalah gerbang yang berbeda dan independen: flag mengatur "apakah Kyan mengizinkan publishing secara umum", hard gate mengatur "apakah live publishing diizinkan pada sprint ini" — dan jawaban kedua selama Sprint 3 selalu TIDAK. Seseorang yang menghapus flag tanpa otorisasi live tetap tidak bisa publish.
- **P0-1 vs K2-6 (status CLI 5 baris):** bukan kontradiksi — P0-1 adalah alasan K2-6 ada. Baris "Live publishing authorization: NOT AUTHORIZED" kini BUKAN sekadar informasi: ia menampilkan nilai hard gate yang ditegakkan (`LIVE_PUBLISHING_AUTHORIZED = False` di `publish_guard.py`, §B3). RV3-5 membuktikan pemisahannya dari baris kill switch.
- **P0-1 vs §B5/§B5b (urutan implementasi + rencana commit):** perubahan urutan yang disengaja, bukan kontradiksi — hard gate WAJIB menjadi bagian dari `publish_guard.py` (C-S3-1) SEBELUM jalur lain dibuka; commit-commit berikutnya menguji penolakan hard gate, bukan keberhasilan publish. §B5 urutan 1 dan §B5b C-S3-1 diperbarui.
- **P0-1 vs §B8 (file tidak disentuh):** bukan kontradiksi — P0-1 tidak menambah file baru di luar daftar §B5 (hard gate hidup di `publish_guard.py` yang sudah direncanakan); daftar §B8 tidak berubah.
- **P1-1 vs K0-5 (reconcile default read-only):** bukan kontradiksi — `--check` tetap read-only dan tetap tanpa lock (dengan penanganan torn-read yang dinyatakan di §B4-C3). Hanya `--apply` yang wajib lock. P1-1 mempersempit K0-5 (mode tulis), bukan mengubahnya.
- **P1-1 vs K2-2 (semua RMW history di bawah flock bersama):** perluasan yang konsisten — `reconcile.py --apply` adalah penulis history ketiga (setelah publisher dan `update_history` repost) dan kini secara eksplisit tunduk pada aturan yang sama. Tidak ada aturan lama yang dilonggarkan.
- **P1-1 vs K1-1/K2-1 (re-entrancy/fork):** bukan kontradiksi — reconcile adalah proses terpisah yang tidak memanggil publisher, jadi tidak ada re-entrancy; ia acquire lock secara normal dan gagal = batal. Aturan fork (K2-1) tetap berlaku bila reconcile sendiri mem-fork.
- **P1-1 vs K0-4 (HTTP 400 ≠ bukti tidak terbit):** bukan kontradiksi — P1-1 menambahkan satu syarat prosedural (baca ulang bukti DI BAWAH lock sebelum menulis), tanpa mengubah standar bukti K0-5/K0-4. Bukti yang dikumpulkan `--check` bisa basi; `--apply` wajib memverifikasi ulang di bawah lock.
- **P1-2 vs D5/K2-5 (CLI wajib `--live`):** perluasan, bukan perubahan — `--live` di CLI tetap wajib sebagai lapis eksplisit-intent; P1-2 menambahkan lapis keamanan di DALAM `create_pin()` sehingga batas keamanan tidak lagi bergantung pada CLI. D5/K2-5 tidak diubah.
- **P1-2 vs K0-6 (default-deny):** konsisten — pemanggilan langsung `create_pin()` dari Python adalah kasus default-deny yang dimaksud K0-6; P1-2 menutupnya secara eksplisit untuk Pinterest, sejajar dengan yang sudah dirancang untuk `_post()`.

---

## TAHAP A — Audit kondisi awal

### A1. Seluruh jalur publishing (di mana publish bisa terjadi)

| # | Jalur | Entry point | Panggilan publish | Guardrail | Dedup vendor | Idempotency Sprint 2 | Keterangan |
|---|---|---|---|---|---|---|---|
| 1 | **run_slot.py — API** (jalur timer) | `tools/run_slot.py:main()` → `--slot --api` | `publish_api.publish_text()` 2× (`run_slot.py` ~baris 380–400) | ✅ `check_chain()` sebelum publish | ✅ `dedup.check()` | ✅ `find_existing_publication(content_id, sub_id)` sebelum publish | Satu-satunya jalur yang lengkap. Dry-run return sebelum publish. |
| 2 | **run_slot.py — Playwright** | `tools/run_slot.py:main()` (tanpa `--api`) | `ThreadsPoster.post()` (`run_slot.py` ~baris 430) | ✅ sama | ✅ sama | ✅ sama (cek sebelum publish) | Receipt maksimal `posted_receipt_incomplete` (tanpa media_id). Cookie 16 Nov kena 429. |
| 3 | **publish_api.py CLI** | `tools/publish_api.py:main()` | `publish_text()` langsung | ❌ tidak ada | ❌ tidak ada | ❌ tidak ada | `--dry-run` bersifat opt-in — tanpa flag itu, perintah langsung publish. Bypass penuh. |
| 4 | **publish_video.py** (PC saja) | `tools/publish_video.py:main()` | `publish_api._post()` langsung (~baris 149, 155, 166) + `publish_text()` untuk reply | ✅ `check_chain()` + `--qc-ok` wajib | ❌ tidak ada | ❌ tidak ada | `--dry-run` default True, `--live` eksplisit. **Masih memfabrikasi permalink fallback** (~baris 174: `or f"https://www.threads.com/@{USERNAME}/post/{pid}"`) — perbaikan Sprint 2 TIDAK diterapkan di sini. Tidak menulis ke `post_history.json` sama sekali (hanya `data/video_publish_log.json`). |
| 5 | **auto_comment.py** (PC saja) | `tools/auto_comment.py:main()` → `send_comment_threads()` (~baris 477) | `publish_api.publish_text()` / `publish_media_reply()` langsung | ✅ `validate_comment()` pakai `check_chain()` | ⚠️ history sendiri (`comment_history.json`: `already_commented` + `sent_today`, `MAX_PER_DAY = 10`) | ❌ tidak ada vs `post_history.json` | `--dry-run` default True, `--live` eksplisit. **Owner-check fail-OPEN**: bila cek pemilik gagal (exception), kode mencetak peringatan lalu "lanjut kirim". `/keyword_search` 403 (rusak). |
| 6 | **vendor CLI** | `vendor/threads-affiliate/threads_poster/cli.py:cmd_post` (~baris 62) + `cmd_post_auto` (~baris 139) | `poster.post()` langsung | ❌ TIDAK ADA `check_chain` | ✅ `dedup.check()` + `record()` + `mark_used()` | ❌ tidak ada | `python -m threads_poster.cli post / post-auto` = bypass: tanpa guardrail, tanpa idempotency Sprint 2. `cmd_post_auto` memilih link UNUSED berikutnya lalu memanggil `cmd_post`. |
| 7 | **run_pinterest.py** (PC saja) | `tools/run_pinterest.py:main()` | `pinterest_api.create_pin()` (~baris 207) | ✅ `check_chain()` | ⚠️ history sendiri (`pinterest_history.json`: set link + maks 1/hari) | ❌ tidak ada (tanpa content_id/sub_id) | **Live adalah DEFAULT**: `--dry-run` bersifat opt-in (`if args.dry_run:` ~baris 196). Timer service memanggil TANPA `--dry-run`. Saat ini aman hanya karena timer disabled + tidak ada token. |
| 8 | **Panggilan langsung (import)** | sembarang `python -c "from publish_api import publish_text"` / `ThreadsPoster.post()` | langsung ke API / browser | ❌ | ❌ | ❌ | Tidak ada penghalang apa pun di level fungsi. |

**Temuan A1-a — `poster.post()` mentah.** `vendor/threads-affiliate/threads_poster/poster.py` (md5 PC = VM `5bae70e6…`) TIDAK mengandung referensi `check_draft` / `check_chain` / `dedup` sama sekali. Seluruh keamanan Playwright hidup di pemanggil (`run_slot.py` atau `cli.py`), bukan di publisher-nya.

**Temuan A1-b — `publish_api._post()` adalah choke point API.** Semua jalur API (1, 3, 4, 5) akhirnya melewati `_post()` untuk mutasi (`/me/threads`, `/me/threads_publish`). `_get()` hanya membaca (verifikasi permalink, `get_media`). Token tidak pernah tercetak; error dipotong 300 karakter; `grep -c access_token logs/cron.log` = **0**.

### A2. Scheduler & proses

**Systemd PC (user instance, terverifikasi `systemctl --user` 17 Nov 01:14 WIB):**

| Timer | Status | Jadwal | Service (`ExecStart`) |
|---|---|---|---|
| `threads-affiliate-0900.timer` | enabled + active | `OnCalendar=*-*-* 09:00:00`, `RandomizedDelaySec=1800`, `Persistent=true` | `run_slot.py --slot 09:00 --api` |
| `threads-affiliate-1230.timer` | enabled + active | 12:30, sama | `run_slot.py --slot 12:30 --api` |
| `threads-affiliate-1930.timer` | enabled + active | 19:30, sama | `run_slot.py --slot 19:30 --api` |
| `pinterest-1000.timer` | **disabled + inactive** | 10:00, `RandomizedDelaySec=900`, `Persistent=true` | `run_pinterest.py` (tanpa `--dry-run`) |

- Service: `Type=oneshot`, `WorkingDirectory=%h/threads-affiliate-system`, `StandardOutput=append:%h/threads-affiliate-system/logs/cron.log`, `StandardError=append:` (file yang sama). `TimeoutStartUSec=infinity` (run panjang tidak di-kill systemd), `TimeoutStopUSec=1min 30s`, `KillMode=control-group`.
- Slot 19:30 terakhir jalan 16 Nov 19:35 WIB (BONBOX). Slot 09:00 berikutnya 17 Nov 09:01:45 WIB (sudah termasuk jitter acak).
- **Tidak ada proses publisher yang berjalan saat audit** (`ps aux | grep run_slot/publish` kosong, 01:14 WIB).

**Cron VM:** `riset-shopee-mingguan` enabled, Senin 08:15 WIB (definisi dibaca langsung). Isinya riset produk + laporan — **tidak memanggil publisher apa pun** (tidak ada `run_slot` / `publish` / `cli post` di definisinya). Bukan jalur posting. Catatan: definisinya masih menyebut Sub-ID lama per kategori dan handle lama `@temuanhariann.id` (basi, tidak memengaruhi posting).

**Perilaku `Persistent=true` (penting untuk kill switch):** slot yang terlewat karena PC mati akan dieksekusi SEKALI saat timer aktif kembali / PC boot. Men-disable timer tidak membatalkan run yang sudah "terutang" — run itu akan menembak saat timer di-enable lagi.

### A3. Cara menghentikan publishing hari ini (dan apa yang terjadi)

| Cara | Efek | Celah |
|---|---|---|
| `systemctl --user stop/disable <timer>` | Slot berikutnya tidak jalan | Tidak menghentikan proses yang sedang berjalan; tidak membatalkan run `Persistent` yang terutang |
| `systemctl --user stop <service>` saat run berjalan | SIGTERM ke seluruh cgroup; 90 detik kemudian SIGKILL | **Celah kritis (lihat A3-a)** |
| Hapus/rename file token `~/.threads_poster/threads_token.env` | Jalur API gagal di `load_token` | Jalur Playwright tidak terpengaruh; merusak kredensial (bukan saklar) |
| Hapus cookies | Jalur Playwright gagal | Jalur API tidak terpengaruh |
| Tidak ada kill switch | — | Tidak ada satu pun saklar global; setiap jalur harus dimatikan satu per satu |

**Temuan A3-a — kill di tengah publish = double-post di slot berikut (celah terbesar).**
Alurnya: `publish_text(post_1)` berhasil di API → proses di-SIGTERM sebelum `dedup.record(entry)` → **tidak ada jejak apa pun**: link tetap UNUSED, history kosong. Slot berikutnya memilih link yang sama, `find_existing_publication` tidak menemukan apa-apa, `dedup.check` lolos (link belum pernah dipakai) → post 1 yang sama terbit **dua kali**. Idempotency Sprint 2 hanya bekerja bila proses hidup cukup lama untuk mencatat. Tidak ada *intent record* (catatan "saya akan publish X") sebelum panggilan irreversible.

**Temuan A3-b — akar duplikasi baris "Terkirim" di `cron.log` (TERJAWAB).**
Bukan double-post. `run_slot.py:log()` melakukan DUA hal untuk tiap pesan: `print()` ke stdout DAN `append` ke `logs/cron.log`. Sementara unit systemd mengarahkan `StandardOutput=append:` ke file `logs/cron.log` YANG SAMA. Setiap baris mendarat dua kali. Bukti: unit file + kode `log()` + ekor log 16 Nov 19:35 yang menampilkan tiap baris dua kali. BONBOX hanya terbit 1× (terverifikasi API, Sprint 2).

**Temuan A3-c — timeout API di tengah publish.** Bila `publish_text(post_1)` timeout SETELAH container terbit tapi SEBELUM respons kembali: `run_slot.py` menangkap exception; `r1` kosong → return 5 tanpa entri history (bukan `publish_interrupted` — cabang itu hanya bila `r1.get("id")` ada). Status menjadi ambigu: mungkin terbit, mungkin tidak. Satu-satunya jalan = verifikasi manual via `get_media` / permalink. Bila timeout terjadi pada `post_2` (reply) setelah `r1` ada → entri `publish_interrupted` tercatat dengan benar (Sprint 2).

### A4. Race condition / dua publisher bersamaan

- **Tidak ada locking di mana pun.** `grep -ri "flock|fcntl|filelock|O_EXCL|lockfile|.lock"` pada `tools/` + `vendor/.../threads_poster/*.py` = **0 hasil**.
- **Celah TOCTOU pada idempotency Sprint 2.** `find_existing_publication()` membaca `post_history.json`, lalu proses publish (~10–60 detik), lalu `dedup.record()` menulis. Dua proses yang start bersamaan SAMA-SAMA membaca history sebelum satu pun menulis → keduanya lolos cek → keduanya publish produk yang sama. `dedup.check()` (aturan 1: link reuse, aturan 2: kategori hook 2 terakhir, aturan 3: kemiripan hook >60%) memakai pola baca-cek-tulis yang sama → celah yang sama.
- **Kapan dua proses bisa bersamaan:** (1) run manual (live) + timer slot yang sama; (2) catch-up `Persistent=true` setelah PC boot bersamaan dengan run manual; (3) dua timer yang tumpang tindih — kecil kemungkinannya (slot berjarak 3,5 jam, jitter maks 30 menit) tapi tidak mustahil bila satu run macet lama (poll container maks 30 dtk × 2 + retry rantai 5×, masih < 3,5 jam — risiko rendah); (4) `run_slot.py` + `publish_video.py --live` / `auto_comment.py --live` / `run_pinterest.py` yang dijalankan manual pada jam yang sama — tidak ada yang saling mengenal.
- **Batas harian juga racy.** `posted_today` dihitung dari `dedup.load()` di awal run; dua proses bersamaan sama-sama melihat 0 lalu sama-sama publish → 2 post dalam satu slot, batas 3/hari bisa tembus bila 3 proses bersamaan.

### A5. Status konfigurasi & backup

**Divergensi PC ↔ VM (temuan audit — klaim "VM disinkronkan" Sprint 2 ternyata SEBAGIAN):**

| File | PC | VM | md5 |
|---|---|---|---|
| `tools/run_slot.py` | Sprint 2 | sama | `81e74f86…` identik ✅ |
| `tools/publish_api.py` | Sprint 2 | sama | `460c59b0…` identik ✅ |
| `tools/check_draft.py` | v5 + batas 470/500 | sama | `4de464be…` identik ✅ |
| `config.yaml` | **v5** (disclosure dilarang, API LIVE, ada section `pinterest`) | **v1 BASI** (disclosure `#affiliate` WAJIB, API "MENUNGGU", TIDAK ADA section `pinterest`) | beda ❌ |
| `guardrails.md` | **v5** (kata komisi/affiliate dilarang) | **v1 BASI** (§4 masih MEWAJIBKAN disclosure `#affiliate` / kalimat komisi) | beda ❌ |
| `tools/publish_video.py` | ada | **TIDAK ADA** | — |
| `tools/auto_comment.py` | ada | **TIDAK ADA** | — |
| `tools/pinterest_api.py` | ada | **TIDAK ADA** | — |
| `tools/run_pinterest.py` | ada | **TIDAK ADA** | — |
| `vendor/.../dedup.py`, `poster.py` | — | sama | identik ✅ |
| `data/post_history.json` | 2 entri (Kikkoman + BONBOX receipt lengkap) | sama | `b7f0d50c…` identik ✅ |
| `data/affiliate_links.md` | 29 link | sama | identik (Sprint 1) ✅ |

**Dampak divergensi:** bila VM dipakai sebagai publisher fallback, ia menegakkan aturan yang SUDAH DIBATALKAN Kyan (disclosure komisi wajib) dan tidak punya 4 tool PC. VM tidak punya `~/.threads_poster/` (tidak ada token) sehingga jalur API di VM akan gagal di `load_token` — tapi jalur Playwright di VM masih bisa posting bila cookie ada (tidak diverifikasi ada/tidaknya cookie di VM dalam audit ini).

**Backup yang ada (PC, terverifikasi):**
- `data/affiliate_links.md.bak-20261116-1830` + `data/affiliate_links.md.bak-20261117-0024` (md5 `715611b8…`, cocok dengan DB pra-Sprint 1).
- `data/post_history.json.bak-20261117-0100` (md5 `ac0687a1…`).
- `~/.config/git/config.bak-20261117` (perbaikan helper gh).
- `.gitignore` menutupi `*token*.env`, `data/affiliate_links.md`, `data/post_history.json`, `data/pinterest_history.json`, `data/comment_history.json`, `data/video_publish_log.json`, `logs/`, `cookies/`.
- Token Threads: `~/.threads_poster/threads_token.env` mode 600, ada. Direktori `~/.pinterest_poster/` TIDAK ADA (Pinterest belum live). Nilai token tidak pernah dibaca/ditampilkan dalam audit ini.
- Git PC: HEAD `6c6eb1a`; uncommitted: `templates/hooks_{dapur,organizer,kebersihan}.json` (v5.1) + untracked: `docs/audit-operating-system-20261116.md`, 3× `templates/*.bak-20261116`, `tools/check_combo_rate.py`, `tools/merge_new_hooks.py`, `tools/repost_product.py`.

**Log:** `logs/cron.log` PC 45 baris (±22 peristiwa unik — sisanya duplikat, lihat A3-b). Tidak ada structured ops log; receipt hidup di `post_history.json`; metrik di `data/performance.csv`. File debug Playwright (`debug-*.png`, `login-check.png`, 16 Nov) masih di `logs/`.

### A6. Kepatuhan idempotency Sprint 2 per jalur

| Jalur | Idempotency (content_id, sub_id) | Penilaian |
|---|---|---|
| run_slot → API text | ✅ cek sebelum publish + receipt validation | Patuh, kecuali celah TOCTOU + kill-mid-publish (A3-a, A4) |
| run_slot → Playwright | ✅ cek sama (receipt dibatasi `posted_receipt_incomplete`) | Patuh, celah yang sama |
| publish_api CLI | ❌ | Bypass |
| publish_video | ❌ (tanpa cek, tanpa tulis history) | Tidak patuh + permalink difabrikasi |
| auto_comment | ❌ (hanya history komen sendiri) | Tidak patuh terhadap post_history |
| vendor CLI | ❌ (hanya dedup vendor) | Tidak patuh + tanpa guardrail |
| run_pinterest | ⚠️ sebagian (link reuse + 1/hari, tanpa content_id/sub_id) | Sebagian; default live pula |

---

## A7. Audit ulang entry point & choke point (Tahap 1, 17 Nov 2026 ~02:00 WIB)

Audit ulang dilakukan dengan membaca ulang SEMUA file `tools/` + `vendor/.../threads_poster/` di PC (mesin LIVE) dan membandingkan md5 dengan VM. Ditemukan **2 entry point yang TERLEWAT di audit Tahap A** + 1 flag bypass tambahan.

### A7-a. Tabel entry point lengkap (revisi)

| # | Jalur | Entry point | Panggilan publish | Guardrail | Idempotency S2 | Kill switch tercakup dalam desain? | Status |
|---|---|---|---|---|---|---|---|
| 1 | run_slot → API | `tools/run_slot.py:main()` `--slot --api` | `publish_api.publish_text()` 2× | ✅ | ✅ | ✅ Ya — cek [1]+[2]+[3] | Tercakup |
| 2 | run_slot → Playwright | `tools/run_slot.py:main()` (tanpa `--api`) | `ThreadsPoster.post()` | ✅ | ✅ | ✅ Ya — cek [1]+[2]+[3b] | Tercakup |
| 3 | publish_api CLI | `tools/publish_api.py:main()` `--text` | `publish_text()` langsung | ❌ | ❌ | ✅ Ya — via `_post()` [3] | Tercakup (baru ditutup) |
| 4 | publish_video | `tools/publish_video.py:main()` `--live` | `publish_api._post()` langsung + `publish_text()` (reply) | ✅ | ❌ | ✅ Ya — via `_post()` [3] + D4 | Tercakup (baru ditutup) |
| 5 | auto_comment | `tools/auto_comment.py:main()` `--live` | `publish_text()` / `publish_media_reply()` | ✅ | ❌ | ✅ Ya — via `_post()` [3] + D2 | Tercakup (baru ditutup) |
| 6 | vendor CLI | `vendor/.../cli.py:cmd_post` (~62) + `cmd_post_auto` (~139) | `poster.post()` | ❌ | ❌ (hanya dedup vendor) | ✅ Ya — via `poster.post()` [3b] + D6 | Tercakup (baru ditutup) |
| 7 | run_pinterest | `tools/run_pinterest.py:main()` (live = DEFAULT) | `pinterest_api.create_pin()` | ✅ | ⚠️ sebagian | ✅ Ya — via `create_pin()` [3c] + D5 | Tercakup (baru ditutup) |
| 8 | Panggilan langsung (import) | `python -c "from publish_api import publish_text"` | langsung | ❌ | ❌ | ✅ Ya — via `_post()` [3] | Tercakup (baru ditutup) |
| 9 | **repost_product (BARU — terlewat di Tahap A)** | `tools/repost_product.py:main()` (UNTRACKED di git; ada di PC + VM, md5 identik `e9050612…`) | `publish_text()` 2× + **`delete_media()` (DELETE via API)** | ✅ `check_chain` | ❌ | ⚠️ **SEBAGIAN** — publish tertutup via `_post()` [3]; **`delete_media()` TIDAK melewati `_post()`** (panggilan `urllib` sendiri dengan token di URL) → butuh gate sendiri | **Celah — D9 kini DISETUJUI YA (17 Nov 2026 01:34 WIB); gate di §B5 urutan 8** |
| 10 | **pinterest_api CLI (BARU — terlewat di Tahap A)** | `tools/pinterest_api.py:main()` | `create_pin()` langsung | ❌ (hanya cek judul ≤100) | ❌ | ✅ Ya — via `create_pin()` [3c] + D5 (wajib `--live`) | Tercakup (baru ditutup) |

**Bukan entry point (diverifikasi):** `debug_poster.py` (diagnosis saja — membuka composer, TIDAK mengetik/mengirim; docstring "tanpa posting"), `probe_composer.py` (probe read-only), `check_login.py`, `test_sso.py`, `whoami.py`, `extract_brave_cookies.py`, `check_combo_rate.py`, `merge_new_hooks.py` (tidak ada yang memanggil publish).

### A7-b. Temuan baru dari audit ulang

- **A7-b1 — `repost_product.py` adalah entry point ke-9.** File ini UNTRACKED (belum pernah di-commit; tidak ada di `git log`). Ia publish ulang produk + MENGHAPUS post lama via `delete_media()` (DELETE `/{media_id}?access_token=...`). Delete adalah tindakan irreversible di luar jalur publish — choke point `_post()` TIDAK menutupnya. Keputusan D9 (di bawah) diperlukan: apakah delete ikut kill switch.
- **A7-b2 — `update_history()` di `repost_product.py` MENIMPA riwayat.** `entry.update({...})` menimpa `date/hook/media_id/permalink/status` entri lama di `post_history.json` — melanggar koreksi K0-7 (append/audit-preserving). Wajib diubah di Tahap 2 menjadi append entri baru + catatan `supersedes` (lihat §B5 urutan 8).
- **A7-b3 — vendor CLI punya flag `--force` (bypass dedup).** `cli.py` ~baris 253: opsi "Bypass dedup check (NOT recommended)". D6 wajib menutupnya (hapus flag, atau buat flag itu tetap tunduk pada gate kill switch + idempotency).
- **A7-b4 — `publish_api.py main()` live adalah default.** `--dry-run` opt-in; tanpa flag, `--text` langsung publish (terverifikasi baca kode `main()` ~baris 168–184). Ditutup oleh gate di `_post()`, tapi CLI-nya sendiri juga harus diberi guardrail (D6) agar pesan penolakannya jelas, bukan error samar dari `_post()`.
- **A7-b5 — `auto_comment.py` owner-check fail-OPEN terkonfirmasi.** `send_comment_threads()` ~baris 496: `except Exception → print("…lanjut kirim.")`. Tambahan: `resolve_media_id()` mendekode shortcode yang TERBUKTI bukan ID media API (Sprint 2) — owner-check hampir pasti gagal → fail-open hampir selalu terpicu. Wajib diubah menjadi fail-CLOSED di Tahap 2 (gagal cek = JANGAN kirim).
- **A7-b6 — divergensi PC ↔ VM MASIH ADA (re-verifikasi 02:00 WIB).** `config.yaml` PC `eb1eb3ab…` vs VM `f344636d…`; `guardrails.md` PC `fce5939b…` vs VM `655bc2b1…` (VM masih v1, mewajibkan disclosure `#affiliate`). File kunci lain identik: `run_slot.py 81e74f86…`, `publish_api.py 460c59b0…`, `repost_product.py e9050612…`, `post_history.json b7f0d50c…`, `affiliate_links.md 4b35b6d4…`. D7 menegaskan VM bukan publisher.
- **A7-b7 — scheduler re-verifikasi 02:00 WIB.** 3 timer aktif (berikutnya 09:01:45 WIB hari ini); timer Pinterest disabled; service `threads-affiliate-0900` ExecStart `run_slot.py --slot 09:00 --api`, `StandardOutput=append:logs/cron.log`; service Pinterest ExecStart `run_pinterest.py` TANPA `--dry-run` dan TANPA `--live` (live default — D5). Tidak ada publisher yang sedang berjalan saat audit ulang (yang terlihat di `ps` hanya perintah audit itu sendiri).
- **A7-b8 — git status PC (02:00 WIB).** HEAD `6c6eb1a`; uncommitted: hooks v5.1 (3 file); untracked: `docs/audit-operating-system-20261116.md`, `docs/rancangan-kill-switch-sprint3.md`, 3× `templates/*.bak-20261116`, `tools/check_combo_rate.py`, `tools/merge_new_hooks.py`, `tools/repost_product.py`. Implementasi Tahap 2 TIDAK BOLEH menyentuh file-file ini kecuali yang memang masuk daftar §B5.

---

## TAHAP B — Desain kill switch

### B1. Prinsip desain

1. **Satu sumber kebenaran, di luar kode.** Saklar berupa file penanda (flag file), bukan nilai di kode — bisa diubah manusia tanpa edit Python/YAML dan tanpa deploy.
2. **Fail closed.** Bila status saklar tidak bisa ditentukan (file tidak terbaca, direktori hilang, modul rusak) → publishing DINONAKTIFKAN.
3. **Diperiksa di titik terakhir sebelum tindakan irreversible** — bukan hanya di awal program. Saklar yang dibuat DI TENGAH run harus menghentikan rantai di panggilan publish berikutnya.
4. **Dry-run tidak pernah diblokir.** Dry-run tidak memanggil API mutasi, jadi tidak perlu izin saklar.
5. **Tidak bisa dilewati.** Semua jalur (termasuk pemanggilan langsung fungsi publisher) melewati titik cek yang sama.
6. **Pembacaan (read) tidak diblokir.** Verifikasi receipt (`_get`, `get_media`) harus tetap jalan saat saklar OFF — kalau tidak, recovery pasca-crash menjadi mustahil.
7. **Re-enable hanya oleh manusia, eksplisit.** Tidak ada kode, timer, atau retry yang bisa menghidupkan kembali publishing.
8. **Otorisasi live adalah hard gate yang terpisah dari kill switch (P0-1).** Selama Sprint 3, otorisasi live bernilai NOT AUTHORIZED secara hard-coded di `publish_guard.py` (`LIVE_PUBLISHING_AUTHORIZED = False`) dan diperiksa pada SETIAP choke point mutasi SEBELUM pemeriksaan lain. Kill switch ALLOWED tidak pernah berarti live publishing diizinkan; lulus seluruh tes tidak mengaktifkannya; menghapus flag file tidak mengaktifkannya. Otorisasi live hanya bisa diaktifkan oleh keputusan manusia terpisah SETELAH Sprint 3 selesai (perubahan kode + persetujuan Kyan yang tercatat). Dry-run dan operasi read-only tidak melewati hard gate ini.

### B2. Lokasi & format (**DISETUJUI — D1**)

**Sumber kebenaran: flag file di `data/` (PC; VM punya salinannya sendiri, tidak disinkronkan via git).** Keputusan D1: flag file, bukan kunci `config.yaml`.

| File | Arti bila ADA | Cakupan |
|---|---|---|
| `data/publishing_disabled` | SEMUA publishing mati | Global (semua channel) |
| `data/publishing_disabled_threads` | Threads mati (API + Playwright + auto-komen) | Per channel |
| `data/publishing_disabled_facebook` | Facebook mati (publisher masa depan) | Per channel |
| `data/publishing_disabled_pinterest` | Pinterest mati | Per channel |

- Isi file: satu baris alasan + siapa + kapan, contoh: `dimatikan manual oleh Kyan 17 Nov 2026 02:00 — jeda sebelum audit iklan`. Isi dibaca untuk log; file kosong pun tetap berarti OFF (keberadaan file yang menentukan, bukan isinya — supaya `touch` saja cukup).
- File-file ini WAJIB masuk `.gitignore` (sudah tercakup pola `data/`? — verifikasi saat implementasi; bila belum, tambahkan).
- `config.yaml` HANYA mendokumentasikan pointer-nya (bukan sumber kedua):
  ```yaml
  publishing:
    kill_switch_dir: "data"   # flag file di sini; ADA = publishing OFF
    # file: publishing_disabled (+ _threads/_facebook/_pinterest)
    # default bila file tidak bisa dibaca: OFF (fail closed)
  ```
- **K1-4 — `config.yaml` BUKAN sumber kebenaran (tegas).** Hilangnya `config.yaml` (terhapus, rusak, tidak terbaca) TIDAK mengubah status flag sedikit pun: bila flag ADA → BLOCKED; bila flag TIDAK ADA → ALLOWED (selama pemeriksaan lain lolos). Alasannya: `is_publishing_allowed()` TIDAK BOLEH membaca `config.yaml` sama sekali — ia hanya memeriksa keberadaan/keterbacaan flag file di direktori data. Satu-satunya hal yang boleh dibaca dari config adalah pointer direktori (`kill_switch_dir`, default `"data"`) — dan bila pointer itu pun tidak bisa dibaca, fallback-nya adalah direktori `data` relatif terhadap repo root, BUKAN "izinkan". Sebaliknya, **direktori data hilang atau flag tidak dapat diperiksa → BLOCKED** (fail closed): bila `data/` tidak ada, tidak bisa di-list, atau terjadi I/O error saat memeriksa flag → `is_publishing_allowed()` mengembalikan `False` dengan alasan "direktori/flag tidak dapat diperiksa". Ini menutup celah "hapus direktori data untuk mematikan saklar". Uji: RV-7, RV-8 (§B7).
- **P0-1 — menghapus flag file TIDAK memberikan otorisasi live.** Flag kill switch dan otorisasi live adalah dua gerbang independen. Menghapus `data/publishing_disabled*` (re-enable, D3) hanya mengubah baris kill switch menjadi ALLOWED; baris otorisasi live tetap NOT AUTHORIZED dan semua mutasi tetap ditolak hard gate selama Sprint 3. Tidak ada urutan penghapusan flag, tidak ada hasil tes, dan tidak ada status kill switch apa pun yang mengaktifkan otorisasi live. Satu-satunya jalan adalah keputusan manusia terpisah pasca-Sprint 3 (perubahan nilai `LIVE_PUBLISHING_AUTHORIZED` di `publish_guard.py` + persetujuan Kyan yang tercatat + verifikasi `publish_guard.py status`).
- **Alternatif yang dipertimbangkan dan DITOLAK sebagai sumber utama:** kunci `publishing.enabled: true/false` di `config.yaml` — edit YAML berisiko (sintaks rusak = seluruh config gagal dibaca = semua slot mati dengan cara yang membingungkan; dan file config ikut ter-commit ke git, sehingga saklar bisa tidak sengaja berubah lewat `git pull`/sync VM↔PC). Flag file bersifat lokal per mesin dan tidak ikut version control — tepat untuk saklar darurat.

### B3. Titik pemeriksaan (di mana cek dilakukan) — **DISETUJUI dengan koreksi K0-3**

Satu modul baru **`tools/publish_guard.py`** — satu-satunya tempat yang tahu soal saklar. **Prinsip K0-6 (default-deny):** daftar jalur yang diizinkan bersifat eksplisit (allowlist). Jalur apa pun yang belum terintegrasi dengan gate ini = DITOLAK, bukan diizinkan. Tidak adanya kill switch bukan izin otomatis.

```python
def is_publishing_allowed(channel: str) -> tuple[bool, str]
#   channel: "threads" | "facebook" | "pinterest"
#   True  -> ("", ...) bila tidak ada flag relevan
#   False -> (alasan) bila ada flag global/per-channel, ATAU bila status
#            tidak bisa ditentukan (I/O error, direktori hilang)
def require_publishing(channel: str) -> None
#   raise PublishingBlocked(reason) bila tidak diizinkan
```

Titik cek (berlapis — yang terdalam tidak bisa dilewati; **K0-3: cek TEPAT SEBELUM request irreversible, bukan hanya di entry point**). **P0-1 — hard gate otorisasi live adalah lapis [0], diperiksa SEBELUM semua lapis lain pada setiap choke point mutasi** (lihat subsection "Hard gate otorisasi live (P0-1)" di bawah):

```
[0] HARD GATE otorisasi live — di setiap choke point mutasi, SEBELUM kill switch
        │  LIVE_PUBLISHING_AUTHORIZED == False (hard-coded selama Sprint 3)
        │  → raise LiveNotAuthorized, TIDAK ADA request yang dikirim,
        │  tidak ada intent yang ditulis, tidak ada lock yang diambil
        ▼
[1] run_slot.py main() — awal, sebelum pilih link
        │  gagal cepat, log jelas, exit 1
        ▼
[2] run_slot.py — TEPAT SEBELUM publish_text/poster.post (cek ulang)
        │  (menangkap flag yang dibuat di tengah run)
        ▼
[3] publish_api._post() — SEBELUM SETIAP POST mutasi  ★ TITIK TERAKHIR
        │  Urutan di dalam `_post()`: [0] hard gate otorisasi live (P0-1)
        │  → [kill switch] → [lock] → [idempotency] → [intent] → request.
        │  Mencakup: publish_text, publish_media_reply, publish_video,
        │  auto_comment (D2: komen ikut kill switch Threads),
        │  CLI main, repost_product, import langsung. _get() TIDAK dicek
        │  (read-only — verifikasi receipt harus tetap jalan).
        ▼
[3b] ThreadsPoster.post() — awal method (jalur Playwright)
        │  Urutan yang sama: [0] hard gate (P0-1) → kill switch →
        │  lock → idempotency → intent → browser. + gate yang sama di
        │  vendor cli.py cmd_post/cmd_post_auto (D6), termasuk penutupan
        │  flag --force (bypass dedup) — lihat §A7-b3.
[3c] pinterest_api.create_pin() — awal fungsi
        │  Urutan yang sama: [0] hard gate (P0-1) → kill switch →
        │  lock → idempotency → intent → HTTP. **P1-2: seluruh urutan
        │  ini ditegakkan DI DALAM `create_pin()` sendiri** — pemanggilan
        │  langsung dari Python tidak bisa melewatinya (CLI `--live`
        │  tetap wajib sebagai lapis eksplisit-intent, D5/K2-5, tetapi
        │  BUKAN batas keamanannya). + gate di run_pinterest.py main()
        │  dan pinterest_api.py main() (D5: keduanya wajib --live
        │  eksplisit).
[3d] repost_product.delete_media() — awal fungsi (DELETE = irreversible)
        │  Urutan yang sama: [0] hard gate (P0-1) → kill switch → lock
        │  → idempotency (`del:`) → delete intent → HTTP DELETE.
        │  ★ D9 DISETUJUI YA (17 Nov 2026 01:34 WIB): ikut kill switch
        │  Threads (blokir bila OFF), termasuk pemanggilan langsung.
        │  Sebelum DELETE: cek saklar + lock (re-entrant, K1-1) +
        │  intent record DELETE terpisah (K1-2, file
        │  data/delete_history.json). Penghapusan hanya lewat alur
        │  yang melewati seluruh pemeriksaan keamanan.
        ▼
    API / browser  (tindakan irreversible)
```

- **Mengapa `_post()` adalah titik kunci:** semua jalur API — termasuk pemanggilan langsung `publish_text()` dari Python dan `publish_api.py --text` dari CLI — melewatinya. Satu baris `require_publishing("threads")` di `_post()` menutup seluruh bypass API sekaligus.
- **Hard gate otorisasi live (P0-1) — BUKAN informasi CLI, melainkan penegakan.** Di `tools/publish_guard.py`:
  ```python
  LIVE_PUBLISHING_AUTHORIZED = False  # hard-coded selama Sprint 3 — TIDAK dibaca dari
                                       # config, flag file, env var, atau hasil tes.

  def require_live_authorization(channel: str) -> None:
      # raise LiveNotAuthorized(channel) bila LIVE_PUBLISHING_AUTHORIZED is not True.
      # Dipanggil sebagai BARIS PERTAMA di setiap choke point mutasi:
      #   _post(), poster.post(), create_pin(), delete_media(),
      #   dan di awal live path auto_comment / vendor CLI / repost.
      # Dry-run dan _get()/get_media() TIDAK memanggil fungsi ini.
  ```
  Aturan yang mengikat: (a) hard gate diperiksa SEBELUM kill switch, lock, idempotency, dan intent — penolakan hard gate tidak menulis intent, tidak mengambil lock, tidak menyentuh history; (b) selama Sprint 3, SEMUA mutasi live ditolak sekalipun kill switch ALLOWED dan sekalipun seluruh tes lulus — tidak ada jalur kode yang mengubah `LIVE_PUBLISHING_AUTHORIZED` menjadi `True` (grep: nilai ini hanya ditulis di satu tempat, di `publish_guard.py`, dan tidak ada fungsi yang mengubahnya); (c) pengaktifan otorisasi live hanya bisa terjadi SETELAH Sprint 3 selesai, melalui perubahan kode eksplisit + persetujuan Kyan yang tercatat + verifikasi `publish_guard.py status` — bukan oleh hasil tes, bukan oleh penghapusan flag, bukan oleh timer; (d) penolakan hard gate mencatat satu baris log: `[ISO] ⛔ LIVE NOT AUTHORIZED: mutasi <channel>/<operasi> ditolak selama Sprint 3 — 0 request dikirim.` (tanpa token/secret). Uji: RV3-1 s.d. RV3-5 (§B7). **Pengecualian yang dinyatakan, bukan celah:** `reconcile.py --apply` TIDAK melewati hard gate — ia tidak mengirim mutasi live apa pun ke platform, ia hanya mengubah status history lokal. Ia diatur oleh aturannya sendiri: lock bersama (P1-1) + bukti rangkap tiga + `--apply` eksplisit manusia (K0-5). Pengecualian ini dicatat di sini agar tidak ada yang mengira reconcile adalah jalan memutar menuju publish.
- **Mengapa tetap ada cek [1] dan [2]:** gagal cepat (tanpa buang waktu generate rantai + guardrail) dan pesan log yang menjelaskan ALASAN (bukan error API samar).
- **Playwright tidak melewati `_post()`** → butuh cek sendiri di `ThreadsPoster.post()` (vendor — edit via patch yang didokumentasikan di `VENDOR-NOTES.md`; DISETUJUI D6). Gate yang sama di `cli.py cmd_post`/`cmd_post_auto` (D6).
- **K1-1 — nested flock dilarang; cek kill switch tetap berlapis.** Satu proses = SATU pemilik lock. `acquire_publisher_lock()` bersifat **idempotent dalam satu proses**: bila proses ini sudah memegang lock (dicatat di memori proses: fd + PID + counter re-entrancy), pemanggilan kedua langsung berhasil TANPA mengambil `flock()` kedua. Publisher terdalam (mis. `publish_text()` yang dipanggil dari dalam `run_slot.py` yang sudah memegang lock) TETAP WAJIB memeriksa kill switch di choke point-nya (`_post()`), tetapi TIDAK BOLEH mengambil lock lagi. Sebaliknya, **pemanggilan langsung** (CLI, `python -c`, import dari proses baru) TIDAK punya lock → WAJIB memperoleh lock dulu (gagal = exit 4). Aturan ringkas: *cek saklar di setiap lapis; lock hanya sekali per proses.* Implementasi: `publish_guard.py` menyimpan `_LOCK_FD` + `_LOCK_OWNER_PID` + `_LOCK_DEPTH` di level modul; `acquire_publisher_lock()` menaikkan counter bila pemiliknya adalah proses ini, dan hanya memanggil `fcntl.flock()` bila belum dimiliki. `release_publisher_lock()` menurunkan counter; fd ditutup hanya bila counter kembali 0. Uji: RV-1, RV-2 (§B7). **K2-1 — fork safety (lihat §B4-C1):** pemeriksaan PID di atas juga yang membedakan nested (PID sama, boleh lanjut) dari fork (PID berbeda, wajib acquire baru) — proses anak tidak pernah mewarisi hak lock parent.
- **Pinterest tidak melewati `_post()`** → cek di `create_pin()` + di `run_pinterest.py main()`.
- **Dry-run:** `run_slot.py --dry-run` return SEBELUM titik [2]/[3] (sudah begitu hari ini); `publish_video.py`/`auto_comment.py`/`run_pinterest.py --dry-run` juga tidak menyentuh `_post`/`create_pin`. Tidak ada perubahan perilaku dry-run.

**Alur keputusan (ASCII):**

```
pengguna / timer / cron
        │
        ▼
  run_slot.py main()
        │  ┌─ flag ADA? ──YA──▶ log "⛔ KILL SWITCH OFF (alasan)" → exit 1
        │  └─ TIDAK → lanjut (pilih link, generate, guardrail, dedup,
        │                    idempotency, lock — lihat §B5)
        ▼
  TEPAT SEBELUM publish (cek ulang flag)
        │  ┌─ flag ADA? ──YA──▶ catat publish_interrupted? TIDAK —
        │  │                    belum ada yang terbit → log + exit 1,
        │  │                    link TETAP UNUSED (aman diulang nanti)
        │  └─ TIDAK → lanjut
        ▼
  publish_api._post() / poster.post() / create_pin() / delete_media()
        │  ┌─ [0] hard gate: LIVE_PUBLISHING_AUTHORIZED False? ──YA──▶
        │  │   raise LiveNotAuthorized (Sprint 3 — 0 request, 0 intent)
        │  ├─ flag ADA? ──YA──▶ raise PublishingBlocked (tidak ada
        │  │                    request yang dikirim ke Meta)
        │  └─ TIDAK → lock → idempotency → intent (atomik + fsync)
        │             → kirim ke API/browser
        ▼
  receipt + catat history (Sprint 2, tidak berubah)
```

**Logging pemblokiran:** tiap penolakan menulis satu baris ke `logs/cron.log` (dan stdout bila interaktif):
`[ISO] ⛔ KILL SWITCH: publishing threads DIBLOKIR (data/publishing_disabled: <isi/alasan>) — tidak ada request dikirim.`
Satu file log khusus `logs/kill-switch.log` (append-only, satu baris per kejadian: block + "flag dihapus, publishing diizinkan kembali" yang terdeteksi pada run pertama setelah penghapusan) diusulkan sebagai audit trail saklar. TIDAK PERNAH menulis token/secret ke log mana pun (verifikasi: `grep access_token` di log = 0, sudah begitu hari ini).

**Re-enable (eksplisit manusia):**
```bash
# PC (mesin LIVE) — via SSH:
rm ~/threads-affiliate-system/data/publishing_disabled   # global, atau:
rm ~/threads-affiliate-system/data/publishing_disabled_threads  # per channel
python3 tools/publish_guard.py status   # verifikasi: harus "ALLOWED"
```
Tidak ada perintah otomatis, cron, atau kode yang menghapus flag. Bila flag dihapus, run berikutnya mencatat "kill switch OFF" di log sebagai jejak.

### Status CLI — kill switch dan kesehatan sistem dipisah (K2-6)

`python3 tools/publish_guard.py status` adalah perintah READ-ONLY (tidak mengubah flag, tidak mengambil lock — pengecekan lock dilakukan dengan percobaan `flock()` non-blocking yang langsung dilepas bila berhasil). Output SELALU lima baris terpisah, tidak pernah diringkas menjadi satu "OK":

```
Kill switch:                   BLOCKED (data/publishing_disabled: <alasan>)
Data directory:                HEALTHY
Lock:                          FREE
Publisher integration:         INCOMPLETE
Live publishing authorization: NOT AUTHORIZED (Sprint 3 — pengujian hanya mock/dry-run)
```

| Baris | Nilai | Arti | Sumber |
|---|---|---|---|
| Kill switch | ALLOWED / BLOCKED | Apakah publishing diizinkan oleh flag file (D1) + fail-closed (K1-4) | `is_publishing_allowed()` |
| Data directory | HEALTHY / ERROR | `data/` ada, bisa di-list, bisa dibaca | Pemeriksaan I/O langsung; ERROR memaksa kill switch BLOCKED (satu-satunya kopling yang diizinkan — karena status flag tidak dapat ditentukan) |
| Lock | FREE / HELD (+ PID bila terbaca) | Apakah `data/.publisher.lock` sedang dipegang proses lain | Percobaan `flock()` non-blocking (langsung dilepas bila berhasil) |
| Publisher integration | COMPLETE / INCOMPLETE | Apakah semua 9 publisher + DELETE sudah melewati gate | Daftar integrasi §B5 vs kode (selama Tahap 2–3: INCOMPLETE sampai semua commit C-S3-1 s.d. C-S3-10 teruji) |
| Live publishing authorization | NOT AUTHORIZED (selama Sprint 3) | Apakah live publishing diizinkan — FAKTA otorisasi sprint, BUKAN status kill switch | **P0-1: nilai hard gate `LIVE_PUBLISHING_AUTHORIZED = False` di `publish_guard.py`, DITEGAKKAN pada setiap choke point mutasi** (bukan sekadar informasi CLI — `require_live_authorization()` menolak semua mutasi selama Sprint 3). Berubah hanya dengan keputusan manusia terpisah pasca-Sprint 3 + perubahan kode yang tercatat; TIDAK otomatis saat implementasi selesai, saat tes lulus, atau saat kill switch ALLOWED |

Aturan: nilai satu baris tidak boleh disimpulkan dari baris lain (kecuali kopling data ERROR → kill switch BLOCKED di atas). Khususnya: kill switch ALLOWED **bukan** berarti live publishing diizinkan — selama Sprint 3, baris otorisasi tetap NOT AUTHORIZED. Uji: RV2-10 (§B7).

### B4. Desain pendukung — Tahap C (rancangan, bukan implementasi)

**C1. Single-instance lock (anti dua publisher bersamaan) — SATU mekanisme bersama (K0-2).**
- Mekanisme: `fcntl.flock()` pada file `data/.publisher.lock`, mode `LOCK_EX | LOCK_NB` (non-blocking), dipegang selama SELURUH live run. **SATU lock untuk SEMUA publisher di PC** — `run_slot.py`, `publish_video.py --live`, `auto_comment.py --live`, `run_pinterest.py`, vendor CLI (`cmd_post`/`cmd_post_auto`), `repost_product.py`, dan `pinterest_api.py` CLI — melalui SATU helper `acquire_publisher_lock()` di `tools/publish_guard.py`. Lock per-jalur DILARANG (masih membiarkan dua jalur berbeda berjalan bersamaan).
- Bila lock sudah dipegang → proses kedua langsung keluar dengan exit code baru `4` + log `BATAL: publisher lain sedang berjalan (lock dipegang) — coba lagi slot berikutnya`. Tidak menunggu, tidak antre.
- **Mengapa `flock`, bukan PID file:** lock dilepas otomatis oleh kernel saat proses mati (termasuk SIGKILL) → tidak ada stale lock. PID file bisa tertinggal setelah crash dan memblokir semua slot sampai manusia menghapusnya.
- **K1-1 — re-entrancy (anti nested flock).** `acquire_publisher_lock()` di `publish_guard.py` menyimpan state di memori proses (`_lock_fd`, `_lock_pid`, `_lock_depth`). Bila dipanggil lagi dari proses yang sama → kembalikan sukses instan, `_lock_depth += 1`, TANPA `flock()` kedua. (Alasan teknis: `flock()` kedua pada fd baru oleh proses yang sama akan memblokir — karena itu pemanggilan kedua harus dicegah di level helper, bukan diandalkan ke kernel.) `release_publisher_lock()` menurunkan depth; fd ditutup + lock dilepas hanya saat depth = 0. **Kill switch TIDAK ikut aturan ini**: cek saklar dilakukan di setiap lapis tanpa kecuali, termasuk oleh publisher terdalam yang sudah memegang lock. Jalur yang dipanggil langsung (proses baru) tidak punya state lock → wajib `flock()` normal. Uji: RV-1, RV-2 (§B7).
- **K2-1 — fork safety: proses anak tidak mewarisi lock parent.** `flock()` dilekatkan pada deskripsi file terbuka, dan `fork()` menduplikasi fd — tanpa pemeriksaan, proses anak akan "mewarisi" lock parent dan bisa publish sementara parent memegang lock. Karena itu `acquire_publisher_lock()` SELALU memvalidasi PID dulu: bila `_lock_pid is not None` dan `_lock_pid != os.getpid()` → state warisan DIANGGAP TIDAK ADA (fd warisan ditutup, `_lock_depth` direset ke 0), lalu acquire baru dilakukan dengan `flock()` pada fd yang baru dibuka. Bila parent masih memegang lock, `flock()` anak gagal → exit 4. `release_publisher_lock()` juga no-op bila PID tidak cocok (anak tidak boleh melepas lock parent). Aturan ini berlaku untuk `fork()` langsung maupun `multiprocessing` (start method fork mewarisi memori proses); `subprocess` (exec) memulai memori baru sehingga tidak punya state warisan dan acquire secara normal. Perbedaan dengan K1-1 ditegaskan: nested dalam satu proses = PID sama = idempotent, boleh lanjut; fork = PID berbeda = proses berbeda = wajib lock sendiri. Uji: RV2-1, RV2-2 (§B7).
- Cakupan: per mesin (PC). VM dan PC tidak berbagi filesystem — penegakan lintas mesin tetap mengandalkan aturan "PC satu-satunya publisher LIVE" (lihat Sprint 6). Lock TIDAK dipegang saat `--dry-run` (dry-run tidak publish, boleh paralel).
- Urutan dengan kill switch: cek kill switch DULU (gagal cepat, tanpa lock), lalu ambil lock, lalu kerja. Lock dilepas otomatis saat proses keluar (gunakan context manager + `finally`).
- **P1-1 — `reconcile.py --apply` memakai lock yang SAMA.** Recovery bukan pengecualian dari lock: `--apply` WAJIB memanggil `acquire_publisher_lock()` yang sama (proses terpisah → acquire normal; tidak ada re-entrancy karena reconcile tidak memanggil publisher). Bila lock gagal diperoleh → batalkan SELURUH perubahan (tidak ada satu pun tulis), keluar non-zero, log mencatat "lock tidak diperoleh — reconcile dibatalkan". Ini menjamin recovery tidak pernah menimpa atau berkompetisi dengan history yang sedang diperbarui publisher — semua RMW history, dari jalur mana pun, terjadi di bawah flock yang sama (K2-2). `--check` (default, read-only) TIDAK mengambil lock — lihat penanganan torn-read di §B4-C3.

**C2. Penanganan crash di tengah publikasi — intent record ATOMIK (K0-1) + ambiguitas ≠ gagal (K0-4).**
- **Intent record (baru, menutup celah A3-a) — ATOMIK + fsync — K1-2: berlaku untuk SEMUA jalur.** TEPAT SEBELUM panggilan publish pertama, publisher menulis entri `status="publish_started"` (content_id, sub_id, product_id, timestamp, pid, jalur/publisher, slot) dengan cara: tulis ke file sementara di direktori yang sama → `fsync` file → `os.replace` → `fsync` direktori. **Urutan ini WAJIB**: intent record harus dipastikan tersimpan di disk SEBELUM request publikasi dikirim. Jalur yang wajib: `run_slot` (API + Playwright), `publish_video`, `auto_comment`, Pinterest (`run_pinterest` + `pinterest_api` CLI), vendor CLI, `repost_product`. Satu helper bersama `write_intent()` di `publish_guard.py` dipakai semua jalur — tidak ada jalur yang menulis intent dengan caranya sendiri. Bila publish sukses → entri di-update menjadi `posted`/`posted_receipt_incomplete` (update ini pun atomik; riwayat lama tidak dihapus — lihat K0-7). Idempotency Sprint 2 diperluas ke semua jalur: cek `(content_id, sub_id)` SEBELUM menulis intent (bila sudah ada `publish_started`/`posted` → tolak), sehingga intent record + idempotency bekerja sebagai satu kesatuan.
- **K2-2 — atomic history + concurrent writes.** Semua operasi read-modify-write pada history (`post_history.json`, `delete_history.json`, intent index) WAJIB dilakukan sambil memegang flock bersama (§B4-C1) — baca, ubah, tulis sebagai satu bagian kritis; tanpa lock, dua proses bisa membaca state yang sama lalu saling menimpa (lost update). Setiap intent punya **ID operasi unik** `op_id` (format `op-<jenis>-<yyyymmddHHMMSS>-<pid>-<rand4>`, mis. `op-pub-20261117023000-1234-a1b2`). `write_intent()` MENOLAK duplikasi idempotency key secara atomik di bawah lock: bila sudah ada intent dengan kunci yang sama dalam status non-terminal (`publish_started`, `publish_interrupted`, `delete_started`, `delete_ambiguous`) → raise `DuplicateIntent`, TIDAK ada intent kedua, TIDAK ada request. Intent baru untuk kunci yang sama hanya boleh ditulis setelah intent lama mencapai status terminal (`posted`, `posted_receipt_incomplete`, `abandoned`, `deleted`, `delete_failed`) — dan itu pun dengan `op_id` baru; intent lama tetap tersimpan. **Update receipt HARUS berdasarkan ID intent** (`intent_id`/`op_id`), bukan berdasarkan pencocokan `content_id` — supaya update tidak pernah mengenai entri yang salah bila ada dua intent untuk produk yang sama (mis. retry setelah interrupted). **Kegagalan menulis intent WAJIB membatalkan request**: bila `write_intent()` gagal (I/O error, direktori tidak bisa ditulis) → publisher batal SEBELUM request apa pun dikirim (fail closed), log mencatat "intent gagal ditulis — dibatalkan", exit non-zero. DELETE punya ID operasi tersendiri (`delete_operation_id`, format `delop-<yyyymmddHHMMSS>-<pid>-<rand4>`) dan intent-nya ditulis via `write_delete_intent()` ke `data/delete_history.json`. Uji: RV2-3, RV2-4, RV2-5 (§B7).
- **K2-3 — skema idempotency key per jenis operasi.** Kunci selalu ber-prefix namespace jenis operasi, sehingga kunci antarjenis TIDAK PERNAH bertabrakan walau komponen tengahnya sama:

| Jenis operasi | Skema kunci | Contoh |
|---|---|---|
| Post affiliate / video (Threads) | `pub:<channel>:<content_id>:<sub_id>` | `pub:threads:ecoco-brush-threads-20261117:threadsdapurecocobrush20261117` |
| Auto-comment (Threads) | `cmt:<channel>:<comment_id>:<target_media_id>` | `cmt:threads:cmt-9f3ac21bd0e4:4025292505889269875` |
| Pinterest (pin) | `pin:pinterest:<content_id>:<sub_id>` | `pin:pinterest:ecoco-brush-pinterest-20261117:threadsdapurecocobrush20261117` |
| DELETE (Threads) | `del:<delete_operation_id>:<media_id>` | `del:delop-20261117023000-1234-a1b2:18135902441497212` |

  `comment_id` bersifat deterministik agar idempotency bermakna: `cmt-` + 12 karakter hex pertama dari `sha256(target_media_id + "|" + teks_komen_normalisasi + "|" + tanggal_yyyy-mm-dd)`, dengan teks yang dinormalisasi = teks persis yang akan dikirim (setelah template terisi). Komen yang sama ke target yang sama di hari yang sama → kunci sama → ditolak; teks/target/tanggal berbeda → kunci berbeda. Prefix `pub:` / `cmt:` / `pin:` / `del:` membuat namespace saling lepas: pencarian kunci satu jenis tidak pernah mengenai jenis lain, dan pemeriksaan duplikat selalu dibatasi pada namespace jenis itu. Kunci Sprint 2 `(content_id, sub_id)` dipertahankan sebagai komponen tengah kunci `pub:` — pemetaan lama → baru bersifat mekanis. Uji: RV2-6 (§B7).
- **DELETE dicatat TERPISAH dari publikasi (K1-2).** Tindakan DELETE (`delete_media()` di `repost_product.py`) punya intent record + history SENDIRI — **bukan** dicampur ke `post_history.json` / publication receipt. File baru `data/delete_history.json` (gitignored, format daftar entri JSON seperti `post_history.json`) + intent record `status="delete_started"` (media_id target, permalink target, alasan, timestamp, pid, operator/jalur) yang ditulis atomik + fsync SEBELUM request DELETE dikirim. Setelah DELETE: entri di-update menjadi `deleted` (dengan respons API) atau `delete_failed` / `delete_ambiguous` (bila respons hilang / HTTP 400 — K0-4: kegagalan verifikasi ≠ bukti tidak terhapus). Alasan pemisahan: receipt publikasi adalah bukti "post ini terbit"; mencampur DELETE ke dalamnya mengaburkan audit (apakah entri ini soal terbit atau soal hapus?) dan berisiko menimpa receipt post yang sah. `reconcile.py` memeriksa kedua file secara terpisah. Uji: RV-3, RV-4, matriks DELETE §B7.
- **Signal handler — K1-3: HANYA menandai, tidak menulis.** Handler `SIGTERM`/`SIGINT` HANYA menyetel flag in-memory (`_SHUTTING_DOWN = True`) lalu kembali — TIDAK menulis file, TIDAK memanggil API, TIDAK melakukan I/O apa pun di dalam handler (menulis dari dalam signal handler tidak aman: bisa terjadi di tengah tulis lain → file rusak). Penulisan status `publish_interrupted` dilakukan oleh **cleanup yang aman**: loop utama / blok `finally` memeriksa flag secara berkala (sebelum dan sesudah tiap langkah publish) dan, bila flag menyala, menulis entri `publish_interrupted` lewat jalur tulis atomik biasa lalu keluar dengan rapi. Bila proses mati sebelum cleanup sempat jalan (SIGKILL, atau SIGTERM yang datang persis di tengah request), **intent record atomik + fsync tetap menjadi perlindungan utama**: entri `publish_started` SUDAH ada di disk sebelum request dikirim, sehingga `reconcile.py --check` bisa menemukannya. Cleanup best-effort TIDAK BOLEH diandalkan sebagai satu-satunya jejak. Uji: RV-5, RV-6 (§B7).
- **Timeout API ambigu** (respons hilang setelah container terbit): tidak ada retry otomatis. Status tetap `publish_started`/`publish_interrupted` → prosedur recovery C3. **K0-4 — kegagalan API / HTTP 400 TIDAK BOLEH dianggap bukti post tidak terbit.** Bila verifikasi (`get_media`, `/me/threads`, fetch web) gagal dengan HTTP 400 / timeout / error lain, status tetap AMBIGU: blokir publish ulang + verifikasi manual. Preseden yang melarang asumsi ini: repost Kikkoman v4 (media_id 18135902441497212) — TIDAK resolve via API (HTTP 400) pada 17 Nov 00:45 WIB, padahal post itu PERNAH terbit dan terverifikasi 16 Nov 18:18 WIB. Menganggap "400 = tidak terbit" akan menghapus/menimpa riwayat yang sah.

**C3. Recovery `publish_interrupted` / `publish_started` (prosedur manual) — default READ-ONLY (K0-5) + append-only (K0-7).**
- Tool baru yang diusulkan: `tools/reconcile.py --content-id <id>` — **default READ-ONLY** (`--check`: hanya laporan, TIDAK mengubah file apa pun):
  1. `get_media(media_id)` + fetch permalink → post ADA atau TIDAK.
  2. ADA → lengkapi receipt entri, tandai link USED, status `posted` (+ catatan `reconciled manual <tanggal> <operator>` — ditambahkan sebagai catatan baru, entri lama tidak ditimpa).
  3. TIDAK ADA → ubah entri menjadi `abandoned` (alasan + operator + tanggal, entri TIDAK dihapus) → link menjadi bisa dipilih lagi slot berikutnya. **Perubahan ke `abandoned` HANYA boleh dilakukan dengan bukti kuat** bahwa post tidak pernah terbit: `get_media` 404 yang konsisten (bukan sekali) + tidak ada di `/me/threads` + fetch web gagal — ketiganya, bukan salah satu. Perintah perubahan status adalah `--apply` eksplisit (bukan default) dan hanya oleh manusia.
  4. AMBIGU (API error / HTTP 400 / timeout saat cek — lihat K0-4) → **biarkan terblokir, eskalasi ke Kyan**. Tidak ada perubahan status apa pun.
- DELETE direkonsiliasi terpisah (K1-2): `reconcile.py --delete --media-id <id>` memeriksa `data/delete_history.json` (bukan `post_history.json`): `delete_started` tanpa hasil → cek `get_media` + fetch permalink; post masih ADA → status `delete_failed` (bukan `deleted`); post TIDAK ADA + bukti rangkap tiga → `deleted`; AMBIGU → `delete_ambiguous` + blokir + eskalasi. Tidak ada perubahan status tanpa `--apply` eksplisit manusia.
- **K2-4 — pemisahan publish dan DELETE pada repost.** Publish baru dan DELETE lama adalah DUA OPERASI INDEPENDEN: masing-masing punya intent sendiri (`op_id` sendiri), kunci idempotency sendiri (`pub:` vs `del:`), dan entri history sendiri (`post_history.json` vs `data/delete_history.json`). DELETE gagal/ambigu TIDAK BOLEH memicu retry otomatis — baik retry DELETE maupun retry publish — dan TIDAK BOLEH memicu rollback dengan menghapus post baru. Bila DELETE gagal, sistem berakhir di status akhir yang tercatat: post baru live (`posted`), post lama tetap live, entri DELETE `delete_failed`/`delete_ambiguous`, tanpa aksi lanjutan otomatis; pengulangan DELETE hanya boleh dilakukan manual setelah `reconcile.py --delete --check`. History lama TIDAK BOLEH dihapus: entri post lama tetap ada apa adanya. Relasi antar-post harus eksplisit dan append-only: entri baru mendapat catatan `replaces: <media_id_lama>`; entri lama mendapat catatan tambahan `superseded_by: <media_id_baru>` — keduanya sebagai catatan tambahan, bukan dengan menimpa field asli entri (K0-7). Uji: RV2-7, RV2-8 (§B7).
- **P1-1 — prosedur `--apply` di bawah lock bersama (mengikat).** Urutan `--apply` yang sah: (1) peroleh shared publisher lock via `acquire_publisher_lock()` — gagal → batalkan SELURUH perubahan, 0 tulis, exit non-zero, log "lock tidak diperoleh — reconcile dibatalkan"; (2) baca ULANG history + verifikasi ULANG bukti DI BAWAH lock — bukti yang dikumpulkan `--check` sebelumnya bisa basi (post bisa terbit/hilang di antaranya; entri bisa berubah oleh publisher lain), jadi keputusan `--apply` TIDAK BOLEH memakai snapshot lama; (3) tulis perubahan secara atomik (file sementara + `os.replace` + fsync) sambil tetap memegang lock, lalu lepas lock. **Default `--check` tetap read-only dan tanpa lock** — tetapi karena publisher bisa menulis history pada saat yang sama, `--check` WAJIB menangani torn-read dengan aman: baca file; bila JSON gagal di-parse (tulis setengah jalan) → laporkan "history tidak dapat dibaca konsisten — publisher mungkin sedang menulis, ulangi" dan keluar non-zero TANPA mengubah apa pun (bukan crash, bukan laporan setengah benar). `--check` tidak pernah mengambil lock agar pemeriksaan status tidak terblokir oleh publisher yang sedang berjalan.
- Aturan: riwayat tidak pernah dihapus; recovery selalu MENAMBAH catatan, bukan menimpa (K0-7). Semua aksi recovery dicatat di `logs/kill-switch.log` atau `logs/ops.jsonl` (lihat C4).

**C4. Pemisahan log (memperbaiki A3-b) — DISETUJUI D8: satu penulis, `log()` print-only.**
- Hari ini: `log()` print + append, systemd append ke file yang sama → semua baris ganda.
- **Keputusan D8: `log()` hanya `print()` (stdout), dan systemd tetap `StandardOutput=append:logs/cron.log`** — maka tiap baris tercatat tepat 1×. Perubahan: hapus cabang append-file dari `log()` di `run_slot.py` (dan samakan di tool lain yang punya `log()` sendiri, mis. `run_pinterest.py`). Unit systemd TIDAK diubah.
- Log baru terstruktur `logs/ops.jsonl` (satu JSON per run: `slot`, `start`, `finish`, `exit_code`, `kill_switch`, `lock_acquired`, `content_id`, `status`) — untuk audit mesin, bukan dibaca manusia tiap hari. Receipt tetap di `post_history.json`; metrik tetap di `data/performance.csv`.

**C5. Backup & recovery (prosedur, bukan kode baru).**
- Yang sudah ada dan dipertahankan: `.bak` bertanggal untuk DB + history sebelum tiap sprint; `.gitignore` menutupi data/token; token mode 600.
- Tambahan yang diusulkan: snapshot `data/` (DB + history + mapping + performance.csv) sebelum MENGAKTIFKAN kembali publishing setelah kill switch lama (supaya ada titik kembali bila slot pertama pasca-aktif bermasalah). Restore = `cp` file `.bak` kembali + verifikasi md5 + `--dry-run`.
- Pemulihan token (bila file hilang/rusak): token TIDAK di-backup di repo — diterbitkan ulang lewat aplikasi Meta (Kyan menyalin sendiri via Secure Vault), lalu disimpan ke `~/.threads_poster/threads_token.env` mode 600. Prosedur ini didokumentasikan di `docs/pemulihan-token.md` (baru, tanpa nilai apa pun).

**C6. Cara menghentikan publisher dengan aman (prosedur operasi). — K0-8: tidak ada live posting selama Sprint 3 (Tahap 1–3).**
1. `touch data/publishing_disabled` — run baru gagal cepat; run yang sedang berjalan berhenti di batas publish berikutnya (cek ulang §B3).
2. `systemctl --user stop threads-affiliate-*.timer` — tidak ada slot baru.
3. Bila sebuah service sedang berjalan: `systemctl --user stop <service>` — SIGTERM; handler menulis `publish_interrupted`; verifikasi via `get_media` apakah post sempat terbit; recovery C3.
4. Verifikasi: `tools/publish_guard.py status` → BLOCKED; `systemctl --user list-timers` → tidak ada timer affiliate aktif.
5. Perhatian `Persistent=true`: run yang terutang akan menembak SEKALI saat timer di-enable lagi — jangan enable timer sebelum flag dihapus DENGAN SENGAJA (urutan: hapus flag → verifikasi status → enable timer).

### B5. File yang AKAN diubah + URUTAN implementasi (Tahap 2)

Urutan mengikuti dependensi: guard dulu (fondasi), lalu lock, lalu intent record, lalu penutupan bypass per jalur, lalu logging, lalu reconcile. Satu langkah diuji sebelum lanjut ke langkah berikutnya; commit per langkah (bukan satu commit raksasa). K2-1 s.d. K2-6 tidak menambah file baru di luar daftar ini: semuanya diimplementasikan di dalam `publish_guard.py` + tool yang sudah ada di daftar (skema kunci, op ID, pemisahan publish/DELETE, flag CLI Pinterest, status 5 baris). **P0-1 mengubah rencana commit: hard gate otorisasi live WAJIB menjadi bagian dari guard (urutan 1, commit C-S3-1) SEBELUM jalur lain dibuka — tidak ada satu pun commit yang membuka jalur publish tanpa hard gate sudah aktif dan teruji menolak. P0-1, P1-1, dan P1-2 juga tidak menambah file baru di luar daftar ini.**

| Urutan | File | Perubahan | Alasan | Risiko utama |
|---|---|---|---|---|
| 1 | `tools/publish_guard.py` (BARU) | `is_publishing_allowed(channel)`, `require_publishing(channel)`, **`LIVE_PUBLISHING_AUTHORIZED = False` (hard-coded, P0-1) + `require_live_authorization(channel)` — diperiksa sebagai baris pertama di setiap choke point mutasi, sebelum kill switch**; `acquire_publisher_lock()` (re-entrant, K1-1; fork-safe, K2-1: validasi PID pemilik), `write_intent()` + `write_delete_intent()` (atomik + fsync, K1-2; menolak duplikasi key, K2-2), skema kunci idempotency per jenis operasi (K2-3), CLI `status` 5 baris terpisah (K2-6); fail-closed bila flag tidak terbaca / direktori hilang / modul rusak (K1-4: TIDAK membaca `config.yaml`) | Satu-satunya tempat yang tahu soal saklar + lock + intent; semua jalur bergantung padanya | Bila modul ini rusak, SEMUA publishing mati (fail-closed — disengaja, tapi harus diuji T3) |
| 2 | `tools/publish_api.py` | `require_publishing("threads")` di awal `_post()` (K0-3: titik terakhir API) | Menutup seluruh bypass API sekaligus (CLI, video, auto-komen, repost, import langsung). `_get()` tidak dicek | `_post` dipakai juga oleh alur baca? Tidak — hanya mutasi. Verifikasi: `_get` tetap jalan saat OFF |
| 3 | `tools/run_slot.py` | Cek saklar di awal `main()` + cek ulang sebelum publish; ambil flock via helper (K0-2, re-entrant K1-1, fork-safe K2-1); tulis intent record atomik + fsync via `write_intent()` (K1-2) dengan `op_id` unik dan kunci `pub:threads:<content_id>:<sub_id>` (K2-2, K2-3); update receipt berdasarkan `intent_id` (K2-2); signal handler hanya menyetel flag `_SHUTTING_DOWN` + cleanup aman di `finally` (K1-3); `log()` jadi print-only (D8) | Gagal cepat + anti race + jejak crash + log tunggal | Signal handler best-effort (SIGKILL tidak tertangkap — ditutup intent record); intent record menambah 1 tulis disk per slot |
| 4 | `vendor/threads-affiliate/threads_poster/poster.py` | `require_publishing("threads")` di awal `post()` + `acquire_publisher_lock()` (re-entrant, K1-1) + intent record via `write_intent()` (K1-2) | Playwright tidak melewati `_post()`; ini titik terakhirnya | Edit vendor — catat patch di `VENDOR-NOTES.md` (R7); update vendor bisa menimpa patch |
| 5 | `vendor/threads-affiliate/threads_poster/cli.py` | Gate yang sama di `cmd_post` + `check_chain` (D6); tutup flag `--force` (hapus, atau buat tetap tunduk pada gate + idempotency); `acquire_publisher_lock()` | Menutup bypass CLI (tanpa guardrail + `--force` bypass dedup hari ini) | CLI dipakai manual — pesan penolakan harus jelas agar tidak dikira error |
| 6 | `tools/publish_video.py` (D4) | Gate + hapus fabrikasi permalink (samakan Sprint 2: `permalink=None`, `permalink_verified=False` bila GET gagal); tulis receipt ke `post_history.json` (kolom Sprint 2); cek idempotency kunci `pub:threads:<content_id>:<sub_id>` (K2-3); `acquire_publisher_lock()`; intent record dengan `op_id` unik (K2-2) | Menutup celah A6; receipt video saat ini tidak terlacak | `build_caption` hanya cek 500 (bukan 470 operasional) — samakan dengan `check_chain` (WARN 471–500 sudah ada) |
| 7 | `tools/auto_comment.py` (D2) | Gate di `main()` live path (ikut kill switch Threads); owner-check fail-open → **fail-closed** (gagal cek = JANGAN kirim); `acquire_publisher_lock()` (re-entrant, K1-1); intent record via `write_intent()` (K1-2) dengan kunci `cmt:threads:<comment_id>:<target_media_id>` (K2-3; `comment_id` deterministik dari target + teks + tanggal) | Fail-open hari ini bisa mengirim komen ke postingan sendiri; komen adalah publikasi Threads | `resolve_media_id` mendekode shortcode yang terbukti bukan ID API — owner-check akan sering gagal → komen sering tertahan (benar secara keamanan; target harus dicari via cara lain — di luar Sprint 3) |
| 8 | `tools/repost_product.py` | Gate di `main()` + gate di `delete_media()` (**D9 — DISETUJUI YA 17 Nov 2026 01:34 WIB**: DELETE ikut kill switch Threads, termasuk pemanggilan langsung); intent record DELETE terpisah via `write_delete_intent()` ke `data/delete_history.json` (K1-2) dengan `delete_operation_id` + kunci `del:<delete_operation_id>:<media_id>` (K2-2, K2-3); **K2-4: publish baru dan DELETE lama adalah dua operasi independen** — masing-masing intent + kunci sendiri; DELETE gagal/ambigu TANPA retry otomatis dan TANPA rollback menghapus post baru; relasi `replaces` / `superseded_by` eksplisit dan append-only; `update_history()` diubah dari menimpa → **append entri baru + `supersedes`** (K0-7); `acquire_publisher_lock()` (re-entrant, K1-1); intent record publish via `write_intent()` (K1-2) | Menutup entry point ke-9 + memperbaiki pelanggaran append-only + menutup DELETE | File UNTRACKED — Tahap 2 harus men-commit-nya dulu (atau nyatakan arsip); `delete_media` memakai token di URL (bukan di log — verifikasi) |
| 9 | `tools/run_pinterest.py` (D5) | Gate + ubah default: **wajib `--live` eksplisit** (tanpa flag = dry-run/batal); **K2-5: tanpa `--live` = tidak ada mutasi + tampilkan DRY-RUN; `--dry-run` + `--live` bersamaan = konflik, ditolak (exit 2), 0 mutasi**; `acquire_publisher_lock()` (re-entrant, K1-1); intent record via `write_intent()` (K1-2) dengan kunci `pin:pinterest:<content_id>:<sub_id>` (K2-3) | Default live saat ini berbahaya; timer memanggil tanpa flag | Unit systemd/timer TIDAK diubah (batas kewenangan): D5 dipenuhi lewat perubahan default di kode — timer yang memanggil tanpa `--live` hasilnya batal/dry-run, bukan publikasi. Bila timer Pinterest mau diaktifkan lagi, ExecStart `--live` butuh persetujuan terpisah |
| 10 | `tools/pinterest_api.py` | `require_live_authorization("pinterest")` + `require_publishing("pinterest")` di awal `create_pin()`; **P1-2: SELURUH urutan gate ditegakkan DI DALAM `create_pin()` sendiri — hard gate (P0-1) → kill switch → `acquire_publisher_lock()` (re-entrant, K1-1) → cek idempotency kunci `pin:pinterest:<content_id>:<sub_id>` (K2-3) → `write_intent()` (K1-2) → baru HTTP — sehingga pemanggilan langsung dari Python tidak bisa melewati satu pun lapis**; CLI `main()` wajib `--live` eksplisit (D5); **K2-5: tanpa `--live` = tidak ada mutasi + tampilkan DRY-RUN; `--dry-run` + `--live` bersamaan = konflik, ditolak (exit 2), 0 mutasi — konsisten dengan `run_pinterest.py`** | Titik terakhir Pinterest + CLI default-live | Token Pinterest belum ada (`~/.pinterest_poster/` tidak ada) — gate tetap diuji via mock; percobaan live pasca-otorisasi yang gagal di token load akan meninggalkan intent `publish_started` (fail-closed by design, recovery via reconcile) |
| 11 | `tools/reconcile.py` (BARU) | Verifikasi + recovery `publish_interrupted`/`publish_started` DAN `delete_started`/`delete_ambiguous` (file terpisah, K1-2); **default `--check` read-only** (K0-5); `--apply` hanya oleh manusia + bukti kuat; ambiguitas → blokir (K0-4); **K2-2: pencocokan dan update status berdasarkan `intent_id` / `delete_operation_id`, bukan berdasarkan `content_id` saja**; **P1-1: `--apply` WAJIB memperoleh shared publisher lock yang sama — gagal lock = batalkan SELURUH perubahan; bukti diverifikasi ULANG di bawah lock; tulis atomik di bawah lock; `--check` tetap tanpa lock dengan penanganan torn-read (§B4-C3)** | Tanpa ini, entri interrupted memblokir link selamanya | `--apply` yang salah bisa menandai post yang pernah terbit sebagai `abandoned` — mitigasi: bukti rangkap tiga + operator manusia + catatan audit + lock bersama |
| 12 | `config.yaml` | Tambah section `publishing:` (pointer kill-switch dir + dokumentasi) — BUKAN sumber kebenaran kedua | Dokumentasi | Jangan sampai `config.yaml` dibaca sebagai sumber kebenaran oleh kode mana pun |
| 13 | `.gitignore` | Pastikan `data/publishing_disabled*`, `data/.publisher.lock`, `data/delete_history.json`, `logs/kill-switch.log`, `logs/ops.jsonl` tercakup | Saklar + lock + history DELETE + log operasi tidak boleh ter-commit | Pola `data/` mungkin belum menutupi file tanpa ekstensi — verifikasi saat implementasi |
| 14 | `docs/pemulihan-token.md` (BARU) | Prosedur pemulihan token tanpa nilai | Bagian dari C5 | — |
| 15 | `docs/rancangan-kill-switch-sprint3.md` | Dokumen ini → ditambah hasil implementasi + pengujian | Jejak audit | — |
| 16 | `data/delete_history.json` (BARU, K1-2) | Intent record + history DELETE terpisah (`delete_started` → `deleted` / `delete_failed` / `delete_ambiguous`); ditulis atomik + fsync; gitignored (urutan 13) | DELETE tidak boleh dicampur ke publication receipt (audit jadi kabur + berisiko menimpa receipt sah) | File baru — format disamakan dengan `post_history.json`; `reconcile.py` memeriksa file ini terpisah |

**Tidak diubah:** `data/post_history.json` (riwayat — hanya ditambah entri, tidak ditimpa), `data/affiliate_links.md` (DB), template hook, guardrail disclosure, timer/jadwal (unit systemd TIDAK diubah — lihat urutan 9), akun/token. Daftar lengkap file yang TIDAK disentuh + mekanisme jaminannya ada di §B8.

### B5b. Rencana commit (Tahap 2) — rencana saja, JANGAN commit sekarang

Commit dilakukan SETELAH implementasi + hasil tes dilaporkan untuk pemeriksaan dan disetujui terpisah oleh Kyan (batas kewenangan). Pengelompokan logis di bawah ini adalah rencana; tiap commit diuji sendiri sebelum lanjut ke commit berikutnya. Urutan commit = urutan implementasi §B5.

**P0-1 — catatan pengujian per commit (mengikat).** Selama Sprint 3, hard gate menolak semua mutasi — karena itu ekspektasi "mock publish sukses" pada kolom uji di bawah ini dibaca dengan semantik Sprint 3: yang diuji adalah penolakan hard gate (0 mutasi, 0 panggilan mock) + komponen terisolasi (guard, lock, intent writer, pemeriksa idempotency diuji unit-tanpa-melewati-choke-point-live). Jalur sukses penuh (gate → lock → intent → HTTP mock → receipt) adalah uji TERTUNDA (T2-live, D-1-live, D-6-live, K3-live — §B7) yang HANYA dijalankan setelah keputusan manusia terpisah mengaktifkan otorisasi live pasca-Sprint 3. Tidak ada commit yang dinyatakan lolos berdasarkan keberhasilan publish selama Sprint 3.

| Commit | Isi (file) | Cakupan uji sebelum commit berikutnya |
|---|---|---|
| C-S3-1 | `tools/publish_guard.py` (baru) + `.gitignore` | **Hard gate otorisasi live (P0-1) + guard + lock re-entrant + status CLI**; lock fork-safe (K2-1), skema kunci idempotency (K2-3), status 5 baris (K2-6); T3, T10, K7, RV-1, RV-2, RV-7, RV-8, RV2-1, RV2-2, RV2-6, RV2-10, **RV3-1 s.d. RV3-5 (hard gate)** |
| C-S3-2 | `tools/publish_api.py` (gate `_post()`) | Menutup bypass API; T1, T4, K6 |
| C-S3-3 | `tools/run_slot.py` (cek awal + cek ulang + lock + intent atomik + signal handler flag + cleanup + `log()` print-only) | Jalur timer; op ID + update receipt by intent ID (K2-2); T1, T2, T5, T6, T7, K1, K2, K3, RV-5, RV-6, RV2-3, RV2-5 |
| C-S3-4 | `vendor/.../poster.py` + `vendor/.../cli.py` + `VENDOR-NOTES.md` (patch vendor) | Playwright + CLI; T4, K6, RV-1, RV-2 |
| C-S3-5 | `tools/publish_video.py` (D4) | Video; kunci `pub:` (K2-3); T1, T5, D-4, matriks per publisher, RV2-3 |
| C-S3-6 | `tools/auto_comment.py` (D2) | Auto-komen; kunci `cmt:` (K2-3); T1, T5, matriks per publisher, RV2-6 |
| C-S3-7 | `tools/repost_product.py` (D9: gate publish + gate `delete_media` + delete intent/history terpisah + `update_history` append-only) + file ini masuk git (baru ter-commit) | Repost + DELETE; pemisahan publish/DELETE (K2-4), delete op ID (K2-2), `supersedes`/`replaces` eksplisit; matriks DELETE (D-1 s.d. D-8), RV-3, RV-4, RV2-7, RV2-8 |
| C-S3-8 | `tools/run_pinterest.py` + `tools/pinterest_api.py` (D5: wajib `--live`) | Pinterest; perilaku CLI K2-5 (dry-run default + penolakan konflik); **P1-2: `create_pin()` menegakkan hard gate + kill switch + lock + intent + idempotency di titik mutasi terdalam (direct import tidak bisa bypass)**; T1, T9, matriks per publisher, RV2-9, **RV3-9, RV3-10, RV3-11** |
| C-S3-9 | `tools/reconcile.py` (baru, default read-only) + `docs/pemulihan-token.md` (baru) | Recovery; pencocokan by intent ID / delete op ID (K2-2); **P1-1: `--apply` wajib shared lock — gagal lock = batalkan seluruh perubahan; bukti diverifikasi ulang di bawah lock**; K8, RV-4, RV-6, RV2-5, **RV3-6, RV3-7, RV3-8** |
| C-S3-10 | `config.yaml` (section `publishing:` pointer saja) + `docs/rancangan-kill-switch-sprint3.md` (hasil implementasi + pengujian) | Dokumentasi; RV-7 (config.yaml hilang tidak mengubah status flag) |

Aturan commit: tiap commit = satu langkah §B5, pesan commit menyebut nomor urutan + keputusan yang diterapkan (mis. `sprint3: gate _post + lock re-entrant (D1, K1-1)`); `git status` + `git diff --stat` diverifikasi sebelum commit (hanya file commit itu yang berubah — lihat §B8); push HANYA setelah semua commit + semua tes dilaporkan dan disetujui terpisah.

### B6. Risiko + mitigasi

| # | Risiko | Dampak | Mitigasi |
|---|---|---|---|
| R1 | Fail-closed memblokir slot jadwal bila `data/` tidak terbaca / flag tidak sengaja dibuat | Slot terlewat, tidak ada post hari itu | Cek saklar gagal cepat + log jelas (`⛔ KILL SWITCH`); `status` command untuk verifikasi sebelum slot; flag hanya dibuat manual (tidak ada kode yang membuatnya) |
| R2 | Lock tertinggal setelah crash | Semua slot diblokir | `flock` dilepas kernel saat proses mati — tidak ada stale lock (alasan memilih flock, bukan PID file). Bila tetap ragu: lock file bisa dicek `status` |
| R3 | Playwright / vendor CLI tidak melewati `run_slot.py` | Saklar di `run_slot` saja tidak cukup | Gate di `_post()` + `poster.post()` + `create_pin()` (§B3) — tiga titik terakhir, bukan satu |
| R4 | Manusia lupa mengaktifkan kembali setelah kill switch | Sistem diam berhari-hari tanpa post | Log `kill-switch.log` mencatat tanggal OFF; `status` command; laporan mingguan menampilkan "hari tanpa post karena kill switch" (bila laporan sudah ada — Sprint laporan mingguan belum jalan, catat sebagai pengingat) |
| R5 | `Persistent=true` menembak run terutang saat timer di-enable lagi | Post terbit padahal Kyan masih ingin jeda | Prosedur C6: hapus flag HANYA bila memang mau publish; urutan enable timer setelah flag dihapus dan status terverifikasi |
| R6 | Intent record `publish_started` salah dipahami sebagai "sudah terbit" | Link terblokir selamanya | Status `publish_started` dibedakan dari `posted`; recovery C3 adalah satu-satunya jalan keluar (manual + tercatat) |
| R7 | Edit vendor (`poster.py`, `cli.py`) tertimpa saat update vendor | Gate hilang diam-diam | Catat patch di `VENDOR-NOTES.md` + uji regresi Tahap D memeriksa gate vendor; pertimbangkan wrapper di luar vendor bila memungkinkan |
| R8 | Flag file terhapus tidak sengaja (mis. cleanup `data/`) | Publishing hidup lagi tanpa keputusan | Flag file + lock + log masuk daftar "jangan dihapus" di dokumen operasi; `status` command sebelum slot pertama pasca-maintenance |
| R9 | Perbedaan PC ↔ VM (config/guardrails basi, tool hilang — A5) | VM sebagai fallback akan posting dengan aturan yang dibatalkan Kyan | Sprint 6: sinkronkan VM ← PC SEBELUM VM boleh dipakai publish; sampai saat itu VM dinyatakan BUKAN publisher (tidak ada token di VM — verifikasi: `~/.threads_poster/` tidak ada) |
| R10 | Auto-komen ikut saklar Threads — atau tidak? | Bila tidak ikut, komen tetap jalan saat posting mati (bukan yang diinginkan saat darurat) | **DISETUJUI D2: ikut.** |
| R11 | `repost_product.py` UNTRACKED + `update_history()` menimpa riwayat (§A7-b1/b2) | Riwayat bisa rusak diam-diam; file tidak terlacak git | Tahap 2 urutan 8: ubah ke append + `supersedes`; commit file-nya (atau nyatakan arsip bila Kyan memutuskan tidak dipakai) |
| R12 | HTTP 400 / kegagalan verifikasi dibaca sebagai "post tidak terbit" | Riwayat yang sah ditandai `abandoned` / link diterbitkan ulang → double-post | K0-4 + K0-5: ambiguitas = blokir + eskalasi; bukti rangkap tiga untuk `abandoned` |
| R13 | Vendor CLI flag `--force` (bypass dedup) | Dedup + idempotency bisa dilewati dari CLI | D6: tutup flag (hapus / buat tunduk pada gate + idempotency); uji K-skenario import langsung |
| R14 | `pinterest_api.py` CLI default-live + `run_pinterest.py` default-live | Publish Pinterest tidak sengaja (timer memanggil tanpa flag) | D5: wajib `--live` eksplisit di keduanya; timer diubah memanggil `--live` eksplisit |
| R15 | `delete_media()` tidak melewati `_post()` (panggilan urllib sendiri, token di URL) | Delete bisa jalan saat publishing OFF; token muncul di URL (bukan di log — verifikasi saat implementasi) | **D9 DISETUJUI YA:** gate `delete_media()` ikut kill switch Threads + lock re-entrant + intent record DELETE terpisah (§B5 urutan 8); matriks DELETE §B7 |
| R16 | Nested flock salah implementasi (K1-1) | Helper yang tidak re-entrant bisa deadlock proses sendiri (flock kedua memblokir); sebaliknya, state proses yang disalahartikan bisa membiarkan dua proses berbeda lolos | State lock di memori proses (`_lock_fd`/`_lock_pid`/`_lock_depth`) + uji RV-1 (nested acquire sukses instan) + RV-2 (proses kedua tetap exit 4); flock kernel tetap penegak antar-proses |
| R17 | Intent record DELETE tidak tertulis (K1-2) | DELETE tanpa jejak di `delete_history.json` → tidak bisa direkonsiliasi | `write_delete_intent()` WAJIB sebelum request DELETE; gagal tulis (I/O error) = batalkan DELETE (fail closed); uji RV-3, RV-4 |
| R18 | Proses anak hasil fork mewarisi lock parent (K2-1) | Anak bisa publish sementara parent memegang lock → double-post tanpa jejak lock | Validasi PID pemilik di setiap `acquire_publisher_lock()`; state warisan dibuang bila PID berbeda, acquire baru via `flock()`; uji RV2-1, RV2-2 (subprocess/multiprocessing) |
| R19 | Read-modify-write history tanpa lock bersama | Dua proses membaca state yang sama lalu saling menimpa (lost update); intent duplikat lolos | K2-2: semua RMW history di bawah flock bersama; `write_intent()` menolak duplikasi key secara atomik; uji RV2-3, RV2-4 |
| R20 | Idempotency key bertabrakan antarjenis operasi | Intent komen memblokir publish (atau sebaliknya); update receipt mengenai entri yang salah | K2-3: prefix namespace `pub:`/`cmt:`/`pin:`/`del:`; update receipt by `intent_id`; uji RV2-5, RV2-6 |
| R21 | DELETE gagal di repost memicu retry/rollback otomatis | Retry DELETE yang ambigu bisa menghapus post yang salah; rollback menghapus post baru yang sah | K2-4: publish dan DELETE independen; tanpa retry/rollback otomatis; status akhir tercatat + eskalasi manual; uji RV2-7, RV2-8 |
| R22 | Ambiguitas flag CLI Pinterest (live default + `--dry-run`/`--live` campur) | Publish Pinterest tidak sengaja dari timer/manual; operator mengira dry-run padahal live | K2-5: default dry-run + banner; kombinasi konflik ditolak (exit 2); konsisten di kedua file; uji RV2-9 |
| R23 | Status kill switch tercampur dengan kesehatan sistem | Satu "OK" menyembunyikan kill switch OFF atau sistem tidak sehat; operator salah mengira live publishing diizinkan | K2-6: 5 baris terpisah; otorisasi live NOT AUTHORIZED selama Sprint 3 walau kill switch ALLOWED; uji RV2-10 |
| R24 | Hard gate (P0-1) disalahartikan sebagai "tes gagal" atau "kill switch rusak" | Operator menghapus flag / mengubah kode untuk "memperbaiki" penolakan yang sebenarnya disengaja; atau ekspektasi uji lama (T2 "mock publish sukses") dibaca sebagai kegagalan | Hard gate didokumentasikan sebagai perilaku yang diharapkan (§B3, §B7); log penolakan menyebut eksplisit "LIVE NOT AUTHORIZED (Sprint 3)"; ekspektasi uji di-re-scope (§B7, subsection dampak P0-1); uji RV3-1 s.d. RV3-5 |
| R25 | `reconcile.py --apply` tanpa lock menimpa history yang sedang ditulis publisher (P1-1) | Lost update / entri history rusak / keputusan recovery berdasarkan snapshot basi | P1-1: `--apply` wajib shared lock; gagal lock = batalkan seluruh perubahan; bukti diverifikasi ulang di bawah lock; tulis atomik di bawah lock; uji RV3-6, RV3-7, RV3-8 |
| R26 | Direct import `create_pin()` melewati gate (P1-2) | Pin Pinterest terbit tanpa otorisasi live / kill switch / lock / intent / idempotency — bypass penuh lewat satu baris Python | P1-2: seluruh urutan gate ditegakkan DI DALAM `create_pin()` (titik mutasi terdalam); CLI `--live` hanya lapis eksplisit-intent; uji RV3-9, RV3-10, RV3-11 |
| R27 | Otorisasi live diaktifkan tanpa keputusan manusia yang tercatat (pasca-Sprint 3) | Seseorang mengubah `LIVE_PUBLISHING_AUTHORIZED` menjadi `True` "sementara" saat debugging / testing dan lupa mengembalikan; publishing hidup tanpa persetujuan | Konstanta hanya ditulis di satu tempat (`publish_guard.py`) + grep audit di Tahap 3; `publish_guard.py status` menampilkan baris otorisasi di setiap pemeriksaan; pengaktifan mensyaratkan perubahan kode + persetujuan Kyan yang tercatat (bukan flag, bukan env var, bukan hasil tes) — tidak ada mekanisme otomatis apa pun yang bisa mengubahnya |

### B7. Rencana pengujian — Tahap 3 (skenario + cara uji, tanpa live post)

Semua uji memakai mock transport API / fixture / dry-run. Tidak ada live post (K0-8).

#### Dampak P0-1 terhadap rencana pengujian (Sprint 3) — baca dulu sebelum tabel di bawah

Hard gate (P0-1) mengubah SEMANTIK pengujian selama Sprint 3. Tiga lapis pengujian berlaku:

- **Lapis A — uji penolakan gate (integrasi, WAJIB selama Sprint 3).** Setiap choke point mutasi dipanggil langsung (mock transport): hard gate harus menolak SEBELUM request apa pun — 0 panggilan mock, 0 intent tertulis, 0 perubahan DB/history. Inilah yang diuji T1, T4, T5, T6, K1, K2, K4, K5, K6, K7, matriks per publisher (kolom ON), matriks DELETE, RV-1–RV-8, RV2-1–RV2-10, dan RV3-1–RV3-11. Bila sebuah skenario di tabel bawah masih tertulis "mock publish sukses", baca sebagai "penolakan hard gate + 0 mutasi" — ekspektasi itu di-re-scope di sini dan pada baris yang bersangkutan.
- **Lapis B — uji komponen terisolasi (unit, WAJIB selama Sprint 3).** Fungsi guard, lock, `write_intent()`, dan pemeriksa idempotency diuji langsung sebagai unit (tanpa melewati choke point live): `acquire_publisher_lock()` re-entrant + fork-safe; `write_intent()` menolak duplikat + gagal tulis = batal; pencocokan kunci per namespace; update receipt by `intent_id`. Lapis ini membuktikan komponen bekerja TANPA perlu mengirim request — karena request tidak boleh dikirim selama Sprint 3.
- **Lapis C — uji jalur sukses penuh (DITUNDA, dilarang selama Sprint 3).** Uji end-to-end gate → lock → intent → HTTP mock → receipt (T2-live, D-1-live, D-6-live, K3-live, P-live, RV3-live) HANYA dijalankan setelah keputusan manusia terpisah mengaktifkan otorisasi live pasca-Sprint 3. Daftarnya ada di akhir subsection ini. Menjalankan lapis C selama Sprint 3 = pelanggaran batas kewenangan (live publishing tanpa otorisasi), walau transport-nya mock — karena ia mensyaratkan hard gate dinonaktifkan.

**Re-scope eksplisit (yang diubah P0-1 terhadap tabel di bawah):** T2 ("ON → mock publish sukses") → penolakan hard gate; kolom ON matriks per publisher (P1–P9) → "kill switch ALLOWED, hard gate menolak, 0 mutasi"; D-1 (DELETE terkirim) → penolakan hard gate; D-4 (publish sukses lalu flag) → run berhenti sebelum mutasi pertama, 0 mutasi; D-6 (DELETE terkirim lalu timeout) → DITUNDA ke D-6-live; K3 (timeout setelah server menerima) → DITUNDA ke K3-live (cabang penanganan timeout diuji unit pada level fungsi respons, bukan end-to-end); T6/K4 (kontensi lock antar-proses) → level komponen (`acquire_publisher_lock()` langsung; publisher runs-nya ditolak hard gate); T7/K2 (crash setelah intent) → intent dibuat via `write_intent()` langsung (fixture, lapis B) + simulasi crash; T9/K5 (per-channel) → keputusan per channel diuji unit via `is_publishing_allowed()` (publisher runs-nya ditolak hard gate); D-7 (DELETE dibalas HTTP 400) → unit pada level fungsi penangan respons; RV-3/RV-4 (intent tertulis sebelum request di semua jalur) → lapis B (unit `write_intent()` + inspeksi statis call-site) + RV3-live; RV-5/RV-6 (SIGTERM/SIGKILL setelah intent) → fixture intent yang dibuat langsung (bukan via live path) + RV3-live; RV2-7/RV2-8 (DELETE gagal / supersedes di repost) → fixture + RV3-live; RV2-9(b) (`--live` → mock pin sukses) → `--live` tetap ditolak hard gate, 0 mutasi. Uji yang TIDAK berubah: T1, T3, T4 (ekspektasi pengecualian diperbarui menjadi `LiveNotAuthorized` — hard gate mendahului kill switch), T5, T8, T10, K1, K6 (ekspektasi pengecualian diperbarui menjadi `LiveNotAuthorized`), K7, K8, D-2, D-3, D-5, D-8, RV-1, RV-2, RV2-1, RV2-2, RV2-3, RV2-4, RV2-5, RV2-6, RV2-10.

**Uji tertunda pasca-Sprint 3 (hanya setelah otorisasi live diaktifkan oleh keputusan manusia terpisah):** T2-live (publish sukses mock + receipt lengkap), P-live (matriks per publisher kolom ON, jalur sukses penuh), D-1-live (DELETE terkirim + `deleted`), D-6-live (DELETE timeout → `delete_ambiguous` → reconcile), K3-live (timeout setelah server menerima → reconcile menemukan post), RV3-live (intent end-to-end semua jalur + signal handler end-to-end). Uji-uji ini TIDAK BOLEH dijalankan, dijadwalkan, atau dianggap "sudah lolos" selama Sprint 3.

| # | Skenario | Cara uji | Harapan |
|---|---|---|---|
| T1 | Kill switch OFF (flag global ada) → semua live publishing diblokir | `touch data/publishing_disabled`; jalankan `run_slot.py --slot 09:00 --api` (mock transport), `publish_api.py --text`, `publish_video.py --live` (mock), `auto_comment.py --live` (mock), `run_pinterest.py` (mock), `repost_product.py` (mock) | Semua keluar dengan pesan `⛔ KILL SWITCH`, exit ≠ 0, TIDAK ADA request ke API (mock mencatat 0 panggilan), DB/history tidak berubah |
| T2 | Kill switch ON (tidak ada flag) → hard gate TETAP menolak (P0-1) | Hapus semua flag; jalankan tiap jalur (mock transport): `run_slot.py --slot 09:00 --api`, `publish_api.py --text`, `publish_video.py --live`, `auto_comment.py --live`, `run_pinterest.py --live`, `repost_product.py` | **RE-SCOPE P0-1:** semua jalur DITOLAK hard gate (`LiveNotAuthorized`) sekalipun kill switch ALLOWED; 0 panggilan mock; 0 intent tertulis; DB/history tidak berubah; `publish_guard.py status` → kill switch ALLOWED + otorisasi NOT AUTHORIZED. Jalur sukses penuh DITUNDA ke T2-live (pasca-Sprint 3, hanya setelah otorisasi live diaktifkan manusia) |
| T3 | Konfigurasi hilang/invalid → fail closed | Rename `config.yaml` sementara / buat `data/` tidak terbaca (chmod) / hapus `publish_guard.py` (simulasi import gagal) / buat flag file tidak dapat dibaca (chmod 000) | Semua jalur live DITOLAK; dry-run tetap jalan (kecuali bila config memang dibutuhkan dry-run — catat pengecualiannya) |
| T4 | API + Playwright diblokir saat OFF | Flag ada; panggil `publish_text()` langsung (import) dan `ThreadsPoster.post()` (mock browser) | Keduanya raise `LiveNotAuthorized` (hard gate mendahului kill switch selama Sprint 3 — ekspektasi lama `PublishingBlocked` berlaku bila hard gate sudah tidak aktif) sebelum request/browser dibuka |
| T5 | Dry-run tetap berjalan saat OFF | Flag ada; `run_slot.py --dry-run`, `publish_video.py --dry-run`, `auto_comment.py --dry-run`, `run_pinterest.py --dry-run` | Semua sukses (exit 0), tidak ada panggilan mutasi |
| T6 | Dua proses publisher bersamaan → satu lock | **RE-SCOPE P0-1:** kontensi lock diuji pada level komponen — dua proses memanggil `acquire_publisher_lock()` langsung (tanpa live path); secara terpisah jalankan 2× `run_slot.py` (mock) bersamaan | Komponen: proses ke-2 gagal acquire (exit 4); lock tidak macet setelah dilepas. Publisher runs: keduanya ditolak hard gate (`LiveNotAuthorized`), 0 panggilan mock |
| T7 | Crash simulation → tanpa blind retry / double-post | **RE-SCOPE P0-1:** intent `publish_started` dibuat via `write_intent()` langsung (fixture, lapis B), lalu proses di-SIGTERM sebelum `record()`; jalankan slot lagi | Entri `publish_started` ADA di disk (bukti fsync bekerja); run ke-2 MENOLAK publish ulang (idempotency — dan selama Sprint 3 juga ditolak hard gate); recovery `reconcile.py --check` menemukan post lewat mock `get_media`. End-to-end crash-setelah-request DITUNDA ke RV3-live |
| T8 | Tidak ada token di log | Jalankan T1–T7 + K1–K8, lalu `grep -ri "access_token\|THREADS_ACCESS_TOKEN\|PINTEREST_ACCESS_TOKEN=" logs/` | 0 hasil; error API tetap terpotong 300 karakter |
| T9 | Per-channel flag | **RE-SCOPE P0-1:** uji `is_publishing_allowed()` per channel (unit) + jalankan jalur Threads dan Pinterest (mock) dengan hanya `publishing_disabled_pinterest` ada | Unit: Threads ALLOWED, Pinterest BLOCKED (dan sebaliknya); global memblokir semua. Publisher runs: semua ditolak hard gate (0 mutasi) — pembeda per-channel dibuktikan pada level fungsi `is_publishing_allowed()`, bukan pada panggilan mock |
| T10 | Re-enable eksplisit | Hapus flag → `publish_guard.py status` → `ALLOWED`; jalankan dry-run | Status berubah hanya oleh aksi manusia (hapus file); log mencatat peristiwa |

#### Pengujian khusus (dari Kyan — Tahap 3)

| # | Skenario | Cara uji | Kriteria PASS |
|---|---|---|---|
| K1 | Kill switch dibuat KETIKA proses sedang berjalan | Jalankan `run_slot.py` (mock, sleep sebelum publish); di tengah jalan `touch data/publishing_disabled`; biarkan lanjut | Proses berhenti di cek ulang [2]/[3] SEBELUM request; TIDAK ADA request ke API; link tetap UNUSED; log mencatat `⛔ KILL SWITCH` |
| K2 | Proses mati SETELAH intent record TETAPI SEBELUM request | **RE-SCOPE P0-1:** intent ditulis via `write_intent()` langsung (lapis B), lalu SIGKILL proses sebelum request; jalankan slot lagi | Entri `publish_started` ADA di history (bukti fsync bekerja); run ke-2 MENOLAK publish ulang (idempotency); `reconcile.py --check` melaporkan status AMBIGU (bukan `abandoned`, bukan `posted`). End-to-end (intent-dalam-run → SIGKILL → request) DITUNDA ke RV3-live |
| K3 | API timeout SETELAH server diduga menerima request | **DITUNDA ke K3-live (pasca-Sprint 3).** Selama Sprint 3, cabang penanganan timeout diuji unit pada level fungsi respons (mock respons timeout, tanpa melewati choke point live) | K3-live: mock transport container POST "berhasil" tapi respons timeout; lalu mock `get_media` mengembalikan post ADA → status `publish_started`/`publish_interrupted` (BUKAN publish ulang otomatis); `reconcile.py --check` menemukan post; TIDAK ADA double-post di run berikutnya. Unit Sprint 3: fungsi penangan timeout mengembalikan status ambigu yang benar + tidak memanggil API mutasi |
| K4 | Dua publisher BERBEDA mencoba berjalan bersamaan | **RE-SCOPE P0-1:** kontensi lock diuji pada level komponen (dua proses berbeda memanggil `acquire_publisher_lock()` langsung); secara terpisah jalankan `run_slot.py` + `publish_video.py --live` (mock) bersamaan | Komponen: hanya SATU yang memperoleh lock; yang lain exit 4. Publisher runs: keduanya ditolak hard gate, 0 panggilan mock |
| K5 | Flag global DAN flag per-channel aktif bersamaan | `touch` global + `publishing_disabled_threads` + `publishing_disabled_pinterest`; uji `is_publishing_allowed()` per channel (unit) + jalankan semua jalur (mock) | Unit: keputusan per channel benar (global memblokir semua; hapus global saja → per-channel tetap memblokir channel-nya). Publisher runs: semua ditolak (hard gate mendahului — hasil observasi sama, pembedanya adalah pesan log / nilai `is_publishing_allowed()`, bukan jumlah panggilan) |
| K6 | Import langsung fungsi publisher saat kill switch OFF | Flag ada; `python -c "from publish_api import publish_text; publish_text('x')"`, `poster.post()` (mock), `create_pin()` (mock), `delete_media()` (mock) | Semua raise `LiveNotAuthorized` (hard gate mendahului kill switch selama Sprint 3 — ekspektasi lama `PublishingBlocked` berlaku bila hard gate sudah tidak aktif) SEBELUM request; TIDAK ADA panggilan jaringan |
| K7 | File flag tidak dapat dibaca | Flag ada tapi `chmod 000` (atau direktori `data/` tidak terbaca) | Fail closed: semua jalur live DITOLAK; `publish_guard.py status` melaporkan BLOCKED + alasan "tidak dapat dibaca"; dry-run tetap jalan |
| K8 | Recovery tidak boleh mengubah status tanpa bukti | Buat entri `publish_started` fiktif (fixture); jalankan `reconcile.py` default (tanpa `--apply`) dengan mock `get_media` yang (a) mengembalikan post ADA, (b) HTTP 400, (c) timeout | (a) default TIDAK mengubah file (laporan saja); (b)+(c) status tetap terblokir + eskalasi; hanya `--apply` eksplisit + bukti rangkap tiga yang boleh mengubah status; md5 history tidak berubah pada mode default |

#### Matriks pengujian per publisher (Tahap 3) — RE-SCOPE P0-1

Setiap publisher diuji pada 5 dimensi yang sama (mock transport / fixture / dry-run, tanpa live post). "—" = tidak berlaku untuk jalur itu. **Kolom ON dibaca dengan semantik Sprint 3: kill switch ALLOWED, hard gate (P0-1) tetap menolak — 0 mutasi. Jalur sukses penuh (kolom ON versi lama) DITUNDA ke P-live pasca-Sprint 3. Kolom "Intent + idempotency" diuji pada lapis B (unit `write_intent()` + inspeksi call-site), bukan via live path.**

| # | Publisher | OFF → diblokir | ON (ALLOWED) → hard gate menolak (P0-1) | Dry-run jalan saat OFF | Lock bersama (flock) | Intent + idempotency (lapis B) |
|---|---|---|---|---|---|---|
| P1 | `run_slot.py` → API | Flag global/threads → exit 1, 0 request, link UNUSED | `LiveNotAuthorized` sebelum request; 0 panggilan mock; 0 intent; DB/history tidak berubah | `--dry-run` exit 0, 0 mutasi | Proses ke-2 exit 4 | Unit: `write_intent()` menulis `publish_started` atomik + menolak duplikat; call-site `run_slot.py` memanggilnya sebelum request (inspeksi statis) |
| P2 | `run_slot.py` → Playwright | Sama (mock browser tidak dibuka) | Sama (`LiveNotAuthorized`; mock browser tidak dibuka) | `--dry-run` exit 0 | Sama (flock bersama P1) | Sama |
| P3 | `publish_api.py` CLI (`--text`) | `PublishingBlocked` sebelum request; tanpa `--dry-run` pun diblokir | `LiveNotAuthorized` sebelum request (mendahului kill switch); tanpa `--dry-run` pun ditolak | `--dry-run` exit 0 | Import/CLI dari proses baru wajib lock (RV-2) | Unit: `write_intent()` sebelum request (inspeksi call-site `_post()`) |
| P4 | `publish_video.py --live` | Diblokir; tidak ada container dibuat | `LiveNotAuthorized`; tidak ada container dibuat; 0 intent | `--dry-run` (default) exit 0 | Sama | Unit: `write_intent()` + cek kunci `pub:` (inspeksi call-site) |
| P5 | `auto_comment.py --live` | Diblokir (ikut kill switch Threads, D2) | `LiveNotAuthorized` (ikut hard gate Threads, P0-1) | `--dry-run` (default) exit 0 | Sama | Unit: `write_intent()` + kunci `cmt:` (inspeksi call-site) |
| P6 | vendor CLI (`cmd_post` / `cmd_post_auto`) | Diblokir; `--force` tidak bisa melewati gate | `LiveNotAuthorized`; `--force` tidak bisa melewati hard gate | — (CLI tidak punya dry-run; uji via mock + gate) | Sama | Unit: `write_intent()` + dedup vendor (inspeksi call-site `poster.post()`) |
| P7 | `run_pinterest.py` | Diblokir (flag pinterest/global) | `LiveNotAuthorized` — bahkan DENGAN `--live` eksplisit (hard gate mendahului flag CLI) | Tanpa `--live` = batal/dry-run (D5) | Sama | Unit: `write_intent()` + kunci `pin:` (inspeksi call-site `create_pin()`) |
| P8 | `pinterest_api.py` CLI | Diblokir | `LiveNotAuthorized` — bahkan DENGAN `--live` eksplisit | Tanpa `--live` = batal (D5) | Sama | Unit: `write_intent()` + kunci `pin:` (inspeksi call-site `create_pin()`) |
| P9 | `repost_product.py` (publish) | Diblokir | `LiveNotAuthorized`; 0 panggilan mock; `update_history` tidak berjalan | — (uji via mock; tidak ada mode dry-run — catat bila perlu ditambah) | Sama | Unit: `write_intent()` + cek `(content_id, sub_id)` (inspeksi call-site) |

#### Matriks DELETE (Tahap 3) — D9 DISETUJUI YA

Semua uji memakai mock transport API. Tidak ada DELETE sungguhan.

| # | Skenario | Cara uji | Kriteria PASS |
|---|---|---|---|
| D-1 | DELETE saat Threads ON, via repost | Flag tidak ada; jalankan `repost_product.py` (mock) | **RE-SCOPE P0-1:** DITOLAK hard gate (`LiveNotAuthorized`) — publish baru tidak terkirim, DELETE tidak terkirim; 0 panggilan mock; 0 intent tertulis; `delete_history.json` tidak berubah. Jalur sukses penuh DITUNDA ke D-1-live (pasca-Sprint 3): `delete_started` tertulis SEBELUM request (atomik + fsync); DELETE terkirim (mock 1 panggilan); entri menjadi `deleted`; `post_history.json` TIDAK berisi entri DELETE |
| D-2 | DELETE saat Threads OFF, via repost | Flag threads ada; jalankan `repost_product.py` (mock) | `PublishingBlocked` sebelum request DELETE; 0 panggilan DELETE; `delete_history.json` tidak berubah (tidak ada intent — gate mendahului intent) |
| D-3 | DELETE langsung (import) saat OFF | Flag ada; `python -c "from repost_product import delete_media; delete_media('123')"` (mock transport) | Raise `PublishingBlocked` SEBELUM request; 0 panggilan jaringan |
| D-4 | Flag dibuat DI TENGAH alur repost (antara publish dan delete) | Mock: jalankan `repost_product.py`; `touch` flag sebelum mutasi pertama; varian fixture: intent publish sudah ada sebagai fixture, lalu `touch` flag sebelum `delete_media()` | **RE-SCOPE P0-1:** run berhenti sebelum mutasi pertama (`LiveNotAuthorized`), 0 mutasi; varian fixture: DELETE diblokir (`PublishingBlocked`); post lama TETAP ADA (mock `get_media` masih mengembalikan post lama); log mencatat penolakan DELETE; tidak ada publish ulang / hapus ulang otomatis |
| D-5 | Proses mati setelah intent DELETE, sebelum request | Mock: tulis `delete_started` lalu SIGKILL sebelum request DELETE; jalankan `reconcile.py --delete --check` | Entri `delete_started` ADA di disk (bukti fsync); reconcile melaporkan AMBIGU (bukan `deleted`, bukan `delete_failed`); tidak ada perubahan status |
| D-6 | DELETE terkirim, respons timeout | **DITUNDA ke D-6-live (pasca-Sprint 3).** Selama Sprint 3, cabang penanganan timeout diuji unit pada level fungsi penangan respons (tanpa melewati choke point live): mock `get_media` (a) post masih ADA, (b) post sudah HILANG | D-6-live: status `delete_ambiguous`; (a) `--apply` + bukti → `delete_failed`; (b) `--apply` + bukti rangkap tiga → `deleted`; tanpa `--apply` tidak ada perubahan. Unit Sprint 3: fungsi penangan timeout mengembalikan status `delete_ambiguous` yang benar untuk kedua varian mock, tanpa memanggil API mutasi |
| D-7 | DELETE dibalas HTTP 400 | **RE-SCOPE P0-1:** cabang penanganan respons 400 diuji unit pada level fungsi penangan respons (mock respons 400, tanpa melewati choke point live) | TIDAK dianggap bukti tidak terhapus (K0-4); status `delete_ambiguous` + eskalasi; tidak ada publish ulang / hapus ulang otomatis. End-to-end DELETE-400 DITUNDA ke D-6-live |
| D-8 | Reconcile DELETE tidak mengubah tanpa bukti | Buat entri `delete_started` fiktif (fixture); jalankan `reconcile.py --delete` default dengan mock `get_media` (a) ADA, (b) 400, (c) timeout | Default TIDAK mengubah file (md5 `delete_history.json` tidak berubah); hanya `--apply` eksplisit + bukti rangkap tiga yang boleh mengubah status |

#### Pengujian khusus koreksi revisi final (Tahap 3) — kode RV-1 s.d. RV-8

(Kode `RV` dipakai agar tidak tertukar dengan skenario K1–K8 yang sudah ada di atas. Semua uji mock/fixture/dry-run, tanpa live post.)

| # | Koreksi | Skenario | Cara uji | Kriteria PASS |
|---|---|---|---|---|
| RV-1 | K1-1 | Nested acquire dalam satu proses | Dalam satu proses (mock): panggil `acquire_publisher_lock()` 2× berurutan | Keduanya sukses instan (tanpa deadlock; timeout 5 detik tidak tercapai); `_lock_depth` kembali 0 setelah `release_publisher_lock()` 2× |
| RV-2 | K1-1 | Proses kedua tetap diblokir meski re-entrancy ada | Proses A pegang lock; proses B (proses baru) panggil `acquire_publisher_lock()` → exit 4; lalu dalam proses A panggil acquire lagi (nested) → sukses | Membuktikan re-entrancy TIDAK membuka celah antar-proses: nested dalam proses yang sama boleh, proses lain tetap ditolak |
| RV-3 | K1-2 | Intent record di SEMUA jalur | Jalankan tiap publisher P1–P9 (mock) | Tiap jalur menulis `publish_started` via `write_intent()` SEBELUM request; isi intent lengkap (content_id, sub_id, product_id, pid, jalur); file ada di disk sebelum request (uji dengan mematikan proses tepat setelah intent) |
| RV-4 | K1-2 | DELETE tercatat terpisah | Jalankan `delete_media()` (mock, flag tidak ada) | Entri `delete_started` ada di `data/delete_history.json`; TIDAK ADA entri baru di `post_history.json`; receipt publikasi tidak berubah |
| RV-5 | K1-3 | SIGTERM di tengah publish | Mock `run_slot.py` sleep panjang; kirim SIGTERM; amati keluarnya proses | Proses keluar rapi; entri `publish_interrupted` tertulis oleh cleanup di `finally` (BUKAN oleh handler); tidak ada file `.tmp` setengah tertulis / JSON rusak |
| RV-6 | K1-3 | SIGKILL setelah intent record | Proses di-SIGKILL tepat setelah `write_intent()` + sebelum request; jalankan slot lagi + `reconcile.py --check` | Entri `publish_started` ADA di disk (bukti fsync bekerja); run berikutnya MENOLAK publish ulang; reconcile melaporkan AMBIGU (bukan `abandoned`, bukan `posted`) |
| RV-7 | K1-4 | `config.yaml` hilang | Rename `config.yaml` sementara; uji (a) flag ADA, (b) flag TIDAK ADA | (a) tetap BLOCKED; (b) tetap ALLOWED (dry-run + mock publish jalan); status TIDAK BERUBAH oleh hilangnya config; kembalikan file setelah uji |
| RV-8 | K1-4 | Direktori data tidak terbaca | `chmod` direktori `data/` tidak terbaca (atau rename sementara) | Semua jalur live BLOCKED + alasan "direktori/flag tidak dapat diperiksa"; `publish_guard.py status` → BLOCKED; dry-run boleh gagal karena tidak bisa baca DB (bukan karena kill switch — catat pengecualiannya) |

#### Pengujian khusus koreksi revisi final tambahan (Tahap 3) — kode RV2-1 s.d. RV2-10

(Kode `RV2` dipakai agar tidak tertukar dengan RV-1–RV-8 di atas dan K1–K8. Semua uji mock/fixture/dry-run, tanpa live post.)

| # | Koreksi | Skenario | Cara uji | Kriteria PASS |
|---|---|---|---|---|
| RV2-1 | K2-1 | Proses anak hasil `fork()` tidak mewarisi lock | Parent (mock publisher) pegang lock + sleep; `os.fork()` → anak memanggil `acquire_publisher_lock()` lalu mencoba publish (mock) | Anak GAGAL acquire (jalur exit 4); 0 panggilan publish dari anak; parent tidak terganggu; anak tidak melihat `_lock_depth` parent sebagai miliknya |
| RV2-2 | K2-1 | Proses anak via `multiprocessing` / `subprocess` tidak bisa melewati lock | Parent pegang lock; spawn anak via `multiprocessing` (start method fork) dan via `subprocess` (interpreter baru) — keduanya mencoba acquire + publish (mock); ulangi setelah parent melepas lock | Selama parent memegang lock: kedua anak GAGAL acquire; setelah parent melepas: anak baru BISA acquire (lock tidak macet) |
| RV2-3 | K2-2 | Duplikasi intent key secara bersamaan | Dua proses (atau dua thread + lock) memanggil `write_intent()` dengan kunci idempotency yang sama secara bersamaan | Tepat SATU intent berhasil; yang kedua mendapat `DuplicateIntent` (tanpa intent kedua, tanpa request); history berisi tepat satu `publish_started` untuk kunci itu |
| RV2-4 | K2-2 | Kegagalan menulis intent membatalkan request | Mock `write_intent()` agar raise I/O error (mis. direktori dibuat read-only sementara) lalu jalankan jalur publish (mock transport) | Publisher batal SEBELUM request apa pun (0 panggilan API); log mencatat "intent gagal ditulis — dibatalkan"; exit non-zero |
| RV2-5 | K2-2 | Update receipt berdasarkan ID intent | Fixture: dua intent untuk `content_id`/`sub_id` yang sama (retry setelah interrupted, `op_id` berbeda); update receipt untuk `op_id` kedua | Hanya entri dengan `intent_id` yang cocok yang berubah; entri pertama byte-identik (diff JSON per entri); tidak ada update berdasarkan pencocokan `content_id` saja |
| RV2-6 | K2-3 | Namespace kunci tidak bertabrakan | Bangun kunci keempat jenis operasi dengan `content_id`/`sub_id`/`media_id` yang SAMA; uji lookup + duplikasi lintas jenis | Keempat kunci berbeda; lookup satu jenis tidak pernah mengenai jenis lain; duplikat dalam jenis yang sama ditolak, lintas jenis tidak saling memblokir |
| RV2-7 | K2-4 | DELETE gagal/ambigu di repost | Mock: publish baru sukses, DELETE timeout / HTTP 400; amati perilaku repost | TIDAK ADA retry DELETE otomatis; TIDAK ADA retry publish; TIDAK ADA penghapusan post baru; status akhir tercatat (post baru `posted`, post lama tetap live, entri `delete_ambiguous`); history lama utuh (entri lama byte-identik) |
| RV2-8 | K2-4 | Relasi `supersedes`/`replaces` eksplisit | Mock repost sukses penuh (publish baru + DELETE sukses) | Entri baru punya catatan `replaces: <media_id_lama>`; entri lama mendapat catatan tambahan `superseded_by: <media_id_baru>`; field asli entri lama byte-identik (bukan ditimpa) |
| RV2-9 | K2-5 | Perilaku flag CLI Pinterest | Untuk `run_pinterest.py` DAN `pinterest_api.py` CLI (mock transport): (a) tanpa flag, (b) `--live` saja, (c) `--dry-run --live`, (d) `--dry-run` saja | (a) banner DRY-RUN + 0 mutasi; **(b) RE-SCOPE P0-1: `--live` tetap ditolak hard gate (`LiveNotAuthorized`), 0 mutasi — mock pin sukses DITUNDA ke P-live**; (c) error konflik (exit 2) + 0 mutasi; (d) dry-run + 0 mutasi; perilaku IDENTIK di kedua file |
| RV2-10 | K2-6 | Output `status` 5 baris terpisah | Jalankan `publish_guard.py status` pada 4 keadaan: (a) tanpa flag + sehat, (b) flag ada, (c) direktori `data/` tidak terbaca, (d) lock dipegang proses lain | Selalu tepat 5 baris; (a) ALLOWED/HEALTHY/FREE/INCOMPLETE (selama Tahap 2–3)/NOT AUTHORIZED; (b) BLOCKED, baris lain tidak berubah; (c) Data ERROR + Kill switch BLOCKED; (d) Lock HELD; tidak ada keadaan yang merangkum semuanya menjadi satu "OK" |

#### Pengujian khusus koreksi revisi terakhir (Tahap 3) — kode RV3-1 s.d. RV3-11

(Kode `RV3` dipakai agar tidak tertukar dengan RV-1–RV-8, RV2-1–RV2-10, dan K1–K8. Semua uji mock/fixture/dry-run, tanpa live post. Acceptance criteria terukur per skenario.)

| # | Koreksi | Skenario | Cara uji | Kriteria PASS (acceptance criteria) |
|---|---|---|---|---|
| RV3-1 | P0-1 | Hard gate menolak di SEMUA choke point mutasi, sekalipun kill switch ALLOWED | Hapus semua flag; panggil langsung tiap choke point (mock transport): `_post()`, `poster.post()`, `create_pin()`, auto-comment live path, vendor CLI `cmd_post`, repost publish, `delete_media()` | Setiap panggilan raise `LiveNotAuthorized` SEBELUM request; mock mencatat tepat 0 panggilan di semua choke point; 0 intent tertulis; md5 DB/history tidak berubah |
| RV3-2 | P0-1 | Hard gate tidak bisa dilewati dengan menghapus flag | Hapus semua flag → `publish_guard.py status` menunjukkan kill switch ALLOWED; jalankan `run_slot.py --slot 09:00 --api` (mock) + `create_pin()` (mock) | Status ALLOWED, tetapi mutasi tetap ditolak (`LiveNotAuthorized`); 0 panggilan mock; log menyebut "LIVE NOT AUTHORIZED", bukan "KILL SWITCH" |
| RV3-3 | P0-1 | Hard gate tidak aktif otomatis setelah tes lulus | Jalankan seluruh suite Tahap 3 (mock) sampai semua PASS, lalu segera coba satu mutasi (`publish_text()` mock) tanpa perubahan apa pun | Mutasi tetap ditolak; `grep -rn "LIVE_PUBLISHING_AUTHORIZED = True" tools/ vendor/` = 0 hasil; konstanta hanya ditulis di satu tempat (`publish_guard.py`) dan bernilai `False` |
| RV3-4 | P0-1 | Dry-run + read-only tetap diperbolehkan saat hard gate menolak | Hard gate aktif; jalankan `run_slot.py --dry-run`, `publish_video.py --dry-run`, `auto_comment.py --dry-run`, `run_pinterest.py --dry-run`, dan `_get()`/`get_media()` (mock) | Semua dry-run exit 0, 0 mutasi; `_get()`/`get_media()` mengembalikan data mock (read-only jalan); tidak ada `LiveNotAuthorized` pada jalur read-only |
| RV3-5 | P0-1 | Status CLI memisahkan hard gate dari kill switch | Jalankan `publish_guard.py status` pada 2 keadaan: (a) tanpa flag, (b) flag ada | Selalu tepat 5 baris; (a) kill switch ALLOWED + otorisasi NOT AUTHORIZED (bukti pemisahan); (b) kill switch BLOCKED + otorisasi NOT AUTHORIZED; tidak ada keadaan yang menampilkan otorisasi AUTHORIZED selama Sprint 3 |
| RV3-6 | P1-1 | `reconcile.py --apply` gagal memperoleh lock → batalkan seluruh perubahan | Proses lain memegang shared lock (sleep); jalankan `reconcile.py --apply` pada fixture entri `publish_interrupted` | Exit non-zero; 0 tulis ke history (md5 `post_history.json` tidak berubah); log mencatat "lock tidak diperoleh — reconcile dibatalkan"; tidak ada perubahan status apa pun |
| RV3-7 | P1-1 | `--apply` membaca ulang bukti + history DI BAWAH lock | Fixture: jalankan `--check` (bukti: post TIDAK ADA) → ubah history secara eksternal (tambah entri baru) → jalankan `--apply` sambil memegang observasi | `--apply` melihat state TERBARU (entri baru ikut terbaca) sebelum menulis; keputusan memakai bukti yang diverifikasi ulang di bawah lock, bukan snapshot `--check`; tulis atomik di bawah lock (tidak ada file `.tmp` tersisa) |
| RV3-8 | P1-1 | `--check` tetap read-only dan tanpa lock | Proses lain memegang shared lock; jalankan `reconcile.py --check` pada history yang sedang ditulis publisher (simulasi torn-read: file JSON setengah tertulis) | `--check` tetap menghasilkan laporan ATAU melaporkan "history tidak dapat dibaca konsisten — ulangi" (exit non-zero); md5 history tidak berubah; tidak ada lock yang diambil `--check` |
| RV3-9 | P1-2 | Direct import `create_pin()` tanpa `--live` → ditolak | `python -c "from pinterest_api import create_pin; create_pin(...)"` (mock transport), tanpa flag CLI apa pun | Raise `LiveNotAuthorized` (hard gate mendahului) SEBELUM request; 0 panggilan mock; 0 intent; pesan penolakan menyebut otorisasi live, bukan error token |
| RV3-10 | P1-2 | `create_pin()` menegakkan urutan gate di titik mutasi terdalam | Mock fungsi guard (`require_live_authorization`, `require_publishing`, `acquire_publisher_lock`, pemeriksa idempotency, `write_intent`) agar merekam urutan pemanggilan; panggil `create_pin()` langsung (tanpa CLI) | Urutan tercatat: live-auth → kill switch → lock → idempotency → intent → HTTP; bila satu lapis menolak, lapis berikutnya TIDAK dipanggil dan HTTP tidak pernah terjadi; inspeksi AST memastikan `create_pin()` memanggil kelima guard sebelum HTTP |
| RV3-11 | P1-2 | CLI Pinterest `--live` tanpa otorisasi live tetap ditolak | `run_pinterest.py --live` dan `pinterest_api.py --live` (mock transport), tanpa flag kill switch | Keduanya ditolak hard gate (`LiveNotAuthorized`); 0 mutasi; 0 pin mock; perilaku IDENTIK di kedua file (RV2-9 diperluas dengan hard gate) |

#### Matriks choke point × gate (Tahap 3) — P0-1 / P1-1 / P1-2

Setiap baris = satu choke point mutasi. Kolom gate dibaca dari kiri ke kanan sesuai urutan penegakan: hard gate → kill switch → lock → idempotency → intent → guardrail. "—" = tidak berlaku. Perilaku "tidak diotorisasi" adalah perilaku saat lapis mana pun menolak (penolakan pertama yang ditemui menghentikan alur; tidak ada lapis berikutnya yang dijalankan).

| # | Choke point | Hard gate live (P0-1) | Kill switch flag | Shared lock | Intent record | Idempotency | Guardrail / flag eksplisit | Perilaku bila tidak diotorisasi |
|---|---|---|---|---|---|---|---|---|
| G1 | Threads API `_post()` | ✅ `require_live_authorization("threads")` baris pertama | ✅ `require_publishing("threads")` | ✅ `acquire_publisher_lock()` | ✅ `write_intent()` atomik + fsync, kunci `pub:` | ✅ cek `pub:threads:<content_id>:<sub_id>` sebelum intent | ✅ `check_chain()` di pemanggil (bukan di `_post`) | `LiveNotAuthorized` / `PublishingBlocked` sebelum request; 0 panggilan API; 0 intent; exit non-zero; log `⛔ LIVE NOT AUTHORIZED` / `⛔ KILL SWITCH` |
| G2 | Playwright `poster.post()` | ✅ sama (threads) | ✅ sama | ✅ sama | ✅ `write_intent()` kunci `pub:` | ✅ sama | ✅ `check_chain()` di `run_slot.py`/`cli.py` (D6) | Sama; mock browser TIDAK dibuka |
| G3 | Pinterest `create_pin()` (P1-2) | ✅ `require_live_authorization("pinterest")` DI DALAM `create_pin()` | ✅ `require_publishing("pinterest")` di dalam `create_pin()` | ✅ `acquire_publisher_lock()` di dalam `create_pin()` | ✅ `write_intent()` kunci `pin:` di dalam `create_pin()` | ✅ cek `pin:pinterest:<content_id>:<sub_id>` di dalam `create_pin()` | ✅ `--live` eksplisit di CLI (D5/K2-5) + `check_chain()` | `LiveNotAuthorized` / `PublishingBlocked` sebelum HTTP; 0 panggilan; direct import tidak bisa bypass; `--live` tanpa otorisasi tetap ditolak |
| G4 | Auto-comment live path (`publish_text` / `publish_media_reply` via `_post()`) | ✅ via `_post()` [G1] + gate di `main()` live path | ✅ via `_post()` + D2 | ✅ via helper bersama | ✅ `write_intent()` kunci `cmt:` | ✅ cek `cmt:threads:<comment_id>:<target_media_id>` | ✅ `validate_comment()` + owner-check fail-CLOSED | Sama seperti G1; gagal owner-check = JANGAN kirim (bukan lanjut) |
| G5 | Vendor CLI `cmd_post` / `cmd_post_auto` (via `poster.post()`) | ✅ via `poster.post()` [G2] | ✅ via `poster.post()` + gate di `cli.py` (D6) | ✅ via helper bersama | ✅ `write_intent()` kunci `pub:` | ✅ cek `pub:` + dedup vendor | ✅ `check_chain()` di `cli.py`; flag `--force` ditutup | Sama seperti G2; `--force` tidak melewati gate mana pun |
| G6 | Repost publish (via `_post()`) | ✅ via `_post()` [G1] | ✅ via `_post()` + gate di `main()` | ✅ via helper bersama | ✅ `write_intent()` kunci `pub:` (intent publish terpisah dari DELETE) | ✅ cek `pub:` | ✅ `check_chain()` | Sama seperti G1 |
| G7 | Repost `delete_media()` (DELETE) | ✅ `require_live_authorization("threads")` baris pertama (P0-1, D9) | ✅ `require_publishing("threads")` (D9) | ✅ `acquire_publisher_lock()` | ✅ `write_delete_intent()` ke `data/delete_history.json`, kunci `del:` | ✅ cek `del:<delete_operation_id>:<media_id>` | — (DELETE tidak punya guardrail konten; alur repost yang sah adalah satu-satunya pemanggil) | `LiveNotAuthorized` / `PublishingBlocked` sebelum HTTP DELETE; 0 panggilan; 0 delete intent; post lama tetap ada |
| G8 | `reconcile.py --apply` (mutasi history LOKAL, bukan live) | — (bukan mutasi live; TIDAK melewati hard gate — pengecualian yang dinyatakan di §B3) | — (bukan publishing; kill switch tidak memblokir perbaikan history) | ✅ `acquire_publisher_lock()` WAJIB (P1-1); gagal = batalkan seluruh perubahan | ✅ perubahan status dicatat sebagai catatan append + `intent_id` terkait | ✅ pencocokan by `intent_id` / `delete_operation_id` (K2-2) | ✅ `--apply` eksplisit manusia + bukti rangkap tiga (K0-5); default `--check` read-only | Lock gagal → batalkan seluruh perubahan, 0 tulis, exit non-zero; bukti tidak cukup / ambigu → tetap blokir + eskalasi |

**Kriteria COMPLETE (disepakati — Tahap 3):** T1–T10 + K1–K8 + matriks per publisher (P1–P9) + matriks DELETE (D-1–D-8) + RV-1–RV-8 + RV2-1–RV2-10 + **RV3-1–RV3-11 + matriks choke point × gate (G1–G8)** SEMUA PASS dengan bukti (log + mock call count + md5 DB/history sebelum/sesudah). TIDAK ADA live post selama Sprint 3. TIDAK ADA kredensial di log mana pun (T8 = 0 hasil). Checksum `data/affiliate_links.md` + `data/post_history.json` TIDAK BERUBAH kecuali perubahan yang memang disetujui (entri baru hasil pengujian harus memakai fixture di `/tmp`, bukan DB/history asli — atau bila pengujian menyentuh history asli, backup dulu + restore + verifikasi md5). **Uji tertunda T2-live, P-live, D-1-live, D-6-live, K3-live, RV3-live TIDAK termasuk kriteria COMPLETE Sprint 3** — ia baru diuji setelah otorisasi live diaktifkan oleh keputusan manusia terpisah pasca-Sprint 3. Satu saja gagal → PARTIAL/BLOCKED, bukan COMPLETE.

---

## B8. File yang TIDAK disentuh (di luar ruang lingkup) + mekanisme jaminan

### B8-a. Daftar eksplisit — TIDAK disentuh pada Tahap 2

| File / area | Alasan tidak disentuh |
|---|---|
| `templates/hooks_{dapur,organizer,kebersihan}.json` (v5.1, masih uncommitted) | Template hook bukan bagian kill switch; perubahan apa pun di sini berisiko merusak antrean posting. |
| `data/affiliate_links.md` (+ `.bak-*`) | Isi DB link hanya dibaca; Sub-ID / Product ID sudah final di Sprint 1. |
| `data/post_history.json` — ISI riwayat | Tidak ditimpa / tidak dihapus. Yang diizinkan: APPEND entri baru (`publish_started`, receipt) yang sudah disetujui Sprint 2, dan `update_history` repost diubah jadi append + `supersedes` (bukan menimpa). Entri lama harus byte-identik sebelum/sesudah (dibuktikan diff JSON). |
| `data/performance.csv`, `data/subid_mapping.md` | Artefak Sprint 1; metrik + pemetaan tidak berubah. |
| `tools/calc_performance.py`, `docs/skema-id-dan-subid.md`, `docs/isi-performance-manual.md` | Artefak Sprint 1; tidak terkait kill switch. |
| Token / kredensial: `~/.threads_poster/threads_token.env`, Secure Vault, `~/.pinterest_poster/` | Tidak dibaca nilainya, tidak diubah, tidak di-backup ke repo. Satu-satunya yang diverifikasi: keberadaan file + mode 600 (sudah begitu). |
| Timer / systemd / cron: `threads-affiliate-*.timer/service`, `pinterest-1000.timer/service`, cron VM `riset-shopee-mingguan` | Jadwal tidak diubah. D5 dipenuhi lewat perubahan default di kode (tanpa `--live` = batal), BUKAN lewat edit unit systemd. |
| `config.yaml` — selain section pointer `publishing:` | Nilai lain tidak diubah; dan `config.yaml` TIDAK dibaca sebagai sumber kebenaran kill switch (K1-4). |
| `guardrails.md`, `tools/check_draft.py` | Aturan kata terlarang + batas 470/500 sudah final (Sprint 1–2); bukan bagian Sprint 3. |
| `vendor/threads-affiliate/threads_poster/` selain `poster.py` + `cli.py` | `dedup.py`, `database.py`, `content_generator.py`, dll. tidak disentuh. |
| File yang diverifikasi BUKAN entry point (§A7): `debug_poster.py`, `probe_composer.py`, `check_login.py`, `test_sso.py`, `whoami.py`, `extract_brave_cookies.py`, `check_combo_rate.py`, `merge_new_hooks.py` | Tidak memanggil publish; tidak ada alasan menyentuhnya. |
| `docs/` lain: `audit-operating-system-20261116.md`, `laporan-sprint2-verifikasi.md`, `sistem-video-ugc-v2.md`, `uji-auto-komen-pertama.md`, dll. | Dokumen audit/laporan lama tidak diubah; hanya dokumen ini + `VENDOR-NOTES.md` + `docs/pemulihan-token.md` (baru) yang ditulis. |

### B8-b. Mekanisme yang menjamin daftar di atas

1. **Daftar file eksplisit (§B5, 16 file + §B5b, 10 commit):** hanya file di daftar yang boleh diubah. Implementer bekerja dari daftar ini; file di luar daftar yang muncul di `git diff` = STOP + laporkan.
2. **Baseline sebelum implementasi:** `git status` + `git diff --stat` + md5 semua file §B8-a dicatat SEBELUM langkah pertama Tahap 2. Baseline md5 (dari audit, diverifikasi ulang saat Tahap 2 dimulai): `affiliate_links.md 4b35b6d4…`, `post_history.json b7f0d50c…`, `config.yaml` PC `eb1eb3ab…`, `guardrails.md` PC `fce5939b…`.
3. **Verifikasi sesudah tiap commit:** `git diff --stat` commit itu hanya berisi file commit tersebut (§B5b); md5 file §B8-a diverifikasi ulang — `affiliate_links.md`, `performance.csv`, `subid_mapping.md`, template hook, `guardrails.md`, `check_draft.py` harus IDENTIK dengan baseline; `post_history.json` hanya boleh bertambah entri (entri lama byte-identik — dibuktikan dengan diff JSON per entri, bukan sekadar md5 file).
4. **Backup `.bak` bertanggal** sebelum perubahan apa pun pada file data/history; prosedur restore = `cp` kembali + verifikasi md5 + `--dry-run`.
5. **Token grep pasca-pengujian:** `grep -ri "access_token\|THREADS_ACCESS_TOKEN\|PINTEREST_ACCESS_TOKEN=" logs/` harus = 0 (T8).
6. **Gerbang persetujuan:** hasil implementasi + hasil tes dilaporkan dulu untuk pemeriksaan; commit/push HANYA setelah persetujuan terpisah Kyan. Tanpa persetujuan itu, tidak ada commit — sehingga file di luar ruang lingkup tidak mungkin ikut ter-commit diam-diam.

---

## Keputusan — status akhir Tahap 1

| # | Keputusan | Status |
|---|---|---|
| D1 | Sumber kebenaran kill switch: flag file | ✅ **DISETUJUI** 17 Nov 01:22 WIB — flag file `data/publishing_disabled*` |
| D2 | Auto-komen ikut kill switch Threads? | ✅ **DISETUJUI** — ya |
| D3 | Siapa boleh re-enable? | ✅ **DISETUJUI** — Kyan saja; agent hanya baca + verifikasi status |
| D4 | Perbaiki `publish_video.py` dalam Sprint 3? | ✅ **DISETUJUI** — ya (hapus fabrikasi permalink, receipt ke `post_history.json`, idempotency) |
| D5 | `run_pinterest.py` wajib `--live` eksplisit? | ✅ **DISETUJUI** — ya (berlaku juga untuk `pinterest_api.py` CLI) |
| D6 | Guardrail ke vendor `cli.py`? | ✅ **DISETUJUI** — ya (termasuk penutupan flag `--force`) |
| D7 | VM tetap BUKAN publisher sampai Sprint 6? | ✅ **DISETUJUI** — ya |
| D8 | Perbaiki duplikasi log (`log()` print-only)? | ✅ **DISETUJUI** — ya |
| D9 | **`delete_media()` di `repost_product.py` ikut kill switch Threads?** (temuan baru §A7-b1) | ✅ **DISETUJUI — YA (17 Nov 2026 01:34 WIB).** Saat Threads OFF, SEMUA tindakan DELETE diblokir, termasuk pemanggilan langsung. Penghapusan hanya boleh dilakukan melalui alur yang telah melewati seluruh pemeriksaan keamanan (gate kill switch + lock re-entrant + intent record DELETE terpisah di `data/delete_history.json`, §B3, §B4-C2, §B5 urutan 8, matriks DELETE §B7). |

**Status keputusan: D1–D9 SEMUA DISETUJUI — tidak ada keputusan terbuka lagi, kecuali persetujuan Tahap 2 (implementasi) atas dokumen final ini.** Koreksi K2-1 s.d. K2-6 dimasukkan sebagai persyaratan mengikat pada revisi final tambahan 17 Nov 2026 ~02:45 WIB (lihat tabel koreksi di atas dan matriks §B9) — tidak ada keputusan D1–D9 yang diubah. Koreksi P0-1, P1-1, P1-2 dimasukkan sebagai persyaratan mengikat pada revisi terakhir 17 Nov 2026 ~08:05 WIB (lihat tabel koreksi di atas dan matriks §B9) — tidak ada keputusan D1–D9 maupun koreksi K0–K2 yang diubah; yang diubah hanya ekspektasi pengujian §B7 yang diselaraskan dengan hard gate P0-1 (re-scope T2 / matriks per publisher / D-1 / D-4 / D-6 / K3 / RV-3 / RV-4 / RV-5 / RV-6 / RV2-7 / RV2-8 + uji tertunda pasca-Sprint 3).

**Batas kewenangan Tahap 2–3 (dari Kyan, tetap berlaku):** tidak boleh live posting; tidak boleh mengaktifkan kembali publishing (re-enable hanya Kyan, D3); tidak boleh mengubah jadwal timer; tidak boleh mengubah akun maupun token; tidak boleh menghapus atau menimpa riwayat; **jangan commit atau push sebelum implementasi dan hasil tes dilaporkan untuk pemeriksaan;** jangan mulai implementasi sebelum persetujuan terpisah dari Kyan atas dokumen final ini.

---

## B9. Matriks keputusan dan koreksi — status akomodasi

| Item | Status | Lokasi di dokumen |
|---|---|---|
| D1 — flag file sumber kebenaran | ✅ DISETUJUI 17 Nov 01:22 WIB | §B2 |
| D2 — auto-komen ikut kill switch Threads | ✅ DISETUJUI | §B3 [3], §B5 urutan 7 |
| D3 — re-enable hanya Kyan | ✅ DISETUJUI | §B3 (re-enable) |
| D4 — perbaiki `publish_video.py` | ✅ DISETUJUI | §B5 urutan 6 |
| D5 — Pinterest wajib `--live` (+ K2-5 perilaku CLI) | ✅ DISETUJUI | §B5 urutan 9–10 |
| D6 — vendor CLI wajib guardrail | ✅ DISETUJUI | §B5 urutan 4–5 |
| D7 — VM bukan publisher sampai Sprint 6 | ✅ DISETUJUI | §A5, §B5 |
| D8 — `log()` print-only | ✅ DISETUJUI | §B4-C4 |
| D9 — `delete_media()` ikut kill switch Threads | ✅ DISETUJUI YA 17 Nov 01:34 WIB | §B3 [3d], §B5 urutan 8, matriks DELETE |
| K0-1 — intent atomik + fsync sebelum request | Mengikat | §B4-C2 |
| K0-2 — satu flock bersama | Mengikat | §B4-C1 |
| K0-3 — cek tepat sebelum request irreversible | Mengikat | §B3 |
| K0-4 — HTTP 400 ≠ bukti tidak terbit | Mengikat | §B4-C2/C3 |
| K0-5 — reconcile default read-only | Mengikat | §B4-C3 |
| K0-6 — default-deny jalur belum terintegrasi | Mengikat | §B3, §B5 |
| K0-7 — recovery append-only | Mengikat | §B4-C3, §B5 urutan 8 |
| K0-8 — tanpa live posting selama Sprint 3 | Mengikat | §B4-C6, batas kewenangan |
| K1-1 — cegah nested flock | Mengikat | §B3, §B4-C1 |
| K1-2 — durable intent + idempotency semua jalur; DELETE terpisah | Mengikat | §B4-C2, §B5 |
| K1-3 — signal handler hanya menandai | Mengikat | §B4-C2 |
| K1-4 — `config.yaml` bukan sumber kebenaran | Mengikat | §B2, §B3 |
| K2-1 — fork safety flock (validasi PID) | Mengikat (revisi tambahan 17 Nov ~02:45 WIB) | §B4-C1, §B3; uji RV2-1, RV2-2 |
| K2-2 — atomic history; op ID unik; tolak duplikat key; receipt by intent ID; gagal tulis intent = batal | Mengikat (revisi tambahan) | §B4-C2, §B4-C3, §B5 urutan 1/3/11; uji RV2-3, RV2-4, RV2-5 |
| K2-3 — idempotency key per jenis operasi (namespace prefix) | Mengikat (revisi tambahan) | §B4-C2; uji RV2-6 |
| K2-4 — pemisahan publish/DELETE repost | Mengikat (revisi tambahan) | §B3 [3d], §B4-C3, §B5 urutan 8; uji RV2-7, RV2-8 |
| K2-5 — perilaku CLI Pinterest | Mengikat (revisi tambahan) | §B5 urutan 9–10; uji RV2-9 |
| K2-6 — status kill switch vs kesehatan dipisah (5 baris) | Mengikat (revisi tambahan) | §B3 (status CLI), §B5 urutan 1; uji RV2-10 |
| P0-1 — hard gate otorisasi live (bukan informasi CLI) | Mengikat (revisi terakhir 17 Nov ~08:05 WIB) | §B1 prinsip 8, §B2, §B3 [0] + subsection hard gate, §B5 urutan 1, §B5b C-S3-1, §B6 R24/R27, §B7 (dampak P0-1 + matriks G1–G8); uji RV3-1 s.d. RV3-5 |
| P1-1 — shared lock untuk `reconcile.py --apply` | Mengikat (revisi terakhir) | §B4-C1, §B4-C3, §B5 urutan 11, §B5b C-S3-9, §B6 R25; uji RV3-6, RV3-7, RV3-8 |
| P1-2 — default-deny Pinterest direct import (`create_pin()` menegakkan semua gate di titik mutasi terdalam) | Mengikat (revisi terakhir) | §B3 [3c], §B5 urutan 10, §B5b C-S3-8, §B6 R26, §B7 matriks G3; uji RV3-9, RV3-10, RV3-11 |

## Lampiran — bukti audit (nilai yang diverifikasi)

- Timer: 3 aktif (0900/1230/1930), Pinterest disabled; `Persistent=true`, jitter 30 mnt; `TimeoutStartUSec=infinity`, `TimeoutStopUSec=90s`, `KillMode=control-group`. Re-verifikasi 17 Nov ~02:00 WIB: timer berikutnya 09:01:45 WIB; service Pinterest ExecStart `run_pinterest.py` tanpa `--dry-run`/`--live`.
- md5 identik PC↔VM: `run_slot.py 81e74f86…`, `publish_api.py 460c59b0…`, `repost_product.py e9050612…`, `post_history.json b7f0d50c…`, `dedup.py fa83b999…`, `poster.py 5bae70e6…`, `affiliate_links.md 4b35b6d4…`.
- md5 BERBEDA (divergen): `config.yaml` (PC `eb1eb3ab…` vs VM `f344636d…`), `guardrails.md` (PC `fce5939b…` vs VM `655bc2b1…`).
- `grep -c access_token logs/cron.log` = 0; `grep -c THREADS_ACCESS_TOKEN logs/cron.log` = 0.
- Grep locking (`flock|fcntl|filelock|O_EXCL|lockfile|.lock`) pada `tools/` + `threads_poster/*.py` = 0 hasil.
- Token: `~/.threads_poster/threads_token.env` mode 600 ada (PC); `~/.pinterest_poster/` tidak ada; VM tidak punya `~/.threads_poster/`.
- `data/post_history.json`: `{"posts": [...]}` — 2 entri (Kikkoman `posted` + catatan verifikasi Sprint 2; BONBOX `posted` receipt lengkap).
- Git PC HEAD `6c6eb1a`; uncommitted: hooks v5.1 (3 file) + untracked (dokumen audit, dokumen ini, 3× `.bak`, `tools/check_combo_rate.py`, `tools/merge_new_hooks.py`, `tools/repost_product.py`).
- Cron VM `riset-shopee-mingguan` enabled, Senin 08:15 — riset saja, bukan publisher.

## Yang TIDAK dilakukan dalam tahap ini (Tahap 1 — revisi final dokumen Tahap 2)

- Tidak ada file sistem yang diubah (hanya dokumen ini yang diperbarui — revisi D9 + K1-1 s.d. K1-4, matriks pengujian, §B5b rencana commit, §B8 daftar file tidak disentuh; revisi final tambahan: + K2-1 s.d. K2-6, matriks RV2-1 s.d. RV2-10, §B9 matriks keputusan dan koreksi; revisi terakhir: + P0-1 hard gate otorisasi live, P1-1 shared lock reconcile, P1-2 default-deny Pinterest direct import, matriks choke point × gate G1–G8, matriks RV3-1 s.d. RV3-11, re-scope pengujian §B7 + uji tertunda pasca-Sprint 3).
- Tidak ada commit / push.
- Tidak ada live posting, tidak ada perubahan timer, tidak ada perubahan akun/token.
- Tidak ada implementasi kill switch, lock, intent record, atau reconcile tool — semuanya menunggu persetujuan terpisah Kyan atas dokumen final ini (Tahap 2). **Pernyataan eksplisit: implementasi Tahap 2 MASIH MENUNGGU persetujuan terpisah Kyan — revisi ini hanya desain dan rencana.**
