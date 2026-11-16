# Audit — nerin81-netizen/threads-affiliate-automation

- **Repo:** https://github.com/nerin81-netizen/threads-affiliate-automation
- **Bintang:** 77 (paling banyak di pencarian "threads affiliate") · **Versi:** 1.5.3 · **Lisensi:** MIT
- **Bahasa:** JavaScript/Node.js (ES modules) · **Commit terakhir saat audit:** `3e8ae55` (17 Okt 2026)
- **Tanggal audit:** 16 Nov 2026 · **Metode:** clone read-only → baca kode + jalankan selftest logika murni
- **Catatan penting:** repo ini **BUKAN Shopee**. Nol (0) kemunculan kata "shopee" di seluruh repo (grep seluruh file, di luar `.git`).

## 1. Ringkasan — ini repo apa sebenarnya

Repo Korea untuk **Toss** (fintech/super-app Korea), bukan Shopee. Deskripsi di `package.json`
(Korea): *"스레드(Threads) 맞팔 늘리기 및 토스 핫딜 제휴링크 자동 포스팅 봇"* — bot
penambah follow-balik Threads + auto-posting link affiliate **hot-deal Toss**. Seluruh
konten, template, timezone (Asia/Seoul, KST), bahasa, dan integrasi affiliate-nya Korea:
Toss Sharelink Open API, Naver API, Azure (PostgreSQL + Blob + Key Vault).

Kenapa repo ini muncul di pencarian "shopee threads affiliate": GitHub search mencocokkan
kata kunci "threads affiliate", bukan Shopee. Angka 77 star-nya nyata, tapi relevansinya
untuk sistem Shopee Kyan **hampir nol secara langsung** — nilainya ada di 3 komponen
yang bisa dipinjam (lihat §5).

Struktur (total ~16.900 baris, termasuk satu file aturan 5.238 baris):

| Bagian | File | Isi |
|---|---|---|
| Bot Playwright | `scripts/threads_bot.mjs` (630) | login IG, auto-follow, posting kartu, hot-deal |
| API resmi | `scripts/threads_api.mjs` (322) | Meta Threads Graph API (container → publish) |
| Affiliate | `scripts/toss_openapi.mjs` | OAuth2 Toss: best-seller, today-deals, sharelink |
| Guard | `scripts/publish_guard.mjs`, `scripts/safety_guard.mjs` | idempotensi posting, kuota harian, kill switch |
| Kualitas | `scripts/post_quality.mjs` | detektor "AI-tell" statis (aturan bahasa Korea) |
| Konten AI | `scripts/story_writer.mjs`, `scripts/vault_generator.mjs` | Gemini → tulis → saring klaim palsu |
| Kartu | `scripts/card_generator.mjs`, `scripts/card_render.mjs` | Card Studio: template kartu + gambar |
| Dashboard | `server.mjs` (2.140) + `public/app.js` (3.062) + `public/index.html` (1.296) | server lokal port 3500, 8 bahasa, SSE log |
| Engagement | `scripts/feed_heart_bot.mjs`, `scripts/feed_rapport_bot.mjs`, `scripts/rapport_engine.mjs` | auto-like, auto-reply ke post orang |
| Bloat | `scripts/scene_rules_1000.mjs` (5.238) | 1.000 aturan visual untuk AI image-gen |

## 2. Cara kerja

### 2.1 Jalur posting — ada DUA, keduanya terpasang

**A. Playwright (utama, `threads_bot.mjs`)**
- Profil Chromium persisten `.threads_chrome_profile` + `storage_state.json`.
- Evasion anti-bot eksplisit: `--disable-blink-features=AutomationControlled`,
  `navigator.webdriver` disembunyikan, `window.chrome` dipalsukan, UA Chrome 124
  Windows, locale `ko-KR`, timezone `Asia/Seoul`.
- Login: `tryAutoLogin()` mengetikkan `THREADS_ID` / `THREADS_PW` dari `.env` ke
  form login Instagram (password di env — sudah bukan hardcode sejak PR keamanan
  Okt 2026, lihat §4.5). Bila gagal, menunggu login manual max 5 menit.
- `growFollowers()`: auto-follow akun dari hashtag follow-balik Korea
  (`#스팔 #맞팔 #선팔하면맞팔 #소통환영`), max 40/hari, 15/sesi, jeda 6–16 dtk,
  cooldown 25–35 dtk tiap 5 follow.
- `postSingleCard()`: buka composer (3 strategi + fallback `/intent/post`),
  ada guard bagus — menolak posting bila yang terbuka adalah composer **reply**
  (`REPLY_COMPOSER_DETECTED`), ketik ala manusia (emoji-safe, lihat §3.1),
  lampirkan media, klik Post. Tidak ada verifikasi URL post.
- `postHotDeal()`: ambil best-seller Toss → buat sharelink → posting dengan
  template. **Selalu item rank 1** — tidak ada rotasi produk.

**B. API resmi Meta (`threads_api.mjs`)** — ini bagian terbaik repo ini
- `graph.threads.net/v1.0`, alur container → `threads_publish`, token dicek via
  `/debug_token` (scope), ada mode `--check` (buat container tanpa publish
  untuk tes izin).
- `verifyPublishedThread()`: read-back pasca-publish, mengembalikan **postId +
  permalink asli** — jauh lebih kuat dari verifikasi substring-profil di
  d4ncboz. Kegagalan verifikasi TIDAK melempar (tidak memicu re-post).
- `publishText()`: teks saja, **top-level saja — dengan sengaja TIDAK bisa
  membuat reply** (komentar kode: "안전 정책상 이 모듈은 답글 컨테이너를 만들지
  않는다"). Untuk pola Kyan (link di self-reply) modul ini perlu ditambah
  dukungan `reply_to`.
- `publishMediaPost()`: butuh **URL publik** (Azure Blob) — file lokal tidak
  bisa diunggah lewat API.
- `fetchPostInsights()` + `summarizeByHour()`: metrik views/likes/replies/
  reposts/quotes + rata-rata per jam (KST) — berguna untuk optimasi jam posting.

Kedua jalur terpasang di dashboard: `/api/cards/:id/post` → Playwright;
jalur API dipakai dari handler publish lain (baris ~1816/1841 `server.mjs`).

### 2.2 Sisi affiliate — Toss, bukan Shopee

`toss_openapi.mjs`: OAuth2 client-credentials (`TOSS_SHARELINK_ACCESS_KEY` +
`SECRET_KEY`), token di-cache di `.toss_token.json` (**tanpa `chmod`** — token
tertulis polos), endpoint `best-selling`, `today-deals`, `createShareLink`.
Pola ini (OAuth2 → daftar produk → buat shortlink) adalah **pola yang sama
yang kita butuhkan untuk Shopee Open API di fase 2** — strukturnya bisa
dicontek, isinya tidak.

### 2.3 Konten — template + Gemini, bukan murni template

- `card_generator.mjs`: 4 template kartu. **Dua template menjanjikan "link di
  komentar pertama"** ("💬 최저가 구매 좌표는 '첫 번째 댓글'에 남겨둘게요 👇")
  tapi kode **menghapus baris itu** (`.replace(/\n💬[\s\S]*$/, '')`) lalu
  **menempel link ke badan post** (`🔗 구매 좌표: ${shortUrl}`). Field
  `firstComment` selalu `''` di mana-mana (`getSavedCards`, `updateCard`) —
  fitur "link di komentar pertama" adalah **stub yang tidak pernah jalan**.
  Ini persis melanggar aturan Kyan (link hanya di self-reply).
- Template `실사용_간증형` (gaya testimoni pemakaian): "후기 평점 폭발한
  갓성비 꿀템", tag "⭐ 만족도 1위" — klaim testimoni palsu, risiko yang sama
  seperti template d4ncboz.
- Dedup kartu berdasarkan `itemId` (max 30 kartu) — ada, tidak seperti
  `postHotDeal` yang selalu rank 1.
- `estimatedReward = harga × 10%` — asumsi komisi 10% (Toss), bukan data.
- `story_writer.mjs` / `vault_generator.mjs`: panggil Gemini
  (`generativelanguage.googleapis.com`, model default **`gemini-3.8-flash`** —
  nama model ini **tidak terverifikasi**; waspada bila diadopsi), lalu
  **saring output** dengan `findFabrication()` (klaim prestasi/palsu) +
  `findAiTells()` sebelum diterima. Pola generate-then-filter ini bagus.
- `post_quality.mjs`: detektor "AI-tell" statis tanpa LLM (gratis): pola
  "A가 아니라 B", kata abstrak, deret kalimat pendek, pengulangan akhiran,
  penutup tanpa pertanyaan. **Aturannya bahasa Korea** — idenya portable,
  regex-nya tidak.

### 2.4 Dashboard + autopilot

- `server.mjs`: server HTTP mentah (bukan Express), port 3500, SSE log
  real-time, auth `DASHBOARD_ADMIN_PASSWORD` + **bypass localhost bila
  password tidak diset** (aman lokal, berbahaya bila terekspos), rate-limit
  login (10 percobaan / 15 menit), header keamanan dasar.
- Endpoint: auth, logs, status, config, cards CRUD + post, bot/action,
  **autopilot** (`timed_3h`: siklus 30 menit × 6 = 3 jam; tiap siklus
  follow, tiap siklus ke-2 posting hot-deal), comments-history, rapport,
  heart-bot, feed-rapport, trends, vault.
- **Autopilot memakai timer in-memory** (`setTimeout`) — jadwal hilang bila
  server restart. `config.json` punya `scheduler.enabled: false` yang tidak
  dipakai di mana-mana. Tidak ada cron.
- `DEPLOY.md`: aslinya jalan di **VM Azure pribadi penulis**
  (Standard_D4s_v5, PM2, Nginx, 5 service berbagi satu VM). Klaim "local
  dashboard" benar untuk jalan lokal, tapi fitur penuh butuh Azure
  PostgreSQL + Blob + Key Vault.

## 3. Yang lebih baik dari scaffold v1 kami

### 3.1 Layak dipinjam (dengan adaptasi)

1. **`threads_api.mjs` — modul API resmi (PALING BERHARGA).** Satu-satunya
   implementasi Graph API yang bersih di antara repo yang diaudit: container
   → publish, cek scope, `--check` tanpa posting, verifikasi read-back +
   permalink. **Adaptasi wajib:** tambah dukungan reply (`reply_to`) karena
   modul ini sengaja tidak bisa reply — padahal pola Kyan butuh link di
   self-reply. Media butuh URL publik (jadi kartu gambar fase 2 butuh hosting
   publik atau tetap lewat Playwright). Prasyarat tetap sama: undangan tester
   diterima + App Review `threads_content_publish` lolos.
2. **`publish_guard.mjs` — idempotensi posting.** Kunci SHA-256 dari
   (body ternormalisasi + nama file media); state machine
   `claim → publishing → published/verification_pending`; crash di tengah
   posting TIDAK auto-republish; tulis atomik (temp + rename). Test
   bawaannya lolos (verifikasi §6). **Port ke Python di `run_slot.py`** —
   menutup celah double-post yang saat ini tidak ditangani v1.
3. **`safety_guard.mjs` — kuota + kill switch + human-typing.**
   Kuota terstruktur (post 5/hari, follow 40/hari, like 300/hari, komentar
   100/hari, outbound 10/hari dengan jeda 45–120 dtk + cooldown 5 menit
   tiap 3), kill switch env `DISABLE_OUTBOUND=1`, dan `humanType()` yang
   benar menangani emoji (iterasi code-point, bukan index — menghindari
   karakter rusak U+FFFD). **Pinjam polanya** (kuota + kill switch) ke
   `config.yaml`; human-typing emoji-safe relevan bila v1 mengetik
   teks ber-emoji.
4. **Insights per jam (`fetchPostInsights` + `summarizeByHour`).**
   Metrik asli dari API + rata-rata views per jam posting — bisa dipakai
   nanti untuk menguji apakah slot 08:00/13:00/20:00 memang optimal.
   Adaptasi: KST → WIB.
5. **Pola generate-then-filter (`story_writer.mjs`).** LLM menulis, lalu
   `findFabrication` + `findAiTells` menyaring sebelum diterima — pola yang
   tepat untuk fase-2 AI drafting (9Router). **Tulis ulang aturannya dalam
   Bahasa Indonesia** (aturan aslinya Korea); padanan `findFabrication`
   untuk klaim review adalah `check_draft.py` yang sudah ada di v1.

### 3.2 Ide bagus, jangan diadopsi mentah-mentah

- **Dashboard lokal** (3.062 baris JS + 1.296 baris HTML + server 2.140
  baris, i18n 8 bahasa): tampilannya bagus (Card Studio, live console),
  tapi permukaannya besar untuk diaudit dan fitur penuhnya mengikat Azure.
  Untuk v1 (CLI + cron di PC), dashboard adalah beban — pertimbangkan hanya
  bila Kyan minta UI.
- **`post_quality.mjs` (detektor AI-tell):** ide bagus, tapi 100% aturan
  bahasa Korea (akhiran `~입니다/~해요`, pola `A가 아니라 B`). Perlu
  ditulis ulang total untuk Bahasa Indonesia.

## 4. Temuan — lebih buruk / lebih berisiko dari v1

### 🔴 Kritis

1. **Bukan Shopee — nol relevansi affiliate langsung.** Tidak ada satu pun
   kode, endpoint, atau template Shopee. Mengadopsi repo ini apa adanya
   berarti membangun sistem untuk Toss Korea, bukan Shopee Indonesia.
2. **Link selalu di badan post utama.** Template `config.json`, template
   kartu, dan `postHotDeal` semuanya menaruh link di post utama
   (`linkPosition: 'body'`). Fitur "link di komentar pertama" yang
   dijanjikan template **tidak pernah diimplementasikan** (`firstComment`
   selalu string kosong). Ini melanggar aturan inti Kyan + menghilangkan
   keunggulan format kami.
3. **Otomasi engagement (follow/like/reply massal).** Auto-follow hashtag
   follow-balik, auto-like 300/hari, auto-reply ke post orang asing
   (`feed_rapport_bot`, `rapport_engine`, `rapport_reply_service`).
   Ini spam automation, zona abu-abu ToS yang lebih gelap dari sekadar
   auto-posting, dan rawan pembatasan akun. Kyan tidak meminta ini —
   **jangan diadopsi**.
4. **Template testimoni palsu.** Gaya `실사용_간증형` + klaim "만족도 1위"
   / "후기 평점 폭발" — klaim pemakaian & peringkat yang tidak
   diverifikasi. Risiko yang sama seperti template d4ncboz yang sudah
   kami tulis ulang.

### 🟡 Penting

5. **Tidak ada validasi batas 500 karakter** di mana pun (grep: nihil).
   Template + nama produk panjang bisa melampaui batas Threads.
6. **Tidak ada kriteria produk** (rating, jumlah terjual, rentang harga).
   `postHotDeal` selalu mengambil best-seller rank 1 — tanpa rotasi,
   tanpa filter kualitas. Satu-satunya "dedup" adalah `publish_guard`
   yang memblokir body identik — jadi hot-deal yang sama akan diblokir
   sebagai duplikat, bukan diganti produk lain.
7. **Login otomatis mengetikkan password IG dari `.env`** ke form login
   (Playwright). Password di file env + profil Chrome persisten berisi
   sesi penuh. Lebih berisiko dari ekstraksi cookie read-only d4ncboz.
8. **Evasion anti-bot eksplisit** (sembunyikan `webdriver`, palsukan
   `window.chrome`, UA palsu). Sama-sama grey-area seperti d4ncboz, tapi
   lebih agresif dan lebih mudah dikenali sebagai tooling otomatis.
9. **Riwayat kebocoran secret di git.** Rilis awal (Sep 2026) mengandung
   password Threads hardcode, ID akun pribadi, host DB cloud, nama Key
   Vault, cookie sesi, dan screenshot token Meta — dibersihkan Okt 2026
   via force-push (CHANGELOG 2026-10-16, PR #1). Tree saat ini bersih,
   tapi riwayat ini menunjukkan higiene keamanan yang pernah buruk.
10. **Tidak ada `package-lock.json`; dependensi mati.** `threads-api`
    (`^1.6.3`, library Threads tidak resmi berbasis login IG) dideklarasi
    tapi **tidak pernah di-import** di mana pun. Tanpa lockfile, `npm
    install` mengambil versi terbaru sesuai semver — build tidak
    reproduksibel.
11. **Model Gemini default tidak terverifikasi.** `gemini-3.8-flash`
    (`.env.example`, `story_writer.mjs`, `vault_generator.mjs`) — nama
    model ini tidak dapat dikonfirmasi; image-gen memakai Gemini Image /
    Nano Banana dan Veo (berbayar). Klaim "gratis" repo ini hanya berlaku
    untuk tier gratis Gemini, dan tetap butuh API key (bukan tanpa biaya
    sama sekali bila melewati kuota).
12. **Autopilot rapuh.** Timer in-memory — restart server = jadwal hilang.
    Tidak ada cron, tidak ada persistensi jadwal.

### ⚪ Minor / stale

13. **Bloat:** `scene_rules_1000.mjs` 5.238 baris aturan visual AI image-gen
    + `scene_illustrator.mjs`, `video_generator.mjs` — tidak relevan untuk
    sistem Kyan.
14. **Token Toss di-cache tanpa `chmod`** (`.toss_token.json` ditulis
    polos).
15. **Hardcode zona Korea di mana-mana:** locale, timezone, hashtag,
    Naver API, KST (+9) di semua perhitungan jam.
16. **Klaim "40–60 detik → 1–2 detik"** untuk API vs browser (komentar di
    `threads_api.mjs`) — masuk akal, tapi tidak ada benchmark di repo.

## 5. Keputusan: apa yang dipinjam

| Komponen | Keputusan | Alasan |
|---|---|---|
| `threads_api.mjs` | **PINJAM (fase 2)** | Satu-satunya modul Graph API bersih; tambah dukungan reply + adaptasi WIB |
| `publish_guard.mjs` | **PINJAM (segera)** | Idempotensi SHA-256, test lolos; port ke Python |
| Kuota + kill switch (`safety_guard.mjs`) | **PINJAM polanya** | Kuota eksplisit + `DISABLE_*` kill switch ke `config.yaml` |
| Insights per jam | **PINJAM nanti** | Optimasi slot posting berbasis data, adaptasi KST→WIB |
| Pola generate-then-filter | **PINJAM polanya** | Untuk AI drafting fase 2; aturan ditulis ulang ID |
| Playwright bot + evasion | **TOLAK** | Sudah ada basis d4ncboz yang lebih kecil; evasion lebih agresif |
| Auto-follow / like / reply | **TOLAK** | Spam automation, bukan permintaan Kyan, risiko ban |
| Template kartu + Toss | **TOLAK** | Link di body + testimoni palsu + bukan Shopee |
| Dashboard (server + UI) | **TUNDA** | Terlalu besar untuk v1; pertimbangkan bila Kyan minta UI |
| `scene_rules_1000` dkk | **TOLAK** | Bloat image-gen, tidak relevan |

**Verdict:** Repo ini **layak dipinjam secara selektif, bukan diadopsi**.
Nilai sebenarnya hanya 3 komponen (§3.1 poin 1–3). Sebagai sistem affiliate
Shopee, repo ini bernilai **nol** — ia adalah sistem Toss Korea. Jangan
ganti basis v1 (d4ncboz) dengan repo ini; tambahkan komponen pinjamannya
ke v1.

Catatan untuk klaim "banyak repo Shopee affiliate di GitHub": hasil pencarian
GitHub mencocokkan kata kunci "threads affiliate" — repo peringkat teratas
(77 star) ternyata bukan Shopee sama sekali. Jumlah repo yang benar-benar
Shopee + Threads jauh lebih sedikit dari kesan hasil pencarian.

## 6. Verifikasi yang dijalankan

- Clone read-only ke `/tmp/nerin81-audit` (commit `3e8ae55`, 17 Okt 2026).
- Grep: 0 kemunculan "shopee" di seluruh repo; `threads-api` hanya muncul
  di `package.json` (tidak pernah di-import); tidak ada pengecekan batas
  500 karakter; tidak ada `package-lock.json`.
- Selftest logika murni (Node v24, tanpa network/login):
  - `node scripts/post_quality.mjs --selftest` → **lolos**
    (Before/AI 45 vs After/manusia 100).
  - `node scripts/test_publish_guard.mjs` → **lolos** (duplikat + crash
    di tengah posting ditangani).
  - `node scripts/test_publish_safety.mjs` → **lolos** (pemisahan post
    top-level vs reply, batasan root).
- Test yang butuh server (`test_dashboard_security.mjs`,
  `test_content_diversity.mjs`, `test_rapport_reply_service.mjs`)
  **tidak bisa jalan di VM audit** (dependensi npm belum terinstal;
  sengaja tidak diinstal — di luar ruang lingkup audit). Ini keterbatasan
  lingkungan, bukan temuan soal repo.
- Tidak ada posting ke Threads, tidak ada login akun, PC Kyan tidak
  disentuh, tidak ada instalasi di PC. Satu-satunya network call adalah
  `git clone`.
