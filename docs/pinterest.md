# Pinterest — Modul Pin Otomatis (API v5)

Akun Pinterest **Yozo (@dirtoflegend)** sudah terhubung ke Shopee Affiliate
'pratama' (16 Nov 2026, dikonfirmasi Kyan). Modul ini membuat Pin dari
database link yang sama dengan Threads, maks **1 Pin/hari**, via Pinterest
API v5 resmi.

## Yang modul ini BISA dan TIDAK BISA

- BISA: membuat Pin (judul + deskripsi + link shortlink Shopee + gambar)
  lewat `POST /v5/pins`, lalu verifikasi dengan `GET /v5/pins/{id}`.
- TIDAK BISA: tagging produk native Shopee. Tagging adalah fitur manual di
  aplikasi Pinterest (kemitraan resmi Shopee x Pinterest) — setelah Pin
  terbit, buka Pin di aplikasi Pinterest → Edit Pin → Tag products → cari
  produk Shopee-nya (maks 5 produk/Pin). Tagging manual ini jalur yang
- TIDAK BISA: melihat Pin publik sebelum Standard access. Akun API Trial:
  Pin hanya terlihat oleh pembuatnya (sandbox). Standard access butuh
  pengajuan + video demo alur OAuth (lihat bawah).

## Prasyarat (blokir saat ini — belum ada satu pun)

1. **Pinterest Business app** — buat di developers.pinterest.com
   (akun Business Yozo), dengan scope `boards:read, boards:write,
   pins:read, pins:write`.
2. **Token akses (Trial)** — dari OAuth app di atas. Simpan di
   `~/.pinterest_poster/pinterest_token.env` (mode 600), isi satu baris:
   `PINTEREST_ACCESS_TOKEN=<token>`. JANGAN commit file ini, JANGAN
   tempel token di chat. Token Trial berlaku ±30 hari.
3. **Board + board_id** — buat board di Pinterest (mis. "Kos Rapi" /
   home living), lalu isi `board_id` di `config.yaml` (section
   `pinterest`). Board ID didapat dari URL board atau dari API.
4. **Standard access** — ajukan di dashboard Pinterest developer dengan
   video demo (app menyelesaikan satu aksi via API termasuk OAuth).
   Tanpa ini Pin tidak terlihat publik.
5. **Kolom Image URL terisi** — lihat bawah. Tanpa ini modul BATAL
   (bukan error): tidak ada gambar = tidak ada Pin.

## Gambar (wajib)

Pinterest API butuh `image_url` yang bisa diakses publik. Isi kolom
`Image URL` di `data/affiliate_links.md` dengan URL gambar produk dari
listing Shopee: buka halaman produk → klik kanan gambar → "Copy image
address" (URL `https://cf.shopee.co.id/file/...`). Satu produk = satu
gambar utama. Sistem TIDAK scraping gambar dari Shopee.

Format baris database (kolom ke-7, opsional, boleh kosong):

```
| 1 | Nama Produk | `https://s.shopee.co.id/...` | ❌ UNUSED | - | threadsdapur20261116 | https://cf.shopee.co.id/file/xxx |
```

Parser Threads mengabaikan kolom tambahan di belakang, jadi format ini
tetap kompatibel dengan `run_slot.py`.

## Cara jalanin

```bash
# Dry-run (tidak butuh token, tidak memanggil API):
.venv/bin/python tools/run_pinterest.py --dry-run
.venv/bin/python tools/run_pinterest.py --dry-run --category dapur

# Posting beneran (butuh token + board_id):
.venv/bin/python tools/run_pinterest.py

# Tes API langsung (tanpa guardrails):
.venv/bin/python tools/pinterest_api.py --board-id <id> --title "..." \
    --description "..." --link "https://s.shopee.co.id/..." \
    --image-url "https://cf.shopee.co.id/file/..." --dry-run
```

Riwayat Pin tersimpan di `data/pinterest_history.json` (tidak di-commit).
Link yang sudah di-Pin tidak akan di-Pin lagi; link yang sama BOLEH tetap
dipakai Threads (channel berbeda).

## Timer (DISABLED)

Timer systemd `pinterest-1000` (10:00 WIB, 1x/hari) sudah dibuat di
`ops/pinterest-1000.{service,timer}` dan terpasang di
`~/.config/systemd/user/` dalam keadaan **DISABLED**. Aktifkan hanya
setelah token ada + dry-run lolos + board_id terisi:

```bash
systemctl --user enable --now pinterest-1000.timer
systemctl --user list-timers | grep pinterest
```

## Aturan (guardrails.md §4b)

  biaya tambahan buat kamu."
- Kata "affiliate" dilarang di judul/deskripsi Pin (dicek `check_draft.py`).
- Judul maks 100 karakter, deskripsi maks 500 karakter.
- Link harus shortlink resmi Shopee (`s.shopee.co.id` / `shope.ee`).
- Maks 1 Pin/hari. Pinterest melarang Pin afiliasi "repetitif atau dalam
  jumlah besar" — pelanggaran bisa berujung pembatasan akun.
