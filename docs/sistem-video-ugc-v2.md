# Sistem Video UGC v2 — Affiliate Shopee → Threads + Facebook + Pinterest + Meta Ads

**Tanggal:** 16 November 2026 (malam)
**Akun:** Threads @temuanhariann.id · Facebook Page Temuan Harian · Pinterest "Shopee Harian" (@215kyan)
**Niche:** home living / kos-kosan (dapur, organizer, kebersihan)
**Sumber riset:** `~/workspace/research_notes/shopee-affiliate-video-platforms-20261116-1221/report.md`
(Riset web 16 Nov 2026: Pinterest Newsroom terverifikasi live; halaman lain via index/text fetch hari yang sama.)

> **Baca dulu:** dokumen ini adalah RENCANA + SPESIFIKASI v2. Bukan semua bagian sudah jalan.
> Status tiap channel ada di §8. Angka komisi & performa di sini adalah hasil riset
> (bukan data akun sendiri) — selalu cek dashboard Shopee per produk pada hari itu.

---

## 1. Ranking platform — mana yang paling ngasilin cuan

Hasil riset 16 Nov 2026 (organik, 1 video/hari, akun kecil faceless):

| Rank | Platform | Kenapa |
|------|----------|--------|
| **#1** | **Facebook (Page + Reels, tagging Shopee native)** | Audiens Indonesia terbesar (~121 jt), Reels diuji ke non-follower dulu, dan sejak 22 Okt 2025 produk Shopee bisa di-tag langsung di Reel (banner beli otomatis) — tidak butuh link di postingan sama sekali. |
| **#2** | **Pinterest (tagging Shopee native, long-tail)** | Niat beli tertinggi (80% weekly Pinners belanja dengan niat; 85% pernah beli dari Pin), satu video bisa men-tag BANYAK produk (mis. satu kamar kos: lampu + rak + storage), umur Pin 3,5+ bulan — traffic menumpuk. |
| **#3** | **Threads (repurpose saja)** | Algoritma paling ramah akun kecil + engagement tertinggi, tapi audiens Indonesia paling kecil (~8,15 jt), feed text-first, video format sekunder, TIDAK ADA tagging Shopee, dan TIDAK ADA bukti penjualan Shopee lewat Threads yang ditemukan. |

**Per klik**, Pinterest kemungkinan konversi terbaik (niat beli + link langsung di Pin).
**Per akun**, Facebook menang (skala audiens + tagging native). Threads dipakai sebagai
lapisan distribusi gratis (video + hook yang sama), bukan taruhan utama penjualan.

### Ekspektasi realistis (bukan janji cuan)

Hitungan ilustrasi dari benchmark global (bukan data Shopee Indonesia):

- 10.000 views × 1% views-to-click = **100 klik Shopee**
- 100 klik × 2% click-to-purchase = **2 order**
- 2 order × Rp100.000 × 4% komisi = **Rp8.000 per 10.000 views**
- Produk Komisi XTRA 10% (total 14%) → **Rp28.000 per 10.000 views**

Artinya: bulan pertama yang wajar adalah puluhan klik/hari dan order satu digit,
alias puluhan ribu rupiah — bukan jutaan. Yang menentukan penghasilan adalah
**volume + pemilihan produk XTRA / harga tinggi**, bukan satu platform ajaib.
Siapa pun yang janji Rp5–25 jt/bulan di bulan pertama dari Shopee Affiliate
sedang jualan kursus: komisi dasar 4% membuat itu mustahil secara aritmatika
tanpa volume besar atau produk XTRA/AOV tinggi.

### Yang BELUM terverifikasi (jujur)

- **Tidak ada data head-to-head konversi Shopee** Threads vs Facebook vs Pinterest
  di sumber publik — ranking di atas adalah inferensi dari audiens, niat beli,
  tagging native, dan friksi link, bukan tes A/B terukur.
- **Angka komisi sumbernya konflik:** halaman resmi Shopee bilang hingga 4% + XTRA
  (>5% dari penjual); panduan lain bilang hingga 10%, cap Rp10.000/order,
  atau 3,5% cap Rp7.000. **Pakai angka dashboard per produk, jangan kutip satu rate.**
- Pinterest–Shopee: rate komisi, attribution window, daftar produk eligible, dan
  kriteria "eligible creator" TIDAK dipublikasikan; kemitraan baru ~7 minggu
  (diumumkan 23 Sep 2026), belum ada studi kasus kreator.
- Facebook Affiliate Partnerships: klaim ambang ~1.000 follower hanya dari panduan US;
  Shopee Help tidak mencantumkan angka. Apakah tombol boost tetap aktif di Reel
  ber-tag di akun Indonesia belum terverifikasi di Ads Manager.
- Atribusi: klaim sekunder 7-day cookie, last-click, order tidak langsung
  (pembeli beli apa saja di Shopee dalam 7 hari) juga dapat komisi — belum
  diverifikasi dari halaman resmi Indonesia.

---

## 2. Pipeline 7 tahap (satu produk → satu video → tiga platform)

```
[1] LINK          Ambil link dari DB (data/affiliate_links.md) atau link HP Kyan.
                  Kriteria: rating ≥4,8 · terjual ≥1.000 · harga Rp20–100 rb
                  (tes Rp100–300 rb terpisah, lihat §6) · seller Star/Star+/Mall
                  · Komisi XTRA. XTRA dicek di HP/dashboard, bukan halaman publik.
[2] FOTO FRAME    Foto produk asli dari halaman Shopee = frame awal video.
                  WAJIB: produk di video harus SAMA PERSIS dengan foto.
[3] GENERATE      Google Flow (Veo 3) — image-to-video dari foto frame awal.
                  Tangan saja, tanpa muka, close-up produk, cahaya studio.
                  2–3 klip × 8 detik (lihat §3). Voiceover dari ulasan pembeli.
[4] QC            Lolos semua cek §4 baru boleh lanjut. Gagal = buang / generate ulang.
[5] CAPTION       Hook template v5.1 (templates/hooks_*.json, 117 hook, 9 gaya).
                  Fokus review: rating / terjual / kata pembeli. Link di reply
                  pertama (Threads) / Pin (Pinterest) / komentar (Facebook).
[6] PUBLISH       Facebook dulu (Reel + tag Shopee native) → Pinterest (video Pin
                  + multi-tag) → Threads (repurpose, 5 menit). Satu video/hari.
[7] META ADS      HANYA video organik pemenang yang lolos 5 gerbang §7.
                  Selain itu: Rp0 iklan. Jangan boost link Shopee langsung.
```

**Kredit Flow (16 Nov 2026):** akun PRO, 1.050 kredit, reset **22 Nov 2026 17:37 WIB**,
tidak ada rollover. Veo 3 Fast ±20 kredit per klip 8 detik → ~50 klip per siklus kredit.
Satu video (3 klip) ≈ 60 kredit → ~17 video per siklus. Prioritaskan produk XTRA/AOV tinggi.

---

## 3. Struktur video — 3 klip

Satu video = 15–30 detik vertikal (9:16, 1080×1920), hook dalam 3 detik pertama,
produk terlihat dipakai, harga + 1 masalah yang diselesaikan tampil di layar.

| Klip | Isi | Durasi | Prompt inti (Flow) |
|------|-----|--------|---------------------|
| 1 — Masalah | Dapur berantakan / barang numpuk / meja penuh | 8 dtk | Tangan saja, tanpa muka; tunjukkan kekacauan ruangan sebelum produk |
| 2 — Produk dipakai | Tangan memakai produk sesuai fungsinya | 8 dtk | Close-up produk (frame awal = foto asli), gerakan halus, cahaya studio |
| 3 — Hasil | Ruangan rapi / bersih / beres | 8 dtk | Hasil akhir yang sama persis dengan produk di klip 2 |

**Voiceover:** diambil dari ULASAN PEMBELI di listing (bukan klaim "aku pakai").
Contoh gaya: "Rating 4.8+, ribuan terjual — apa kata pembelinya?"

**Contoh acuan:** video @osiyoiyoi (dilihat 16 Nov 2026) — 3 klip vertikal looping
faceless, hands-only, pencahayaan studio. Kelemahannya yang harus dihindari:
teks label produk ngaco ("SCHELETT", "PORE CLEARLAR") dan voiceover yang tidak
nyambung dengan gambar. Itu ciri video AI yang gagal QC.

**Aturan teks di video:** seminimal mungkin. Teks label yang digenerate AI hampir
pasti typo — jangan biarkan Flow menulis merek/nama produk di layar.

---

## 4. QC — checklist sebelum upload

Semua harus ✅. Satu ❌ = video tidak di-upload.

- [ ] Produk di video **sama persis** dengan foto Shopee (bentuk, warna, ukuran, merek)
- [ ] Teks/label di video **tidak ngaco** (tidak ada typo merek, tidak ada huruf aneh)
- [ ] Voiceover **nyambung** dengan gambar di klip yang sama
- [ ] Tidak ada klaim pengalaman pribadi ("aku pakai", "hasil di kulitku")
- [ ] Tidak ada kata terlarang di caption/audio: komisi / commission / affiliate
- [ ] Tidak ada klaim garansi ("dijamin", "pasti ampuh", "100%")
- [ ] Durasi total 15–30 detik, format 9:16, 1080×1920
- [ ] Label AI sudah ditambahkan sesuai aturan platform (§5)

QC dilakukan oleh manusia (Kyan/Eman) dari hasil generate Flow — belum ada QC
otomatis. Flow TIDAK bisa dipakai dari API otomatis: generate dilakukan manual
di Google Flow, lalu file video masuk ke pipeline publish.

---

## 5. Aturan per platform (upload)

### 5.1 Facebook — prioritas #1

- Post **natif di aplikasi Facebook** (bukan scheduler/cross-post) supaya banner
  tagging muncul. Reel >10 detik, produk terlihat dipakai & stok tersedia.
- Tag produk via **Affiliate Partnerships** (Professional Dashboard → Monetisation →
  Affiliate Partnerships): cari produk Shopee → "Add to new reel". Satu produk
  per post yang muncul banner-nya.
- Syarat (Shopee Help): 18+, Page atau profil profesional, patuh Meta Monetisation
  Policies, tidak ada riwayat pelanggaran integritas. **Tidak ada angka follower
  resmi** (klaim ~1.000 dari panduan US belum terverifikasi untuk Indonesia).
- **Hati-hati — cap link post:** Meta menguji batas 2 postingan link organik/bulan
  untuk Page non-berbayar (Des 2025–Sep 2026, masih expanding test). Link afiliasi
  partner dikecualikan menurut laporan, dan tagging native melewati batas ini
  sepenuhnya. Jangan andalkan postingan link mentah.
- Label AI: wajib disclose ("AI info") untuk video fotorealistis / audio realistis
  yang dibuat/diubah digital. Video tangan + voiceover AI realistis = kena aturan ini.
- Monetisasi Meta sendiri (Content Monetization, invite-only, dulu 5.000 follower /
  60.000 menit) TIDAK dikejar dulu — komisi affiliate dibayar dari hari pertama.

### 5.2 Pinterest — prioritas #2

- Video Pin: 4 detik–5 menit, MP4/MOV, 9:16 1080×1920. Judul ≤100 karakter
  (pakai kata pencarian Indonesia: "rak kamar kos", "storage kamar sempit",
  "lampu meja aesthetic"), deskripsi ≤800 karakter, **#ad di depan**.
- Tag **semua produk di scene** via tagging native Shopee (kemitraan resmi
  23 Sep 2026, Indonesia + Brazil): hubungkan akun Shopee Affiliate di Pinterest →
  pilih produk eligible di dalam Pinterest → tag di Pin/video. Link afiliasi
  langsung di Pin tetap boleh sebagai fallback.
- **Larangan:** "Creating affiliate Pins repetitively or in large volumes" dilarang.
  Modul sistem dibatasi **maks 1 Pin/hari** (tools/run_pinterest.py).
- Label AI: Pinterest memberi label "AI modified" sendiri (metadata IPTC +
  classifier). Pengguna bisa memilih "see fewer" Pin GenAI di kategori home decor
  (sejak 16 Okt 2025) — risiko jangkauan nyata untuk video AI home-living.
- Umur Pin 3,5+ bulan: Pinterest adalah aset menumpuk, bukan ledakan harian.
  Harapkan start lambat, traffic search datang berbulan-bulan kemudian.

### 5.3 Threads — prioritas #3 (repurpose)

- Video maks 5 menit / 1 GB, MP4/MOV, sampai 20 media per post. Teks maks 500 karakter.
- Link di **reply pertama** + bio hub (maks 5 link/post, 5 link bio). Postingan
  berisi link cenderung dapat engagement kecil → distribusi ikut turun meski
  tidak ada penalti resmi yang terkonfirmasi (Mosseri: link post tidak di-downrank,
  tapi "undervalued" karena engagement rendah).
- API resmi LIVE (token di PC, scope threads_basic + threads_content_publish +
  threads_manage_replies + threads_manage_insights + threads_read_replies).
  Timer systemd: 09:00 dapur / 12:30 organizer / 19:30 kebersihan (WIB).
- Label AI: aturan Meta yang sama dengan Facebook ("Add AI label").
- **Tidak ada** dana kreator, revenue share, atau Bonus Program (berhenti bayar
  musim semi 2025). Threads = distribusi gratis, bukan sumber cuan utama.

---

## 6. Pemilihan produk

Urutan prioritas (riset §6 laporan):

1. **Komisi XTRA** (cek dashboard — XTRA tidak ada cap, dikutip 5–40% vs dasar 4%)
2. **AOV** (harga): organizer Rp300–500 rb di 4% membayar 3–5× per order dibanding
   barang Rp100 rb. Tes produk Rp100–300 rb sedang berjalan (main chat).
3. **Eligibilitas**: hanya Mall / Star+ / Star yang membayar komisi.
4. **Demo-ability**: produknya bisa didemokan tangan saja dalam klip 8 detik.

Kriteria organik standar tetap: rating ≥4,8 · terjual ≥1.000 · Rp20–100 rb.
Produk di luar rentang itu (mis. rak LAZZEN Rp194.999) masuk daftar kandidat
Meta Ads / tes harga tinggi, bukan DB organik.

---

## 7. Meta Ads — JANGAN boost link Shopee langsung

### 7.1 Kenapa ekonomi tidak masuk (komisi standar)

Break-even: **EPC = click-to-purchase × komisi/order**. Untung hanya jika CPC < EPC.

- CPC Indonesia ≈ **Rp1.250–3.000** (CPM Rp19.500–37.363, CTR link 1–2%).
- Produk standar Rp100.000 × 4% = Rp4.000 komisi/order; CVR 2% → EPC = **Rp80/klik**.
- CPA pada CPC Rp2.000 = Rp2.000 ÷ 0,02 = **Rp100.000/order — 25× komisinya**.
- Produk XTRA (total 14%): EPC Rp280 — CPA tetap Rp100.000, **7× komisi**.
- **Break-even di CPC Rp2.000 & CVR 2% butuh komisi/order ≥ Rp100.000**
  (mis. item Rp500.000 di total 20%, atau Rp1 jt+ di 10%+). Di CVR 5% bar turun
  ke Rp40.000/order.

**Tes yang valid** butuh Rp100.000–150.000/hari per ad set selama 5–7 hari
(≈Rp3–5 jt per tes) karena learning phase Meta butuh ~50 event optimasi/minggu.
Minimum teknis hanya ~Rp18.000/hari — tapi itu terlalu kecil untuk menilai apa pun
(Rp50.000/hari = 25 klik/hari di CPC Rp2.000). Plus PPN 12% di invoice Meta (Indonesia).

### 7.2 Yang TIDAK boleh dilakukan

- **Jangan** jadikan URL afiliasi mentah (`shope.ee` / `s.shopee.co.id`) sebagai
  destinasi iklan. Praktik Meta: destinasi harus landing page yang kamu miliki;
  direct-link berisiko ditolak / akun dibatasi. (Konsensus praktisi — belum ada
  halaman resmi Meta yang eksplisit melarang/mengizinkan.)
- **Jangan** pakai "Shopee" sebagai keyword iklan tanpa izin tertulis (T&C Shopee
  6.3(h)); jangan iklan clickbait (6.3(n)/(o)) — pelanggaran bisa bikin komisi
  ditahan / ditarik kembali (6.5).
- **Jangan** pakai objective Sales/Purchase: Meta tidak bisa melihat pembelian
  di Shopee (tidak ada Pixel/CAPI di checkout Shopee) → kampanye tidak pernah belajar.
- **Jangan** klaim palsu di iklan: tanpa personal-attributes ("kamu yang kosnya
  berantakan…"), tanpa before/after palsu, tanpa testimoni palsu, tanpa diskon
  karangan. Harga yang ditampilkan harus harga Shopee yang sebenarnya.

### 7.3 Yang BOLEH: boost Reel pemenang via tagging native

Satu-satunya boost yang dibangun sistem ini:

- **Format:** Use Existing Post / Post ID di Ads Manager — Reel Facebook yang
  sudah ber-tag Shopee native, supaya social proof (like/komen/share) ikut.
- **Objective:** Traffic, optimasi **Landing Page Views** (bukan Link Clicks).
  Engagement (video views) hanya kalau tujuannya social proof / retargeting pool.
  Sales hanya dengan bridge page sendiri + Pixel — di luar scope v2.
- **Placement:** Advantage+ placements, Facebook + Instagram Reels + Feed dulu.
  Threads kini placement default (sejak 19 Okt 2026); cek Breakdown → Placement
  dan potong Threads dengan value rule −90% kalau menghabiskan tanpa order.
  Exclude Audience Network.
- **Struktur:** 1 campaign (Traffic) → 1 ad set → 1 Post ID pemenang.
  Jangan pecah Rp100 rb/hari ke banyak ad set — tidak ada yang belajar.

### 7.4 Alternatif tanpa biaya media: Affiliate Ads (seller-funded)

Shopee + Meta sedang menguji **Affiliate Ads** (diumumkan 6 Jul 2026, pilot terbatas
di Asia Tenggara): seller/brand boleh mempromosikan konten affiliate kreator
sebagai iklan Meta berbayar **setelah mendapat persetujuan kreator** — seller yang
bayar, kreator tetap dapat komisi (+ fee yang dinegosiasikan). Ini satu-satunya
rute berbayar yang tidak membebani kreator dengan masalah break-even.
Kreator tidak bisa mendaftar sendiri; kalau ada seller yang menawarkan boost,
minta syaratnya tertulis (post mana, berapa lama, bayaran di luar komisi).

### 7.5 Lima gerbang boost — SEMUA harus lolos

| # | Gerbang | Pemicu (per video, relatif ke median akun sendiri) |
|---|---------|---------------------------------------------------|
| 1 | Pemenang organik | Di **48 jam**: views ≥ **3× median** video seusia + shares+saves per view di kuartil teratas 30 video terakhir |
| 2 | Sampel cukup | ≥1.000 impressions / ≥500 views **dan** ≥30 klik Shopee organik |
| 3 | Niat klik | Views-to-click ≥ **1%** (atas rentang normal 0,5–2%) |
| 4 | Hitungan uang | **EPC (organik) ≥ 1,5 × CPC yang diharapkan** (Rp1.250–3.000) **dan** komisi/order ≥ Rp40.000 (AOV tinggi / XTRA tinggi) — atau Affiliate Ads seller-funded |
| 5 | Kepatuhan | Tag Shopee native ada di Reel Facebook (atau bridge page + Pixel jalan); label AI sudah ada di post organik; tanpa headline clickbait, tanpa keyword "Shopee", tanpa before/after palsu |

**Video yang lolos gerbang 1–3 tapi gagal gerbang 4: JANGAN dibayar.**
Buat varian organik lagi dari hook/produk itu — videonya aset organik yang bagus,
bukan aset berbayar.

**Protokol tes berbayar (pertama kali):** 1 campaign Traffic–LPV → 1 ad set →
1 Post ID, **Rp100.000/hari, 5 hari**, tanpa edit 4 hari pertama (edit merestart learning).

**Aturan kill:** spend ≥3× target CPA tanpa order di dashboard Shopee → pause.
CPC > EPC 3 hari berturut-turut → pause. CPA > komisi/order setelah 5 hari → pause,
jangan "dioptimasi" lagi.

**Aturan scale (hanya jika CPA < komisi/order setelah 5 hari):** +20–30% budget
tiap 2–3 hari, tidak pernah >50% sekali lompat. Nilai dari dashboard Shopee
(order/EPC), **bukan** ROAS Meta (Meta tidak melihat revenue Shopee).

**Catatan:** pemenang Pinterest TIDAK di-boost via Meta Ads (tidak ada placement
Meta di Pinterest; pemenang Pinterest = sinyal untuk membuat lebih banyak video
seperti itu). Pemenang Threads = sinyal untuk copy/hook, bukan target boost.

---

## 8. Modul auto-komen — tools/auto_comment.py

Tujuan: komen di postingan RAMAI di niche home living/kos-kosan supaya orang
penasaran cek profil → profil berisi postingan produk + link.

**Cara kerja:**

1. Target dari file `--targets` (post ID / URL Threads per baris, opsional
   `post_id<TAB>topik`) atau pencarian keyword Threads API (`--search`).
2. Draf komen dipilih acak dari template gaya hook v5.1 — tiga gaya:
   `tanya_rating` (tanya rating/ulasan pembeli), `info_fungsi` (info fungsi produk),
   `tips` (tips memilih: cek rating, ukur space, baca ulasan bintang 3–4).
3. Setiap draf wajib lolos guardrail `tools/check_draft.py` (kata terlarang,
   klaim review, bahasa garansi) + cek tambahan: maks 200 karakter, tanpa URL,
   tanpa ajakan beli ("cek link", "link di bio", "checkout", "beli sekarang").
   Gagal = skip + catat alasan.
4. Live: kirim sebagai reply via Threads API resmi (`publish_api.publish_text`
   dengan `reply_to_id`), lalu catat ke `data/comment_history.json`.

**Batasan keamanan (keras):**

- **Maks 10 komen/hari**, jeda acak **10–30 menit** antar komen (live).
- Jangan komen 2× di postingan yang sama (cek riwayat).
- Jangan komen di postingan sendiri (cek `username` pemilik sebelum kirim).
- **Link affiliate TIDAK PERNAH** ditaruh di komen postingan orang lain.
- Default mode = `--dry-run` (hanya cetak draf + hasil guardrail, tidak kirim).
  Live hanya dengan flag eksplisit `--live`.
- Facebook + Pinterest = **stub** (fungsi ada, melempar NotImplementedError
  "belum tersedia — menunggu API"). Jangan pura-pura jalan.

**Contoh pakai:**

```bash
python tools/auto_comment.py --targets data/comment_targets.txt --dry-run
python tools/auto_comment.py --targets data/comment_targets.txt --live
python tools/auto_comment.py --search "rak dapur kos" --live
python tools/auto_comment.py --text "Ratingnya 4.8+, ulasan pembelinya bilang apa?" --dry-run
```

**Catatan kejujuran:** endpoint keyword search Threads API (`/keyword_search`)
belum terverifikasi jalan di app ini — kalau gagal, tool otomatis jatuh ke
file `--targets` dan mencetak peringatan. Fitur ini belum diuji live
(tidak ada komen yang dikirim saat penulisan dokumen ini).

---

## 9. Metrik & aturan keputusan (per platform, mingguan)

Sumber kebenaran uang = **dashboard Shopee Affiliate**. Analitik platform hanya
indikator awal.

| Metrik | Definisi | "Bagus" (arah, bukan angka mutlak) |
|--------|----------|-------------------------------------|
| Views / impressions | Views platform | Bandingkan dengan median akun sendiri |
| Views-to-click (VTC) | Klik Shopee ÷ views | Video sosial normal 0,5–2%; <0,5% = masalah hook/CTA |
| Click-to-purchase (CVR) | Order Shopee ÷ klik Shopee | Afiliasi umum 1–5%; video short-form 2–4% |
| EPC | Komisi ÷ klik Shopee | Satu-satunya metrik uang lintas platform. EPC = CVR × komisi/order |
| Order, komisi, AOV | Dashboard Shopee | Lacak per video (link per produk / UTM) |
| Saves/shares (Pinterest) | Saves ÷ views | Indikator awal traffic long-tail |
| Replies / kedalaman reply (Threads) | Reply per post | Indikator awal distribusi Threads |

**Aturan keputusan (setelah 30 video / ~30 hari, min ~30 klik Shopee per platform):**

- Gandakan platform dengan **EPC tertinggi DAN klik ≥2× platform lain**.
- Kalau EPC seri, pilih yang VTC-nya lebih tinggi (perhatian lebih murah).
- Matikan platform hanya jika setelah 30 postingan: VTC <0,3% **dan** nol order.
  Sebelum itu sampelnya terlalu kecil untuk menghakimi.

**Ritme laporan:** laporan mingguan EPC (sesuai model operasi yang disetujui),
bukan persetujuan per post.

---

## 10. Status channel — 16 Nov 2026 malam

| Channel | Status |
|---------|--------|
| Threads @temuanhariann.id | **LIVE** — API resmi, token di PC `~/.threads_poster/threads_token.env` (mode 600). Timer systemd 09:00 / 12:30 / 19:30 WIB. Template hook v5.1 (117 hook, 9 gaya). Post Kikkoman lama (DfzLtteH2Zl) tetap live atas perintah Kyan — jangan dihapus. |
| Facebook Page Temuan Harian | **0 follower.** Belum ada modul posting otomatis. Tagging native Shopee (Affiliate Partnerships) belum dihubungkan — perlu dicek di Professional Dashboard Page. |
| Pinterest "Shopee Harian" (@215kyan) | **Business account JADI** (konversi 16 Nov 2026 19:11 WIB). **App developer DIJEDA** — form di developers.pinterest.com sudah diisi tapi belum disubmit: butuh link website + link privacy policy + ikon app. **Website DITUNDA** atas perintah Kyan ("nanti dulu", maunya mirip jagonya.my.id). Logo dipilih: background oranye (ikon app/profil), putih (header web). Timer Pinterest (`pinterest-1000.timer`) **disabled** sampai token + board + image URL ada. |
| Google Flow | Akun PRO, 1.050 kredit, reset 22 Nov 2026 17:37 WIB. Generate manual di Flow (tidak ada API otomatis). |
| Meta Ads | **Belum ada akun iklan yang dipakai.** Rp0 sampai ada video yang lolos 5 gerbang §7. |
| Auto-komen | Tool baru (tools/auto_comment.py), dry-run terverifikasi, **belum pernah live**. |

---

## 11. Yang masih harus dikerjakan

1. **Website Shopee Harian** (mirip jagonya.my.id) — prasyarat submit app Pinterest
   (butuh link website + privacy policy). Domain shopeeharian.my.id direncanakan
   diambil Jumat 20 Nov 2026 (promo domain gratis) — belum dimiliki.
2. **Submit app Pinterest** → Trial token → simpan di PC
   `~/.pinterest_poster/pinterest_token.env` (mode 600) → isi `board_id` di
   config.yaml (board home living/kos-kosan belum ada — buat dulu) → isi kolom
   Image URL di DB → apply Standard access (video demo OAuth) → baru enable timer.
3. **Hubungkan Facebook Affiliate Partnerships** di Page Temuan Harian + cek
   apakah tombol boost aktif di Reel ber-tag.
4. **Modul publish Facebook Reels** (API) — belum ada; posting FB masih manual.
5. **Pipeline video**: Flow generate manual → file video → publish 3 platform.
   Belum ada skrip yang menyambungkan file video ke `publish_api.py` /
   `run_pinterest.py` (keduanya baru menangani teks/gambar).
6. **Uji live auto-komen** (1–2 komen, pantau 24 jam) sebelum dipakai harian.
7. **Tracking EPC per video** — sheet/laporan mingguan belum dibuat.
8. **Sinkronisasi VM ↔ PC**: VM masih di guardrail + post3 v4 (PC sudah v5/v5.1)
   — keputusan sync masih terbuka.

---

## 12. Sumber riset utama

- Pinterest Newsroom (primer, terverifikasi live 16 Nov 2026):
  https://newsroom.pinterest.com/en-sg/news/shopeexpinterest-affiliate-partnership/
- Shopee Indonesia (primer): https://shopee.co.id/m/affiliates
- Shopee Help PH — Facebook Affiliate Partnerships:
  https://help.shopee.ph/portal/10/article/185198
- Shopee Help ID — T&C Affiliate Individu (primer):
  https://help.shopee.co.id/portal/4/article/71217
- Selular.ID — Instagram Affiliate Partnerships + Affiliate Ads pilot (6 Jul 2026):
  https://selular.id/2026/07/shopee-dan-meta-perluas-program-afiliasi-ke-instagram/
- DataReportal Digital 2027 Indonesia:
  https://datareportal.com/reports/digital-2027-indonesia
- Laporan riset lengkap (VM):
  `~/workspace/research_notes/shopee-affiliate-video-platforms-20261116-1221/report.md`
