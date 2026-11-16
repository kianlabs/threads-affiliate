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
- Kata "review" sebagai klaim pengalaman pribadi akun ("gw review",
  "review jujur gw") untuk produk yang tidak dipegang. YANG BOLEH:
  membahas ULASAN PEMBELI di listing ("menurut ulasan pembeli",
  "rating 4.8+, ribuan terjual", "yang paling sering dipuji pembeli")
  — itu fokus review sistem ini, bukan pengalaman akun.
- Sebelum/sesudah (before-after) palsu.

Format yang benar: **"ilustrasi AI / intip produk"** — bahas produk dari
info listing (rating, terjual, harga, klaim seller), ajak diskusi, tanpa
pura-pura pernah memakai.

## 3. Bahasa garansi — dilarang

Dilarang: "dijamin", "pasti" (hasil), "100% ampuh", "terjamin", "paling murah",
"harga termurah", "cures/menyembuhkan", "pasti sembuh", "diskon gila",
"beli sekarang".

Yang boleh: harga + rating + jumlah terjual apa adanya dari listing.

## 4. TIDAK ADA kata komisi / affiliate / commission di teks post

Aturan Kyan 16 Nov 2026 18:50 (mengalahkan aturan 17:56): kata "komisi",
"commission", "affiliate", "#affiliate", "#ShopeeAffiliate", "link
affiliate", "link berbayar", "aku dapat komisi", "tanpa nambah harga"
dan kalimat sejenisnya DILARANG muncul di SEMUA teks post yang terlihat
publik — hook, post 2/CTA, deskripsi. `check_draft.py` menolak post yang
mengandung kata itu (parameter `affiliate_id` di URL link dikecualikan:
itu atribusi, bukan teks yang dibaca pembaca).

TIDAK ADA disclosure komisi di teks post. Jangan menulis kalimat komisi
dalam bentuk apa pun.

RISIKO (dicatat, tapi ikuti perintah Kyan): tanpa disclosure, ada risiko
teguran dari Shopee / Threads / Meta karena platform mengharuskan
pengungkapan hubungan berbayar. Sistem mengikuti perintah Kyan; kalau
Kyan mengubah pikiran, disclosure dikembalikan lewat revisi template.

## 4b. Disclosure Pinterest — "#ad" di awal deskripsi

Pin Pinterest WAJIB diawali `#ad` di deskripsi (aturan Pinterest:
disclosure harus terlihat sebelum deskripsi terpotong). TIDAK ADA kalimat
komisi setelahnya. Contoh: "#ad {produk} — {alasan singkat dari ulasan
pembeli}". Tagging produk Shopee dilakukan MANUAL di aplikasi Pinterest
(kemitraan resmi Shopee x Pinterest); API v5 tidak bisa tagging.

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
