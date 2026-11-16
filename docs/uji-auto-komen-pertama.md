# Uji Auto-Komen Pertama — DRY-RUN (belum dikirim)

> **STATUS: BUTUH APPROVAL Kyan sebelum `--live`. Tidak ada komen yang dikirim
> dalam uji ini. Semua langkah di bawah hanya dry-run.**

Tanggal uji: 16 Nov 2026 malam.
Tool: `tools/auto_comment.py` (dry-run default).

## Kenapa target dari pencarian web, bukan `--search`

`--search` dicoba 3 keyword niche (`rak dapur`, `organizer kos`,
`pembersih rumah`) — ketiganya gagal dengan error yang sama dari Threads API:

```
Threads API 403 GET /keyword_search: {"error": {"message":
"Application does not have permission for this action",
"type": "THApiException", "code": 10}}
```

Artinya endpoint `/keyword_search` **tidak tersedia untuk app
'TemuanHarian Threads API'** (belum diterbitkan, tanpa App Review).
Tool jatuh otomatis ke file `--targets` sesuai desain. Sampai ada App Review /
izin search, target harus dicari manual (pencarian web / pantau feed) lalu
dimasukkan ke file target.

## Target 1

- **URL:** https://www.threads.com/@ginakuhana/post/DfctjUKkmhz
- **Post ID:** `DfctjUKkmhz`
- **Penulis:** @ginakuhana
- **Isi postingan:** Foto "RAK GANTUNG SERBAGUNA" — rak tempel dinding kamar
  mandi/kos 3x3 m, anti karat, perekat kuat, tanpa bor. Penulis cerita baru
  sadar rak tempel bisa bikin kamar kos berantakan jadi rapi tanpa bor
  (takut kena denda kos). Diposting 7 Nov 2026.
- **Kenapa dipilih:** Niche organizer/kos-kosan, produknya sejalan dengan
  kategori organizer di DB (rak gantung). Penulis sudah menerima link Shopee
  di reply-nya sendiri — audiensnya sedang dalam mode cari produk.

### Draf komen 1 (v3 — formula hook v2)

> Izin kak, raknya nempel tanpa bor — katanya perekat kuat anti karat, buat yang berat-berat berani nggak, apa cuma buat yang ringan?

- Panjang: 131 karakter (range v2: 100–200)
- Formula: detail OP ("raknya nempel tanpa bor") + bukti ("katanya perekat
  kuat anti karat" — klaim OP sendiri dari postingannya) + pertanyaan
  pilihan ("buat yang berat-berat berani nggak, apa cuma buat yang ringan?")
- Hook pembuka: `Izin kak` · gaya template v2: `curiosity_gap`
- Regenerasi: `python3 tools/auto_comment.py --targets /tmp/targets-uji1.txt --dry-run --seed 1 --opener "Izin kak" --style curiosity_gap` → exit 0
- **Hasil guardrail: ✅ LOLOS** (`--targets --dry-run` + `--text` check,
  exit 0 — tanpa kata terlarang, tanpa link, tanpa ajakan beli, tanpa
  klaim pribadi, tanpa superlatif)

**Kenapa lebih baik dari v2:** v2 ("ulasan pembeli paling jujur soal rak
gantung serbaguna apa?", 94 karakter) tidak punya detail spesifik
postingan (bisa ditempel di postingan rak mana saja), tidak ada
curiosity gap, dan "paling jujur" adalah superlatif tanpa bukti.
V3 menyebut detail foto (tanpa bor), menguji klaim OP sendiri
(perekat kuat anti karat), dan menutup dengan pertanyaan pilihan yang
gampang dijawab OP.

## Target 2

- **URL:** https://www.threads.com/@inspirasi.rumah26/post/Dfl11LgEXJY
- **Post ID:** `Dfl11LgEXJY`
- **Penulis:** @inspirasi.rumah26 (110 followers)
- **Isi postingan:** Cerita kamar kos sempit dan berantakan bikin stres,
  lalu pasang rak gantung dinding — kamar langsung terasa lebih nyaman dan
  rapi. Postingan diakhiri pertanyaan ke audiens: sudah punya rak gantung
  serupa atau belum. Diposting 11 Nov 2026.
- **Kenapa dipilih:** Niche organizer/kos-kosan, audiensnya sedang
  membicarakan masalah yang sama dengan produk di DB (rak dinding).
  Pertanyaan di akhir postingan mengundang balasan — komen yang relevan
  tidak terlihat seperti spam.

### Draf komen 2 (v3 — formula hook v2)

> Relate banget kak, kamar kos sempit pasang rak dinding — langsung rapi, yang vertikal apa yang susun, yang mana lebih ngebantu biar nggak numpuk?

- Panjang: 145 karakter (range v2: 100–200)
- Formula: detail OP ("kamar kos sempit pasang rak dinding") + bukti
  ("langsung rapi" — hasil yang OP ceritakan sendiri) + pertanyaan
  pilihan ("yang vertikal apa yang susun")
- Hook pembuka: TIDAK ADA opener "Izin kak" di komen ini — variasikan
  (aturan v2: opener tidak di semua komen) · gaya template v2:
  `relatable_pain`
- Regenerasi: `python3 tools/auto_comment.py --targets /tmp/targets-uji2.txt --dry-run --seed 1 --opener none --style relatable_pain` → exit 0
- **Hasil guardrail: ✅ LOLOS** (`--targets --dry-run` + `--text` check,
  exit 0 — tanpa kata terlarang, tanpa link, tanpa ajakan beli, tanpa
  klaim pribadi, tanpa superlatif)

**Kenapa lebih baik dari v2:** v2 ("buat kamar kos sempit rak dinding
kamar kos ngebantu banget, fungsinya buat nyimpen biar nggak numpuk",
115 karakter) adalah pernyataan umum tanpa pertanyaan — OP tidak punya
alasan membalas. V3 membuka dengan relatabilitas ("Relate banget kak"),
menyebut hasil OP sendiri, dan menutup dengan pilihan A/B yang
gampang dijawab.

## Formula hook v2 (riset 16 Nov 2026)

Sumber: `~/workspace/research_notes/threads-reply-hooks-research-20261116-1253/report.md`
(GitHub: d4ncboz, msyamsularif, rediumvex, Sekolah76/syadagentic,
akbarseft86, sergebulaev, Affitor).

**Formula:** 1 detail spesifik dari postingan target + 1 sinyal bukti
nyata + 1 pertanyaan pilihan/tebakan. 100–200 karakter, tanpa link,
tanpa nama produk di hook, tanpa klaim pengalaman pribadi.
`tools/auto_comment.py` kini punya 10 template v2 dalam 8 pola
(curiosity_gap, relatable_pain, specific_question, hot_take,
social_proof, humor, specificity_data, permission_reframe) dengan slot
`{detail}` dan `{bukti}`. File target diperluas: kolom TAB ke-3 =
detail, ke-4 = bukti. Flag baru: `--detail`, `--proof`, `--opener none`,
`--v1` (kembali ke template lama).

**Bukti terverifikasi (angka listing Shopee, dicek langsung 16 Nov 2026):**

| Produk DB | Bukti | Sumber |
|---|---|---|
| YESALL Rak Dapur Serbaguna | rating 4,9 dari 4.452 ulasan | shopee.co.id/product/1043883019/27672762637 |
| WARS Rak Dapur Panci Wajan | rating 4,8 dari 1.581 ulasan | shopee.co.id/product/21738068/25602903412 |

Tersimpan di `VERIFIED_PROOFS` di `tools/auto_comment.py` (diambil via
`--product`). **Catatan jujur:** kedua produk itu BUKAN rak tempel
dinding — jadi angkanya TIDAK dipakai di 2 draf uji ini (memakainya
berarti mengarang atribusi). Untuk kedua target ini `{bukti}` diisi
klaim OP sendiri yang bisa dicek dari postingannya (perekat kuat anti
karat / kamar langsung rapi). Angka listing hanya dipakai bila target
cocok dengan jenis produknya.

**Bug yang ketemu & diperbaiki saat uji v3:** `pick_template_v2()`
menempel opener di depan template yang diawali "Kak," sehingga
hasilnya "Izin kak, kak, ..." (sapaan dobel). Diperbaiki: sapaan "kak"
di badan template dibuang otomatis bila opener dipakai. Template v1
"Ulasan pembeli paling jujur..." juga diperbaiki (melanggar aturan
superlatif v2 yang baru) — guardrail baru menolak superlatif/garansi
("paling jujur/murah", "dijamin", "pasti ampuh").

## Foto/video di komen — hasil cek API (16 Nov 2026 19:46)

**BISA secara API.** Threads API mendukung reply bermedia: container
`media_type=IMAGE` + `image_url` (atau `VIDEO` + `video_url`) +
`reply_to_id`, alur dua tahap (buat container → poll FINISHED → publish).
Implementasi: `publish_api.publish_media_reply()` + flag opsional
`--image-url` / `--video-url` / `--product` di `tools/auto_comment.py`
(keduanya saling eksklusif; URL harus publik `https://`).

**TAPI saat ini belum bisa dipakai — Image URL di DB masih kosong.**
Kolom Image URL (ke-7) di `data/affiliate_links.md` terisi **0 dari 29
produk** (itu juga sebabnya dry-run Pinterest abort). Sampai Image URL
diisi dari foto listing Shopee, komen jalan **teks saja** — tool memberi
peringatan jelas (`Produk '...' belum punya Image URL di DB — komen
jalan teks saja`) dan tetap lanjut. `--product` tanpa Image URL terverifikasi
di dry-run: warning muncul, draf tetap LOLOS.

**Keputusan:** foto/video produk tetap tampil di postingan akun sendiri
(Threads post + FB Reel + Pinterest Pin). Komen ke postingan orang lain
tetap teks saja untuk sekarang — komen berfoto di postingan orang lebih
gampang dikira iklan/spam, dan tanpa Image URL di DB pun tidak ada yang
bisa dilampirkan. Setelah Image URL terisi, media di komen dipakai hemat:
hanya bila foto produk relevan langsung dengan isi postingan target.

**Belum terverifikasi:** pengiriman reply bermedia live (belum pernah
dicoba untuk app ini) — uji live pertama wajib dry-run dulu + approval Kyan.

## Cara kirim (setelah approval Kyan)

```bash
# 1. Tulis target ke file (post ID + topik + detail + bukti, dipisah TAB)
printf "DfctjUKkmhz\trak gantung serbaguna\traknya nempel tanpa bor\tkatanya perekat kuat anti karat\nDfl11LgEXJY\trak dinding kamar kos\tkamar kos sempit pasang rak dinding\tlangsung rapi\n" > /tmp/targets-uji.txt

# 2. Dry-run dulu, cek draf v3-nya
python3 tools/auto_comment.py --targets /tmp/targets-uji.txt --dry-run --seed 1

# 3. Kirim HANYA 2 komen ini (limit harian tool: 10, jeda 10-30 menit otomatis)
python3 tools/auto_comment.py --targets /tmp/targets-uji.txt --live

# 3. Pantau 24 jam: apakah ada balasan / kunjungan profil / kena limit?
#    Hasil pantauan dicatat di sini sebelum uji lanjutan.
```

## Catatan jujur

- **Engagement target tidak besar.** Kedua postingan di atas ditemukan lewat
  pencarian web; data like/komen di indeks pencarian tidak lengkap (target 1:
  1 komen tercatat; target 2: jumlah like tidak tampil). Ini postingan
  niche yang relevan, bukan postingan viral besar — "ramai" di niche ini
  memang skalanya kecil. Kalau Kyan mau target yang lebih ramai, cari manual
  di feed Threads (topik kos-kosan / home living) dan catat URL-nya.
- **Bug yang ketemu & diperbaiki saat uji ini:** `pick_template()` di
  `tools/auto_comment.py` mengganti kata `ini` dengan `str.replace`,
  sehingga template "Yang kayak gini..." jadi "Yang kayak grak dinding
  kamar kos..." (huruf `ini` di dalam kata `gini` ikut keganti). Diperbaiki
  jadi regex kata utuh (`\bini\b`), dry-run ulang lolos dengan teks benar.
- **Belum terverifikasi:** pengiriman live (belum pernah dicoba), dan apakah
  Threads membatasi reply dari akun ini setelah beberapa komen.
- **Aturan yang ditegakkan tool (v3):** tanpa link di komen orang lain, tanpa kata
  komisi/affiliate, tanpa klaim pengalaman pribadi, tanpa superlatif/garansi
  ("paling jujur", "dijamin"), hook pembuka sopan bervariasi (tidak di semua
  komen), formula v2 (detail + bukti + pertanyaan pilihan), 100–200 karakter,
  maks 10 komen/hari, jeda acak 10–30 menit, tidak komen 2x di postingan yang
  sama, tidak komen di postingan sendiri.

## Hasil LIVE — GAGAL (16 Nov 2026 20:08 WIB)

> **STATUS: GAGAL — 0 komen terkirim. Kyan sudah menyetujui pengiriman
> (20:06 WIB), tapi Threads API menolak. BERHENTI sesuai aturan: tidak
> dicoba jalur lain (tanpa Playwright/cookie).**

### Komen 1 — @ginakuhana / DfctjUKkmhz — GAGAL 20:08:47 WIB

- Perintah: python3 tools/auto_comment.py --targets /tmp/targets-uji1.txt --live --seed 1 --opener "Izin kak" --style curiosity_gap
- Dry-run sebelumnya: teks regenerasi PERSIS sama dengan yang disetujui (131 karakter, LOLOS).
- Error 1 (cek pemilik, warning — tool lanjut kirim): Threads API 400 GET /DfctjUKkmhz: "Unsupported get request. Object with ID 'DfctjUKkmhz' does not exist, cannot be loaded due to missing permissions, or does not support this operation" (code 100, subcode 33)
- Error 2 (kirim, fatal): Threads API 500 POST /me/threads: "Param reply_to_id is not a valid threads_media ID" (code 100)
- Output tool: [LIVE] Terkirim: 0, dilewati/ditolak: 1.
- Tercatat di data/comment_history.json (tidak di-commit): 1 entri, status failed, alasan = error 2 di atas.

### Komen 2 — @inspirasi.rumah26 / Dfl11LgEXJY — TIDAK DIKIRIM

- Tidak dicoba. Aturan tugas: kalau API error, BERHENTI — tidak coba jalur
  lain. Kemungkinan besar gagal dengan error yang sama (masalahnya di
  reply_to_id, bukan di target spesifik).

### Dugaan penyebab (BELUM terverifikasi — perlu pengecekan, bukan klaim)

- reply_to_id mungkin butuh ID media numerik Threads, bukan kode pendek
  publik (DfctjUKkmhz adalah kode URL, bukan ID media API). Tool saat ini
  memakai kode pendek langsung sebagai reply_to_id.
- Error 400 saat GET postingan juga menandakan app (belum diterbitkan,
  tanpa App Review) mungkin tidak bisa membaca postingan orang lain —
  sejalan dengan /keyword_search yang 403 sebelumnya.
- Yang perlu dicek berikutnya (oleh developer, bukan dengan kirim ulang
  buta): bagaimana cara dapat ID media numerik sebuah postingan Threads
  (misal via oEmbed / tampilan web / endpoint lain), dan apakah scope
  threads_manage_replies saja cukup untuk reply ke postingan orang lain.

## Retry LIVE dengan ID numerik — GAGAL LAGI (16 Nov 2026 20:31 WIB)

> **STATUS: GAGAL — 0 komen terkirim. Retry memakai ID numerik hasil decode
> shortcode. Komen 2 TIDAK DIKIRIM (aturan tugas: kalau komen 1 gagal,
> BERHENTI — tanpa Playwright/cookie/repo privat).**

### Perbaikan tool sebelum retry

- `tools/auto_comment.py` sekarang punya `decode_shortcode()` +
  `resolve_media_id()` (alfabet Instagram base64 `A-Za-z0-9-_`).
  Unit check lolos: `DfctjUKkmhz` -> `4025292505889269875`,
  `Dfl11LgEXJY` -> `4027862192699306584` (round-trip encode kembali ke
  shortcode yang sama — implementasi decode-nya benar).
- Dry-run sebelum live: target ter-resolve ke `4025292505889269875`, teks
  regenerasi PERSIS sama dengan yang disetujui Kyan (131 karakter, LOLOS).

### Komen 1 — @ginakuhana / 4025292505889269875 — GAGAL 20:31:05 WIB

- Perintah: python3 tools/auto_comment.py --targets /tmp/targets-uji1.txt --live --seed 1 --opener "Izin kak" --style curiosity_gap
- Error 1 (cek pemilik, warning — tool lanjut kirim): Threads API 400 GET /4025292505889269875: "Unsupported get request. Object with ID '4025292505889269875' does not exist, cannot be loaded due to missing permissions, or does not support this operation" (code 100, subcode 33)
- Error 2 (kirim, fatal): Threads API 500 POST /me/threads: "Param reply_to_id is not a valid threads_media ID" (code 100)
- Output tool: [LIVE] Terkirim: 0, dilewati/ditolak: 1.
- Tercatat di data/comment_history.json (tidak di-commit): entri ke-2, status failed, post_id numerik, alasan = error 2 di atas.

### Komen 2 — @inspirasi.rumah26 / 4027862192699306584 — TIDAK DIKIRIM

- Tidak dicoba, sesuai aturan berhenti saat komen 1 gagal.

### Bukti penentu: decode shortcode BUKAN ID media Threads API

- Postingan kita sendiri (Kikkoman repost) tercatat di
  `data/post_history.json`: permalink shortcode `DfzOch6n5SE` tapi
  `media_id` API = `18135902441497212`. Decode Instagram-base64 dari
  `DfzOch6n5SE` = `4031629624640246916` — TIDAK SAMA.
- Kesimpulan: shortcode Threads TIDAK bisa di-decode jadi ID media API
  Threads dengan alfabet Instagram. ID media Threads API punya namespace
  sendiri (contoh: 17 digit diawali 18...). Jadi retry dengan ID hasil
  decode pasti gagal — dan memang gagal dengan error yang sama persis.
- Yang masih perlu dijawab (bukan dengan kirim ulang buta): dari mana
  mendapatkan ID media numerik Threads API untuk postingan orang lain.
  API resmi TIDAK punya endpoint URL -> media ID, dan membaca postingan
  orang lain butuh Advanced Access / App Review (GET 400 subcode 33
  konsisten dengan itu). Sampai ada sumber ID yang valid, auto-komen ke
  postingan orang lain via API resmi TIDAK BISA jalan.
