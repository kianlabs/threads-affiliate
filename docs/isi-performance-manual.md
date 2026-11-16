# Cara Isi performance.csv (Input Manual)

`data/performance.csv` adalah satu-satunya tempat angka performa dicatat.
Tidak ada penarikan otomatis — semua angka disalin manual dari dua sumber:
**Threads Insights** (views/likes/replies) dan **Shopee Click Report**
(klik/order/komisi per Sub-ID). Sekarang Sub-ID sudah unik per produk
(Sprint 1), jadi angka Shopee bisa dipetakan ke produk yang benar.

## Aturan keras

1. **Hanya isi angka yang benar-benar terlihat di dashboard.** Yang tidak
   ada datanya biarkan KOSONG — jangan isi 0, jangan kira-kira.
   Kosong = UNKNOWN, dan `tools/calc_performance.py` akan menampilkannya
   sebagai UNKNOWN, bukan 0.
2. **Jangan mencampur pending dengan validated.** Kolom
   `validated_commission` hanya diisi komisi berstatus tervalidasi di
   dashboard Shopee. Komisi pending dicatat di tempat lain, bukan di sini.
3. **Satu baris = satu publikasi.** Jangan menimpa baris lama dengan angka
   baru — tambah baris baru dengan `date` tanggal pengamatan, atau update
   baris yang sama dan ubah `last_updated`.
4. **Jangan ubah `product_id`, `content_id`, `sub_id` baris yang sudah ada.**
   Itu kunci penghubung ke DB link dan ke histori posting.

## Langkah 1 — Threads Insights (impressions)

1. Buka Threads → profil @shopee_harian → buka post yang dimaksud.
2. Catat angka yang tampil: views (impressions), likes, replies.
   (CSV saat ini hanya punya kolom `impressions` — likes/replies belum
   dicatat; cukup impressions dulu.)
3. Isi kolom `impressions` di baris yang `content_id`-nya cocok.
4. Isi `data_source` dengan `threads-insights` bila baris itu hanya berisi
   angka Threads, atau `threads-insights+shopee-click-report` bila sudah
   lengkap dari kedua sumber.

## Langkah 2 — Shopee Click Report (klik / order / komisi)

1. Buka Shopee Affiliate dashboard (HP Kyan) → Laporan → Click Report
   (atau menu Laporan Kinerja).
2. Filter per **Sub-ID** — cari Sub-ID unik produk itu, misal
   `threadsdapurecocobrush20261117`.
3. Catat untuk periode yang sama dengan `date` baris: jumlah klik
   (`clicks`), jumlah order (`orders`), komisi tervalidasi
   (`validated_commission`, dalam Rupiah, tanpa titik/koma — contoh
   `23400`), pembatalan (`cancellations`), retur (`returns`).
4. Komisi XTRA dan komisi standar yang sudah tervalidasi digabung ke
   `validated_commission` (satu angka).
5. Isi `data_source` dengan `shopee-click-report` (atau gabungan, lihat
   Langkah 1).

## Langkah 3 — Biaya (production_cost / ad_spend)

- `production_cost`: biaya kredit Flow untuk video produk itu.
  Kredit PRO tidak berbayar uang — isi `0` HANYA bila videonya memang
  dibuat dari kredit PRO gratis; bila ada biaya lain (mis. aset berbayar),
  isi jumlah Rupiah-nya. Kosongkan bila tidak ada video / tidak tahu.
- `ad_spend`: isi `0` selama belum ada Meta Ads (saat ini belum ada).
  Bila nanti ada boost, isi sesuai pengeluaran iklan untuk konten itu.

## Langkah 4 — Hitung dan periksa

```bash
python tools/calc_performance.py            # semua produk
python tools/calc_performance.py --product P-28007581-1702781107
```

- EPC = validated_commission / clicks; conversion rate = orders / clicks;
  net earnings = validated_commission − production_cost − ad_spend.
- Bila hasilnya UNKNOWN, berarti ada komponen yang masih kosong — itu
  benar, bukan error. Lengkapi datanya dari dashboard, jangan paksa angka.

## Contoh 1 baris terisi (FIKSI — jangan disalin ke CSV asli)

```csv
2026-11-16,P-28007581-1702781107,kikkoman-threads-20261116,threads,threadsdapur20261116,5000,100,2,8000,0,0,0,0,threads-insights+shopee-click-report,2026-11-17
```

Artinya: post Kikkoman 16 Nov — 5.000 impressions, 100 klik, 2 order,
komisi tervalidasi Rp8.000 → EPC Rp80, conversion rate 2%.
Angka di atas HANYA contoh rumus, bukan data nyata.

## Kolom-kolom CSV

| Kolom | Isi |
|---|---|
| date | Tanggal publikasi (YYYY-MM-DD) |
| product_id | `P-<shop_id>-<item_id>`, lihat docs/skema-id-dan-subid.md |
| content_id | `<slug>-<platform>-<yyyymmdd>` |
| platform | `threads` / `facebook` / `pinterest` |
| sub_id | Sub-ID unik publikasi itu |
| impressions | Views dari Threads Insights |
| clicks | Klik dari Shopee Click Report |
| orders | Order dari Shopee Click Report |
| validated_commission | Komisi tervalidasi (Rp, angka saja) |
| cancellations | Order batal |
| returns | Order retur |
| production_cost | Biaya produksi konten (Rp) |
| ad_spend | Biaya iklan (Rp) |
| data_source | `post_history.json` / `threads-insights` / `shopee-click-report` / gabungan |
| last_updated | Tanggal terakhir baris ini diubah (YYYY-MM-DD) |
