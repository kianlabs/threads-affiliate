"""extract_brave_cookies.py — ekstrak cookie IG+Threads dari Brave (bukan Chrome).

Kenapa file ini ada: PC Kyan memakai Brave sebagai browser utama
(~/.config/BraveSoftware/Brave-Browser/Default/Cookies); Google Chrome
tidak pernah dipakai (folder ~/.config/google-chrome hanya berisi
NativeMessagingHosts). Vendor threads-affiliate hanya mendukung Chrome
(`browser_cookie3.chrome`), jadi ekstraksi bawaan gagal dengan
"Chrome cookies DB not found".

Script ini memanggil `browser_cookie3.brave()` (kunci dekripsi
"Brave Safe Storage") dan menulis format session.json yang SAMA dengan
yang dihasilkan vendor (`~/.threads_poster/cookies/session.json`):
{"instagram": {...}, "threads": {...}}.

Pemakaian di PC:
  cd ~/threads-affiliate-system
  .venv/bin/python tools/extract_brave_cookies.py
  .venv/bin/python -m threads_poster.cli setup --validate-cookies

Catatan: Brave boleh tetap jalan saat ekstraksi (browser_cookie3 menyalin
DB ke file sementara), tapi bila sessionid tidak ketemu, tutup Brave dulu
lalu ulangi — data cookie di WAL yang belum ter-checkpoint bisa terlewat.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

BRAVE_COOKIES = (
    Path.home() / ".config/BraveSoftware/Brave-Browser/Default/Cookies"
)
DEFAULT_COOKIES_DIR = Path.home() / ".threads_poster" / "cookies"


def main() -> None:
    import browser_cookie3

    if not BRAVE_COOKIES.exists():
        raise FileNotFoundError(f"Brave cookies DB tidak ketemu: {BRAVE_COOKIES}")

    ig_jar = browser_cookie3.brave(
        domain_name=".instagram.com",
        cookie_file=str(BRAVE_COOKIES),
    )
    ig_cookies = {c.name: c.value for c in ig_jar}

    threads_jar = browser_cookie3.brave(
        domain_name=".threads.com",
        cookie_file=str(BRAVE_COOKIES),
    )
    threads_cookies = {c.name: c.value for c in threads_jar}

    required_ig = {"sessionid", "csrftoken", "ds_user_id"}
    missing = required_ig - set(ig_cookies.keys())
    if missing:
        raise ValueError(
            f"Cookie IG penting hilang: {missing}. "
            "Pastikan sudah login Instagram di Brave PC."
        )

    output_path = DEFAULT_COOKIES_DIR / "session.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"instagram": ig_cookies, "threads": threads_cookies}
    output_path.write_text(json.dumps(data, indent=2))
    try:
        os.chmod(output_path, 0o600)
    except Exception:
        pass

    print(f"OK — cookie tersimpan di {output_path}")
    print(f"IG cookies: {len(ig_cookies)} (sessionid: {'ada' if ig_cookies.get('sessionid') else 'HILANG'})")
    print(f"Threads cookies: {len(threads_cookies)}")


if __name__ == "__main__":
    main()
