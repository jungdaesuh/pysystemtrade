#!/usr/bin/env bash
# Headless IB Gateway: Xvfb virtual display + IBC auto-login (paper, port 4002).
# Config (credentials): ~/ibc/config.ini   Logs: ~/ibc/logs/
set -u
DISPLAY_NUM=:99
LOG_DIR="$HOME/ibc/logs"
mkdir -p "$LOG_DIR"

if ! pgrep -f "[X]vfb ${DISPLAY_NUM}" >/dev/null; then
    Xvfb "$DISPLAY_NUM" -screen 0 1280x1024x24 >>"$LOG_DIR/xvfb.log" 2>&1 &
    sleep 1
fi

export DISPLAY="$DISPLAY_NUM"
exec "$HOME/opt/ibc/scripts/ibcstart.sh" 1045 --gateway \
    --mode=paper \
    --ibc-path="$HOME/opt/ibc" \
    --ibc-ini="$HOME/ibc/config.ini" \
    --tws-path="$HOME/Jts" \
    --tws-settings-path="$HOME/Jts" \
    >>"$LOG_DIR/ibc-gateway.log" 2>&1
