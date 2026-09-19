#!/usr/bin/env bash
#
# trading_heartbeat_check.sh — durable watchdog for the pysystemtrade paper
# trading program. Detects the failure mode of 2026-09-04: the session-only
# Claude crons (morning / midday / evening passes) expired, nobody noticed, and
# trading was dead for three weeks.
#
# It depends on NOTHING except bash, git and coreutils — no Claude session, no
# python, no Mongo, no IB. It never places orders and never runs trading code.
#
# Two independent checks, both evaluated in business days (Mon-Fri):
#   (a) docs/custom/DECISIONS.md must carry an entry dated today or the last
#       business day  (heading form "## YYYY-MM-DD").
#   (b) the newest git commit whose subject starts with "custom:" must be dated
#       today or the last business day.
# Either failing raises one alert carrying both findings.
#
# Alert channel, in order:
#   1. email via the repo's own sender, but ONLY if the private config actually
#      has email_address/email_server set. It does not today: private_config.yaml
#      sets email_store_filename only, so pysystemtrade "stores not sent"
#      (see syslogdiag/email_via_db_interface.py:148 and email.log).
#   2. fallback: write /home/jungdaesuh/ibc/logs/HEARTBEAT_ALERT (authoritative,
#      failure to write is fatal) and best-effort desktop notify-send.
#
# Exit codes: 0 healthy, 1 alert raised, 2 internal error.
#
# PROPOSED system crontab line (NOT installed by this script) — weekday evenings
# at 19:10 ET, after the 18:30 daily cycle and the 18:47 evening pass:
#
#   10 19 * * 1-5 /data/code/software/trading/pysystemtrade/scripts/ops/trading_heartbeat_check.sh >> /home/jungdaesuh/ibc/logs/heartbeat_check.log 2>&1
#
set -Eeuo pipefail

REPO="/data/code/software/trading/pysystemtrade"
PRIVATE_CONFIG="/home/jungdaesuh/pysystemtrade-private/private_config.yaml"
PRIVATE_CONFIG_DIR="/home/jungdaesuh/pysystemtrade-private"
DECISIONS="${REPO}/docs/custom/DECISIONS.md"
ALERT_FILE="/home/jungdaesuh/ibc/logs/HEARTBEAT_ALERT"
VENV_PYTHON="${REPO}/.venv/bin/python"
export TZ="America/New_York"

fail() {
    printf 'trading_heartbeat_check: FATAL: %s\n' "$1" >&2
    exit 2
}

trap 'fail "unhandled error at line ${LINENO}"' ERR

[ -d "${REPO}" ] || fail "repo not found: ${REPO}"
[ -f "${DECISIONS}" ] || fail "decision journal not found: ${DECISIONS}"

# --- business-day arithmetic -------------------------------------------------
# previous_business_day <YYYY-MM-DD> -> the latest Mon-Fri date strictly before it
previous_business_day() {
    local day="$1" back=1 candidate dow
    while [ "${back}" -le 7 ]; do
        candidate="$(date -d "${day} -${back} day" +%F)"
        dow="$(date -d "${candidate}" +%u)"
        if [ "${dow}" -le 5 ]; then
            printf '%s\n' "${candidate}"
            return 0
        fi
        back=$((back + 1))
    done
    fail "could not resolve a business day before ${day}"
}

TODAY="$(date +%F)"
TODAY_DOW="$(date +%u)"
if [ "${TODAY_DOW}" -le 5 ]; then
    REF_DAY="${TODAY}"
else
    # weekend run: the newest day trading could have happened is the last weekday
    REF_DAY="$(previous_business_day "${TODAY}")"
fi
PREV_BD="$(previous_business_day "${REF_DAY}")"
CUTOFF_EPOCH="$(date -d "${PREV_BD} 00:00:00" +%s)"

# --- check (a): DECISIONS.md freshness ---------------------------------------
decisions_problem=""
# a weekend catch-up entry dated literally today also counts
if grep -Eq "^## (${TODAY}|${REF_DAY}|${PREV_BD})" "${DECISIONS}"; then
    last_entry="$(grep -Eo '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' "${DECISIONS}" | tail -n 1 | awk '{print $2}')"
    printf 'OK  decisions: entry present for %s / %s / %s (newest heading %s)\n' \
        "${TODAY}" "${REF_DAY}" "${PREV_BD}" "${last_entry}"
else
    last_entry="$(grep -Eo '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' "${DECISIONS}" | tail -n 1 | awk '{print $2}')"
    [ -n "${last_entry}" ] || last_entry="(none found)"
    decisions_problem="DECISIONS.md has no entry dated ${TODAY}, ${REF_DAY} or ${PREV_BD}; newest entry is ${last_entry}"
    printf 'ALERT decisions: %s\n' "${decisions_problem}"
fi

# --- check (b): newest custom: commit ----------------------------------------
commit_problem=""
commit_line="$(git -C "${REPO}" log -1 --grep='^custom:' --format='%H%x09%cI%x09%ct%x09%s' || true)"
if [ -z "${commit_line}" ]; then
    commit_problem="no git commit with prefix 'custom:' exists in ${REPO}"
    printf 'ALERT commits: %s\n' "${commit_problem}"
else
    commit_epoch="$(printf '%s' "${commit_line}" | cut -f3)"
    commit_when="$(printf '%s' "${commit_line}" | cut -f2)"
    commit_subject="$(printf '%s' "${commit_line}" | cut -f4)"
    commit_sha="$(printf '%s' "${commit_line}" | cut -c1-8)"
    if [ "${commit_epoch}" -ge "${CUTOFF_EPOCH}" ]; then
        printf 'OK  commits: newest custom: commit %s at %s (%s)\n' \
            "${commit_sha}" "${commit_when}" "${commit_subject}"
    else
        age_days=$(( ( $(date +%s) - commit_epoch ) / 86400 ))
        commit_problem="newest 'custom:' commit is ${commit_sha} at ${commit_when} (${age_days} days old; cutoff ${PREV_BD} 00:00 ${TZ}) — subject: ${commit_subject}"
        printf 'ALERT commits: %s\n' "${commit_problem}"
    fi
fi

if [ -z "${decisions_problem}" ] && [ -z "${commit_problem}" ]; then
    printf 'trading_heartbeat_check: HEALTHY at %s\n' "$(date -Is)"
    exit 0
fi

# --- build the alert ---------------------------------------------------------
SUBJECT="pysystemtrade HEARTBEAT ALERT: trading passes appear dead (${TODAY})"
BODY="$(cat <<EOF
Checked at $(date -Is) on $(hostname) by scripts/ops/trading_heartbeat_check.sh

Reference business day: ${REF_DAY}   previous business day: ${PREV_BD}

$( [ -n "${decisions_problem}" ] && printf -- '- DECISIONS: %s\n' "${decisions_problem}" )
$( [ -n "${commit_problem}" ] && printf -- '- COMMITS:   %s\n' "${commit_problem}" )

Most likely cause: the session-only Claude crons (morning 08:57 / midday 11:36 /
evening 18:47 ET) have expired again. They die ~7 days after creation and with
the session that created them.

Fix: re-create all three from the ready-to-paste prompts in
docs/custom/plans/trading_cron_prompts_2026-09.md, then verify positions
IB-vs-system (zero break) before resuming.
EOF
)"

# --- channel 1: email, only if actually configured ---------------------------
email_sent="no"
if [ -f "${PRIVATE_CONFIG}" ] \
   && grep -Eq '^[[:space:]]*email_address:' "${PRIVATE_CONFIG}" \
   && grep -Eq '^[[:space:]]*email_server:' "${PRIVATE_CONFIG}" \
   && [ -x "${VENV_PYTHON}" ]; then
    printf 'email: configured in %s, sending via syslogdiag.emailing\n' "${PRIVATE_CONFIG}"
    if PYSYS_PRIVATE_CONFIG_DIR="${PRIVATE_CONFIG_DIR}" \
       "${VENV_PYTHON}" -c 'import sys
from syslogdiag.emailing import send_mail_msg
send_mail_msg(sys.stdin.read(), sys.argv[1])' "${SUBJECT}" <<<"${BODY}"; then
        email_sent="yes"
    else
        printf 'email: send FAILED (exit %s) — falling back to file + desktop\n' "$?" >&2
    fi
else
    printf 'email: not configured (no email_address/email_server in %s) — using file + desktop fallback\n' \
        "${PRIVATE_CONFIG}"
fi

# --- channel 2: alert file (authoritative) + desktop notification ------------
if [ "${email_sent}" != "yes" ]; then
    alert_dir="$(dirname "${ALERT_FILE}")"
    [ -d "${alert_dir}" ] || fail "alert directory missing: ${alert_dir}"
    {
        printf '%s\n' "${SUBJECT}"
        printf '%s\n' "${BODY}"
        printf '\n'
    } >> "${ALERT_FILE}" || fail "could not write alert file ${ALERT_FILE}"
    printf 'alert written to %s\n' "${ALERT_FILE}"

    if command -v notify-send >/dev/null 2>&1; then
        if notify-send --urgency=critical "${SUBJECT}" "Trading passes appear dead — see ${ALERT_FILE}"; then
            printf 'desktop notification sent\n'
        else
            printf 'desktop notification FAILED (exit %s; no session bus?) — alert file stands\n' "$?" >&2
        fi
    else
        printf 'notify-send not installed — alert file stands\n' >&2
    fi
fi

printf 'trading_heartbeat_check: ALERT RAISED at %s\n' "$(date -Is)"
exit 1
