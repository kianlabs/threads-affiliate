# Riset Jam Posting — Threads Affiliate Shopee

**Tanggal:** 16 November 2026
**Tujuan:** menentukan 3 slot posting harian (WIB) untuk @temuanhariann.id pakai data jam online, bukan asumsi.
**Status:** rekomendasi awal berbasis studi global + pola Indonesia — wajib diuji dengan data akun sendiri (lihat §6).

## 1. Rekomendasi: 3 slot

| # | Slot (WIB) | Nama | Bukti utama |
|---|-----------|------|-------------|
| 1 | **09:00** | Pagi | Slot tunggal terbaik di studi Threads terbesar (Buffer, Kamis 09:00); pagi hari kerja 06:00–11:00 adalah jendela terkuat |
| 2 | **12:30** | Siang / makan siang | Rabu 12:00 slot terbaik ke-2 di Buffer; jam istirahat makan siang 11:30–13:00 konsisten di semua sumber Indonesia |
| 3 | **19:30** | Malam / santai | Prime time Indonesia 19:00–21:00 (banyak sumber lokal); Vista Social: 21:00–24:00 impressions Threads +12% — slot ini hipotesis yang harus dites, lihat catatan di bawah |

- **Jitter:** tiap slot digeser acak ±15–30 menit per hari (konsep dari faustzaki, lihat REFERENCES.md) supaya tidak terlihat seperti jadwal robot.
- **Jeda antar slot:** minimal 3 jam (09:00 → 12:30 → 19:30 sudah memenuhi; pola d4ncboz juga ≥4 jam).
- **Hari:** 7 hari seminggu dengan slot yang sama di v1 — penyesuaian per hari baru dilakukan setelah ada data sendiri (§6).

## 2. Perbandingan dengan jadwal lama d4ncboz (08:00 / 13:00 / 20:00)

Jadwal repo teman itu dekat dengan hasil riset, tapi tanpa sumber data yang dikutip di repo — murni rekomendasi penulisnya. Perbedaan rekomendasi baru:

| Slot lama | Slot baru | Alasan pergeseran |
|-----------|-----------|-------------------|
| 08:00 | **09:00** | 09:00 adalah slot tunggal terbaik Buffer (Kamis 09:00); 08:00 masih di dalam jendela pagi yang kuat, tapi 09:00 lebih tepat di puncak |
| 13:00 | **12:30** | Rabu 12:00 adalah slot terbaik ke-2 Buffer; jam makan siang Indonesia mulai 11:30 — 12:30 menangkap awal istirahat |
| 20:00 | **19:30** | Prime time Indonesia dimulai 19:00 menurut sumber lokal; 20:00 masih valid, 19:30 menangkap awal sesi santai malam |

Perubahan ini kecil dan sengaja — jadwal lama tidak salah besar, hanya belum ditopang data.

## 3. Bukti: Threads (data khusus platform)

### Buffer 2026 — studi Threads terbesar yang tersedia
- **Sampel:** 2,5 juta post Threads yang dikirim lewat Buffer, dipublikasi 4 Februari 2026.
- **Metrik:** median engagement per jam dan hari (like, reply, repost). Waktu dinormalisasi ke waktu lokal audiens — jadi 09:00 berarti 09:00 di tempat audiens berada, langsung bisa dibaca sebagai WIB untuk audiens Indonesia.
- **Temuan:**
  - Slot tunggal terbaik: **Kamis 09:00**. Berikutnya: Rabu 12:00 dan Rabu 09:00.
  - Hari terbaik: **Rabu, Kamis, Selasa**. Hari terburuk: **Sabtu**, lalu Minggu.
  - Jendela terkuat: **pagi hari kerja 06:00–11:00**.
  - **Malam 18:00–23:00 konsisten underperform** di semua hari.
  - Puncak per hari: Senin 12:00, Selasa 10:00, Rabu 12:00, Kamis 09:00, Jumat 10:00, Sabtu 10:00, Minggu 11:00.
  - Median engagement rate Threads ~3,6% (2025, turun dari ~4%).
  - Bonus: post yang kreatornya membalas komentar mendapat engagement +42% di Threads (Buffer, korelasi — bukan bukti sebab-akibat).
- **Batasan:** sampel hanya dari pelanggan Buffer (konten terjadwal brand/kreator), dan tidak ada dataset publik sebanding untuk cross-check.

### Hootsuite 2025 — searah dengan Buffer
- Sampel 1 juta+ post lintas platform (porsi Threads tidak dirinci).
- Slot terbaik Threads: **Selasa 08:00** — juga pagi hari kerja.
- Kesimpulan gabungan Buffer + Hootsuite: **pagi hari kerja adalah taruhan teraman untuk Threads**.

### Vista Social 2027 — HASIL BERTENTANGAN (penting dibaca)
- Sampel: 11,4 juta post dari 63 ribu profil brand, Nov 2025–Okt 2026, dipublikasi 10 November 2026.
- **Metriknya impressions (dilihat), bukan engagement (reply/like).**
- Temuan: post 21:00–24:00 mendapat **+12% impressions di Threads** dibanding jam lain; Minggu adalah hari terbaik untuk impressions di semua 7 platform (+6–10% di Threads); post 09:00–12:00 justru mendapat impressions lebih rendah karena jam itu paling ramai diposting (kompetisi feed).
- **Cara membaca konflik ini:** Buffer mengukur interaksi (reply/like), Vista mengukur keterlihatan. Untuk affiliate, yang menghasilkan klik dan penjualan adalah interaksi — jadi Buffer lebih relevan untuk slot utama. Tapi Vista memberi alasan untuk **tidak membuang slot malam**: malam hari feed lebih sepi kompetisi dan orang masih scroll santai. Itulah kenapa slot 19:30 dipertahankan sebagai hipotesis yang dites, bukan kepastian.

### Sprout Social 2026 — tidak mencakup Threads
- Studi ~2 miliar engagement di ~307 ribu profil (Nov 2025–Feb 2026) **tidak memasukkan Threads sama sekali**. Jadi tidak ada angka Threads dari Sprout — jangan mengutip Sprout untuk Threads.

### Ringkasan konsensus lintas studi
- Perbandingan 6 studi (post-quest.com): **09:00 dan 10:00 adalah satu-satunya jam yang disebut 4 dari 6 studi**.
- Data jam Threads itu tipis: Threads baru ada sejak Juli 2023, dan praktis hanya Buffer yang punya sampel khusus Threads dengan ukuran sampel yang dinyatakan.

## 4. Bukti: pola umum Indonesia (proxy, bukan data Threads)

Studi Threads di atas bersifat global. Data Indonesia berikut dipakai sebagai pelengkap, bukan pengganti:

- **APJII 2026** (survei 8.700 responden, 38 provinsi): 235,26 juta orang Indonesia memakai internet (81,72% penduduk). Media sosial paling sering diakses: TikTok 31,8%, Facebook 29,4%, Instagram 27,7%. **APJII tidak mempublikasikan breakdown per jam** — tidak ada angka jam online dari APJII.
- **DataReportal Digital 2027: Indonesia** (We Are Social/Meltwater): 240 juta identitas pengguna media sosial (83,2% populasi, Okt 2026); rata-rata 22 jam 52 menit/minggu di media sosial. **Juga tidak ada breakdown per jam.**
- **Pola harian dari sumber lokal (konsisten di banyak artikel):**
  - Istirahat makan siang **11:30–13:00 WIB** — orang buka medsos saat istirahat kerja/sekolah.
  - Pulang kerja & santai **17:30–20:30 WIB**; malam **19:00–21:00 WIB** disebut prime time oleh banyak sumber Indonesia.
  - Rekomendasi umum sociagates.com (membandingkan Buffer/Sprout/Hootsuite untuk Indonesia): Rabu/Kamis 12:00–13:00 atau 19:00–21:00 WIB.
  - Radaar.io untuk Jakarta: puncak aktivitas 19:00–21:00; akhir pekan 20:00–22:00; hari kerja juga 12:00 dan 17:00.
- **Instagram sebagai proxy (audiens Meta yang sama dengan Threads):** Buffer IG (9,6 juta post): Kamis 09:00, Rabu 12:00, Rabu 18:00 terbaik; Jumat/Sabtu terburuk. Sprout IG: Selasa 13:00–19:00, Rabu 12:00–21:00. Polanya searah: tengah pekan + siang/malam.

## 5. Weekday vs weekend

- **Buffer (engagement):** Rabu–Kamis–Selasa terbaik; **Sabtu terburuk**, Minggu kedua terburuk. Artinya slot pagi di tengah pekan adalah yang paling aman.
- **Vista Social (impressions):** Minggu terbaik untuk impressions di semua platform.
- **Keputusan v1:** slot sama setiap hari (09:00 / 12:30 / 19:30). Alasannya: konsistensi memudahkan pengukuran per slot, dan bukti engagement (yang relevan untuk affiliate) lebih mendukung tengah pekan. Setelah 2–4 minggu data, pertimbangkan varian akhir pekan (mis. geser slot pagi ke 10:00–11:00 di Sabtu/Minggu, sesuai puncak per hari Buffer).

## 6. Yang harus dites setelah jalan (pengukuran per jam)

Studi global hanya titik awal. Jam terbaik akun ini hanya bisa dibuktikan dari datanya sendiri:

1. **Catat setiap post:** tanggal, hari, slot jam (aktual, termasuk jitter), produk, jumlah like, reply, repost, klik link (via Sub-ID/UTM per post), dan konversi Shopee.
2. **Threads Insights tidak punya tampilan per jam** — pengukuran harus manual dari log di atas, bukan dari dashboard Threads.
3. **Setelah 2–4 minggu (42–84 post):** bandingkan median reply + klik per slot. Slot terlemah digeser ±1 jam dan dites lagi. Ubah satu slot dalam satu waktu supaya penyebabnya jelas.
4. **Prioritas tes pertama: slot malam (19:30).** Ini slot yang paling diperdebatkan data (Buffer bilang malam lemah, Vista + sumber lokal bilang malam ramai). Kalau setelah 2 minggu klik malam jauh di bawah pagi/siang, geser ke 20:30 atau ganti dengan slot sore 17:00.
5. **Balas komentar cepat:** Buffer menemukan +42% engagement pada post Threads yang dibalas kreatornya. Balasan adalah bagian dari strategi jam — post di jam kita bisa membalas dalam 15–30 menit pertama lebih berharga daripada post di jam "sempurna" lalu ditinggal.
6. **Jangan menilai dari 1–2 hari.** Buffer sendiri menegaskan: timing adalah bonus, bukan penyelamat — post yang kuat di jam biasa tetap mengalahkan post lemah di jam terbaik.

## 7. Yang tidak terverifikasi / batasan

- **Tidak ada data jam khusus Threads untuk Indonesia.** Semua studi Threads bersifat global dengan waktu lokal audiens — bisa dibaca sebagai WIB, tapi bukan bukti perilaku orang Indonesia di Threads.
- **Tidak ada data niat beli per jam.** Semua studi mengukur engagement/impressions, bukan klik affiliate atau penjualan. Jam dengan engagement tertinggi belum tentu jam dengan penjualan tertinggi.
- **APJII dan DataReportal tidak memberi breakdown per jam** — hanya durasi dan platform.
- **Studi-studi ini mengukur akun brand/kreator yang memakai scheduling tool**, bukan akun affiliate kecil. Perilaku audiens @temuanhariann.id bisa berbeda.
- **Angka-angka di atas adalah titik awal, bukan janji.** Satu-satunya bukti yang berlaku untuk akun ini adalah log pengukurannya sendiri (§6).

## 8. Sumber

- Buffer — "The Best Time to Post on Threads in 2026", 2,5 juta post, 4 Feb 2026 (diringkas via kompozy.io, antwork.io, eksis.io, post.buzz, zilfu.app, getkebo.com, socialmediaschedular.com)
- Hootsuite 2025 — best time Threads Selasa 08:00 (via eksis.io)
- Vista Social — "Best Times to Post on Social Media (2027 Report)", 11,4 juta post, 10 Nov 2026 — https://vistasocial.com/research/best-times-to-post/
- Sprout Social 2026 — ~2 miliar engagement, 307 ribu profil (tidak mencakup Threads)
- APJII 2026 — survei 8.700 responden, 38 provinsi (via sidiaimpact.com)
- DataReportal Digital 2027: Indonesia — We Are Social/Meltwater (via suaragarut.id, demokratis.co.id)
- sociagates.com — "Jam Terbaik Posting Instagram dan TikTok 2026" — https://sociagates.com/jam-terbaik-posting-instagram-tiktok-2026/
- Radaar.io — best times Jakarta — https://www.radaar.io/free-tools/best-times-to-post/fr/asia-jakarta/jakarta/
- Kompozy — "The 2026 Best-Time-to-Post Index" — https://kompozy.io/research/best-time-to-post-index
