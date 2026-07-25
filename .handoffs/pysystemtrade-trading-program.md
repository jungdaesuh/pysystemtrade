# HANDOFF — Personal systematic trading program on pysystemtrade   ·   task-key: pysystemtrade-trading-program

> Updated 2026-07-17 00:15 EDT · Status: **PAPER SYSTEM IS LIVE WITH POSITIONS** —
> commissioning executed 2026-07-15 (9 real paper fills; EUROSTX +4 complete @ avg
> 6297.25, V2X −5 of −62 partial @ avg 19.97; NLV ~$999.7k). Four US instruments
> (CORN/US10/MXP/SOFR) blocked on CME+CBOT data-subscription ACTIVATION (bought
> 2026-07-16 pm; re-probed 07-17 00:14 in LIVE mode with exact conIds — still Error
> 354 on all three ⇒ "next-day activation" ruled mostly out, billing hold on the
> unfunded live account is now the leading explanation → USER portal check/deposit).
> Daily cycle ran 07-17 00:14: all six instruments current through 07-16, exit 0.
> Cron RESUMED 07-17 + 18:47 Claude wakeup. Gate 1 CLOSED. **Gate 2p/2s ADOPTED 2026-07-17**; the
> 07-17 session found+fixed a zero-limit-price defect (IB sentinel quotes, commit
> `7ce72fb0`) so per counting rules the day does NOT count — **next Day-1 candidate
> Mon 2026-07-20** on fixed code. Positions: EUROSTX +4, V2X −7 (2 more fills @20.30).

## Goal
Production-grade personal systematic trading program: (a) real-money barbell per
policy, (b) paper futures pipeline against IBKR through three gates, (c) engine live
~Sept 2026 if gates pass, (d) research factory. **Done when:** engine trades live on
micro futures with clean daily reconciliation, scaled per policy.

## Next actions  (start here)
1. [ ] **Verify CME/CBOT data active** (blocks the 4 US instruments): USER checks
       Portal → Settings → Market Data Subscriptions for Active/Pending/billing flag
       (probably needs the LIVE-account deposit — fees bill there; balance $0).
       Machine-side probe, **during trading hours only** (closed markets report
       NO LIVE DATA for everything and prove nothing):
       `PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private .venv/bin/python scripts/data_utilities/probe_market_data.py CORN US10 MXP SOFR EUROSTX V2X`
       Dark since purchase 07-16 through 07-24 (9 sessions).
2. [ ] **Evening ops now scheduled (user-approved 2026-07-17)**: system cron RESUMED
       (18:30 weekdays, daily_cycle_pilot → ~/ibc/logs/daily_cycle.log) + a Claude
       session-only wakeup 18:47 weekdays (verifies cron, runs EOD stack cleanup +
       data probe, reports; expires ~07-24 or when session dies — RE-CREATE it in a
       new session). Manual fallback:
       `PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private .venv/bin/python scripts/data_utilities/daily_cycle_pilot.py`
3. [ ] **Sessions RECURRING weekdays 09:37 ET** (standing auth, user 07-21;
       Claude cron cc9dca64) + **evening ops 18:47 weekdays** (cron 2e11985b).
       BOTH are session-only and AUTO-EXPIRE AFTER 7 DAYS (~08-01) — they died
       once already and Friday 07-24's cleanup silently didn't run. RE-CREATE
       them in any new session and after each expiry; check with CronList.
       Morning sequence: gateway up → `scripts/data_utilities/probe_market_data.py
       CORN US10 MXP SOFR EUROSTX V2X` → spike/trio sanity (approve via
       `scripts/data_utilities/approve_contract_spike.py`) → phase6_bringup →
       **commission_stack_handler --minutes 3 FOREGROUND, 300000ms timeout**
       (short so it finishes in-foreground; kills 07-22..07-24 are HOST MEMORY
       CONTENTION from the user's 15.5Gi fusion job, NOT a pipeline defect —
       DECISIONS 07-24; one cleanly booked fill = the day's pipeline-proof).
       Killed → verify clean, re-run once, then STOP. **After ANY interrupted
       pass, check IB open orders + positions vs system FIRST** (a killed
       session can hide a BOOKED fill). Evening: cycle check → spike check →
       `scripts/data_utilities/eod_stack_cleanup.py` (verify it RAN) →
       reconcile. Never kill the user's processes. Day-judging with the user.
       Stacks are cleared nightly (EOD cleanup) — Monday's session starts with
       phase6_bringup.py to regenerate orders from fresh optimals (07-17 optimals
       were ~CORN −27, US10 −1, MXP −1, SOFR −2, V2X −58 remaining). With data
       active, expect all six to execute. Afterwards run the reconcile report.
4. [ ] USER DECISIONS pending: **margin application** status on U26413969; **ACH
       deposit** (unblocks data billing + Phase 1 barbell deploy + Gate 3 math →
       Gate 2s config); security sudo items below. (Gate 2p/2s: ADOPTED 07-17 —
       clean-day criteria + counting rules in DECISIONS 2026-07-17.)
5. [ ] USER security items (from 2026-07-16 audit, commands in DECISIONS/chat):
       remove passwordless sudo (`sudo visudo`); disable SSH password auth; enable
       ufw (allow tailscale0 first!); `sudo apt upgrade` + reboot off-hours.
6. [x] **Battery queue COMPLETE 07-18** (all verdicts in DECISIONS 2026-07-18):
       every slot NULL — baseline survives; estimation nulls re-certified on
       post-#1650 code. Remaining from lit review: Tier-1 hygiene (statsmodels
       0.14.6 → drop scipy pin; schedule cost reports; execution measurement
       fields) and Tier-3 universe expansion at funding. Upstream PR
       contributions (tif fix → issue #1580, sentinel fix) PENDING USER.
7. [ ] Pre-registered follow-ups: schedule full automation only after 3 clean
       supervised days; G1b re-check 2026-08-10; immigration-attorney consult before
       live go-live (visa note, DECISIONS 2026-07-16); tax pro (PFIC/FBAR).

## State (with evidence)
- [x] **Commissioning 2026-07-15**: first-ever execution through the full path.
      9 fills booked correctly through broker→contract→instrument stacks, zero
      position break at close. Evidence: DECISIONS 2026-07-15 entry; positions at IB.
- [x] **Root-cause fix**: IB error 10349 (blank tif) killed all broker orders —
      fixed in `sysbrokers/IB/client/ib_orders_client.py` (tif="DAY" on market/
      limit/stop). Proven by the fills that followed. Commit `9f6ce4a8`.
- [x] **Discovered gate**: 'best' algo sizes from market depth; CME/CBOT delayed
      data provides none → the 4 US instruments never spawn broker orders. EUREX
      delayed works. Fix = CME+CBOT subscription (bought, awaiting activation).
- [x] **Position-break war story resolved**: fill raced its 10349 "cancel";
      broker-side-only flatten then created the reverse break; reconciled through
      system position tables. Rules in learnings (2026-07-15 entries).
- [x] Gate 1 CLOSED under amended faithful criteria (G1a bitwise; G1b per-instrument
      + MXP 44bd exemption, exit-0; G1c full artifact vs independent recompute).
      Both checkers + 9 pure-function tests. Commits `eea1f182`, audit trail in
      DECISIONS 2026-07-12.
- [x] Risk controls: per-instrument position caps + 1-day trade caps in Mongo
      (`scripts/data_utilities/set_paper_limits.py`); orders regenerated through them.
- [x] Security audit 2026-07-16: IBC `AcceptIncomingConnectionAction=reject` set
      (active since evening Gateway restart); mongo localhost-only ✓; secrets 600 ✓;
      REMAINING = user sudo items (next action 5).
- [x] Visa research logged (DECISIONS 2026-07-16): passive investing permitted;
      Matter of Lett (BIA 1980) + Bhakta v. INS (9th Cir. 1981) favorable; engine
      amber → attorney check pre-live. Barbell/paper green.
- [x] IBKR portal progress 2026-07-16 (user): futures trading permissions signed
      (US + Germany), NP questionnaire signed, CME/CBOT data subscribed — activation
      UNVERIFIED (Error 354 at 18:02 probe).
- [ ] Gate 2p: IN PROGRESS — 0/10 clean days (07-17 attempt voided by the
      zero-limit-price defect per counting rules; fixed + 8 regression tests,
      commit `7ce72fb0`; next candidate Mon 07-20). Needs ≥3 counted days with
      CME/CBOT execution to close. Gate 2s: config build gated on funding (Gate 3).
- [ ] Barbell real-money deploy: waits on deposit (script proven on paper 2026-07-10).

## Environment & how to run
- cwd/repo/branch: `/home/jungdaesuh/code/software/trading/pysystemtrade` / fork / `develop`
- HEAD: `b395c665` (all work committed+pushed; transient results/ dirs untracked).
- Env: `.venv/bin/python` everything; `export PYSYS_PRIVATE_CONFIG_DIR="$HOME/pysystemtrade-private"`
  (in ~/.bashrc AND ~/.zshrc since 07-12). Deps LOCKED: `requirements-lock.txt`
  (scipy pinned 1.13.1 — statsmodels needs it; anchor re-verified bitwise).
- Mongo: `docker start pysystemtrade-mongo` (unless-stopped; stays down after manual stop).
- Gateway (headless): `~/ibc/gatewaystart-headless.sh`; port 4002 ~40s; logs
  `~/ibc/logs/`. Exits itself daily 23:45 ET; cycle script self-heals it.
- Daily cycle: `scripts/data_utilities/daily_cycle_pilot.py` — overlap-locked,
  broker-session-verified, freshness-asserting (exit 1 on stale).
- Commissioning: `scripts/data_utilities/commission_stack_handler.py --minutes N`.
- Backtest+orders refresh (idempotent): `scripts/data_utilities/phase6_bringup.py`.
- Gates: `analysis/research_harness/g1b_stitch_check.py`, `g1c_parity_check.py`
  (both exit nonzero on fail); anchor: `run_battery.py --variants baseline --jobs 1`
  → 0.478/32.87/13422 exactly.
- CRON: RESUMED 2026-07-17 (18:30 weekdays daily cycle, user-approved) + Claude
  18:47 wakeup (session-only, see next action 2). Backup: ~/ibc/crontab_backup_20260712.txt.
- Paper account DUR207416: ~$999.7k NLV; futures +4 FESX Sep26, −5 FVS Oct26; five
  ETF rehearsal positions (SGOV 68/VTI 2/VEA 14/GLDM 9/VGIT 11). Live U26413969:
  unfunded, Cash type, futures permissions requested 07-16.

## Decisions & rationale (recent; full journal in docs/custom/DECISIONS.md)
- Gate 2 split ADOPTED 2026-07-17 (2p: 10 clean days chapter-15 pipeline, cumulative,
  pipeline-defect resets count, ≥3 days must include CME/CBOT execution; 2s: ≥10 days
  on micro+25%vol go-live config; both before any live order).
- Free gap-stitch over vendor (funding <$10k); Gate 1 amended criteria; four
  research null-wins; barbell policy; W-9 branch; IRP on hold (PFIC).
- Paper commissioning verdict: pipeline PASSED; days don't count until 2p/2s adopted.
- Full automation deliberately deferred until 3 clean supervised days.

## Dead ends / do NOT retry
- Blank tif on ANY IB order (10349 kills or races); broker-side-only flattening;
  closing gates against weaker criteria than adopted; config in private_config.yaml
  when the consumer reads private_control_config.yaml; `pkill -f` without bracket
  trick; dotted PYSYS paths; apt Mongo; `python -m venv` on uv interpreters;
  DISPLAY=:0 Gateway launch; production price fetcher for expired contracts
  (1y-from-now window — use expiry-anchored, see gap_stitch.py).

## Open questions / blockers
- CME/CBOT data activation (next action 1) — likeliest hold: unfunded live account.
  Probes all Error 354: 07-16 18:02, 07-17 00:14 / 10:33 / 19:17.
- RESOLVED 07-20: EUROSTX NaN-PRICE was the spike guard chronically false-
  positiving on an EMPTY hourly series (aborting all writes, silently — no
  SMTP). Operator-approved via check_for_spike=False write (designed
  workflow); series current intraday. V2X 07/08/09 bare contracts still flag
  the same pattern — harmless (non-trio), approve likewise if persistent.
- Gate 2p: **1/10 counted** (Day 1 = 07-20); Day-3 07-23 (V2X −9) and Day-4
  07-24 (V2X −11, 2 fills) both executed CLEAN after memory-contention kills,
  judgments PENDING USER (recommend both COUNT → 3/10). Day-2 07-22 never
  completed. ≥3 counted days still need CME/CBOT execution to close (data dark
  9 days) — this, not the day count, is the binding constraint.
- HOST HEALTH (user-awareness): memory-tight when the fusion job runs
  (07-24: 1.3Gi free, swap 93%). Trading pipeline unaffected (state clean
  through every kill) but long sessions get reaped — hence --minutes 3.
- Margin application status — user hasn't confirmed submitting it.
- Funding amount/timing — gates Gate 3, barbell deploy, data billing.
- Gate 2p/2s adoption — user.
- V2X remaining −57: fills grind ~1-lot slices; completes over sessions.

## Mental model
- Two engines: barbell (real money, ETFs, human-triggered, green-lit incl. visa-wise)
  and futures engine (paper, autonomous, leveraged — three gates + attorney check
  before real money). Paper time ∝ autonomy × leverage.
- The stack pipeline: instrument order → contract order (spawn) → broker orders
  (algo slices, needs market depth for sizing) → fills propagate back up with
  parent-child links. `commission_stack_handler.py` runs one supervised production
  pass; `run_stack_handler` is the eventual scheduled daemon.
- IB quirks bible: 10349 tif; expired-data expiry-anchoring; dual-listed symbols
  (MXP/6M); 23:45 daily self-exit; one-session-per-account; delayed data has no
  depth on CME (algo starves) but works on EUREX; subscriptions bill the LIVE
  account and shared to paper; activation next-hour-or-next-day.
- The knowledge loop is the product: DECISIONS.md (pre-registered, judged),
  learnings/ (one rule per problem), battery results registry, this handoff.

## Pointers
- Plans: `docs/custom/plans/portfolio_policy.md` · `gate1_parity_definition.md` ·
  `ib_paper_trading_implementation_plan.md` · `upgrade_surgical_map.md`
- Journal/learnings: `docs/custom/DECISIONS.md` · `docs/custom/learnings/README.md`
- Cron backup: `~/ibc/crontab_backup_20260712.txt` · IBC config: `~/ibc/config.ini` (600)
- Mistake book: `~/.claude/skills/crucible/shared/mistake-book.md` (117-118)
