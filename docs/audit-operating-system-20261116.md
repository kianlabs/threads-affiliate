# Audit Operating System — Shopee Affiliate @shopee_harian

> **Koreksi 16 Nov 2026 23:57 WIB:** akun Threads diganti nama oleh Kyan dari `@temuanhariann.id` menjadi **`@shopee_harian`** (nama "SHOPEE HARIAN", user ID API tetap 29489356290657436, bio sama). Isi audit di bawah ini ditulis saat nama lama masih berlaku — semua penyebutan `@temuanhariann.id` di dokumen ini merujuk ke akun yang sama. Dua temuan ikut terjawab oleh rename ini: (1) anomali permalink BONBOX §A6 — URL `@shopee_harian/post/DfzXk9En8B-` adalah akun yang benar, sudah diganti nama sebelum post itu; yang tersisa hanya receipt-nya yang tidak lengkap (media_id/permalink null di post_history.json). (2) Kode posting diperbarui: PC commit `d883441` (USERNAME + config.yaml) + VM. Dokumen hidup repo (README, config, brief, dll.) sudah diperbarui ke nama baru; dokumen ini dipertahankan apa adanya sebagai catatan audit bertanggal.

**Tanggal audit:** 16 Nov 2026, ~23:45 WIB
**Auditor:** subagent read-only (tidak ada file diubah, tidak ada posting, tidak ada login, tidak ada generate)
**Ruang lingkup:** repo `kianlabs/threads-affiliate` — VM `~/workspace/threads-affiliate-system` + PC `~/threads-affiliate-system` (SSH `kian-pc`), halaman Notion "Sistem Otomasi Affiliate Shopee — Konsep", cron scheduler VM.
**Sumber yang dibaca langsung:** Notion (fetch penuh, 27.092 karakter, §1–15.11), `config.yaml` (VM + PC), `guardrails.md` (VM + PC), 7 tools utama PC, template hooks/CTA PC, `data/affiliate_links.md` PC, `data/post_history.json` PC, `logs/cron.log` PC, `data/comment_history.json`, `data/video_publish_log.json`, systemd timers PC, `data/video_briefs/` + `data/videos/` VM, `.gitignore` (VM + PC), `git log` + `git log -p` (PC), `cron.list` VM.

> Aturan audit ini: angka performa yang tidak ada datanya ditulis **UNKNOWN** — tidak dikarang. "Notion bilang X" tidak dihitung sebagai bukti X berjalan (§15.11 Notion sendiri menegaskan hal yang sama).

---

## PHASE A — Temuan audit

### A1. Notion (Single Source of Truth) — DIBACA PENUH, SEBAGIAN BASI

- Halaman dibaca sampai habis: §1 niche, §2 pipeline 5 tahap, §3 keputusan v1, §4 jadwal, §5 video Flow, §6 Facebook, §7 guardrails, §8 ekonomi, §9 kenapa bukan API resmi, §10 prasyarat, §11 fase 2, §12 referensi, §13 (dua §13 — "Yang belum terverifikasi" + "Sistem Video UGC v2" update malam), §14 update sore, §15 Optimasi Arsitektur & Operating System (§15.1–15.11).
- **Basi / bertentangan dengan kondisi aktual:**
  - §2 + §3: pipeline masih menyebut posting via **Playwright + cookie**; aktual: API resmi Threads LIVE sejak 16 Nov 17:51 WIB.
  - §7: masih mewajibkan disclosure `#affiliate` di tiap thread; aktual: Kyan melarang kata affiliate/komisi (16 Nov 18:50) dan PC sudah v5. **§13.5 dan §15.8 Notion justru menuntut disclosure tidak boleh dihapus** — konflik langsung antara Notion dan perintah live Kyan, belum diputuskan (lihat gap P0-4).
  - §9: menyebut Threads API "BELUM SIAP" (undangan tester belum diterima); aktual: undangan diterima, token tersimpan, 2 post terkirim via API.
  - §10 checklist: cookie sesi (sudah tidak relevan — API), DB 50–100 produk (aktual 29), undangan tester (selesai), post uji `--headed` (tidak terjadi — post pertama via API, bukan Playwright).
  - §13.1: menyebut DB "25 link"; aktual 29. §13.2: menyebut "2–3 klip"; aktual gaya baru 1 video/produk.
  - §5: kredit Flow 1.050 — konsisten dengan awal hari; sisa terakhir tercatat 750.
- **Yang masih akurat:** niche home living/kos-kosan, jadwal 09:00/12:30/19:30, kriteria produk §7, ekonomi §8 (komisi 4% + XTRA >5%), §15 sebagai rancangan target (bukan bukti implementasi — dinyatakan eksplisit di §15.11).

### A2. Konfigurasi — PC LIVE, VM BASI (divergensi berbahaya)

| File | Status |
|---|---|
| PC `config.yaml` | **LIVE.** `threads_official_api: LIVE 16 Nov 2026`, token `~/.threads_poster/threads_token.env` (mode 600). `pinterest:` modul siap, `board_id: ""`, `max_pins_per_day: 1`, jadwal 10:00, disclosure `#ad`. `disclosure_wajib: "TIDAK ADA — kata komisi/commission/affiliate DILARANG"`. **Basi:** `facebook:` masih `"RENCANA"` padahal Page sudah terhubung via Affiliate Partnerships 16 Nov 19:41 WIB (verifikasi browser, tidak diverifikasi ulang dalam audit ini). |
| VM `config.yaml` | **BASI v1.** `disclosure_wajib: "#affiliate"`, `facebook: RENCANA`, `threads_official_api: "MENUNGGU — undangan tester belum diterima"`, **tidak ada section `pinterest` sama sekali**. |
| PC `guardrails.md` | **v5, LIVE.** §4: larangan kata komisi/commission/affiliate di semua teks post + catatan risiko (tanpa disclosure ada risiko teguran platform). §4b: Pinterest `#ad` di awal deskripsi. |
| VM `guardrails.md` | **v1, BASI.** §4 masih **mewajibkan** disclosure `#affiliate` / kalimat komisi. Jika VM dipakai sebagai fallback posting, ia akan menegakkan aturan yang sudah dibatalkan Kyan. |
| VM `tools/check_draft.py` | **v4-era.** Masih **mewajibkan** disclosure komisi di thread (`DISCLOSURE_RE`, "Tidak ada disclosure komisi di thread"). Berlawanan dengan PC. |
| PC `tools/check_draft.py` | **v5.** `BANNED_WORD_RE = \b(komisi\|commission\|affiliate)\b`, menolak post yang mengandung kata itu; URL `affiliate_id` dikecualikan. |

### A3. Tools utama (PC) — ADA, 1 BELUM PERNAH LIVE

| Tool | Status |
|---|---|
| `publish_api.py` | **JALAN.** `load_token`, `publish_text`, `publish_media_reply`, poll container → publish → GET permalink. Token tidak pernah dicetak. `USERNAME = "temuanhariann.id"`. |
| `run_slot.py` | **JALAN (mode API).** Flag `--api`, 5x retry saat API, dedup link, guardrail via `check_draft`. Jalur Playwright masih ada sebagai fallback (`threads_poster.poster`) — jalur ini **gagal** 16 Nov 17:20–17:24 (cookie HTTP 429 + "Editor element not found"). |
| `check_draft.py` | **JALAN (v5).** Lihat A2. |
| `publish_video.py` | **SEBAGIAN — belum pernah live.** `probe_video` (ffprobe), `load_qc` (QC JSON 4 item wajib + `--qc-ok`), `build_caption` (hook v5.1 + link di reply), `publish_video` via container `media_type=VIDEO`. **Kunci: Threads API tidak menerima upload file langsung — video harus di-host di URL publik (`--video-url`); tanpa itu live mode ditolak. Hosting publik BELUM ADA.** Log: `data/video_publish_log.json` hanya berisi **1 entri dry-run** (video dummy `/tmp/vidtest/dummy-8s.mp4`, 16 Nov 19:42). |
| `auto_comment.py` | **GAGAL (live), kode ada.** `decode_shortcode` + `resolve_media_id`, template v2 (8 pola, slot `{detail}`/`{bukti}`), `validate_comment` (tolak superlatif/garansi), limit 10/hari, jeda 10–30 mnt, `publish_media_reply` (dukungan reply bermedia). `comment_facebook` / `comment_pinterest` = stub `NotImplementedError`. **2 percobaan live gagal** (lihat A6). |
| `pinterest_api.py` + `run_pinterest.py` | **SIAP, BELUM LIVE.** `POST/GET /v5/pins`, token dari `~/.pinterest_poster/pinterest_token.env`, maks 1 Pin/hari, **abort exit 4 tanpa `image_url`**. Token tidak ada (direktori `~/.pinterest_poster/` tidak ada di PC). Timer `pinterest-1000` **disabled + inactive**. |
| VM `tools/` | **TIDAK LENGKAP.** Hanya `publish_api.py` (versi API), `run_slot.py`, `check_draft.py` (v4), `link_builder.py`, dll. **Tidak ada** `auto_comment.py`, `publish_video.py`, `pinterest_api.py`, `run_pinterest.py`. VM **bukan repo git** (tidak ada `.git`) — hanya salinan file. |

### A4. Template hooks — v5.1 LIVE di PC, BELUM DI-COMMIT

- PC `templates/hooks_{dapur,organizer,kebersihan}.json`: **versi `5.1-hl`, 39 hook/kategori, 9 style** (edukasi 5, hook_pancingan 5, problem_solving 5, social_proof 5, storytelling 5, validasi_mental 5, transformasi 3, urgency 3, controversy 3). Semua berjangkar ulasan/rating/terjual, tanpa nama produk.
- PC `templates/post3_cta_templates.json`: **v5.0, 9 CTA** (fokus baca ulasan + cek detail, tanpa kalimat komisi). `post2_templates.json` ada per kategori.
- **Belum di-commit:** `git status` PC menunjukkan `hooks_*.json` **modified, belum commit** (diff v5.1: +207/−3 baris), 3 file `.bak-20261116` untracked, 3 tools untracked (`check_combo_rate.py`, `merge_new_hooks.py`, `repost_product.py`). HEAD terakhir `4e0c110` (16 Nov 20:31).
- VM: template masih **v4** (guardrail + post3 v4) — divergen dari PC.

### A5. Database produk + link (PC `data/affiliate_links.md`) — ISI ADA, TRACKING CACAT

- **29 link** dalam 3 tabel (dapur 22, organizer 4, kebersihan 3). Header Stats file: Total 29, Used 1, Available 28.
- **Fakta dari isi tabel: USED = 2** (Kikkoman Soy Sauce Dispenser + BONBOX Mop Stick Set), **UNUSED = 27**. **Header Stats basi** — tidak diperbarui setelah post BONBOX 19:35 WIB.
- **Kolom Image URL TIDAK ADA** dalam skema tabel (6 kolom: #, Product, Link, Status, Last Used, Sub-ID). Terisi **0/29**. Ini memblokir Pin Pinterest (abort tanpa gambar) dan komen bermedia.
- **Sub-ID TIDAK UNIK per produk:** semua link dapur memakai `threadsdapur20261116` (22×), organizer `threadsorganizer20261116` (4×), kebersihan `threadskebersihan20261116` (3×). Shopee Click Report hanya bisa membedakan **kategori + tanggal**, bukan produk. EPC per produk **tidak mungkin** dihitung dengan Sub-ID ini (bertentangan dengan Notion §10 checklist + §15.7 unique constraint Sub-ID).
- XTRA: 15 link dapur No. 4–18 terverifikasi via filter dashboard; 10 starter **belum terverifikasi** (hanya bisa dicek dari HP); 4 produk high-ticket Rp100–300rb (dapur No. 19–22) XTRA terverifikasi 12%/10%/5%/15% — produk ini **di luar kriteria organik** (harga >Rp100rb), lane tes terpisah.
- Target Notion §2/§10: 50–100 produk. Aktual 29 — **kurang 21–71 produk**.

### A6. Publishing — Threads JALAN, 2 ANOMALI TERBUKA; FB/Pinterest BELUM

- **Timer systemd PC: 3 aktif** (`threads-affiliate-0900`, `-1230`, `-1930`, enabled). Berikutnya 17 Nov 09:01/12:43/19:47 WIB. Terakhir jalan 16 Nov 19:35 (BONBOX).
- **`data/post_history.json`: 2 post.**
  1. Kikkoman repost, 16 Nov 18:15 WIB (11:15 UTC), `media_id: 18135902441497212`, permalink `.../@temuanhariann.id/post/DfzOch6n5SE` — **receipt lengkap**.
  2. BONBOX Mop Stick, 16 Nov 19:35 WIB — **`media_id: null`, `permalink: null`** — receipt **tidak lengkap** (status "posted" tapi tanpa bukti post ID).
- **Anomali permalink BONBOX (P1, belum terverifikasi):** `logs/cron.log` mencatat "✅ Terkirim" **dua kali** (baris duplikat, 19:35:44) dengan URL `https://www.threads.com/@shopee_harian/post/DfzXk9En8B-` — handle **`@shopee_harian`**, bukan `@temuanhariann.id`, dan shortcode berakhir `-`. `publish_api.py` PC memakai `USERNAME = "temuanhariann.id"` dan permalink diambil dari API GET, jadi URL itu (jika benar dari API) perlu dikonfirmasi: apakah post BONBOX benar-benar terbit, dan di akun mana. Audit ini tidak punya akses browser untuk memeriksanya.
- **ECOCO Cup Washing Brush tidak pernah ter-posting sebagai teks:** `cron.log` menunjukkan produk ini dipilih 3× (18:18, 19:00, 19:22) tanpa satu pun baris "Terkirim" sesudahnya; DB tetap UNUSED — konsisten, tapi 3x pick tanpa post menandakan run yang gagal/dibatalkan tanpa jejak jelas.
- **Jalur Playwright gagal dan ditinggalkan:** 17:20–17:24 WIB cookie HTTP 429 + "Editor element not found after 14s"; 17:51 Kikkoman pertama sukses via API. Guardrail sempat menolak draf BONBOX 18:04 (`[kata-affiliate-dilarang]`) — bukti checker bekerja.
- **Facebook:** Page Temuan Harian (ID 61594139640981) **terhubung ke Shopee via Affiliate Partnerships 16 Nov 19:41 WIB** (verifikasi browser; tidak diverifikasi ulang di audit ini). Status: **0 post, 0 follower** (per Notion §13.4). **Tidak ada tooling Facebook di repo** (hanya stub di `auto_comment.py`). `config.yaml` PC masih menulis `facebook: RENCANA`.
- **Pinterest:** modul kode siap (A3), tapi **belum live**: tidak ada app/token/board, timer disabled. Blokir: website ditunda Kyan (butuh tautan website + Privacy Policy + ikon app untuk form developer). Akun Business "Shopee Harian" @215kyan sudah jadi; tagging produk native tetap manual di aplikasi.

### A7. Auto-komen — GAGAL 2×, AKAR MASALAH TERBUKTI

- Percobaan 1 (20:08 WIB): `reply_to_id` = shortcode `DfctjUKkmhz` → API 400 (objek tidak ada) + 500 (bukan valid threads_media ID). 0 terkirim.
- Percobaan 2 (20:31 WIB): `reply_to_id` = hasil decode base64 shortcode `4025292505889269875` → error identik. 0 terkirim.
- **Bukti penentu:** shortcode decode **bukan** ID media API — repost Kikkoman shortcode `DfzOch6n5SE` decode = `4031629624640246916`, sedangkan `media_id` API aslinya `18135902441497212`.
- Penyebab blokir: Threads API `/keyword_search` mengembalikan **403** (app belum App Review); membaca postingan orang lain butuh Advanced Access `threads_basic`. Keputusan App Review **belum diambil Kyan** (opsi sudah diajukan, belum dijawab).
- Pilot repo privat `molkex/threads-private-api`: **DITOLAK** — tidak ada metode login, tidak ada signing daemon (127.0.0.1:8643 tidak disertakan), klaim "unauthenticated discovery" terbukti salah (`login_required`), lisensi proprietary.
- `data/comment_history.json`: **2 entri, keduanya `failed`**. Playwright untuk auto-komen: ditanyakan Kyan 20:33 WIB ("pakai playwright bisa?") — dijawab "bisa, dengan risiko checkpoint/limit akun", **belum diputuskan/dibangun**.

### A8. Video UGC — PRODUKSI JALAN, DISTRIBUSI BELUM

- **17 brief UGC** (`data/video_briefs/*-ugc.md` + ECOCO redo): 1 video/produk, gaya HP + VO 1 kalimat, standar di `GAYA-UGC.md` + `TEMPLATE-FLOW-UGC.md` (template adaptasi prompt Kyan, 16 Nov 23:26 — prompt asli 30 detik/5 scene/wajah dinilai tidak cocok untuk Flow).
- **5/15 lolos QC** (Kotak Es v2, ZuoShu Keset, Pplus Pisau, APEN Pengasah, EASLIVVO Timbangan). File di VM `data/videos/` (total 38 MB, 14 file .mp4 — termasuk yang **ditolak**: klip landscape ECOCO v1, spare klip2 Panda v1, Kotak Es v1 cacat teks "9:16").
- **2 produk pending foto** (Greenland Tudung Saji, Qiek Deep Fryer) — Shopee anti-bot dari VM; brief berisi peringatan jangan generate sebelum foto ada.
- **Kredit Flow: 750** (terakhir tercatat 16 Nov 21:29 WIB; reset 22 Nov 17:37, no rollover). Perkiraan kebutuhan sisa antrean: 10 produk × 20 = 200 kredit — cukup.
- **Pelajaran tercatat:** literal "9:16" di prompt ikut ter-render jadi teks (Kotak Es v1); foto landscape sebagai first-frame literal = letterbox + teks listing; Flow kadang menawarkan Omni 1.2 Flash 30 kredit (tolak, pakai Veo 3.1 Fast 20). Semua prompt UGC sudah dibersihkan dari literal "9:16".
- **Distribusi video: 0 terbit.** Belum satu pun video UGC dipublikasikan ke Threads/Facebook/Pinterest (publish_video.py hanya dry-run; hosting publik belum ada).

### A9. Tracking / analytics — HAMPIR TIDAK ADA (semua metrik North Star UNKNOWN)

| Data | Status |
|---|---|
| Impressions / views / clicks (Threads) | **UNKNOWN** — Threads Insights tidak pernah ditarik. |
| Klik Shopee (Click Report) | **UNKNOWN** — dashboard Shopee tidak pernah dicek setelah posting. |
| Orders / validated commission | **UNKNOWN** — tidak ada data. |
| EPC, conversion rate, net earnings, ROAS | **UNKNOWN** — tidak bisa dihitung (pembilang + penyebut tidak ada). |
| Biaya konten | Diketahui sebagian: Flow 300 kredit terpakai dari 1.050 (1.050→750); biaya uang Rp0 (kredit PRO). |
| Product scoring (Notion §15.4, bobot 20/20/20/15/10/10/5) | **Tidak diimplementasikan** — tidak ada kode scoring; hanya hitungan break-even di `docs/sistem-video-ugc-v2.md` (ilustratif: Rp100rb × 4% → EPC Rp80/klik pada CVR 2%). |
| Content library / content_id / eksperimen | **Tidak ada** — tidak ada pemetaan content ↔ product ↔ publication ↔ asset; tidak ada eksperimen tercatat. |
| Laporan mingguan (Notion §13/OS §13) | **Belum ada** — yang ada: cron riset produk mingguan (lihat A10), bukan laporan performa. |
| Yang tercatat | `post_history.json` (2 post, 1 receipt tidak lengkap), `video_publish_log.json` (1 dry-run), `comment_history.json` (2 gagal), `logs/cron.log` (jejak run 16 Nov), laporan riset `docs/riset-mingguan/riset-2026-11-16.md`. |

### A10. Jadwal & riset berkala

- Cron VM `riset-shopee-mingguan`: **enabled, Senin 08:15 WIB**, laporan pertama 16 Nov 2026 (`docs/riset-mingguan/riset-2026-11-16.md` di VM). Tidak ada cron affiliate lain di VM (posting jalan via systemd PC, bukan cron VM).

### A11. Keamanan — BERSIH (dengan catatan)

- **Tidak ada token/secret yang ter-commit.** Pemindaian `git log --all -p` (PC): yang cocok pola hanya referensi kode dan placeholder (`PINTEREST_ACCESS_TOKEN=<redacted>` sebagai nama env, `YOUR_RAPIDAPI_KEY`, `access_token` sebagai nama field). **Tidak ada nilai token, password, cookie, atau API key di HEAD maupun histori.** (Catatan: ini pemindaian berbasis pola grep, bukan secret-scanner khusus.)
- `.gitignore` PC mencakup `*token*.env`, `*token*.json`, `data/affiliate_links.md`, `data/post_history.json`, `data/pinterest_history.json`, `data/comment_history.json`, `data/video_publish_log.json`, `logs/`, `cookies/`. **`.gitignore` VM tidak mencakup** `*token*.env`, `data/comment_history.json`, `data/video_publish_log.json`, `data/pinterest_history.json` — VM bukan repo git sehingga saat ini tidak ada risiko commit dari VM, tapi file `.gitignore` VM akan bocor jika VM dijadikan repo.
- Token Threads di PC: file `~/.threads_poster/threads_token.env` **mode 600, ada**. Nilai token **tidak dibaca/ditampilkan** dalam audit ini. Direktori `~/.pinterest_poster/` **tidak ada**.
- Affiliate ID `11369851901` tampil di URL publik — by design (parameter `affiliate_id` wajib untuk atribusi).

---

## PHASE B — Gap analysis

| Komponen | Kondisi Aktual | Target (Notion / prompt OS) | Gap | Prioritas |
|---|---|---|---|---|
| Analytics / EPC | Semua metrik UNKNOWN: tidak ada impressions, klik, order, komisi yang tercatat | North Star: Net Earnings, EPC, Conversion Rate, Validated Commission (§15.6: dashboard minimum + funnel) | Tidak ada sumber data yang terhubung (Threads Insights + Shopee Click Report belum pernah ditarik); Sub-ID tidak unik per produk sehingga EPC per produk tidak mungkin | **P0** |
| Sub-ID tracking | 1 Sub-ID per kategori (22× dapur, 4× organizer, 3× kebersihan) | Sub-ID unik per publikasi; dapat dipetakan ke publication + laporan klik (§10, §15.7) | Perlu skema Sub-ID per produk (dan per platform), + migrasi 29 link yang sudah ada | **P0** |
| Distribusi video | 5 video lolos QC, 0 terbit; `publish_video.py` butuh URL publik, hosting belum ada | 1 produk → 1 video → Threads + FB + Pinterest (§13 v2, §15.3 tahap 8) | Butuh hosting publik video (landing page shopeeharian.my.id ditunda; alternatif sementara diperlukan) + 1 uji live end-to-end | **P0** |
| Disclosure / compliance | Kyan melarang kata affiliate/komisi di teks post (PC v5); Notion §13.5/§15.8 menuntut disclosure tidak boleh dihapus; platform mewajibkan disclosure hubungan berbayar | Disclosure jelas + patuh platform + hukum (§15.8) | Keputusan belum diambil: format disclosure apa yang dipakai tanpa kata terlarang (mis. `#ad` / "link berbayar" di luar teks post, atau disclosure di bio/profil) — risiko teguran Shopee/Threads/Meta | **P0** |
| Divergensi VM ↔ PC | VM: config v1, guardrails v1, check_draft v4 (wajib disclosure komisi), tanpa modul Pinterest/video/auto-komen; PC: v5/v5.1 | Satu sumber konfigurasi yang sama di semua mesin (§15.2: agent berbagi database yang sama) | Sinkronisasi VM ← PC (atau tetapkan PC sebagai satu-satunya mesin posting dan VM hanya produksi video); v5.1 hooks belum di-commit di PC | **P0** |
| Pinterest live | Modul kode siap; 0 token, 0 board, timer disabled, Standard access belum diajukan | 1 Pin/hari via API v5 + tagging native manual (§13.4, §15.9 P2) | Website + Privacy Policy + ikon app (website ditunda Kyan); board home living; isi kolom Image URL (0/29); ajukan Standard access | **P0** |
| Kill switch + backup | Tidak ada kill switch di kode/config (hanya disebut sebagai konsep pinjaman di AUDIT-nerin81.md); tidak ada backup DB/token yang terdokumentasi | Kill switch global + per-channel, teruji; backup DB + secret recovery (§15.8, §15.10) | Implementasi `DISABLE_*` + prosedur backup/restore; uji matikan timer | **P0** |
| Receipt BONBOX | Post tercatat "posted" tanpa media_id/permalink; cron.log menunjukkan permalink `@shopee_harian/post/DfzXk9En8B-` (handle tidak cocok) + baris "Terkirim" duplikat | Setiap publikasi punya receipt lengkap + post ID (§15.3 tahap 8, §15.7 publications) | Verifikasi manual: buka URL-nya, pastikan post ada dan di akun yang benar; perbaiki pencatatan receipt di `run_slot.py` | **P1** |
| DB produk | 29 link (target 50–100); header Stats basi (Used 1 vs aktual 2); tanpa kolom Image URL; tanpa ID produk stabil | DB rapi, ID stabil, sumber + waktu cek tercatat (§15.9 P0) | Tambah 21+ produk; perbaiki Stats; tambah kolom Image URL + product ID; isi 29 URL gambar | **P1** |
| Auto-komen | Gagal 2× live; root cause terbukti (shortcode ≠ media ID); butuh App Review/Advanced Access; Playwright ditawarkan, belum diputuskan | Komen relevan, terbatas, sesuai API/kebijakan, tanpa link (§15.8) | Keputusan Kyan: ajukan App Review, atau parkir auto-komen dan fokus posting + video | **P1** |
| Facebook | Terhubung (Affiliate Partnerships), 0 post, tanpa tooling; config masih "RENCANA" | Upload video + tagging native Shopee; 1 produk 1 video ke semua platform | Buat alur publikasi FB (manual via "Buat reel" dulu, atau tooling); update config | **P1** |
| Product scoring | Tidak ada implementasi | Skor 0–100 + coverage + UNKNOWN (§15.4) | Implementasi scoring di atas DB (tanpa mengarang data hilang) | **P1** |
| Content library + eksperimen | Tidak ada content_id / pemetaan konten ↔ produk ↔ publikasi | Setiap konten punya content_id, hook, angle, asset, Sub-ID (§15.5) | Skema penamaan + pencatatan di post_history/video log | **P1** |
| AI drafting | Template statis v5.1 (bekerja); drafting AI via 9Router belum ada | AI drafting fase 2 (§11) | Opsional — template sudah bekerja; AI drafting bukan pemblokir cuan | **P2** |
| Shopee Open API | Tetap tertahan (AppID/Secret kosong, Apply nonaktif; Kyan melarang minta via CS) | `productOfferV2` + `generateShortLink` gantikan isi manual (§11) | Tidak ada jalur saat ini; DB manual tetap jalan | **P2** |
| Landing page | Ditunda Kyan ("nanti dulu", mau mirip jagonya.my.id); domain shopeeharian.my.id direncanakan 20 Nov 2026 | Landing page sebagai tujuan link + hosting video (§11, §13.4) | Bangun setelah video hosting diputuskan; domain belum dimiliki | **P2** |
| Laporan mingguan | Hanya cron riset produk (Senin 08:15); belum ada laporan performa | Laporan mingguan 12 poin (§13 prompt OS) | Tunggu data analytics ada dulu — laporan tanpa data = kosong | **P2** |
| Meta Ads | Belum dimulai (benar — menunggu pemenang organik) | Hanya boost video organik pemenang, persetujuan manusia (§15.8, §15.9 P3) | Tidak ada aksi sampai ada EPC positif | **P3** |
| Threads `/keyword_search` 403 | Target auto-komen harus dicari manual | App Review / Advanced Access | Tergantung keputusan auto-komen (P1) | **P3** |

**Ringkasan hitung komponen:** JALAN 8 (API Threads posting, timer 3 slot, guardrail v5 PC, hook v5.1, link builder + DB isi, brief + QC video, modul Pinterest kode, cron riset mingguan) · SEBAGIAN 6 (DB tracking, video distribusi, Facebook, receipt posting, Notion, VM/PC sync) · BELUM 7 (Pinterest live, analytics/EPC, scoring, kill switch, AI drafting, landing page, Meta Ads) · GAGAL 2 (auto-komen live 2×, jalur Playwright posting).

---

## PHASE C — Rencana implementasi (per prioritas, tanpa eksekusi)

### P0 — memblokir uang/cuan

1. **Analytics dulu, sebelum scale.** (a) Tarik Shopee Click Report per Sub-ID kategori (manual, dari dashboard — akun tidak diblokir, HP/manual jalan) dan catat klik/order/komisi per tanggal di file `data/performance.csv` (atau tabel sederhana). (b) Tarik Threads Insights per post (views/likes/replies) untuk 2 post yang sudah terbit. (c) Baru setelah itu hitung EPC per kategori. Tanpa langkah ini, semua optimasi berikutnya buta.
2. **Perbaiki Sub-ID.** Skema baru: `threads<kategori><produk-singkat><yyyymmdd>` (huruf+angka, tanpa hubung, ≤ batas Shopee) — 1 Sub-ID = 1 produk = 1 publikasi. Regenerasi 29 link dengan `tools/link_builder.py`, simpan pemetaan lama→baru, dan catat di DB. (Perhatian: link lama yang sudah ter-posting — Kikkoman, BONBOX — jangan diubah; Sub-ID baru berlaku untuk post berikutnya.)
3. **Hosting video sementara.** Sampai landing page jadi, pilih satu: (a) upload video ke host publik sementara yang tahan lama (mis. file statis di hosting yang sudah dimiliki Kyan) lalu uji 1 video live via `publish_video.py` ke Threads; atau (b) posting video manual via aplikasi Threads/Facebook dulu sambil menunggu landing page. Jangan generate video baru untuk produk yang videonya belum terbit.
4. **Putuskan disclosure.** Ajukan ke Kyan 3 opsi: (a) `#ad` di awal post 2 (bukan kata "affiliate"/"komisi"), (b) disclosure di bio + "link berbayar" di post, (c) tetap tanpa disclosure dengan risiko teguran tercatat. Setelah diputuskan, update PC `guardrails.md` + `check_draft.py` + Notion §7/§13.5 — dan sinkronkan ke VM.
5. **Sinkronisasi VM ← PC + commit.** Commit v5.1 hooks + 3 tools untracked di PC (`git add` + commit + push). Salin `config.yaml`, `guardrails.md`, `check_draft.py`, dan tools baru PC ke VM; tetapkan secara tertulis: **PC = mesin posting, VM = mesin produksi video** (atau sebaliknya) — jangan dua mesin posting dengan aturan berbeda.
6. **Pinterest — buka blokir bertahap.** (a) Buat board home living/kos-kosan di aplikasi Pinterest. (b) Isi kolom Image URL di DB (butuh 29 URL gambar — foto sudah ada di `data/product_images/` untuk 14 produk dapur). (c) Selesaikan website + Privacy Policy (prasyarat form developer), submit app, simpan Trial token mode 600, uji 1 Pin dry-run → live. (d) Ajukan Standard access (video demo OAuth) agar Pin terlihat publik.
7. **Kill switch + backup.** Tambah `DISABLE_POSTING` di `config.yaml` yang dibaca `run_slot.py` (tolak posting bila aktif) + perintah manual `systemctl --user stop` terdokumentasi; backup `data/affiliate_links.md` + `data/post_history.json` ke VM setiap selesai posting (salinan bertanggal); simpan instruksi pemulihan token (Secure Vault) di luar repo.

### P1 — perbaiki dalam minggu ini

8. **Verifikasi BONBOX.** Buka permalink dari `cron.log`, konfirmasi post ada + akun benar; bila URL salah, cari post sebenarnya lewat profil dan perbaiki `post_history.json` (isi `media_id` + `permalink`); perbaiki `run_slot.py` agar receipt selalu menyimpan keduanya; selidiki kenapa baris "Terkirim" tercatat dua kali.
9. **Rapikan DB.** Perbaiki header Stats (Used 2 / Available 27); tambah kolom Image URL + Product ID; tambah produk sampai 50 (dari pick-list + riset mingguan); catat sumber + tanggal cek per produk (rating/harga/XTRA).
10. **Keputusan auto-komen.** Kyan memilih: (a) siapkan materi App Review `threads_basic`, atau (b) parkir auto-komen. Jika (a): siapkan screencast + justifikasi; jika (b): hapus `auto_comment.py` dari jalur otomatis (tetap arsip) agar tidak ada yang menjalankan ulang.
11. **Facebook pertama.** Posting 1 Reel manual (video UGC Kotak Es v2) via "Buat reel" di Page Temuan Harian + tag produk Shopee native; catat hasilnya; baru putuskan apakah perlu tooling FB.
12. **Scoring + content library.** Implementasi scoring Notion §15.4 di atas DB (skor + coverage + UNKNOWN, tanpa mengarang); beri setiap publikasi `content_id` (`<produk>-<platform>-<tanggal>`) dan catat di `post_history.json`.

### P2 — setelah P0/P1 jalan

13. **AI drafting (9Router).** Gantikan template statis secara bertahap — checker tetap jalan; uji A/B 1 slot/hari template vs AI selama 1 minggu, bandingkan dari data (bukan perasaan).
14. **Shopee Open API.** Tetap tertahan; cek ulang status akses tiap bulan; jangan buang waktu ke CS (Kyan melarang).
15. **Landing page.** Bangun mirip jagonya.my.id setelah domain shopeeharian.my.id diambil (20 Nov); sertakan Privacy Policy (membuka blokir Pinterest) + hosting video (membuka blokir distribusi video).
16. **Laporan mingguan otomatis.** Setelah analytics (P0-1) punya 1 minggu data, buat template laporan 12 poin prompt OS §13 dari data aktual.

### P3 — hanya bila ada pemenang organik

17. **Meta Ads.** Hanya untuk video dengan EPC positif + klik Shopee jalan (gate di `docs/sistem-video-ugc-v2.md`); budget + audience + creative selalu persetujuan manusia; nilai di EPC Shopee, bukan ROAS Meta.

---

## Lampiran — angka kunci (terverifikasi)

- Link: 29 (22 dapur / 4 organizer / 3 kebersihan) · USED 2 · UNUSED 27 · Image URL 0/29 · Sub-ID unik per produk: 0
- Post Threads: 2 (Kikkoman repost DfzOch6n5SE, BONBOX 19:35 — receipt tidak lengkap)
- Hook: v5.1, 39/kategori, 9 style · CTA v5.0, 9
- Video: 17 brief UGC · 5/15 lolos QC · 0 terbit · kredit Flow 750 (reset 22 Nov 17:37)
- Timer Threads: 3 aktif · Pinterest timer: disabled · Cron riset: Senin 08:15, aktif
- Auto-komen: 0 terkirim (2 gagal) · Komentar FB/Pinterest: stub
- EPC / klik / order / komisi / impressions: **UNKNOWN semua**
- Keamanan: 0 secret ter-commit (pola grep atas `git log --all -p`); token Threads mode 600 di PC; VM `.gitignore` belum mencakup `*token*.env`

## Yang tidak diverifikasi dalam audit ini

- Apakah post BONBOX benar-benar tampil di Threads (dan di akun mana) — butuh buka URL.
- Status koneksi Facebook Page saat ini (terakhir terverifikasi 16 Nov 19:41 WIB via browser).
- Sisa kredit Flow saat ini (terakhir tercatat 750, 16 Nov 21:29 WIB — panel Flow bisa berubah).
- Isi Shopee Click Report / komisi aktual (belum pernah dibuka dalam audit ini).
