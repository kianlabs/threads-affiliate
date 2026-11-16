# Referensi GitHub — Sistem Otomasi Affiliate Shopee → Threads

- **Tanggal survey:** 16 Nov 2026
- **Tujuan:** referensi seluas mungkin untuk sistem otomasi affiliate Shopee → Threads Kyan (@temuanhariann.id), gratis, full-auto.
- **Metode:** 6 query GitHub API Search (tanpa auth) + baca README mentah (raw.githubusercontent.com) dari repo yang paling relevan. Kode tidak dibaca dalam-dalam kecuali dinyatakan — yang dinilai adalah arsitektur, pola, dan klaim README.
- **Yang TIDAK diulang di sini:** audit mendalam `d4ncboz/threads-affiliate` (basis v1) ada di `AUDIT.md`; audit `nerin81-netizen/threads-affiliate-automation` ada di `AUDIT-nerin81.md`. Keduanya hanya dirujuk singkat.

## 0. Hasil pencarian — total per query

| Query | Total repo |
|---|---|
| `shopee affiliate` | 471 |
| `threads auto poster` | 45 |
| `threads affiliate` | 84 |
| `affiliate landing page` | 785 |
| `shopee api` | 498 |
| `threads api` | 4.603 (mayoritas noise: threading pemrograman, bukan Meta Threads) |

**Koreksi penting soal "banyak repo":** angka besar itu menyesatkan. Dari 471 hasil `shopee affiliate`, kebanyakan jalurnya Telegram / WhatsApp / Facebook Reels / TikTok, atau negaranya Vietnam / Brazil. Dari 84 hasil `threads affiliate`, peringkat teratas termasuk `helicon` (ekstensi VS Code untuk Muse Code CLI — noise kata "threads"), bot detektor spam Reddit, dan `nerin81` yang ternyata **bukan Shopee sama sekali** (repo Korea untuk Toss — lihat `AUDIT-nerin81.md`). **Repo yang benar-benar Shopee + Threads auto-posting hanya ±6:** d4ncboz, faustzaki, msyamsularif, Agelakz (taktik spam — lihat §3), momokii (playbook, tanpa kode), dan AffiSocAI (multi-platform, lisensi privat).

## 1. Basis v1 (sudah diaudit — ringkasan saja)

### d4ncboz/threads-affiliate — https://github.com/d4ncboz/threads-affiliate
- 47★ · Python · MIT · update 19 Okt 2026 · repo teman Kyan (D4NNBOZ, @jagonya_shopee, jagonya.my.id).
- Basis v1 kami. Playwright + cookie sesi IG/Threads, database link Markdown manual, template hook (9 gaya × 3 varian), rotasi kategori, dedup (link tidak dipakai ulang, kemiripan hook ≤60% vs 5 post terakhir), jadwal 08:00/13:00/20:00 WIB, maks 3 post/hari.
- Audit menemukan: bug paste Linux (Meta+v hardcode — SUDAH diperbaiki di v1), template berisi klaim review palsu (SUDAH ditulis ulang), tanpa disclosure otomatis, tanpa batas 500 karakter, verifikasi posting lemah. Detail: `AUDIT.md`.

### nerin81-netizen/threads-affiliate-automation — https://github.com/nerin81-netizen/threads-affiliate-automation
- 77★ · JavaScript/Node · MIT · update 12 Nov 2026 · **BUKAN Shopee** — repo Korea untuk affiliate Toss (0 kata "shopee" di seluruh repo; star-nya nyata, pencarian GitHub yang menipu).
- Konsep yang dipinjam (bukan kode): modul Graph API `threads_api.mjs` (fase 2, butuh tambah reply), `publish_guard.mjs` (idempotensi anti-double-post), pola `safety_guard.mjs` (kuota + kill switch), insights per jam, pola generate-then-filter. Ditolak: bot Playwright + evasion, auto-follow/like/reply, template Toss. Detail: `AUDIT-nerin81.md`.

## 2. Posting / publishing ke Threads

### yanstd888/threads-auto-poster — https://github.com/yanstd888/threads-auto-poster
- 61★ · TypeScript (Next.js + SQLite) · Apache-2.0 · update 12 Nov 2026 · v0.3.3.
- Scheduler Threads self-hosted: riset dari source registry HTTPS yang disetujui, drafting dibantu AI (opsional, via Hermes Agent CLI), approval manusia sebagai default, kill switch aktif sejak instalasi, token Threads terenkripsi di SQLite, backup/restore SQLite.
- **Konsep yang layak dipinjam:** (1) *Reply Agent* dengan atomic claim + verifikasi reply yang terbit + kebijakan per-akun (`once` / `continuations_only`) — pola klaim atomik ini sama dengan publish guard; (2) hasil `publish_unknown` TIDAK pernah di-blind-retry; (3) mode default aman (approval + kill switch ON) lalu otomatisasi diaktifkan bertahap setelah workflow terverifikasi — ini pola deployment yang benar untuk v1 kami (uji `--headed` dulu, baru cron); (4) source registry: konten harus mengutip sumber yang disetujui.
- **Hindari / catatan:** approval manusia adalah default dan inti desainnya — berlawanan dengan full-auto Kyan (kami menggantinya dengan guardrails otomatis); butuh Meta app + OAuth callback HTTPS publik + App Review; stack Next.js + SQLite, bukan Python.

### gitroomhq/postiz-app — https://github.com/gitroomhq/postiz-app
- ±41.000★ (per pengecekan 16 Nov 2026) · TypeScript (Next.js + NestJS + Prisma + PostgreSQL + Redis + Temporal) · AGPL-3.0.
- Platform manajemen media sosial: scheduling + analitik + AI copilot, 14 channel termasuk Threads, publikasi lewat OAuth resmi tiap platform, public API + MCP + CLI + node n8n. Self-host gratis selamanya (AGPL); Postiz Cloud berbayar.
- **Konsep yang layak dipinjam:** scheduler multi-channel + API publik sebagai permukaan otomasi (sistem kita bisa memanggil API-nya, bukan membangun scheduler sendiri) — kandidat fase 2 untuk jalur API resmi.
- **Hindari / catatan:** stack berat (Postgres + Redis + Temporal); self-host butuh bikin Meta app sendiri + approval (bisa berminggu-minggu); lisensi AGPL (kalau dimodifikasi dan dijalankan sebagai layanan, perubahan harus dibagikan); Postiz Cloud sempat shutdown karena insiden keamanan Okt 2026 (alasan lain untuk self-host, bukan cloud).

### trypostit/trypost — https://github.com/trypostit/trypost
- 888★ · AGPL-3.0 · update 16 Nov 2026.
- Scheduler open-source "dibangun untuk AI agent": MCP server (80+ tools) + REST API, publikasi lewat API resmi 13 network termasuk Threads, antrean per channel (set jam posting sekali, post mengambil slot bebas berikutnya), workflow approval, webhook saat post terbit/gagal, insights.
- **Konsep yang layak dipinjam:** (1) model *queue-slot* — lebih lentur dari cron jam tetap (cocok digabung dengan randomisasi faustzaki, §4); (2) permukaan MCP/REST untuk agen — sistem kita bisa menjadi "agen" yang menulis ke antrean TryPost; (3) approval sebagai workflow kelas satu + webhook publish/gagal (notifikasi ke owner).
- **Hindari / catatan:** sama seperti Postiz — AGPL + stack berat + butuh Meta app sendiri; ini alternatif fase 2, bukan basis v1.

### paulosabayomi/ThreadsPipe-py — https://github.com/paulosabayomi/ThreadsPipe-py
- 9★ · Python · MIT · `pip install threadspipepy` (PyPI).
- Library Python untuk API resmi Meta Threads: buat post, **balas post/reply (`reply_to_id`)**, ambil post + insights akun, sembunyikan reply, cek kuota (termasuk kuota reply). Otomatis memecah teks >500 karakter menjadi thread berantai dan media >20 file menjadi batch. Auth OAuth (short-lived 1 jam + long-lived 60 hari).
- **Konsep yang layak dipinjam — PALING RELEVAN UNTUK FASE 2:** ini kandidat publisher API resmi untuk stack Python kami. Berbeda dari modul `threads_api.mjs` nerin81 yang *sengaja tidak bisa reply*, library ini mendukung `reply_to_id` — persis yang dibutuhkan pola Kyan (link di self-reply). Juga ada pengecekan kuota reply dan pemecah 500 karakter bawaan.
- **Hindari / catatan:** proyek kecil (9★) — kualitas kode belum diaudit; verifikasi dulu (`pip install` + tes `--check`-style) sebelum dipakai; tetap butuh undangan tester diterima + App Review `threads_content_publish`.

### msyamsularif/affiliate-threads-generator — https://github.com/msyamsularif/affiliate-threads-generator
- 2★ · Python · MIT · update 13 Okt 2026 · plugin Hermes Agent.
- Google Sheets → riset AI → draf → **approval manusia wajib** → publish via API resmi Threads Graph API → tulis Status=Done + URL Threads. Aturan non-negotiable yang ditegakkan kode: scheduler tidak pernah publish; klaim first-hand hanya bila ada testimoni tersimpan; bahasa garansi diblokir ("dijamin", "100% ampuh", "pasti sembuh"); satu topic tag, hashtag liar ditolak; publish gagal tidak pernah mengubah Status; anti-slop audit + naturalization; metrik Threads mingguan ke tab Metrics.
- **Konsep yang layak dipinjam:** (1) "AI creates, code validates, human approves" — untuk Kyan, approval manusia diganti guardrails otomatis (`check_draft.py` kami adalah padanan `guardrails.py` mereka); (2) Sheet sebagai state lock (tanpa DB terpisah) + publish tool yang memvalidasi ulang state sebelum posting; (3) larangan klaim first-hand tanpa testimoni tersimpan — ini aturan yang sama dengan larangan klaim "review" kami, ditegakkan di level publish tool, bukan sekadar template; (4) blok bahasa garansi + validasi topic tag di kode.
- **Hindari / catatan:** butuh Hermes Agent + gateway Telegram + Google Sheets + token Threads long-lived; approval wajib membuatnya bukan full-auto apa adanya (perlu melepas gate approval seperti rencana fase 2 kami).

### faustzaki/threads-affiliate-bot — https://github.com/faustzaki/threads-affiliate-bot
- 0★ · Python + Playwright + SQLite + Notion · MIT · update 31 Okt 2026 · repo Indonesia.
- Bot auto-posting Threads untuk affiliate Shopee. Fitur: randomization engine (jadwal dibangkitkan ulang tiap hari, 12% hari libur, 38% 1 post, 50% 2 post, window 09:00–22:30, jeda min 3 jam, 10% skip), anti-AI caption engine (DNA 441.000 kombinasi + detektor AI 10 pola termasuk em-dash, skor 0–100), quality gate (tolak engagement bait, shortener, tracking param, klaim tanpa dasar "udah gue pake 2 minggu"), image lifecycle (batas pakai per jenis gambar), publish safety (atomic claim + `publish_unknown` tanpa blind-retry), Notion 2-arah + autofill dari 1 URL, notifikasi Telegram (auto-post bila skor ≥90 dan AI 0).
- **Penting: LLM-nya lewat 9Router lokal** — `.env` contoh memakai `NINEROUTER_URL=http://127.0.0.1:20128/v1` (port yang sama persis dengan 9Router di PC Kyan) + `SHOPEE_AFFILIATE_ID`. Pola "LLM lewat endpoint 9Router lokal" ini langsung reusable untuk AI drafting fase 2 kami.
- Riset sendiri (scrape 95 post Threads): format "spill" menang (reply:like 3:1–5:1), `ootd` 18× `fashion`/`outfit`, panjang optimal 80–130 karakter.
- **Konsep yang layak dipinjam:** (1) randomisasi jadwal harian + hari libur + jitter — pengganti cron jam tetap kami; (2) detektor AI berbahasa Indonesia + skor kualitas — perkuat `check_draft.py`; (3) quality gate yang menolak klaim tanpa dasar; (4) image lifecycle dengan batas pakai; (5) auto-post berskor (≥90 + AI 0) sebagai jembatan antara approval penuh dan full-auto.
- **Hindari / catatan:** jujur soal batasnya — tidak bisa scrape produk Shopee (anti-bot: 403, login wall, signature), tidak bisa auto-generate gambar andal, tidak auto-komen di post orang; produk/komisi harus manual dari dashboard (sama seperti v1 kami).

### ibrahimakcayy/Selenium-Multi-Platform-Auto-Poster — https://github.com/ibrahimakcayy/Selenium-Multi-Platform-Auto-Poster
- 7★ · Python (Selenium) · update 3 Agu 2026.
- Satu script posting ke X, Instagram, Facebook, Threads, Bluesky; login berbasis sesi (kecuali Threads — "not the full version").
- **Konsep yang layak dipinjam:** fan-out satu post → banyak platform (sama seperti AffiSocAI).
- **Hindari / catatan:** Selenium lebih lambat dan lebih mudah terdeteksi daripada Playwright (basis d4ncboz sudah lebih baik); dukungan Threads tidak penuh; tidak ada guardrails yang terlihat.

### junhoyeo/threads-api (+ threads-py) — https://github.com/junhoyeo/threads-api
- 1.621★ · TypeScript · **DIARSIPKAN — JANGAN DIPAKAI.**
- Client tidak resmi hasil reverse-engineering untuk Threads (login password IG). Pengembangan dihentikan 8 Sep 2023 setelah Meta mengirim pemberitahuan (cease-and-desist); repo diarsipkan dan tidak lagi dirawat.
- **Hindari total:** mati + sudah ditegur Meta secara langsung. Jangan jadikan dependensi atau referensi implementasi. Gunakan API resmi (ThreadsPipe-py / modul nerin81) untuk fase 2.

## 3. Sisi Shopee (API, link, riset produk)

### bcat95/shopee-aff — https://github.com/bcat95/shopee-aff
- 112★ · dokumentasi (PHP/Node + Postman) · update 16 Nov 2026 · repo Vietnam, berbahasa Vietnam.
- Referensi API Shopee Affiliate terlengkap yang ditemukan: (1) **Open API resmi** — auth `app_id` + `secret_key` (+ signature), endpoint REST `product_item_get` / `product_search` / `product_item_recommend_get`, GraphQL `shopOfferV2` / `productOfferV2` (sortir komisi tertinggi, filter Mall/Preferred, `isAMSOffer` untuk komisi seller), mutation `generateShortLink`, `conversionReport` / `validatedReport`; (2) **Data API tidak resmi** `data.addlivetag.com` — product data, offers, market search, riwayat harga/komisi (cache 3 jam / 10–30 mnt), auth `X-API-Key` (wajib sejak 01/10/2026).
- **Konsep yang layak dipinjam:** dokumentasi endpoint fase 2 kami (productOfferV2 + generateShortLink + conversionReport) + contoh kode PHP/Node + koleksi Postman. Data API adalah *fallback riset* yang mungkin (data produk + harga/komisi historis) — tapi dicatat eksplisit sebagai tidak resmi, untuk belajar/riset/internal non-komersial, dan sekarang butuh key sendiri.
- **Hindari / catatan:** dokumentasi Vietnam (endpoint `affiliate.shopee.vn` / `open.shopee.vn`) — endpoint ID adalah `open-api.affiliate.shopee.co.id/graphql` (sudah terverifikasi hidup dari VM kami, 16 Nov 2026); semua tetap butuh `app_id` + `secret_key` yang akun Kyan **belum punya** (Apply nonaktif, link "contact us" nyasar ke artikel pelanggaran).

### nsiregar/shpee (+ shpee-js) — https://github.com/nsiregar/shpee
- 7★ · Python · MIT · update 27 Okt 2026 (shpee-js: 7★, update Jan 2024).
- Wrapper minimal Shopee Affiliate API: `ShopeeAffiliate(app_id, app_secret).shortlink(url, sub_ids)` → response httpx. Hanya mendokumentasikan shortlink.
- **Konsep yang layak dipinjam:** bentuk client fase 2 yang paling sederhana (app_id + secret + sub_ids untuk tracking per post) — padanan Python dari `generateShortLink`.
- **Hindari / catatan:** README sangat minimal (653 byte) — tidak ada productOfferV2 / laporan; verifikasi dulu apakah wrapper ini masih jalan sebelum dipakai; tetap butuh kredensial API yang belum ada.

### crushedmonster/shopee-affiliate-link-generator — https://github.com/crushedmonster/shopee-affiliate-link-generator
- 8★ · HTML · MIT · update 28 Okt 2026.
- Tool statis sederhana: tempel URL produk + masukkan affiliate ID → generate link affiliate, tombol copy.
- **Konsep yang layak dipinjam:** hanya idenya — generate link dari URL produk + affiliate ID bisa dilakukan client-side tanpa server.
- **Hindari / catatan:** tidak ada validasi produk, tanpa Sub-ID, tanpa kriteria — bukan sistem, hanya utilitas satu fungsi.

### mariaeduarda2212/shopee-affiliate-whatsapp-bot — https://github.com/mariaeduarda2212/shopee-affiliate-whatsapp-bot
- 16★ · JavaScript (WPPConnect + Puppeteer) · Brazil.
- Bot WhatsApp: generate link affiliate Shopee (API Brasil) + kirim promo terformat ke grup.
- **Pelajaran, bukan pinjaman:** README-nya sendiri mendokumentasikan kegagalan — `getProductDetailsFromShopee` mengembalikan 404 ("endpoint API diubah atau dinonaktifkan"). Bukti bahwa endpoint Shopee yang tidak terdokumentasi bisa mati sewaktu-waktu; andalkan hanya Open API resmi yang terdokumentasi (bcat95).
- **Hindari / catatan:** Brazil-only, WhatsApp (bukan Threads), tanpa relevansi langsung untuk sistem Kyan.

### Agelakz/Threadscope — https://github.com/Agelakz/Threadscope
- 11★ · Python · update 25 Sep 2026.
- Bot AI yang membaca timeline Threads, mendeteksi "buying intent", lalu **menaruh link affiliate Shopee di komentar postingan orang lain** ("natural, tidak spammy"). Session-first (cookie browser), LLM Groq (Llama 3) + Gemini fallback, mode Trend Affiliate (target post viral 30+ likes).
- **HINDARI TAKTIK INTINYA:** menaruh link di reply post orang lain adalah comment spam — melanggar model Kyan (link hanya di self-reply post sendiri) dan berisiko tinggi kena flag/ban. Repo filter `eryet/threads-shopee-filter` (menyembunyikan spam affiliate di Threads) adalah bukti spam jenis ini sudah cukup parah sampai ada yang membuat pemblokirnya.
- **Konsep yang layak dipinjam (hanya ini):** pola LLM combo Groq + Gemini fallback untuk drafting (provider gratis berlapis) — sama dengan ide 9Router multi-provider kami; dan session-first cookie injection (sudah dipakai d4ncboz).

## 4. Sistem end-to-end / multi-platform

### omozousha/AffiSocAI — https://github.com/omozousha/AffiSocAI
- 0★ · TypeScript (Node + SQLite + React) · **Lisensi: Private — all rights reserved** · update 16 Okt 2026.
- Auto-posting affiliate Shopee ke IG + FB + Threads: link → scraper (og:tags) → konten AI (mystery caption, 16 kategori) → gambar AI (4-rung chain) → slot jadwal → tick 60 detik → fan-out ke semua platform aktif. Scheduler idempotent, horizon 2 hari, maks 6 slot. Provider Threads via Meta app.
- **Konsep yang layak dipinjam:** (1) fan-out satu slot = satu produk ke semua platform aktif (ekspansi fase lanjut: IG/FB); (2) scheduler tick + idempotensi; (3) enrich produk dari og:tags + dry-run sebelum menyimpan link; (4) UI React + log live via SSE.
- **Hindari / catatan:** lisensi PRIVAT — konsep boleh dipelajari, kode tidak boleh disalin/diadopsi; butuh akun Composio untuk IG/FB.

### imanmukhlisin/Automation-Treads — https://github.com/imanmukhlisin/Automation-Treads
- 1★ · TypeScript · update 2 Agu 2026.
- "Traffic Harvester": bot WhatsApp (Baileys) + Playwright showcase scraper (scroll daftar ReactVirtualized) + Supabase/Drizzle + dashboard + jembatan n8n (retry exponential backoff, webhook heartbeat) → posting ke Threads via Meta Threads API.
- **Konsep yang layak dipinjam:** (1) pola upsert scraper yang mempertahankan status `isPosted` — sinkronisasi ulang tidak membuat post duplikat; (2) monitor produk per tab (Belum Post / Sudah Post); (3) jembatan n8n dengan backoff eksponensial.
- **Hindari / catatan:** scraping showcase Shopee melanggar ToS Shopee (faustzaki mencatat semua jalur scrape diblokir 403/login wall/signature — klaim repo ini belum terverifikasi); stack berat (Supabase + n8n + bot WhatsApp) untuk kebutuhan v1; bukan basis yang tepat.

### deinsteins/deins-affiliate-pipeline — https://github.com/deinsteins/deins-affiliate-pipeline
- 0★ · Python 3.11+ · update 26 Okt 2026.
- Telegram channel → download video produk → caption AI per platform (9Router `deepseek-chat`!) → auto-post YouTube Shorts, FB Reels, Threads via **API resmi**; Shopee Video manual (tidak ada API upload). State machine SQLite (`discovered → downloaded → captioned → packaged → posted:<platform> / failed:<platform> → done`), retry dengan backoff, quota-aware, notifikasi Telegram per item terbit/gagal.
- **Konsep yang layak dipinjam:** (1) state machine item di SQLite dengan status per platform + retry/backoff — pola antrean yang lebih rapi dari file JSON history v1; (2) caption ditulis ulang AI per platform (tidak pernah copy-paste caption sumber — hindari deteksi konten duplikat); (3) `link_tools`: ekstrak URL Shopee + resolve shortlink → URL kanonik (shop id / item id); (4) notifikasi Telegram ke owner untuk tiap hasil posting/gagal; (5) kejujuran soal batas (Shopee Video manual by design).
- **Hindari / catatan:** sumber video adalah milik seller/creator (risiko reused-content — diakui sendiri di README); ingest Telegram via Telethon user client (MTProto userbot — grey-area, sama seperti diskusi bot-to-bot Telegram); caption AI via 9Router sudah sejalan dengan rencana kami.

## 5. Strategi / playbook (tanpa kode — pola pikirnya yang dipinjam)

### momokii/shopee-affiliate-os — https://github.com/momokii/shopee-affiliate-os
- 0★ · tanpa kode (dokumen + template Sheets) · update 14 Sep 2026 · repo Indonesia.
- "Operating system" affiliate Shopee organik, Threads-first, 3–5 jam/minggu, faceless, dari nol. Aturan inti: link hanya di first comment; satu post = satu tagged link (`th_a1_t001_txt`); warm-up 7 hari tanpa link; jangan pernah klaim yang tidak diuji ("ratingnya paling stabil…", "komentar pembeli banyak bilang…"); volume menemukan winner (~0,5% post "hit"); AI mengkloning format winner (P3 format lock-in — 10 klon dari satu winner >3× median views); review bulanan dengan metrik EPC (komisi ÷ klik) → keputusan START / CONTINUE / STOP; tracking Sheets (posts × performance di-join via tag); komisi indirect setengah rate; payout mingguan.
- **Konsep yang layak dipinjam — LAPISAN STRATEGI SISTEM KAMI:** (1) konvensi tag unik per post (padanan Sub-ID kami); (2) EPC sebagai metrik keputusan, bukan likes; (3) P3 format lock-in: kloning winner, bukan terus-menerus cari format baru; (4) review bulanan START/CONTINUE/STOP berbasis angka; (5) warm-up akun baru 7 hari tanpa link.
- **Catatan jujur (perbedaan pendapat):** playbook ini merekomendasikan niche awal *small-space home living / kos-kosan* dan menaruh beauty sebagai "expansion lane #2" — berbeda dari keputusan beauty-first Kyan (didasarkan pada model teman + komisi beauty tertinggi). Bukan koreksi, tapi titik diskusi bila beauty tidak menemukan winner dalam 30–60 hari.
- **Hindari / catatan:** ini playbook manual (Buffer free + Sheets) — bukan otomasi; schedulernya Buffer, bukan cron kami; tidak ada kode yang bisa dipakai langsung.

### Affitor/affiliate-skills — https://github.com/Affitor/affiliate-skills
- 786★ · skill library (agentskills.io) · MIT · update 16 Nov 2026.
- 52 skill AI agent dalam 8 tahap flywheel: riset program → scout konten trending → tulis post berbasis data → infografis → landing page → distribusi → tracking → optimasi → scale. Termasuk skill audit kepatuhan (FTC) + API openaffiliate.dev untuk data program (komisi, cookie).
- **Konsep yang layak dipinjam:** (1) model flywheel 8 tahap sebagai peta jalan sistem (riset → konten → landing → distribusi → analitik → optimasi); (2) skill audit kepatuhan sebagai lapisan keamanan (padanan guardrails kami, tapi untuk funnel); (3) angle ranker — skor angle konten berdasarkan kompetisi + prediksi engagement + kecocokan platform.
- **Hindari / catatan:** berorientasi Barat (FTC, program via openaffiliate.dev) — Shopee ID kemungkinan tidak tercakup; ini skill untuk agen AI, bukan aplikasi posting; tidak ada kode poster.

## 6. Landing page (etalase — tujuan link dari Threads)

### Trias1/Linkhub — https://github.com/Trias1/Linkhub
- 0★ · TypeScript (Next.js 16 + Supabase) · MIT · update 11 Nov 2026 · live: linkhub.west-solutions.web.id.
- Halaman toko gratis untuk affiliate Shopee/Tokopedia/TikTok Shop: katalog bernomor yang tidak pernah berubah (`/halaman?no=12` — sama dengan ide "katalog bernomor" dari alur 22 Okt Kyan), auto-fill nama/harga/foto dari link (Shopee via Affiliate Open API bila key diset), promo berjangka, halaman per produk + share image, satu bio link per aplikasi (`?src=tiktok` dst. — padanan Sub-ID per platform), insights (pengunjung, klik link, klik beli per hari WIB, produk teratas, jam tersibuk), CSV export/import, ringkasan email mingguan.
- **Konsep yang layak dipinjam — REFERENSI LANDING PAGE FASE 2:** (1) nomor produk permanen; (2) atribusi `?src=` per channel; (3) insights klik beli per hari WIB + jam tersibuk; (4) auto-fill dari API bila kredensial ada, fallback manual bila tidak (pola yang sama dengan fallback chain dealradar).
- **Hindari / catatan:** butuh Supabase (slot gratis Kyan penuh 2/2: DanKas + KRING!) + Vercel; auto-fill Shopee tetap butuh `SHOPEE_AFFILIATE_APP_ID/SECRET` yang belum ada — jadi versi Kyan harus manual dulu.

## 7. Riset produk & video (jalur konten, bukan poster teks)

### auliaharitsuddin/dealradar — https://github.com/auliaharitsuddin/dealradar
- 0★ · TypeScript (Next.js) · tanpa lisensi tercatat · update 16 Sep 2026 · dashboard Indonesia.
- Dashboard flash sale / diskon terverifikasi / produk terlaris (Shopee, Tokopedia, Lazada, Zalora, Blibli). Connector nyata hanya Shopee via Affiliate Open API (`lib/connectors/shopeeAffiliate.ts`); platform lain fallback data contoh dengan *source banner* yang jelas. Verifikasi harga pasar via web search + LLM gratis (router multi-provider: Groq/Cerebras/NVIDIA/OpenRouter/Z.ai/Gemini/Moonshot, dicoba berurutan, rotasi key otomatis). Watchlist + notifikasi Telegram. Tombol "Beli" membuka halaman pencarian resmi (deep link) — sengaja tidak mengotomatiskan checkout (ToS).
- **Konsep yang layak dipinjam:** (1) rantai fallback (connector resmi → data contoh + banner sumber) — pola yang sama untuk konektor Shopee fase 2 kami; (2) router LLM multi-provider dengan fallback berurutan — padanan pola 9Router kami; (3) file `shopeeAffiliate.ts` sebagai referensi implementasi pemanggilan Open API (auth/signing) untuk fase 2; (4) prinsip "tidak pernah mengotomatiskan checkout".
- **Hindari / catatan:** dashboard riset, bukan poster; tanpa lisensi tercatat — jangan salin kode tanpa memeriksa; sebagian besar datanya contoh.

### bismillah123-jp/gflow-affiliate — https://github.com/bismillah123-jp/gflow-affiliate
- 0★ · Python · MIT · update 3 Okt 2026.
- Pipeline video affiliate vertikal 9:16 ±10 detik, VO Bahasa Indonesia: riset → gambar katalog → HD → storyboard → video → TTS → finish. Pakai gflow-cli (Nano Banana 2 + Omni Flash), edge-tts, ffmpeg. Aturan kualitas: hanya tangan/POV tangan (tanpa wajah), `ANOMALY_GUARD` di setiap prompt (auditable), konsistensi produk via character reference, teks di video minimal (AI rawan garbled), VO ±120–140 karakter. Jujur soal batas: login Google sekali per mesin, kuota Flow, guard best-effort — **selalu tonton hasil sebelum publish**. Tahap yang selesai otomatis di-skip (idempotent), mode `--dry-run` wajib lolos sebelum produksi.
- **Konsep yang layak dipinjam — JALUR VIDEO (rencana 22 Okt Kyan):** (1) pipeline 7 tahap + dry-run + idempotensi tahap; (2) `ANOMALY_GUARD` sebagai prompt guard yang bisa diaudit; (3) character reference untuk konsistensi produk; (4) gerbang "tonton dulu sebelum publish" sebagai padanan approval untuk video.
- **Hindari / catatan:** butuh kredit Google Flow (tidak gratis selamanya — Kyan punya Google AI Pro; biaya per klip sudah diketahui: Veo 3.1 Lite 10 / Fast 20 / Quality 100 kredit per klip 8 detik); gambar katalog diambil via DuckDuckGo (bukan aset resmi seller).

### rizalfirmansyah120593-byte/KontenKita-AI — https://github.com/rizalfirmansyah120593-byte/KontenKita-AI
- 1★ · Python · MIT · update 16 Nov 2026 (repo lain bernama sama: 0★).
- "AI Video Content Factory" lokal: topik → script → VO → subtitle → visual → video (9:16/16:9/1:1). Modul Shopee UGC Affiliate: baca metadata publik dari URL produk Shopee → brief UGC (gaya review/unboxing/tutorial/masalah-solusi/soft selling) + disclosure affiliate di script. Publikasi YouTube Shorts/TikTok via OAuth resmi. Antrean jadwal lokal + pemeriksaan keamanan konten dasar.
- **Konsep yang layak dipinjam:** (1) brief UGC dari URL produk + disclosure di script; (2) antrean jadwal lokal + content safety check; (3) seri konten (ratusan episode dari satu topik).
- **Hindari / catatan:** ini fork/rebrand MoneyPrinterTurbo (jejak `MoneyPrinterTurbo-main` + aset demo harry0703 di README) — nilai tambahnya tipis di atas upstream; butuh LLM API key + provider gambar/video (berbiaya bila lewat kuota gratis); **tidak ada posting Threads**.

## 8. Sintesis

### Pola yang muncul di 3+ repo
1. **Playwright/Selenium + cookie sesi, bukan API resmi** — d4ncboz, faustzaki, Threadscope, ibrahimakcayy, Automation-Treads (scraper). API resmi adalah "jalan yang benar" tapi semua repo mengaku butuh Meta app + App Review + tester.
2. **API resmi Threads sebagai jalur fase lanjut** — yanstd888, Postiz, TryPost, ThreadsPipe-py, msyamsularif, nerin81 (modul), deins, AffiSocAI. Semua membutuhkan hal yang sama: undangan tester + `threads_content_publish`.
3. **Publish safety: atomic claim + `publish_unknown` tanpa blind-retry** — yanstd888, faustzaki, nerin81 (publish_guard), msyamsularif ("publish gagal tidak pernah mengubah Status"). Ini konsensus lintas repo yang paling kuat.
4. **Approval manusia sebagai default** — yanstd888, msyamsularif, TryPost, faustzaki (auto-post hanya bila skor ≥90 dan AI 0). Sistem Kyan menggantinya dengan guardrails otomatis — tidak ada repo yang melakukan penggantian ini secara penuh.
5. **Kill switch + kuota harian eksplisit** — yanstd888, nerin81 (safety_guard).
6. **Dedup / tidak pernah posting ulang link yang sama** — d4ncboz, faustzaki (image lifecycle), nerin81 (dedup kartu), Automation-Treads (upsert pertahankan `isPosted`).
7. **Link di first comment/reply, bukan badan post** — momokii, deins ("link in post / first reply"), v1 kami. Catatan jujur: nerin81 *menjanjikan* ini tapi tidak mengimplementasikannya (`firstComment` selalu kosong) — janji di README ≠ perilaku kode.
8. **AI drafting + filter/gate** — faustzaki (quality gate + detektor AI), msyamsularif (antislop audit), nerin81 (generate-then-filter), deins (caption ditulis ulang), AffiSocAI (mystery caption).
9. **SQLite sebagai state store** — yanstd888, faustzaki, deins, AffiSocAI (d4ncboz memakai JSON).
10. **LLM lewat provider gratis / 9Router lokal** — faustzaki (`NINEROUTER_URL=http://127.0.0.1:20128/v1` — port yang sama dengan 9Router Kyan), deins (9Router deepseek-chat), dealradar (router multi-provider gratis berurutan).
11. **Tracking via tag/Sub-ID + metrik per klik** — momokii (tag unik + EPC), Linkhub (`?src=` per channel), deins (status per platform), bcat95 (conversionReport).
12. **Kejujuran soal batas** — repo yang bagus menulis apa yang TIDAK bisa: faustzaki (tidak bisa scrape Shopee), deins (Shopee Video manual), dealradar (tidak ada API kalender flash sale; tidak pernah mengotomatiskan checkout), msyamsularif (tanpa antislop skill, preview mengakuinya).

### Celah yang tidak ditutup satu repo pun (yang ditutup sistem kami)
1. **Tidak ada satu repo yang menggabungkan:** API resmi Shopee ID (bila akses ada) + API resmi Threads *dengan dukungan reply* + AI drafting via provider gratis + guardrails otomatis pengganti approval manusia + link di self-reply + tracking Sub-ID. Masing-masing repo hanya memegang 2–3 potong.
2. **Tidak ada repo yang menegakkan aturan Kyan secara otomatis dan lengkap** — filter produk (rating ≥4,8, terjual ≥1 rb, Rp20–100 rb, Star/Mall + XTRA), batas 500 karakter, disclosure wajib, larangan klaim review. msyamsularif paling dekat di aturan kejujuran (tapi butuh approval manusia); faustzaki paling dekat di quality gate (tapi tanpa filter produk).
3. **Tidak ada repo yang menangani masalah akses API Shopee ID** — semuanya mengasumsikan `app_id`/`secret_key` sudah ada. Akun Kyan terbukti belum punya akses (Apply nonaktif, 16 Nov 2026) — sistem kami dirancang dengan fallback database link manual sejak awal.
4. **Tidak ada repo yang mengoptimasi jam posting dari data untuk WIB** — nerin81 punya insights per jam tapi untuk KST/Toss; momokii punya review bulanan tapi manual.
5. **Tidak ada repo yang menggabungkan teks Threads + video (Flow) + landing page** dalam satu sistem — ketiganya hidup di repo terpisah (d4ncboz/faustzaki, gflow-affiliate/KontenKita, Linkhub).
6. **Tidak ada repo berbahasa Indonesia yang menjadi "sistem operasi" lengkap** — momokii paling dekat (playbook ID, tanpa kode); faustzaki paling dekat (bot ID, tanpa lapisan strategi/EPC).

## 9. Lima konsep paling layak dipinjam (ringkas)

1. **Publish guard idempotensi** (nerin81 / faustzaki / yanstd888) — klaim atomik + status `publish_unknown` tanpa blind-retry: crash di tengah posting tidak pernah jadi double-post.
2. **Quality gate + detektor AI berbahasa Indonesia** (faustzaki) — skor AI-tell + tolak klaim tanpa dasar dan shortener: perkuat `check_draft.py`.
3. **Randomisasi jadwal + jitter harian** (faustzaki) — jadwal dibangkitkan ulang tiap hari, ada hari libur dan jeda acak: ganti cron jam tetap v1.
4. **Publisher API resmi Python dengan `reply_to`** (ThreadsPipe-py) — ganti modul JS nerin81 untuk fase 2: API resmi + dukungan reply + auto-split 500 karakter + cek kuota.
5. **Tag/Sub-ID unik + metrik EPC + review bulanan START/CONTINUE/STOP** (momokii) — satu tag per post, ukur komisi per klik, putuskan lanjut/berhenti berbasis data, bukan perasaan.

## 10. Catatan metode & batas survey

- Yang dibaca adalah README (dan, untuk d4ncboz/nerin81, kode + audit penuh di file terpisah). Klaim README belum tentu sama dengan perilaku kode — contoh paling jelas: nerin81 menjanjikan "link di komentar pertama" tapi kodenya tidak pernah mengimplementasikannya.
- Star count dicatat per 16 Nov 2026; repo 0★ bukan berarti tidak berguna (faustzaki 0★ adalah repo paling relevan kedua setelah d4ncboz untuk sistem ini).
- Lisensi dicatat karena menentukan apa yang boleh dipakai ulang: MIT/Apache = aman; AGPL (Postiz, TryPost) = hati-hati bila dijalankan sebagai layanan yang dimodifikasi; Private (AffiSocAI) = konsep saja; tanpa lisensi (dealradar) = jangan salin kode.
- Pencarian GitHub memakai pencocokan kata kunci, bukan pemahaman topik — selalu verifikasi dengan grep/baca sebelum percaya bahwa sebuah repo "tentang Shopee".
