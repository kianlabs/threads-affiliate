# Skema ID & Sub-ID — Shopee Affiliate @shopee_harian

Dokumen ini adalah acuan tunggal penamaan ID di sistem affiliate.
Dibuat Sprint 1 (17 Nov 2026) — sebelumnya tidak ada skema tertulis:
Sub-ID lama `threadsdapur20261116` dipakai 22 produk sekaligus, sehingga
EPC per produk mustahil dihitung (temuan audit 16 Nov 2026).

## 1. Product ID — stabil, dari URL produk

Format:

```
P-<shop_id>-<item_id>
```

Contoh: `P-369346857-24388789494` (ECOCO Cup Washing Brush).

- Diambil dari `https://shopee.co.id/product/{shop_id}/{item_id}` — bagian
  yang sama dipakai `origin_link` di link affiliate.
- Stabil: tidak berubah selama produk yang sama dijual toko yang sama.
- Dipakai sebagai kunci di `data/performance.csv` dan `data/subid_mapping.md`.
- Daftar lengkap 29 product ID ada di `data/subid_mapping.md`.

## 2. Sub-ID — unik per publikasi

Format (berlaku untuk publikasi baru mulai 17 Nov 2026):

```
threads<kategori><slug-produk><yyyymmdd>
```

- Hanya huruf + angka, tanpa hubung (syarat Shopee untuk token sub_id).
- `<kategori>`: `dapur` | `organizer` | `kebersihan`.
- `<slug-produk>`: nama pendek produk, huruf + angka saja, unik per kategori
  (contoh: `ecocobrush`, `bonbox3903`, `pisau10pcs`).
- `<yyyymmdd>`: tanggal regenerasi link, bukan tanggal posting
  (saat ini `20261117` untuk 27 link hasil Sprint 1).
- 1 Sub-ID = 1 produk = 1 publikasi. Link yang sudah USED tidak pernah
  dipakai lagi, jadi Sub-ID-nya tidak pernah dipakai ulang.

### Keputusan tanggal Sub-ID (verifikasi Sprint 1, 17 Nov 2026)

Tanggal di Sub-ID adalah **tanggal link dibuat** (identitas link yang
stabil), BUKAN tanggal publikasi. Alasannya:

- Sub-ID dibuat sekali saat link diregenerasi; produknya baru
  dipublikasikan di tanggal berikutnya — itu normal dan bukan kesalahan.
- Tanggal publikasi aktual tercatat di tempat yang memang untuk itu:
  kolom `date` di `data/performance.csv`, `date` di
  `data/post_history.json`, dan `<yyyymmdd>` di `content_id` (§3).
- Meregenerasi ulang 27 link hanya demi menyamakan tanggal justru
  merusak kestabilan tracking (link lama yang sudah dicatat di
  performance/mapping jadi basi) — **tidak dilakukan**.
- Batch link berikutnya memakai tanggal pembuatannya sendiri, supaya
  Sub-ID tetap unik antar-batch.
- Contoh lengkap: `threadsdapurecocobrush20261117`.
- Batas praktis: jaga total panjang link an_redir ≤ ~185 karakter supaya
  post 2 Threads tetap di bawah 500 karakter (link terpanjang saat ini
  181 karakter — `threadsorganizerhalugantungan20261117`).

Di dalam URL, Sub-ID muncul sebagai slot 1 dari `sub_id`:

```
...&sub_id=threadsdapurecocobrush20261117----
```

(slot 2–5 kosong, format baku `link_builder.py`).

### Aturan perubahan

- Sub-ID baru dibuat dengan `tools/link_builder.py` — jangan merakit manual.
- Link yang SUDAH dipublikasikan (Kikkoman, BONBOX) TIDAK PERNAH diubah:
  Sub-ID lamanya (`threadsdapur20261116`, `threadskebersihan20261116`)
  tetap tercatat di `data/performance.csv` untuk 2 post tersebut.
- Pemetaan lama → baru: `data/subid_mapping.md` (gitignored).

## 3. Content ID — penghubung produk → konten → publikasi

Format:

```
<slug-produk>-<platform>-<yyyymmdd>
```

- `<yyyymmdd>` di sini = tanggal publikasi.
- Contoh: `kikkoman-threads-20261116`, `bonboxmop-threads-20261116`.
- Dipakai di `data/performance.csv` kolom `content_id`.
- Untuk publikasi video nanti: platform `threads` / `facebook` / `pinterest`
  mengikuti tempat video itu terbit; satu produk bisa punya beberapa
  content_id (satu per platform per tanggal).

## 5. Batas panjang caption (Sprint 2, 17 Nov 2026)

- **Absolut: 500 karakter/post** — batas platform Threads. Lebih dari
  itu ditolak guardrail (`ERROR: panjang-post`) dan retry 5x di
  `run_slot.py` mencoba varian lain.
- **Operasional: 470 karakter/post (target).** Caption 471–500 karakter
  lolos tapi dicatat sebagai peringatan (`WARN: panjang-operasional`)
  di `tools/check_draft.py` — supaya ada margin 30 karakter untuk
  variasi template/link dan retry jarang mentok di batas absolut.
- Batas ini berlaku per post (post 1 hook maupun post 2 isi + link).

## 4. Riwayat migrasi (Sprint 1, 17 Nov 2026)

- Sebelum: 3 Sub-ID kategori dipakai 29 produk
  (`threadsdapur20261116` ×22, `threadsorganizer20261116` ×4,
  `threadskebersihan20261116` ×3).
- Sesudah: 27 Sub-ID unik baru untuk 27 link UNUSED; 2 link USED
  dipertahankan apa adanya (link + Sub-ID lama).
- Backup DB sebelum migrasi: `data/affiliate_links.md.bak-20261117-<jam>`
  (gitignored, pola `data/*.bak*`).
