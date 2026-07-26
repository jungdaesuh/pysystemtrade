# HANDOFF — Personal systematic trading program on pysystemtrade   ·   task-key: pysystemtrade-trading-program

> Updated 2026-07-26 00:08 EDT (Sun) · Status: **PAPER SYSTEM LIVE, GATE 2p IN
> PROGRESS 1/10.** Paper account holds EUROSTX +4 / V2X −11, NLV $1,000,631,
> books reconcile exactly (broker == system, verified 07-25). Four US instruments
> (CORN/US10/MXP/SOFR) have NEVER traded — CME/CBOT market data still not
> activated 9 sessions after purchase; this, not the day count, is the binding
> constraint on Gate 2p. Sessions + evening ops run on Claude crons that
> AUTO-EXPIRE ~08-01 (see Next action 2). Gate 1 CLOSED. Research battery queue
> COMPLETE (all null — baseline defended).

## Goal
Production-grade personal systematic trading program: (a) real-money barbell per
policy, (b) paper futures pipeline against IBKR through three gates, (c) engine
live ~Sept 2026 if gates pass, (d) research factory. **Done when:** engine trades
live on micro futures with clean daily reconciliation, scaled per policy.

## Next actions  (start here)

1. [ ] **Unblock CME/CBOT market data — the critical path.** Bought 2026-07-16;
       every probe since has been dark (07-16, 07-17 ×3, 07-19, 07-20, 07-21,
       07-22, 07-23, 07-24). Gate 2p CANNOT CLOSE until ≥3 counted days include
       CME/CBOT execution, so nothing else finishes the gate.
       - USER: IBKR Portal → Settings → Market Data Subscriptions — is it
         Active / Pending / flagged for billing? Leading theory: the fee bills to
         live account U26413969, which holds $0, so activation is held. An ACH
         deposit likely releases it (and also unblocks the barbell + Gate 3 math).
       - MACHINE (during trading hours ONLY — a closed market reports NO LIVE
         DATA for everything and proves nothing):
         `cd /home/jungdaesuh/code/software/trading/pysystemtrade && PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private .venv/bin/python scripts/data_utilities/probe_market_data.py CORN US10 MXP SOFR EUROSTX V2X`
         LIVE on the US four = activated (loud news: all six then execute).

2. [ ] **Re-create the two Claude crons — they expire ~2026-08-01 and die with
       this session.** They already lapsed once and Friday 07-24's cleanup
       silently didn't run. Check with CronList; if absent, recreate:
       - **Morning session, weekdays 09:37 ET** (currently `cc9dca64`) — full
         sequence in "Daily rhythm" below. Standing user authorization granted
         2026-07-21; no fresh "go" needed.
       - **Evening ops, weekdays 18:47 ET** (currently `2e11985b`) — verify the
         18:30 system cron ran, spike check, EOD cleanup, reconcile, report.
       The 18:30 system crontab entry (daily_cycle_pilot) is durable and survives
       — only the Claude jobs expire.

3. [ ] **Judge Gate 2p Days 3 and 4 with the user** (both executed clean; my
       recommendation: both COUNT → 3/10). Details in DECISIONS 2026-07-23 /
       07-24. Day 2 (07-22) never completed and does not count.

4. [ ] **USER decisions still pending:** ACH deposit (unblocks data + barbell +
       Gate 3); margin application status on U26413969; the four security sudo
       items (remove passwordless sudo via `sudo visudo`; disable SSH password
       auth; enable ufw — **allow tailscale0 FIRST**; `sudo apt upgrade` + reboot
       off-hours); optional SMTP credential so price-spike alerts can actually
       deliver (their silence hid a data outage for 3 days — DECISIONS 07-20).

5. [ ] **Open engineering hygiene** (no user decision needed, do on a quiet day):
       statsmodels 0.14.0 → 0.14.6, then drop the `scipy<1.15` cap and the
       `scipy==1.13.1` lock pin (upstream fixed `_lazywhere`); re-verify the G1a
       anchor bitwise after. Schedule `slippage_report.py` / `costs_report.py` and
       update `data/futures/csvconfig/spreadcosts.csv` when realized costs diverge
       >25%. Add execution measurement fields before any execution A/B (passive-vs-
       aggressive final state, data-quality flag, post-fill markouts, rows for
       abandoned orders) — all specified in the lit-review plan doc.

6. [ ] **Pre-registered follow-ups:** G1b re-check 2026-08-10; immigration-attorney
       consult before live go-live (DECISIONS 07-16); tax professional (PFIC/FBAR,
       Samsung sale year); universe expansion 6→~30 at funding (the one
       literature-backed lever worth ~+0.4 SR — Gate 3 design decision, NOT a
       battery experiment); optional upstream PRs (our tif fix matches open
       upstream issue #1580 exactly; sentinel fix has no upstream equivalent;
       statsmodels pyproject bump).

## Daily rhythm (what runs, in order)

- **09:37 weekdays — commissioning session** (Claude cron): Gateway up
  (`~/ibc/gatewaystart-headless.sh`, port 4002 then ~40s for API login) → probe
  market data → data sanity (EUROSTX multiple-prices tail has non-NaN PRICE; grep
  last night's `~/ibc/logs/daily_cycle.log` for `Spike found` on TRIO contracts of
  HELD instruments — verify stored vs broker prices, then approve via
  `scripts/data_utilities/approve_contract_spike.py INSTRUMENT DATE...` BEFORE the
  backtest; bare non-trio flags are harmless) → `phase6_bringup.py` →
  **`commission_stack_handler.py --minutes 3` FOREGROUND, 300000ms Bash timeout**
  → reconcile → report. Do NOT judge the day.
- **18:30 weekdays — daily data cycle** (system crontab, durable):
  `daily_cycle_pilot.py` → `~/ibc/logs/daily_cycle.log`, asserts freshness.
- **18:47 weekdays — evening ops** (Claude cron): verify the cycle logged
  `freshness OK` TODAY → spike check → `eod_stack_cleanup.py` (**verify it
  actually ran**) → reconcile positions → report.
- **Day judging happens with the user**, after the evening cycle. Never self-count.

## State (with evidence)

- [x] **Gate 1 CLOSED** under amended criteria — G1a bitwise anchor
      (0.478 / 32.87 / 13,422), G1b per-instrument continuity + MXP exemption,
      G1c artifact vs independent recompute. Checkers:
      `analysis/research_harness/g1b_stitch_check.py`, `g1c_parity_check.py`
      (both exit nonzero on fail) + 9 tests in `tests/test_g1_checkers.py`.
      Commit `eea1f182`; audit trail DECISIONS 2026-07-12.
- [x] **Gate 2p/2s ADOPTED 2026-07-17.** 2p = 10 clean days on the chapter-15
      pipeline, cumulative, ≥3 of them WITH CME/CBOT execution; a pipeline defect
      needing a code fix RESETS the count; external causes (holiday, vendor
      outage, data pending) simply don't count. 2s = ≥10 days on the real go-live
      config (micro contracts, 25% vol, universe from Gate 3 capital math). Both
      required before any live order. Clean-day criteria + counting rules:
      DECISIONS 2026-07-17. Precedent 2026-07-20: designed human-in-the-loop
      operator gates (verified spike approvals, roll confirmations) do NOT void a
      day.
- [x] **Gate 2p = 1/10 counted.** Day 1 = 2026-07-20 (user-ruled). Day 3 (07-23,
      V2X → −9) and Day 4 (07-24, 2 fills, V2X → −11) both executed clean;
      judgment PENDING USER. Day 2 (07-22) never completed.
- [ ] **Gate 2s:** not started — config can't be built until the funding amount
      fixes the Gate 3 capital math.
- [x] **Positions verified 2026-07-25:** system == broker (EUROSTX/20260900 +4 vs
      FESX Sep26 +4; V2X/20261000 −11 vs FVS Oct26 −11), zero dangling IB orders,
      all three stacks empty, NLV $1,000,631. **Books have reconciled at every
      single check since 07-15 — no unresolved break has ever survived a session.**
- [x] **Three real code bugs found and root-fixed** (all committed, all with the
      failure reproduced first):
      1. Blank `tif` → IB error 10349 killed every broker order, and one filled in
         the same second as its "cancel" → position break. Fix:
         `sysbrokers/IB/client/ib_orders_client.py` explicit `tif="DAY"` on
         market/limit/stop. Commit `9f6ce4a8`.
      2. Sentinel quotes → delayed feeds publish bid `0.0` for an empty book side;
         the validity gate only screened NaN, so limit orders went out priced 0.0
         (5× IB Error 201 "must contain field #44"). Fix:
         `sysbrokers/IB/ib_futures_contract_price_data.py`
         `quote_price_or_nan_if_sentinel` normalises quotes ≤0 to NaN at the
         ingestion boundary + nan-guard in
         `sysexecution/algos/common_functions.py`. 8 tests in
         `tests/test_execution_quote_validity.py`. Commit `7ce72fb0`.
      3. Upstream SR-cost SIGN ERROR — `sysquant/returns.py` double-negated an
         already-negative cost SR, so the weight-ESTIMATION layer ADDED costs to
         returns (rewarding expensive rules). Cherry-picked upstream PR #1650 as
         `b85befbb`; anchor re-verified bitwise; production unaffected (fixed
         weights). Tainted two prior null experiments → re-run, see below.
- [x] **Research battery queue COMPLETE 2026-07-18 — every slot NULL, baseline
      defended.** Slot 1: all 8 estimation variants re-certified null on corrected
      code (asterisk logged: point estimates moved positive but nothing cleared the
      pre-registered CI bar; chasing it needs a NEW pre-registration). Slot 2:
      breakout ensemble null (CI lo −0.001 — a 97% probability-of-beating that did
      not clear the bar, and the bar was not moved). Slot 3: vacuous (chapter-15
      already zero-weights the fast EWMACs). Slot 4: normalised momentum null —
      its cost-reduction claim did not replicate (drag +4.6%). Slot 5: seasonal
      carry null and significantly NEGATIVE. Slot 6: 36-cell vol/buffer sweep —
      defaults re-certified, sanity-anchor cell bitwise. Full menu + citations +
      merged does-not-work list: `docs/custom/plans/lit_review_upgrades_2026-07-18.md`.
      Harness now also records gross curves so cost drag is measurable.
- [x] **Ops scripts promoted from /tmp into the repo 2026-07-25** (commit
      `757836fc`) after a `/tmp` sweep wiped them and broke the scheduled passes:
      `scripts/data_utilities/eod_stack_cleanup.py`, `probe_market_data.py`
      (resolves contracts via the system's own priced-contract mapping — no
      hardcoded conIds, survives rolls), `approve_contract_spike.py`,
      `stack_reporting.py` (shared `print_stacks`; duplicate removed from
      `commission_stack_handler.py`).
- [x] **Risk controls live:** per-instrument position caps + 1-day trade caps in
      Mongo (`scripts/data_utilities/set_paper_limits.py`); every order is
      generated through them.
- [x] **Security audit 2026-07-16:** IBC `AcceptIncomingConnectionAction=reject`
      applied; Mongo localhost-only; secrets mode 600. Remaining = user sudo items
      (Next action 4).
- [x] **Visa research logged** (DECISIONS 2026-07-16): passive investing permitted
      for J-1; *Matter of Lett* (BIA 1980) and *Bhakta v. INS* (9th Cir. 1981)
      favorable. Barbell + paper GREEN; automated live engine AMBER → attorney
      check before go-live.
- [x] **IBKR portal 2026-07-16 (user):** futures permissions signed (US +
      Germany), NP questionnaire signed, CME/CBOT data purchased.
- [ ] **Barbell real-money deploy:** waits on the deposit (script proven on paper
      2026-07-10).

## Environment & how to run

- cwd / repo / branch: `/home/jungdaesuh/code/software/trading/pysystemtrade` /
  personal fork of pst-group/pysystemtrade (upstream moved from robcarver17) /
  `develop`. **HEAD `9e117a5b`**, everything committed and pushed; untracked
  `results/research_battery/*` dirs and `email.log` are transient.
- Python: `.venv/bin/python` for everything. Always
  `PYSYS_PRIVATE_CONFIG_DIR=$HOME/pysystemtrade-private` (also exported in
  `~/.bashrc` and `~/.zshrc`). Deps locked in `requirements-lock.txt`.
- Mongo: `docker start pysystemtrade-mongo` (restart policy unless-stopped; stays
  down after a manual stop).
- Gateway (headless IBC + Xvfb): `~/ibc/gatewaystart-headless.sh`; port 4002 opens
  in ~10-15s, API login ~40s; logs `~/ibc/logs/`. **It self-exits daily 23:45 ET**
  — expect it down every morning; the cycle script self-heals it.
- Scripts (all under `scripts/data_utilities/`): `daily_cycle_pilot.py` (data
  cycle; overlap-locked, broker-verified, exits 1 on stale) ·
  `commission_stack_handler.py --minutes N` (supervised execution pass) ·
  `phase6_bringup.py` (idempotent backtest + order generation) ·
  `eod_stack_cleanup.py` · `probe_market_data.py CODE...` ·
  `approve_contract_spike.py INSTRUMENT DATE...` · `set_paper_limits.py`.
- Research: `analysis/research_harness/run_battery.py --variants NAME --jobs N`
  (anchor: `--variants baseline` → 0.478 / 32.87 / 13,422 exactly);
  `compare_runs.py`; candidate rules quarantined in `battery_rules.py` until a
  verdict graduates them.
- Accounts: paper **DUR207416** (~$1.0M NLV; futures FESX Sep26 +4, FVS Oct26 −11;
  plus five ETF rehearsal positions SGOV 68 / VTI 2 / VEA 14 / GLDM 9 / VGIT 11).
  Live **U26413969**: unfunded, Cash type, futures permissions requested 07-16.
- Host quirk: **memory-tight when the user's fusion job runs** (07-24: 1.3Gi free,
  swap 93%, a 15.5Gi simsopt process). Long background sessions get reaped — hence
  `--minutes 3`. Never kill the user's processes.

## Decisions & rationale (recent; full journal in docs/custom/DECISIONS.md)

- **Gate 2 split** (2p process / 2s strategy) adopted as written 07-17; counting
  rules and clean-day criteria pre-registered BEFORE any day was judged.
- **Designed operator gates don't void days** (07-20 user ruling) — spike
  approvals and roll confirmations are normal operatorship, not manual repairs.
- **Session kills are environmental, not defects** (07-24) — do not void days for
  them; verify state and move on.
- Free gap-stitch over a vendor feed (funding <$10k); Gate 1 amended criteria;
  W-9 tax branch; Korean IRP on hold (PFIC); barbell policy unchanged.
- Full automation stays deferred until 3 clean supervised days.
- **Research posture:** the baseline survives everything tested. At N=6 with our
  costs, no signal / weighting / vol / tuning upgrade has cleared a pre-registered
  bar. More instruments beats better weights by roughly an order of magnitude.

## Dead ends / do NOT retry

- Blank `tif` on ANY IB order (10349 kills, and can race a fill).
- Flattening a position break broker-side only — the fill may already be booked;
  reconcile through the system's own position tables.
- Launching long stack sessions directly with `run_in_background` — they get
  reaped; run FOREGROUND with a timeout (and keep them short under memory load).
- Probing market data outside trading hours — everything reports NO LIVE DATA.
- Keeping operational scripts in `/tmp`/scratchpad — swept without warning.
- Closing a gate against weaker criteria than the adopted text; moving a
  pre-registered bar after seeing results.
- Config in `private_config.yaml` when the consumer reads
  `private_control_config.yaml`.
- Production price fetcher for expired contracts (1y-from-now window — use the
  expiry-anchored fetcher in `gap_stitch.py`).
- `pkill -f` without the bracket trick; dotted PYSYS paths; apt Mongo;
  `python -m venv` on uv interpreters; `DISPLAY=:0` Gateway launch.
- Research dead ends (evidence in the lit-review doc): acceleration rules,
  GARCH / implied-vol / regime vol for sizing, Moreira-Muir vol overlays,
  tail-hedge puts, COT data, fast mean reversion, calendar seasonality,
  cross-sectional anything at N=6, estimated weights at small N in any clothing.

## Open questions / blockers

- **CME/CBOT activation** (Next action 1) — likeliest hold: the unfunded live
  account. Blocks 4 of 6 instruments and therefore Gate 2p closure.
- **Funding amount and timing** — gates Gate 3, the barbell deploy, data billing,
  and the Gate 2s config.
- **Margin application** — user hasn't confirmed submitting it.
- **V2X target not yet reached:** optimal is ≈ −65; position −11. Fills grind
  ~1 lot per session on EUREX delayed data; it will close over many sessions.
- Alerting is deaf until an SMTP credential exists (user item) — treat "no alert"
  as no information, not as good news.

## Mental model

- **Two engines.** The barbell (real money, ETFs, human-triggered, green-lit
  including visa-wise) and the futures engine (paper, autonomous, leveraged —
  three gates + attorney check before real money). Required paper time scales with
  autonomy × leverage.
- **The stack pipeline:** instrument order → contract order (spawn) → broker
  orders (algo slices, sized from market depth) → fills propagate back up through
  parent-child links into the position tables. `commission_stack_handler.py` runs
  one supervised production pass; `run_stack_handler` is the eventual daemon.
  Stacks are cleared nightly, so each morning regenerates orders from fresh
  optimals — never assume yesterday's orders persist.
- **IB quirks bible:** blank tif → 10349; expired-contract history needs
  expiry-anchored fetching; dual-listed symbols (MXP legacy vs 6M); Gateway
  self-exits 23:45 ET; one API session per account; delayed data has NO depth on
  CME so the 'best' algo sizes zero (EUREX delayed works); subscriptions bill the
  LIVE account and share to paper; a "cancelled" order may still have filled.
- **Why live-fire matters:** two of the three real bugs were undiscoverable by
  backtest — they only exist in the broker interaction. That is what paper trading
  is buying.
- **The knowledge loop is the product:** DECISIONS.md (pre-registered, judged
  win-or-null), learnings/README.md (one checkable rule per problem), the battery
  results registry, and this handoff.

## Pointers

- Plans: `docs/custom/plans/portfolio_policy.md` ·
  `gate1_parity_definition.md` · `lit_review_upgrades_2026-07-18.md` ·
  `ib_paper_trading_implementation_plan.md` · `upgrade_surgical_map.md`
- Journal / learnings: `docs/custom/DECISIONS.md` ·
  `docs/custom/learnings/README.md`
- Logs: `~/ibc/logs/daily_cycle.log` · `~/ibc/logs/` (Gateway)
- Config (600, outside repo, never commit): `~/pysystemtrade-private/` ·
  `~/ibc/config.ini` · cron backup `~/ibc/crontab_backup_20260712.txt`
- Mistake book: `~/.claude/skills/crucible/shared/mistake-book.md`
