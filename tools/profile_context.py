#!/usr/bin/env python3
"""Persistent Chromium profile per Threads account (pola dari fork threads-mcp).
Satu user-data-dir per akun, tidak pernah di-switch: ~/.threads_poster/profiles/<handle>
- launch_profile_context(playwright, handle): buka persistent context untuk akun itu.
- profile_dir(handle): path dir profil.
- is_logged_in(page, handle): cek 'Edit profile' di halaman profil akun.
"""
from pathlib import Path

PROFILES_ROOT = Path.home() / '.threads_poster' / 'profiles'


def profile_dir(handle):
    return str(PROFILES_ROOT / handle)


def launch_profile_context(playwright, handle):
    return playwright.chromium.launch_persistent_context(
        profile_dir(handle),
        headless=False,
        args=['--no-sandbox', '--disable-dev-shm-usage'],
        viewport={'width': 1280, 'height': 800},
    )


def is_logged_in(page, handle):
    return page.content().count('Edit profile') > 0
