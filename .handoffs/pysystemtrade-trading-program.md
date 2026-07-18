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
       Machine-side probe script (re-runnable):
       `PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private .venv/bin/python /tmp/claude-1000/-home-jungdaesuh-code-software-trading-pysystemtrade/8c9c89bb-949f-427e-8784-d203f70fff10/scratchpad/probe_cme_data.py`
       (live-mode reqMktData on conIds SOFR3 395594167 / ZN 840227361 / 6M 761663080;
       real bid/ask sizes = active). Last probe 07-17 00:14: Error 354 all three.
2. [ ] **Evening ops now scheduled (user-approved 2026-07-17)**: system cron RESUMED
       (18:30 weekdays, daily_cycle_pilot → ~/ibc/logs/daily_cycle.log) + a Claude
       session-only wakeup 18:47 weekdays (verifies cron, runs EOD stack cleanup +
       data probe, reports; expires ~07-24 or when session dies — RE-CREATE it in a
       new session). Manual fallback:
       `PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private .venv/bin/python scripts/data_utilities/daily_cycle_pilot.py`
3. [ ] **Day-1 session SCHEDULED Mon 07-20 09:37 ET** (user "go" given 07-18; Claude
       one-shot wakeup, session-only — if the session died before it fired, run it
       manually): gateway up → data probe → EUROSTX watch check → phase6_bringup →
       `... .venv/bin/python scripts/data_utilities/commission_stack_handler.py --minutes 15`
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
6. [ ] Pre-registered follow-ups: schedule full automation only after 3 clean
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
- WATCH: EUROSTX 07-17 intraday sampling filled FORWARD (Dec26) but PRICE (Sep26)
  came back NaN → adjusted series stops at 07-16 while multiple is current. Should
  self-heal at Monday's sampling; if PRICE is still NaN then, investigate Sep26
  contract sampling before the session.
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
