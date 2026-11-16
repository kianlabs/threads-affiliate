# Cara Mengisi Database Link (data/affiliate_links.md)

Database ini adalah satu-satunya sumber produk untuk sistem v1. Tidak ada API,
tidak ada scraping — semua link di-generate offline dengan
`tools/link_builder.py` (format an_redir resmi Shopee) dari URL produk.
Dashboard TIDAK bisa dipakai ambil link (diblokir traffic-error, 16 Nov 2026).
Target awal: **50–100 link** (3 kategori home living), cukup untuk
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

## Langkah 3 — Generate link + Sub-ID (pakai generator, BUKAN dashboard)

Dashboard affiliate TIDAK bisa dipakai ambil link (16 Nov 2026: halaman
Komisi XTRA + Custom Link kena traffic-error di browser cloud 3x DAN browser
PC 1x — blokir nempel di akun/sesi). Jadi link dirakit offline:

```bash
python tools/link_builder.py --url <URL produk Shopee> --sub-id threads<kategori><yyyymmdd>
# contoh: python tools/link_builder.py --url https://shopee.co.id/product/197194072/29010572769 --sub-id threadsdapur20261116
```

- Generator membaca `affiliate_id` dari `config.yaml` (11369851901) dan
  memakai format an_redir resmi Shopee — **terverifikasi 16 Nov 2026 14:39
  WIB**: link hasil generator mendarat di halaman produk dengan
  `utm_source=an_11369851901` + `utm_medium=affiliates` (cek: `python
  tools/link_builder.py --self-test`).
- Format Sub-ID: `threads<kategori><tanggal>` — contoh:
  `threadsdapur20261116` (**TANPA tanda hubung** di dalam token — form
  Shopee menolak `-`, cuma huruf+angka yang diterima; terverifikasi langsung
  di form 16 Nov 2026). Generator menaruh token di slot 1 sub_id
  (`v1-v2-v3-v4-v5`, slot 2-5 kosong).
  (Sub-ID dipakai untuk melacak klik & konversi per slot/kategori di
  laporan Shopee).
- JANGAN bungkus dengan bit.ly/s.id (tracking bisa gagal + melanggar S&K).
- Catatan: Commissions XTRA untuk link rakitan manual BELUM terverifikasi —
  cek Click Report setelah ada klik nyata sebelum mengandalkan XTRA.

## Langkah 4 — Masukkan ke tabel

Tambahkan satu baris di bawah kategori yang sesuai di `data/affiliate_links.md`:

```
| 1 | Nama Produk Persis di Listing | `https://s.shopee.co.id/XXXXX` | ❌ UNUSED | - | threadsdapur20261116 |
```

## Langkah 4b — Kolom Image URL (wajib untuk Pinterest, opsional untuk Threads)

Tambahkan kolom ke-7 `Image URL` di tiap baris (boleh kosong kalau produk
hanya dipakai Threads):

```
| 1 | Nama Produk Persis di Listing | `https://s.shopee.co.id/XXXXX` | ❌ UNUSED | - | threadsdapur20261116 | https://cf.shopee.co.id/file/xxx |
```

- URL gambar produk dari listing Shopee: buka halaman produk, klik kanan
  gambar utama, "Copy image address" (URL `https://cf.shopee.co.id/file/...`).
- Tanpa Image URL, `tools/run_pinterest.py` BATAL dengan pesan jelas —
  sistem TIDAK scraping gambar dari Shopee.
- Parser Threads mengabaikan kolom tambahan di belakang, jadi format ini
  tetap kompatibel dengan `run_slot.py`.

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
