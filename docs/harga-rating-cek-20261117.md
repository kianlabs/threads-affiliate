# Cek Harga + Rating 50 Produk Shopee Harian — 17 Nov 2026

**Tanggal cek:** 17 Nov 2026, ±09:33–09:45 WIB (crawl halaman Shopee, satu per satu, jeda 6–7 detik antar produk, tanpa paralel).
**Sumber nilai lama:** `data/landing-page-products.json` (riset 16 Nov + 17 Nov pagi; `docs/pick-list-hp.md`, `docs/pick-list-tambahan-21.md`, `data/video_briefs/*-ugc.md`).
**Aturan:** hanya angka yang benar-benar tampil di teks halaman Shopee yang dipakai. Produk yang halamannya tidak terbaca / angkanya tidak tampil: nilai lama dipertahankan, ditandai "tidak terverifikasi 17 Nov".

## Ringkasan

- **Harga berubah (price_min): 9/50**
- **Rating berubah: 7/50** (termasuk 2 produk yang ratingnya sebelumnya null dan kini terisi)
- **Jumlah ulasan berubah: 22/50** (sebagian besar naik tipis; 4 produk turun — angka lama ternyata estimasi bulat dari dashboard affiliate)
- **Tidak terverifikasi: 1/50** (Greenland Tudung Saji — fetch halaman timeout, tidak di-retry)
- **Terverifikasi harga saja (rating tidak tampil di halaman): 6/50** — harga terverifikasi sama, rating/ulasan dipertahankan dari nilai lama
- **Tidak ada indikasi blokir/CAPTCHA** selama 50 pembacaan; 1 kegagalan murni timeout fetch.

## ⚠️ Perubahan harga (9 produk)

| # | Produk | Harga lama → Harga baru | Rating lama → baru | Ulasan lama → baru |
|---|---|---|---|---|
| 2 | ECOCO Cup Washing Brush | Rp76.000 → **Rp64.600 (flash sale, coret Rp76.000, -15%)** | 4.96 → 4.96 | 1689 → 1692 |
| 14 | POLKI Kitchen Cleaner | Rp37.905 (coret Rp75.000, -49%; dari data JSON-LD halaman produk persis, crawl mesin pencari ~12 Nov 2026; harga bisa berubah) → **Rp75.000** | 4.88 → 4.89 | 17292 → 17324 |
| 16 | SAMONO Pompa Galon Lipat | Rp34.399 → **Rp35.399** | 4.95 → 4.95 | 2182 → 2229 |
| 18 | Qiek Deep Fryer 4 in 1 |  → **Rp69.000 (flash sale, coret Rp169.000, -59%)** | – → 4.85 | – → 7902 |
| 20 | Karpet Ruang Tamu 120x180 | Rp123.759 → **Rp171.875** | 4.8 → 4.77 | 4000 → 1541 |
| 36 | ABC BEAR Storage Box Lipat | Rp50.001–213.000 (varian termurah Rp50.001 masuk rentang) → **Rp100.000–600.000** | 4.85 → 4.85 | 3150 → 3150 |
| 41 | BONBOX Mop Stick Set BCT3505 | Rp69.000 → **Rp144.000–150.000** | 4.88 → 4.88 | 10676 → 10692 |
| 42 | BONBOX Twist Mop BCT3903 | Rp49.900 → **Rp50.000 (flash sale, coret Rp70.000, -29%)** | 4.83 → 4.83 | 3618 → 3647 |
| 43 | BONBOX Twist Mop BCT3802 | Rp75.000 → **Rp140.000–300.000** | 4.92 → 4.92 | 3148 → 3164 |

Catatan perubahan harga:

- **POLKI Kitchen Cleaner (#14): diskon -49% hilang** — Rp37.905 → Rp75.000 (harga normal).
- **BONBOX Mop Stick BCT3505 (#41): Rp69.000 → Rp144.000–150.000.** Harga lama kemungkinan harga flash sale/varian termurah saat riset; halaman kini menampilkan rentang Rp144.000–150.000 (8 variasi).
- **BONBOX Twist Mop BCT3802 (#43): Rp75.000 → Rp140.000–300.000** (14 variasi; harga lama kemungkinan varian termurah saat riset).
- **ABC BEAR Storage Box Lipat (#36): Rp50.001–213.000 → Rp100.000–600.000** — naik besar di semua varian.
- **Karpet Ruang Tamu 120x180 (#20): Rp123.759 → Rp171.875** (30 variasi; harga tampil adalah harga varian yang terpilih di halaman).
- **ECOCO Cup Washing Brush (#2): Rp76.000 → Rp64.600** (flash sale -15%, coret Rp76.000).
- **SAMONO Pompa Galon Lipat (#16): Rp34.399 → Rp35.399** (naik Rp1.000).
- **BONBOX Twist Mop BCT3903 (#42): Rp49.900 → Rp50.000** (flash sale, coret Rp70.000, -29%).
- **Qiek Deep Fryer 4 in 1 (#18): sebelumnya semua null → Rp69.000** (flash sale, coret Rp169.000, -59%), rating 4.85, 7902 ulasan — kini terisi lengkap.

Perubahan tampilan harga saja (price_min tetap, tidak dihitung sebagai "harga berubah"):

- **Oxihom Keranjang Roda (#10):** rentang atas Rp52.138 → Rp54.900 (coret Rp44.750–84.750, -35%); bawah tetap Rp32.900.
- **Keset Dapur Anti Slip (#12):** halaman kini hanya menampilkan Rp38.800 (rentang atas Rp48.500 tidak tampil di fetch ini); price_min tetap Rp38.800.
- **10pcs Pisau Dapur (#11):** tampilan disederhanakan jadi "Rp30.688" (catatan lama soal crawl mesin pencari ~10 Nov dihapus karena kini terverifikasi live).

## ⭐ Perubahan rating (7 produk)

| # | Produk | Rating lama → baru | Ulasan lama → baru | Harga |
|---|---|---|---|---|
| 14 | POLKI Kitchen Cleaner | 4.88 → **4.89** | 17292 → 17324 | Rp75.000 |
| 15 | Rak Panci Susun 3 Tingkat | – (null) → **4.88** | – → 5000 | Rp56.999 – Rp114.999 (coret Rp57.999 – Rp117.000, -3%) |
| 18 | Qiek Deep Fryer 4 in 1 | – (null) → **4.85** | – → 7902 | Rp69.000 (flash sale, coret Rp169.000, -59%) |
| 19 | WARS Rak Dapur Panci Wajan | 4.8 → **4.82** | 3000 → 1581 | Rp114.800 |
| 20 | Karpet Ruang Tamu 120x180 | 4.8 → **4.77** | 4000 → 1541 | Rp171.875 |
| 21 | Standing Mirror Oval 30x120 | 4.9 → **4.87** | 1000 → 399 | Rp121.103 |
| 22 | Aescrafy Cermin Frame Bulat | 4.9 → **4.89** | 10000 → 2936 | Rp117.228 |

Catatan: **WARS Rak Dapur (#19), Karpet (#20), Standing Mirror (#21), Aescrafy (#22)** — jumlah ulasan lama (3000 / 4000 / 1000 / 10000) ternyata angka bulat dari dashboard affiliate; angka halaman live jauh lebih kecil (1581 / 1541 / 399 / 2936). Nilai baru yang dipakai adalah angka halaman live.

## ❌ Tidak terverifikasi 17 Nov (1 produk)

| # | Produk | Nilai yang dipertahankan | Penyebab |
|---|---|---|---|
| 9 | Greenland Tudung Saji 4 Susun | Rp35.900 – Rp99.900 (tergantung varian jumlah tingkat); rating 4.8; 1071 ulasan | tidak terverifikasi 17 Nov (fetch halaman timeout) |

## Tabel lengkap 50 produk

| # | Produk | Harga lama → Harga baru | Rating lama → Rating baru | Ulasan lama → Ulasan baru | Status |
|---|---|---|---|---|---|
| 1 | Kikkoman Soy Sauce Dispenser 150ml | Rp24.000 → Rp24.000 | 4.97 → 4.97 | 3046 → 3046 | terverifikasi |
| 2 | ECOCO Cup Washing Brush | Rp76.000 → Rp64.600 (flash sale, coret Rp76.000, -15%) | 4.96 → 4.96 | 1689 → 1692 | terverifikasi **(BERUBAH)** |
| 3 | ECOCO Panda Spons | Rp21.000–51.000 → Rp21.000–51.000 | 4.93 → 4.93 | 2707 → 2707 | terverifikasi |
| 4 | Kotak Penyimpanan Es Portabel | Rp52.268 → Rp52.268 | 4.85 → 4.85 | 468 → 468 | terverifikasi-harga-saja (rating tidak tampil di halaman) |
| 5 | ZuoShu Keset Dapur 2in1 | Rp47.000 → Rp47.000 | 4.86 → 4.86 | 18284 → 18292 | terverifikasi |
| 6 | Pplus Pisau Dapur Diamond 6 in 1 | Rp75.991 → Rp75.991 | 4.85 → 4.85 | 6639 → 6640 | terverifikasi |
| 7 | APEN Pengasah Pisau 3 Slot | Rp26.541 (coret Rp30.000, -12%) → Rp26.541 | 4.75 → 4.75 | 710 → 710 | terverifikasi-harga-saja (rating tidak tampil di halaman) |
| 8 | EASLIVVO Timbangan Dapur 5KG | Rp46.558 → Rp46.558 | – → – | – → – | terverifikasi-harga-saja (rating tidak tampil di halaman) |
| 9 | Greenland Tudung Saji 4 Susun | Rp35.900 – Rp99.900 (tergantung varian jumlah tingkat) → Rp35.900 – Rp99.900 (tergantung varian jumlah tingkat) | 4.8 → 4.8 | 1071 → 1071 | tidak terverifikasi 17 Nov (fetch halaman timeout) |
| 10 | Oxihom Keranjang Roda Dapur | Rp32.900 – Rp52.138 (tergantung varian) → Rp32.900 – Rp54.900 (coret Rp44.750 – Rp84.750, -35%) | 4.86 → 4.86 | 1140 → 1140 | terverifikasi |
| 11 | 10pcs Pisau Dapur Serbaguna | Rp30.688 (dari data JSON-LD halaman produk persis, crawl mesin pencari ~10 Nov 2026; harga bisa berubah) → Rp30.688 | 4.8 → 4.8 | 8781 → 8781 | terverifikasi-harga-saja (rating tidak tampil di halaman) |
| 12 | Keset Dapur Anti Slip 2 in 1 | Rp38.800 – Rp48.500 (tergantung variasi/motif) → Rp38.800 | 4.87 → 4.87 | 2342 → 2356 | terverifikasi (rentang atas tidak tampil di halaman) |
| 13 | YESALL Rak Dapur Serbaguna | Rp72.900 – Rp169.900 (tergantung variasi) → Rp72.900 – Rp169.900 (coret Rp169.900 – Rp319.900, -57%) | 4.9 → 4.9 | 4452 → 4452 | terverifikasi |
| 14 | POLKI Kitchen Cleaner | Rp37.905 (coret Rp75.000, -49%; dari data JSON-LD halaman produk persis, crawl mesin pencari ~12 Nov 2026; harga bisa berubah) → Rp75.000 | 4.88 → 4.89 | 17292 → 17324 | terverifikasi **(BERUBAH)** |
| 15 | Rak Panci Susun 3 Tingkat | Rp56.999 – Rp114.999 (rentang harga, 4 variasi — kemungkinan per jumlah tingkat) → Rp56.999 – Rp114.999 (coret Rp57.999 – Rp117.000, -3%) | – → 4.88 | – → 5000 | terverifikasi **(BERUBAH)** |
| 16 | SAMONO Pompa Galon Lipat | Rp34.399 → Rp35.399 | 4.95 → 4.95 | 2182 → 2229 | terverifikasi **(BERUBAH)** |
| 17 | Waffle Maker Mini Anti Lengket | Rp89.999 (dari Rp93.999, -4%) → Rp89.999 (coret Rp93.999, -4%) | 4.8 → 4.8 | 10656 → 10663 | terverifikasi |
| 18 | Qiek Deep Fryer 4 in 1 |  → Rp69.000 (flash sale, coret Rp169.000, -59%) | – → 4.85 | – → 7902 | terverifikasi **(BERUBAH)** |
| 19 | WARS Rak Dapur Panci Wajan | Rp114.800 → Rp114.800 | 4.8 → 4.82 | 3000 → 1581 | terverifikasi **(BERUBAH)** |
| 20 | Karpet Ruang Tamu 120x180 | Rp123.759 → Rp171.875 | 4.8 → 4.77 | 4000 → 1541 | terverifikasi **(BERUBAH)** |
| 21 | Standing Mirror Oval 30x120 | Rp121.103 → Rp121.103 | 4.9 → 4.87 | 1000 → 399 | terverifikasi **(BERUBAH)** |
| 22 | Aescrafy Cermin Frame Bulat | Rp117.228 → Rp117.228 | 4.9 → 4.89 | 10000 → 2936 | terverifikasi **(BERUBAH)** |
| 23 | ECOCO Natural Wheat Straw Cutting Board | Rp96.000–150.000 (varian termurah Rp96.000) → Rp96.000–150.000 (varian termurah Rp96.000) | 4.94 → 4.94 | 1052 → 1052 | terverifikasi |
| 24 | One Two Cups Gelas Ukur BR10 | Rp13.900–36.900 (varian ≥ Rp20.000 masuk rentang) → Rp13.900–36.900 (coret Rp18.600 – Rp57.700, -36%) | 4.94 → 4.94 | 3339 → 3340 | terverifikasi |
| 25 | One Two Cups Gelas Ukur B4 | Rp10.900–20.900 (varian tertinggi Rp20.900 masuk rentang) → Rp10.900–20.900 (varian tertinggi Rp20.900 masuk rentang) | 4.95 → 4.95 | 1970 → 1970 | terverifikasi |
| 26 | One Two Cups Bar Mat TY3 | Rp27.900–93.900 → Rp27.900–93.900 | 4.96 → 4.96 | 11788 → 11788 | terverifikasi |
| 27 | GRINN LIVING Neron Glass Jar Mini | Rp20.370 → Rp20.370 | 4.92 → 4.92 | 3550 → 3550 | terverifikasi |
| 28 | GRINN LIVING Terra Jar | Rp28.130 → Rp28.130 | 4.9 → 4.9 | 1877 → 1877 | terverifikasi |
| 29 | Talenan Kayu Mahoni Jumbo Premium | Rp25.000–47.440 (coret Rp50.000–100.000) → Rp25.000–47.440 (coret Rp50.000–100.000, -53%) | 4.9 → 4.9 | 12858 → 12859 | terverifikasi |
| 30 | ECOCO Mop Holder | Rp48.000 → Rp48.000 | 4.93 → 4.93 | 3176 → 3177 | terverifikasi |
| 31 | Halu Gantungan Tempel HSB728 | Rp17.990–27.900 (varian Rp27.900) → Rp17.990–27.900 (varian Rp27.900) | 4.86 → 4.86 | 5510 → 5513 | terverifikasi |
| 32 | ECOCO Medicine Organizer | Rp56.000–66.000 → Rp56.000–66.000 | 4.93 → 4.93 | 1019 → 1021 | terverifikasi |
| 33 | Halu Tempat Tisu HSB639 | Rp18.905–32.205 → Rp18.905–32.205 | 4.87 → 4.87 | 5992 → 5993 | terverifikasi |
| 34 | ECOCO Simple Toothbrush Rack | Rp96.000–180.000 (varian termurah Rp96.000) → Rp96.000–180.000 (varian termurah Rp96.000) | 4.95 → 4.95 | 1397 → 1397 | terverifikasi |
| 35 | ABC BEAR Kotak Bawah Tempat Tidur | Rp88.000 (flash sale, coret Rp128.000) → Rp88.000 (flash sale, coret Rp128.000, -31%) | 4.92 → 4.92 | 3085 → 3085 | terverifikasi |
| 36 | ABC BEAR Storage Box Lipat | Rp50.001–213.000 (varian termurah Rp50.001 masuk rentang) → Rp100.000–600.000 | 4.85 → 4.85 | 3150 → 3150 | terverifikasi **(BERUBAH)** |
| 37 | Dejavu Kotak Make Up Acrylic HRM302 | Rp79.000–199.000 (varian termurah Rp79.000 masuk rentang) → Rp79.000–199.000 (varian termurah Rp79.000 masuk rentang) | 4.9 → 4.9 | 5128 → 5128 | terverifikasi |
| 38 | FIVEVOO Rak Dokumen Kantor | Rp49.290 (flash sale, coret Rp93.000) → Rp49.290 (flash sale, coret Rp93.000, -47%) | 4.86 → 4.86 | 8300 → 8300 | terverifikasi |
| 39 | VOOVA Map Folder Document Organizer | Rp29.597–35.600 → Rp29.597–35.600 | 4.91 → 4.91 | 2638 → 2638 | terverifikasi |
| 40 | VOOVA Tas Dokumen A4 | Rp25.600–30.200 → Rp25.600–30.200 | 4.86 → 4.86 | 2869 → 2869 | terverifikasi |
| 41 | BONBOX Mop Stick Set BCT3505 | Rp69.000 → Rp144.000–150.000 | 4.88 → 4.88 | 10676 → 10692 | terverifikasi **(BERUBAH)** |
| 42 | BONBOX Twist Mop BCT3903 | Rp49.900 → Rp50.000 (flash sale, coret Rp70.000, -29%) | 4.83 → 4.83 | 3618 → 3647 | terverifikasi **(BERUBAH)** |
| 43 | BONBOX Twist Mop BCT3802 | Rp75.000 → Rp140.000–300.000 | 4.92 → 4.92 | 3148 → 3164 | terverifikasi **(BERUBAH)** |
| 44 | Sapu Lantai dan Pengki 1 Set Kleaner | Rp91.800 → Rp91.800 | 4.9 → 4.9 | 3333 → 3333 | terverifikasi |
| 45 | Lap Dapur Microfiber Set 5 pcs AZKO Proclean | Rp62.000 (coret Rp68.900) → Rp62.000 (coret Rp68.900, -10%) | 4.95 → 4.95 | 1183 → 1183 | terverifikasi |
| 46 | Sikat Kamar Mandi 2in1 ZOLELE C4 | Rp94.000 → Rp94.000 | 4.92 → 4.92 | 2065 → 2065 | terverifikasi-harga-saja (rating tidak tampil di halaman) |
| 47 | Astonish Lime Blast Spray 750 ml AZKO | Rp59.800 (coret Rp74.700) → Rp59.800 | 4.89 → 4.89 | 2871 → 2871 | terverifikasi-harga-saja (rating tidak tampil di halaman) |
| 48 | Sikat Lantai 3in1 freemir + Wiper | Rp66.405 → Rp66.405 | 4.88 → 4.88 | 10504 → 10504 | terverifikasi (catatan: Pre-Order, dikirim dalam 30 hari) |
| 49 | Bubbly Bath Sabun Pembersih Kamar Mandi Wifey Project | Rp74.222 (coret Rp195.000) → Rp74.222 (coret Rp195.000, -62%) | 4.92 → 4.92 | 1664 → 1664 | terverifikasi |
| 50 | Lap Microfiber 40x40 CM Tebal | Rp23.500 (coret Rp30.000) → Rp23.500 (coret Rp30.000, -22%) | 4.91 → 4.91 | 2244 → 2244 | terverifikasi |

## Sumber per produk

Semua nilai baru diambil dari halaman produk Shopee (`product_url` masing-masing produk, lihat `data/landing-page-products.json`) yang dibaca 17 Nov 2026 ±09:33–09:45 WIB — harga dari teks halaman + JSON-LD `Product.offers`, rating dari baris "Rating: X/5 (N ratings)".

## Yang diubah di data

- `data/landing-page-products.json` — 49 produk terverifikasi: `price_display`/`price_min`/`rating`/`reviews` diperbarui dari hasil cek, `price_source` = "cek Shopee 17 Nov 2026". 1 produk (Greenland) tidak diubah sama sekali. Field `affiliate_link`, `sub_id`, `status`, `product_url`, `name`, `category`, `image_url` tidak disentuh (diverifikasi tidak berubah).
- `data/landing-page-products.csv` — diregenerasi dari JSON yang sama.
- `data/products.json` di project landing page PC — disalin dari JSON baru (lihat langkah sync).

