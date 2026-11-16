# Cara Mengisi Database Link (data/affiliate_links.md)

Database ini adalah satu-satunya sumber produk untuk sistem v1. Tidak ada API,
tidak ada scraping — semua link dimasukkan manual dari dashboard Shopee
Affiliate. Target awal: **50–100 link** (4 kategori beauty), cukup untuk
±3–4 minggu posting 3x/hari.

## Langkah 1 — Buka dashboard

1. Buka https://affiliate.shopee.co.id/ (login sebagai akun **'pratama'**).
2. Menu **Penawaran → Produk** (Product Offer) untuk cari produk, atau
   **Penawaran → Komisi XTRA** untuk produk ber-Komisi XTRA (didahulukan).

## Langkah 2 — Pilih produk sesuai kriteria (config.yaml)

Coret produk yang TIDAK memenuhi salah satu saja:

| Kriteria | Cara cek | Syarat |
|---|---|---|
| Rating | Buka halaman produk Shopee-nya (UI affiliate TIDAK menampilkan rating) | ≥ 4,8 |
| Terjual | Angka "Terjual" di halaman produk | ≥ 1.000 |
| Harga | Harga varian termurah di listing | Rp20.000 – Rp100.000 |
| Seller | Badge di toko | Star / Star+ / Shopee Mall |
| Komisi XTRA | Label XTRA di daftar Penawaran | WAJIB ada |

Alasan: komisi base Shopee kecil (maks 4%, cap Rp10 rb). Uang sebenarnya
dari Komisi XTRA. Produk tanpa XTRA tidak masuk database.

## Langkah 3 — Generate link + Sub-ID

1. Di dashboard: **Penawaran → Link Khusus / Custom Link**
   (atau **Batch Get Link** kalau mau banyak sekaligus).
2. Tempel URL produk → isi kolom **tag/Sub-ID** dengan format:
   `threads-<kategori>-<tanggal>` — contoh: `threads-skincare-20261116`
   (Sub-ID dipakai untuk melacak klik & konversi per slot/kategori di
   laporan Shopee).
3. Klik **Buat Link** → salin shortlink `s.shopee.co.id/...` yang dihasilkan.
4. JANGAN bungkus dengan bit.ly/s.id (tracking bisa gagal + melanggar S&K).

## Langkah 4 — Masukkan ke tabel

Tambahkan satu baris di bawah kategori yang sesuai di `data/affiliate_links.md`:

```
| 1 | Nama Produk Persis di Listing | `https://s.shopee.co.id/XXXXX` | ❌ UNUSED | - | threads-skincare-20261116 |
```

Perhatikan:

- Nama produk: tulis persis seperti di listing (dipakai sebagai `{product}`
  di template).
- Link **wajib** dibungkus backtick `` ` `` — tanpa backtick, baris TIDAK
  terbaca parser (baris dilewati diam-diam).
- Status awal selalu `❌ UNUSED`, Last Used `-`.
- Nomor `#` urut per kategori (1, 2, 3, ...).
- Jangan memasukkan produk yang sama dua kali (link tidak boleh duplikat).

## Langkah 5 — Verifikasi sebelum jalan

```bash
cd threads-affiliate-system
export PYTHONPATH="$PWD/vendor/threads-affiliate"
python -m threads_poster.cli db --db data/affiliate_links.md --stats
python tools/check_draft.py --db data/affiliate_links.md
```

`--stats` menampilkan total/available per kategori. Checker DB memastikan
semua baris UNUSED berformat benar (link `s.shopee.co.id`, tanpa duplikat).

## Perawatan

- Isi ulang sebelum database habis (peringatan: < 5 link UNUSED = isi ulang).
- Link yang sudah USED jangan dihapus (riwayat untuk dedup) — kecuali reset
  siklus baru dengan `db --reset` (butuh konfirmasi ketik `yes`).
- Kalau produk berubah harga/habis, hapus barisnya manual dari tabel.
