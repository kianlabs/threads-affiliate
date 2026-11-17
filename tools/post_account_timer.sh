#!/bin/bash
# Wrapper timer: satu post akun sekunder (live). Dipanggil systemd.
set -u
ACCOUNT="$1"
cd "$HOME/threads-affiliate-system" || exit 1
exec >> "logs/account_${ACCOUNT}.log" 2>&1
echo "=== $(date -Is) post ${ACCOUNT} ==="
xvfb-run -a .venv/bin/python tools/post_account.py --account "$ACCOUNT" --live
