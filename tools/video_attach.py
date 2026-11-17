"""video_attach.py — helper upload video file ke composer Threads via Playwright.

Kenapa file ini ada: vendor poster.py hanya bisa attach GAMBAR
(, gagal pun lanjut tanpa media).
Composer web Threads sebenarnya menerima video (input tersembunyi dengan
accept mencakup video/mp4, video/quicktime, video/webm) — dibuktikan
dry-run 17 Nov 2026: video Kotak Es v2 ter-attach + preview <video> muncul
di dialog 'New thread' sebagai @shopee_harian.

Aturan keras (fail-closed, beda dengan step gambar di poster.py):
- Video adalah isi postingan — kalau attach gagal / tidak ada preview,
  fungsi mengembalikan ok=False dan ALUR WAJIB BATAL, jangan lanjut ke Post.
- Modul ini TIDAK PERNAH menekan tombol Post; pemanggil yang memutuskan.
- Hanya untuk dry-run / pilot yang disetujui. Live pilot butuh persetujuan
  terpisah Kyan + caption yang sudah di-approve.

Pemakaian (lihat /tmp/pilot_video_dryrun2.py untuk contoh dry-run):
    from tools.video_attach import open_new_thread_composer, attach_video, type_caption
    dialog = open_new_thread_composer(page)
    res = attach_video(page, 'data/videos/kotak-es-ugc/kotak-es-ugc-v2.mp4')
    assert res['ok'], res
    type_caption(page, 'Mitos: ...')
"""

from __future__ import annotations

import time
from pathlib import Path

# Accept yang terbukti di composer web Threads (dry-run 17 Nov 2026).
VIDEO_MIME_PREFIXES = ("video/mp4", "video/quicktime", "video/webm", "video/")
# Durasi maksimum video Threads (detik) — pilot memakai klip ~8 detik.
MAX_VIDEO_SECONDS = 300


def _dialog(page):
    dialogs = page.locator('[role="dialog"]')
    if dialogs.count() == 0:
        raise RuntimeError("Dialog composer tidak ditemukan (role=dialog count 0)")
    return dialogs.first


def open_new_thread_composer(page, timeout_ms: int = 15000) -> object:
    """Klik tombol create sidebar lalu tunggu dialog 'New thread' + editor.

    Mengembalikan locator dialog. Raise bila dialog/editor tidak muncul.
    """
    btn = page.locator('[aria-label="New thread"]').first
    if btn.count() == 0 or not btn.is_visible():
        raise RuntimeError("Tombol create [aria-label='New thread'] tidak ditemukan/terlihat")
    btn.click(timeout=timeout_ms)
    page.wait_for_selector('[role="dialog"]', timeout=timeout_ms)
    page.wait_for_selector('[contenteditable="true"]', timeout=timeout_ms)
    dialog = _dialog(page)
    title = dialog.inner_text()[:120]
    if "New thread" not in title and "Utas baru" not in title:
        raise RuntimeError(f"Dialog terbuka tapi bukan composer baru: {title[:80]!r}")
    return dialog


def enumerate_media_inputs(page) -> list[dict]:
    """Daftar semua input[type=file] di halaman + atribut accept-nya."""
    out = []
    for inp in page.locator('input[type="file"]').all():
        try:
            out.append({
                "accept": inp.get_attribute("accept") or "",
                "visible": bool(inp.is_visible()),
                "multiple": inp.get_attribute("multiple") is not None,
            })
        except Exception as e:
            out.append({"accept": "", "visible": False, "multiple": False, "error": str(e)[:100]})
    return out


def attach_video(page, video_path: str | Path, timeout_ms: int = 30000) -> dict:
    """Attach file video ke composer yang sudah terbuka. FAIL-CLOSED.

    Langkah: cari input file yang accept-nya memuat video -> set_input_files
    -> tunggu elemen <video> preview muncul DI DALAM dialog.
    Return: {'ok': bool, 'accept': str, 'preview': bool, 'error': str|None}
    ok=False berarti pemanggil WAJIB membatalkan alur (jangan Post).
    """
    video_path = Path(video_path)
    if not video_path.exists():
        return {"ok": False, "accept": "", "preview": False,
                "error": f"File video tidak ada: {video_path}"}
    if video_path.suffix.lower() not in (".mp4", ".mov", ".webm"):
        return {"ok": False, "accept": "", "preview": False,
                "error": f"Ekstensi video tidak didukung Threads: {video_path.suffix}"}
    dialog = _dialog(page)
    inputs = page.locator('input[type="file"]').all()
    target = None
    target_accept = ""
    for inp in inputs:
        try:
            acc = inp.get_attribute("accept") or ""
        except Exception:
            continue
        if any(v in acc for v in VIDEO_MIME_PREFIXES):
            target, target_accept = inp, acc
            break
    if target is None:
        return {"ok": False, "accept": "", "preview": False,
                "error": "Tidak ada input file yang menerima video (accept tanpa video/*). " +
                         f"Inputs terlihat: {enumerate_media_inputs(page)}"}
    try:
        target.set_input_files(str(video_path))
    except Exception as e:
        return {"ok": False, "accept": target_accept, "preview": False,
                "error": f"set_input_files gagal: {type(e).__name__}: {str(e)[:150]}"}
    deadline = time.time() + timeout_ms / 1000
    preview = False
    while time.time() < deadline:
        try:
            if dialog.locator("video").count() > 0:
                preview = True
                break
        except Exception:
            pass
        time.sleep(1)
    if not preview:
        return {"ok": False, "accept": target_accept, "preview": False,
                "error": "File ter-set tapi preview <video> tidak muncul di dialog dalam batas waktu"}
    return {"ok": True, "accept": target_accept, "preview": True, "error": None}


def type_caption(page, text: str) -> dict:
    """Ketik caption ke editor composer, lalu verifikasi teksnya masuk.

    Return: {'ok': bool, 'typed': str, 'error': str|None}
    """
    editors = page.locator('[contenteditable="true"]')
    if editors.count() == 0:
        return {"ok": False, "typed": "", "error": "Tidak ada editor contenteditable"}
    try:
        editors.first.click()
        time.sleep(0.5)
        page.keyboard.type(text, delay=20)
        time.sleep(1)
        typed = editors.first.inner_text() or ""
    except Exception as e:
        return {"ok": False, "typed": "", "error": f"{type(e).__name__}: {str(e)[:150]}"}
    if text[:60] not in typed and typed.strip()[:60] != text[:60]:
        return {"ok": False, "typed": typed[:120], "error": "Teks caption tidak terverifikasi di editor"}
    return {"ok": True, "typed": typed[:200], "error": None}
