# Arsip Template Beauty (v2.0-v1)

Diarsipkan: 16 Nov 2026 — niche sistem resmi diganti dari beauty
(skincare / parfum / haircare / makeup) ke home living / kos-kosan
(dapur / organizer / kebersihan), sesuai riset RISET-NICHE.md.

Isi arsip:
- `hooks_skincare.json`, `hooks_parfum.json`, `hooks_haircare.json`,
  `hooks_makeup.json` — file hook beauty (dipindah dari `templates/`).
- `post2_templates.json` — salinan ASLI (masih berisi kunci beauty).
- `post3_cta_templates.json` — salinan ASLI sebelum +3 varian home living.

Kenapa aman: `ContentGenerator` hanya memuat `templates/hooks_{category}.json`
(persis di folder `templates/`), `templates/post2_templates.json`, dan
`templates/post3_cta_templates.json`. File di folder arsip ini TIDAK pernah
dimuat `run_slot.py`.

Cara restore (bila niche beauty kembali dipakai):
1. Pindahkan kembali ke-4 file `hooks_*.json` ke `templates/`.
2. Kembalikan `post2_templates.json` arsip ini (atau gabungkan kuncinya).
3. Pastikan `CATEGORIES` di vendor `content_generator.py` memuat kategori
   beauty (saat ini masih ada) dan `run_slot.py`/`config.yaml` memakai
   slot beauty lagi.
