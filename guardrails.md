# Guardrails — Aturan Wajib Sistem Affiliate v1

Aturan ini menggantikan approval per post (Kyan memilih full automation).
`tools/check_draft.py` dan `tools/run_slot.py` menegakkan aturan ini secara
otomatis sebelum posting. Pelanggaran = post DIBATALKAN, bukan diperbaiki diam-diam.

## 1. Link

- Post utama (hook) **TIDAK BOLEH** berisi link apa pun.
- Link affiliate hanya ada di **post ke-2 (self-reply pertama)** dalam thread.
- Link harus `s.shopee.co.id/...` (shortlink resmi Shopee). **Dilarang:** bit.ly,
  s.id, tinyurl, dan shortener lain (melanggar S&K Shopee, tracking bisa gagal).
- Satu link **tidak pernah dipakai dua kali** (dedup menolak; `--force` dilarang).

## 2. Kejujuran konten — larangan klaim "review"

Produk TIDAK PERNAH dipegang/dicoba oleh akun ini. Maka dilarang keras:

- Klaim pemakaian pribadi: "gw pake", "udah coba", "setelah 2 minggu pake",
  "hasil di kulit gw", "gw test", "repurchase", "beli ulang".
- Klaim hasil: "rontok berkurang 70%", "tekstur berubah", "tahan 12 jam"
  (kecuali mengutip deskripsi seller dengan kata "menurut deskripsi seller").
- Kata "review" untuk produk yang tidak dipegang.
- Sebelum/sesudah (before-after) palsu.

Format yang benar: **"ilustrasi AI / intip produk"** — bahas produk dari
info listing (rating, terjual, harga, klaim seller), ajak diskusi, tanpa
pura-pura pernah memakai.

## 3. Bahasa garansi — dilarang

Dilarang: "dijamin", "pasti" (hasil), "100% ampuh", "terjamin", "paling murah",
"harga termurah", "cures/menyembuhkan", "pasti sembuh", "diskon gila",
"beli sekarang".

Yang boleh: harga + rating + jumlah terjual apa adanya dari listing.

## 4. Disclosure — wajib di tiap thread

Tiap thread WAJIB memuat salah satu, di post CTA:

- `#affiliate`, atau
- `#ShopeeAffiliate`, atau
- kalimat: "Link affiliate — aku dapat komisi kalau kamu beli lewat link ini, tanpa nambah harga buat kamu."

## 5. Batas teknis Threads

- Maksimal **500 karakter per post** (cek otomatis).
- Maksimal **3 post/hari** dari akun ini. Tidak ada pengecualian.
- Hook ≤ 80 karakter lebih disukai (baris pertama terlihat di feed).

## 6. Gambar

- Pakai **foto produk asli dari listing** (bukan AI-generated yang diklaim asli).
- Kalau gambar dibuat/dianimasikan AI, beri label AI (`#AIGenerated` /
  "ilustrasi AI") dan JANGAN sebut itu review.

## 7. Yang tidak pernah dilakukan sistem ini

- Tidak auto-follow / auto-DM / auto-like / auto-komen ke orang lain.
- Tidak scraping data user Threads lain.
- Tidak memakai proxy untuk menghindari rate limit.
- Tidak memposting >5x/hari dalam kondisi apa pun (batas repo: 5; batas kita: 3).

## 8. Jika checker menolak

- Jangan pakai `--force`. Perbaiki draf/template-nya, lalu jalankan ulang.
- Penolakan berulang dari template yang sama = template itu harus ditulis ulang.
