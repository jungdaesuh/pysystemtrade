# Trading cron prompts — reconstruction for re-creation (2026-09-19)

> Renewed 2026-09-25 (IDs d089b9a3 / 600115aa / d0e47293, expire ~10-02): US10 roll text retired, V2X Passive roll + BAG/tmp-quota/orphan-fill guidance added, anchors as of 09-25.

Status: the three session-only Claude crons (morning / midday / evening) created
2026-08-28 (`09737aae`, `80cffa59`, `e9ac7e7e`) expired ~2026-09-04 with the
session that owned them. No trading pass has run since 2026-08-28; the last
`custom:` commit is `0dc5ec3d` (2026-08-28T12:11:03-04:00).

Source of the prompt texts: recovered VERBATIM from the `CronCreate` tool calls
in the session transcript
`~/.claude/projects/-home-jungdaesuh-code-software-trading-pysystemtrade/32339452-8881-4c79-a2e6-01299115b4b2.jsonl`
(entries dated 2026-08-28T13:31:15Z / 13:31:23Z / 13:31:33Z), cross-checked
against the "CRONS RENEWED" entries in `docs/custom/DECISIONS.md`
(2026-07-31 L846, 2026-08-21 L1334, 2026-08-28 L1485).

Repo root: `/home/jungdaesuh/code/software/trading/pysystemtrade`
(same inode as `/data/code/software/trading/pysystemtrade` — bind-mounted, either
path works; the prompts use the `$HOME` spelling, keep it).
Interpreter: `.venv/bin/python`. Private config: `PYSYS_PRIVATE_CONFIG_DIR=/home/jungdaesuh/pysystemtrade-private`.

## Schedules (all weekdays, timezone America/New_York)

| Pass | Cron | Fires | Trading window it targets |
|---|---|---|---|
| Morning session | `57 8 * * 1-5` | 08:57 ET | handler pass lands ~09:28-09:45, inside EUREX 03:00-10:00 |
| Midday pass | `36 11 * * 1-5` | 11:36 ET | CORN/US window 11:30-14:20 |
| Evening ops | `47 18 * * 1-5` | 18:47 ET | after the durable 18:30 system-cron daily cycle |

All three are `recurring: true`. Session-only crons expire ~7 days after
creation — renew weekly, and rely on `scripts/ops/trading_heartbeat_check.sh`
(system crontab) to catch the next silent expiry.

## DECISIONS.md log-entry conventions

Top-of-file template (`docs/custom/DECISIONS.md` lines 7-15):

```
## YYYY-MM-DD — <decision>
- Decision: <what, size, instrument>
- Reasoning: <why now; which rule/policy section authorizes it>
- Expectation: <what should be true, by when, to call this right>
- Judge on: <date>
- Outcome (filled later): <what happened; right/wrong/unclear; lesson → learnings/>
```

Daily operational passes use the lighter house style actually in use since
Day-9 (mirror it exactly):

```
## YYYY-MM-DD — Day-N MORNING pass: <one-line verdict>
- Pass HH:MM-HH:MM. All six LIVE; data sane; no trio spikes.
- Fills: <instrument> <n> x <+/-1> @ <price> -> position <p>. <what was left for midday>
- ZERO breaks; no working orders. NLV <x> (<delta vs last close>; <% inception>; <% from HWM>).
- <roll / ops notes>

## YYYY-MM-DD — Day-N MIDDAY pass: <verdict>
- Fill: ... -> position ...
- ZERO breaks (MXP -2, V2X -90, EUROSTX +7, US10 -2, CORN -16, SOFR -7);
  no working orders. NLV <x>.

## YYYY-MM-DD evening — <verdict>
- Cycle succeeded; prices current. Cleanup verified: stacks 0/0/0.
- ZERO breaks (<per-instrument positions>).
- NLV <x> (<day change>; <% inception>; <% from HWM>).
```

"ZERO breaks" verification = for every held instrument (and, during a roll, every
held *contract* separately), the broker position reported by IB equals the
position the system holds, and there are no dangling/working IB orders. Per the
2026-08-25 precedent a roll may legitimately SPLIT a position across two
contracts; the standard is per-contract zero break, not per-instrument.

Commit convention: every pass appends its entry, then commits with subject
prefix `custom:` (e.g. `custom: Day-29 midday — CORN -16, zero break`) and
pushes.

---

## 1. MORNING session — cron `57 8 * * 1-5` (America/New_York)

Paste as the CronCreate prompt (verbatim recovery, with the explicit
`custom:` commit instruction and the DECISIONS template pointer appended —
see "Gaps" below):

```
Gate 2p Day-N commissioning session (MORNING pass) for the pysystemtrade paper program — standing weekday authorization granted by the user 2026-07-21; schedule per user-approved Option 1 (2026-08-02): trading pass lands INSIDE the EUREX window (03:00–10:00 EDT); CORN is handled by the separate ~11:36 midday pass. SSOT: /home/jungdaesuh/code/software/trading/pysystemtrade/.handoffs/pysystemtrade-trading-program.md; skip silently if today is a US/EUREX holiday. FIRST verify this pass has not already run today (grep docs/custom/DECISIONS.md for today's MORNING entry; if already run, skip with a one-line report). All commands from repo root /home/jungdaesuh/code/software/trading/pysystemtrade with PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private and .venv/bin/python. Sequence: (1) Ensure Gateway up on port 4002 (~/ibc/gatewaystart-headless.sh; wait for "Configuration tasks completed" in ~/ibc/logs/ibc-gateway.log); retry once on failure, else report loudly and stop. (2) Probe: scripts/data_utilities/probe_market_data.py CORN US10 MXP SOFR EUROSTX V2X --wait 5 — all six LIVE is normal; NO LIVE DATA on the US four = subscription regressed, report loudly. (3) Data sanity: EUROSTX multiple-prices tail non-NaN; check last night's daily_cycle.log for "Spike found" on TRIO contracts of HELD instruments (trios: V2X 20261000/20261100, SOFR 20290600, EUROSTX 20261200/20270300, CORN 20261200 chain, MXP 20261200 chain, US10 20261200/20270300) — verify stored vs broker (dataBroker.get_prices_at_frequency_for_contract_object with DAILY_PRICE_FREQ) then approve via scripts/data_utilities/approve_contract_spike.py INSTRUMENT CONTRACTDATE (two separate shell words) BEFORE the backtest and re-run update_multiple_adjusted_prices_with_data(data, instrument_code=CODE); far-month flags (CORN 2027xx, SOFR 2026-2028 and 2029 other than 20290600, V2X 20260800/20260900) are cosmetic noise, ignore. (4) Run scripts/data_utilities/phase6_bringup.py. (5) ROLL STATUS: MXP, EUROSTX and US10 are all on Dec 20261200 (US10 rolled 09-21). V2X is in PASSIVE roll (Oct 20261000 -> Nov 20261100, Oct expiry 10-21): closing trades in Oct, opening in Nov, split positions are legitimate; when Oct is flat finalize via state_change_to_roll_adjusted_prices(data, "V2X", RollState.Passive, confirm_adjusted_price_change=False) and VERIFY priced 20261100, adjusted continuity, state No_Roll, zero break. If by ~10-14 Oct is still large (>20 lots), flag to the user that a Force roll may be needed and that Force spread orders re-trigger the BAG order-listing defect (DECISIONS 2026-09-21) — decide WITH the user. (6) Run scripts/data_utilities/commission_stack_handler.py --minutes 2 FOREGROUND, Bash timeout 300000ms; overrun-to-background = wait then verify, not a kill. If actually killed: verify state clean, re-run once, then STOP. (7) MANDATORY after any interrupted pass: check IB open orders + positions vs system BEFORE anything else (raw ib_async positions/openTrades/fills is acceptable for the check). Then verify positions IB vs system (zero break expected), stacks, fills; if an orphaned broker order filled at IB but not in the DB, run stackHandler.process_fills_stack() then handle_completed_orders(). (8) KNOWN CONTEXT, do not re-diagnose: outage 08-28..09-19 (crons expired) and 09-23 (/tmp quota: Bash returns empty/exit 1 — check df -h /tmp, redirect output to a file under $HOME or /data, never conclude the shell is broken); positions as of 09-25: CORN -11, EUROSTX +2 Dec, MXP -3 Dec, SOFR -11, US10 -4 Dec, V2X -90 Oct / -3 Nov; NLV ~970k (-3% inception); drawdown was the corn short in a squeeze, now unwinding — report NLV plainly, no intervention. Known open items, note but do not fix: BAG order-listing hang (ib_orders.py:212, only when a filled combo trade is in the IB session); FORWARD/CARRY NaN on the last multiple row for EUROSTX/MXP post-roll; V2X carry contract expired/NaN until the roll completes; the 2-min handler window overruns with 3+ US orders (user decision pending on --minutes 4). Gateway auto-logs-off 23:45 ET; memory pressure from the user's other jobs has killed it before — just relaunch. Leave unfilled US-window orders on the stack for the midday pass — do NOT clean stacks. (9) Report concisely; flag loudly on any anomaly/rejection/break; a defect needing a code fix voids the day per DECISIONS 2026-07-17. Append the session to docs/custom/DECISIONS.md using the house entry style ("## YYYY-MM-DD — Day-N MORNING pass: <verdict>"; pass window, fills, ZERO-break line with per-contract positions, NLV), then `git add docs/custom/DECISIONS.md && git commit -m "custom: <one-line summary>"` — the commit subject MUST start with "custom:" — and push. Do NOT judge/count the day. Do NOT kill the user's fusion or other processes. Paper account only; never touch the live account; risk limits stay as configured. CRON EXPIRY: this session-only cron was created 2026-09-25 and expires ~10-02; on 10-01 or the last firing, renew all three crons from docs/custom/plans/trading_cron_prompts_2026-09.md (delete the old IDs first) and record the new IDs in DECISIONS.md.
```

## 2. MIDDAY pass — cron `36 11 * * 1-5` (America/New_York)

```
Gate 2p MIDDAY pass (CORN window 11:30-14:20 EDT) for the pysystemtrade paper program — per user-approved Option 1 (2026-08-02). LIGHT pass: no backtest, no spike approvals — executes whatever orders the morning session left on the stack (V2X Passive roll clips, split Oct/Nov positions, are normal). SSOT: /home/jungdaesuh/code/software/trading/pysystemtrade/.handoffs/pysystemtrade-trading-program.md; skip silently if today is a US holiday, if the morning session did not run (empty instrument stack = one-line report), or if today's MIDDAY entry already exists in docs/custom/DECISIONS.md (duplicate firing — skip with one line). All commands from repo root /home/jungdaesuh/code/software/trading/pysystemtrade with PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private and .venv/bin/python. Sequence: (1) Ensure Gateway up on port 4002 (~/ibc/gatewaystart-headless.sh if down; wait for "Configuration tasks completed"). (2) Run scripts/data_utilities/commission_stack_handler.py --minutes 2 FOREGROUND, Bash timeout 300000ms; overrun-to-background = wait then verify, not a kill. If actually killed: verify state clean, re-run once, then STOP. (3) MANDATORY after any interrupted pass: check IB open orders + positions vs system FIRST (raw ib_async positions/openTrades/fills is acceptable). Then verify positions IB vs system (zero break), stacks, fills — during rolls the position may legitimately SPLIT across two contracts; per-contract zero break is the standard. If an orphaned broker order filled at IB but not in the DB, run stackHandler.process_fills_stack() then handle_completed_orders() and re-check. (4) If V2X Oct reaches zero this pass, finalize via state_change_to_roll_adjusted_prices(confirm_adjusted_price_change=False) and verify promotion + adjusted continuity (08-26 precedent). (5) Report concisely; flag loudly on anomalies. Append a short entry to docs/custom/DECISIONS.md in the house style ("## YYYY-MM-DD — Day-N MIDDAY pass: <verdict>"; fills, ZERO-break line with per-contract positions, NLV), then `git add docs/custom/DECISIONS.md && git commit -m "custom: <one-line summary>"` — the commit subject MUST start with "custom:" — and push. Do NOT judge/count the day. Do NOT kill the user's fusion or other processes. Paper account only; leftover unfilled orders are normal — evening cleanup handles them. Known: the 2-min window overruns with 3+ US orders (user decision pending on --minutes 4); if Bash returns empty output / exit 1 check df -h /tmp (quota) before concluding anything. CRON EXPIRY: session-only cron created 2026-09-25, expires ~10-02; the morning pass owns renewal.
```

## 3. EVENING ops — cron `47 18 * * 1-5` (America/New_York)

```
Scheduled evening ops pass for the pysystemtrade paper program (SSOT: /home/jungdaesuh/code/software/trading/pysystemtrade/.handoffs/pysystemtrade-trading-program.md). All commands from repo root /home/jungdaesuh/code/software/trading/pysystemtrade with PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private and .venv/bin/python. FIRST verify this pass has not already run today (grep docs/custom/DECISIONS.md for today's evening entry) and that the 18:30 system cycle HAS run (freshness OK stamped today in /home/jungdaesuh/ibc/logs/daily_cycle.log) — if the cycle hasn't run yet or this is a duplicate firing, skip with a one-line report. If YESTERDAY's evening entry is also missing (check DECISIONS.md), note the missed cleanup and verify stacks were caught up by the morning pass. Steps: (1) Verify the daily cycle succeeded (freshness OK today); if missing/failed, run scripts/data_utilities/daily_cycle_pilot.py manually (self-heals the Gateway; Gateway self-exits daily 23:45 ET). (2) Check the cycle log for "Spike found" on TRIO contracts of HELD instruments — V2X 20261000/20261100, SOFR 20290600, EUROSTX 20261200/20270300, CORN 20261200 chain, MXP 20261200 chain, US10 20261200/20270300. If a held contract is quarantined: verify stored vs broker daily bars, approve via scripts/data_utilities/approve_contract_spike.py INSTRUMENT CONTRACTDATE (two shell words), then re-run update_multiple_adjusted_prices_with_data(data, instrument_code=CODE) and verify the adjusted tail is current. Far-month flags (CORN 2027xx, SOFR other than 20290600, V2X 20260800/20260900) are cosmetic noise — ignore. (3) Run scripts/data_utilities/eod_stack_cleanup.py; VERIFY exit 0 and stacks 0/0/0 — flag loudly on error. "Couldn't cancel non existent order" for a broker order means it FILLED at IB while unmanaged: expect a one-lot break and book it (process_fills_stack first; if the order is already archived, use the balance-trade path with the IB fill price). (4) Verify positions IB vs system (zero break; split V2X Oct/Nov is legitimate) and report NLV with day's change. (5) Append the pass to docs/custom/DECISIONS.md in the house style ("## YYYY-MM-DD evening — <verdict>"; cycle result, spikes, stacks 0/0/0, ZERO-break line with per-contract positions, NLV and day change), then `git add docs/custom/DECISIONS.md && git commit -m "custom: <one-line summary>"` — the commit subject MUST start with "custom:" — and push. (6) Report concisely; flag loudly on anomalies. ROLL WATCH: V2X Passive roll Oct->Nov (finalize when Oct flat; Oct expiry 10-21; escalate to the user around 10-14 if Oct is still large). Do NOT start execution sessions or place orders. Do NOT kill the user's fusion or other processes. Paper account only. Also verify the standing weekday crons have not expired: if the DECISIONS.md log shows no MORNING entry for today (a business day), say so loudly in the report. If Bash returns empty output / exit 1, check df -h /tmp (quota) before concluding anything. CRON EXPIRY: session-only cron created 2026-09-25, expires ~10-02; the morning pass owns renewal; the system-cron heartbeat (scripts/ops/trading_heartbeat_check.sh, 19:10 weekdays) is the independent backstop.
```

---

## Gaps in recovery, and what was substituted

1. **Nothing was lost from the prompt bodies.** All three texts above are the
   exact `CronCreate` inputs from 2026-08-28; only the additions listed below
   were made. The cron IDs (`09737aae`, `80cffa59`, `e9ac7e7e`) are dead and
   cannot be reused — new IDs will be issued on re-creation.
2. **Added (not in the originals):** the explicit "commit subject MUST start
   with `custom:`" instruction and the house entry-style pointer in each
   prompt's append step. The originals said only "Append the session to
   docs/custom/DECISIONS.md, commit and push"; the `custom:` prefix was a
   convention carried in-session, not in the prompt text, which is exactly the
   kind of thing a fresh session would drop. The wording is derived from the
   actual commit log (`git log --grep='^custom:'`).
3. **Added to the evening prompt only:** the last sentence asking it to flag a
   missing MORNING entry — cheap in-band detection of the failure that went
   unnoticed for three weeks. Belt and braces with the system-cron watchdog.
4. **STALE CONTENT the user must refresh before pasting** (recovered faithfully
   but now out of date, since the prompts were written 2026-08-28 and today is
   2026-09-19):
   - The roll calendar is expired: EUROSTX 20260900 expired 2026-09-18 and MXP
     20260900 on 09-14; US10 20260900 expires 09-21 (two days away). No roll was
     executed after the MXP roll of 08-25/26 because the crons were dead. The
     roll section of the morning prompt and the ROLL WATCH line of the evening
     prompt must be rewritten against the current expiries before re-creation,
     and the open positions inspected first. Do not paste the roll dates as-is.
   - "KNOWN CONTEXT" drawdown framing, position sizes (V2X ~-90, CORN -16,
     EUROSTX +7, US10 -2, MXP -2, SOFR -7) and NLV anchors are as of 2026-08-28.
   - `GMT_offset_hours: -4` in the private config is EDT; per the config comment
     it must become `-5` at the November DST change, and the cron times are ET
     wall-clock so they follow the timezone automatically — the config does not.
   - Day numbering stopped at Day-29 (2026-08-28); the first restored session
     should decide with the user whether the counter resumes at Day-30 or the
     three-week gap is recorded as a break in the Gate 2p streak.
5. **Not recovered because it never existed in prompt form:** no weekend/holiday
   calendar file was referenced — holiday skipping is left to the model's
   judgement, as in the originals.

## Related

- Durable expiry watchdog (does not depend on any Claude session):
  `scripts/ops/trading_heartbeat_check.sh` — proposed system crontab line in
  its header comment. Install it before re-creating the crons.
