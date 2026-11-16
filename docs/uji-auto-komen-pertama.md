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

### Draf komen 1

> Ulasan pembeli paling jujur soal rak gantung serbaguna apa? Penasaran sebelum milih.

- Panjang: 84 karakter (maks 200)
- Gaya template: `tanya_rating`
- **Hasil guardrail: ✅ LOLOS** (`--text` check, exit 0 — tanpa kata
  terlarang, tanpa link, tanpa ajakan beli, tanpa klaim pribadi)

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

### Draf komen 2

> Buat kamar kos sempit rak dinding kamar kos ngebantu banget, fungsinya buat nyimpen biar nggak numpuk.

- Panjang: 102 karakter (maks 200)
- Gaya template: `info_fungsi`
- **Hasil guardrail: ✅ LOLOS** (`--text` check, exit 0 — tanpa kata
  terlarang, tanpa link, tanpa ajakan beli, tanpa klaim pribadi)

## Cara kirim (setelah approval Kyan)

```bash
# 1. Tulis target ke file (post ID + topik, dipisah TAB)
printf "DfctjUKkmhz\trak gantung serbaguna\nDfl11LgEXJY\trak dinding kamar kos\n" > /tmp/targets-uji.txt

# 2. Kirim HANYA 2 komen ini (limit harian tool: 10, jeda 10-30 menit otomatis)
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
- **Aturan yang ditegakkan tool:** tanpa link di komen orang lain, tanpa kata
  komisi/affiliate, tanpa klaim pengalaman pribadi, maks 10 komen/hari,
  jeda acak 10–30 menit, tidak komen 2x di postingan yang sama, tidak komen
  di postingan sendiri.
