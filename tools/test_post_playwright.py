#!/usr/bin/env python3
"""Tes posting TEKS Threads via Playwright. TIDAK menulis post_history.json / DB.
Dua mode sesi:
- default: cookie dari ~/.threads_poster/cookies/session.json (cara lama)
- --profile HANDLE: persistent Chromium profile ~/.threads_poster/profiles/HANDLE
  (pola fork threads-mcp: satu profil per akun, tidak pernah di-switch)
Usage: test_post_playwright.py --handle H --caption T --reply R --probe P [--profile H]
Exit: 0 post+reply terverifikasi | 7 post ok, reply belum terverifikasi | 6 submit/verify post gagal | 3 identitas gagal | 4 composer gagal | 5 ketik gagal | 2 guardrail
"""
import argparse, json, subprocess, sys
sys.path.insert(0, '/tmp')
from playwright.sync_api import sync_playwright
import profile_context

SESS = '/home/kian/.threads_poster/cookies/session.json'
VENV_PY = '/home/kian/threads-affiliate-system/.venv/bin/python'
TOOLS = '/home/kian/threads-affiliate-system/tools'
BANNED = ('affiliate', 'komisi', 'commission')

def load_cookies():
    sess = json.load(open(SESS))
    cookies = []
    for domain, jar in (('.instagram.com', sess.get('instagram', {})), ('.threads.com', sess.get('threads', {}))):
        for name, value in jar.items():
            cookies.append({'name': name, 'value': value, 'domain': domain, 'path': '/'})
    return cookies

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--handle', required=True)
    ap.add_argument('--caption', required=True)
    ap.add_argument('--reply', required=True)
    ap.add_argument('--probe', required=True)
    ap.add_argument('--profile', default=None, help='pakai persistent profile HANDLE, bukan session.json')
    a = ap.parse_args()
    if len(a.caption) > 500 or any(w in a.caption.lower() for w in BANNED):
        print('GUARDRAIL: caption tidak lolos', flush=True)
        return 2
    with sync_playwright() as p:
        browser = None
        if a.profile:
            ctx = profile_context.launch_profile_context(p, a.profile)
            print('PROFILE-DIR:', profile_context.profile_dir(a.profile), flush=True)
        else:
            browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-dev-shm-usage'])
            ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
            ctx.add_cookies(load_cookies())
        page = ctx.new_page()
        # 1. identitas
        page.goto('https://www.threads.com/@' + a.handle, wait_until='networkidle', timeout=90000)
        page.wait_for_timeout(3000)
        if not profile_context.is_logged_in(page, a.handle):
            print('IDENTITY-GAGAL: bukan @' + a.handle, flush=True)
            ctx.close()
            if browser:
                browser.close()
            return 3
        print('IDENTITY-OK: @' + a.handle, flush=True)
        # 2. composer
        page.goto('https://www.threads.com/', wait_until='networkidle', timeout=90000)
        page.wait_for_timeout(3000)
        try:
            page.locator('[aria-label="New thread"]').first.click(timeout=10000)
        except Exception:
            page.get_by_text("What's new?").first.click(timeout=10000)
        try:
            dialog = page.locator('[role="dialog"]').first
            dialog.wait_for(state='visible', timeout=15000)
        except Exception:
            print('COMPOSER-GAGAL: dialog tidak muncul', flush=True)
            ctx.close()
            if browser:
                browser.close()
            return 4
        editor = dialog.locator('[contenteditable="true"]').first
        editor.click(timeout=10000)
        page.keyboard.type(a.caption, delay=10)
        page.wait_for_timeout(1000)
        if a.caption not in (dialog.inner_text() or ''):
            print('KETIK-GAGAL: caption tidak tampil di dialog', flush=True)
            ctx.close()
            if browser:
                browser.close()
            return 5
        print('CAPTION-OK', flush=True)
        # 3. Post
        try:
            dialog.get_by_role('button', name='Post', exact=True).click(timeout=10000)
        except Exception:
            print('SUBMIT-GAGAL: tombol Post tidak bisa diklik', flush=True)
            ctx.close()
            if browser:
                browser.close()
            return 6
        page.wait_for_timeout(6000)
        page.screenshot(path='/tmp/pw-test/' + a.handle + '-after-post.png')
        # 4. verifikasi post di profil (reload sekali lawan cache basi)
        post_url = None
        for attempt in range(2):
            page.goto('https://www.threads.com/@' + a.handle, wait_until='networkidle', timeout=90000)
            page.wait_for_timeout(4000)
            hrefs = []
            for el in page.query_selector_all('a'):
                h = el.get_attribute('href') or ''
                if h.startswith('/@' + a.handle + '/post/'):
                    hrefs.append('https://www.threads.com' + h)
            seen = []
            for h in hrefs:
                if h not in seen:
                    seen.append(h)
            for h in seen[:3]:
                page.goto(h, wait_until='networkidle', timeout=90000)
                page.wait_for_timeout(3000)
                if a.caption in page.content():
                    post_url = h
                    break
            if post_url:
                break
        ctx.close()
        if browser:
            browser.close()
        if not post_url:
            print('POST-UNVERIFIED: caption tidak ditemukan di profil', flush=True)
            return 6
        print('POST-URL:', post_url, flush=True)
    # 5. balasan link (via comment_playwright, sesi yang sama)
    # NOTE: mode --profile belum didukung comment_playwright (masih baca session.json);
    # untuk tes profil, balasan dilewati bila --profile dipakai.
    if a.profile:
        print('HASIL: POSTED (reply dilewati: comment_playwright belum dukung --profile)', flush=True)
        return 0
    r = subprocess.run([VENV_PY, TOOLS + '/comment_playwright.py', '--url', post_url, '--text', a.reply, '--live', '--allow-link'], capture_output=True, text=True, timeout=300)
    print('REPLY-EXIT:', r.returncode, flush=True)
    print((r.stdout or '')[-500:], flush=True)
    v = subprocess.run([VENV_PY, TOOLS + '/verify_comment.py', '--url', post_url, '--probe', a.probe], capture_output=True, text=True, timeout=300)
    print('VERIFY-EXIT:', v.returncode, flush=True)
    print((v.stdout or '')[-300:], flush=True)
    if v.returncode == 0:
        print('HASIL: POSTED+REPLY-TERVERIFIKASI', flush=True)
        return 0
    print('HASIL: POSTED, REPLY-BELUM-TERVERIFIKASI', flush=True)
    return 7

if __name__ == '__main__':
    sys.exit(main())
