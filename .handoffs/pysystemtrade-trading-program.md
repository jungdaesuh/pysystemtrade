# HANDOFF — Personal systematic trading program on pysystemtrade   ·   task-key: pysystemtrade-trading-program

> Updated 2026-07-09 21:15 EDT · Status: infrastructure COMPLETE; research queue CLEARED (HAR and forecast-weight campaigns both judged: no change — four straight null wins; Gate 1 definition DRAFTED awaiting user adoption); remaining work blocked on user's two IBKR applications + the data-gap decision; September go-live on schedule.

## Goal

Build a production-grade personal systematic trading program on this pysystemtrade fork:
(a) real-money barbell portfolio per policy, (b) paper-trading pipeline against IBKR,
(c) engine live ~Sept 2026 if three gates pass, (d) research factory on the Threadripper.
**Done when:** engine trades live on micro futures with clean daily reconciliation, scaled per policy.

## Next actions  (start here)

1. [ ] USER: **margin upgrade application** — live account `U26413989` is Cash; futures need
       margin. Client Portal → Settings → Account Type. Approval takes days; September depends on it.
2. [ ] USER: **ACH deposit** — Portal → Transfer & Pay. Then deploy Phase 1 barbell:
       `.venv/bin/python scripts/ib/deploy_phase1.py --capital <N>` (dry run first; table of
       SGOV 65/VTI 10/VEA 10/GLDM 8/VGIT 7 tickets with whatIf margin preview), then `--live`
       + typed YES during market hours. Record fills in `docs/custom/DECISIONS.md`.
3. [ ] USER DECISION: **close the 2024-03→now price-data gap** — (a) free roll-forward stitch
       (write `gap_stitch.py`: bootstrap gap contract chain, IB fetches with includeExpired,
       repeated multiple-price roll-forwards; pilot six only; window decays monthly) or
       (b) vendor subscription (Norgate/CSI/Barchart ~$30-100/mo; re-seed sidesteps the stitch
       AND unlocks the 100-instrument universe). Pre-registered rule: buy when funded capital
       ≥~$50k or credibly there within 12mo; else stitch free. Blocks plan Phases 5-6 either way.
4. [ ] One **supervised `--live` run of deploy_phase1.py against the PAPER account** (DUR207416,
       port 4002) — the live order path is implemented but UNEXERCISED; validate fills + the
       DECISIONS.md block render before the real-money day.
5. [ ] RESEARCH (unblocked, any session): (a) ~~HAR-vs-default campaign~~ DONE 2026-07-08:
       verdict NO CHANGE — HAR pointwise worse for all 5 variants (baseline −0.042, all CIs
       straddle zero, P(beats default) 0.13–0.40), vol-target overshoot 37.0 vs 32.9 pctpts;
       logged in DECISIONS.md; evidence `results/research_battery/20260708_194002_vol-har_vol_calc/`
       incl. `compare_vs_20260707_212812.csv`. New tool: `analysis/research_harness/compare_runs.py`
       (paired cross-run bootstrap+walkforward for ANY two archived runs).
       (b) Gate 1: DRAFT definition written 2026-07-09 —
       `docs/custom/plans/gate1_parity_definition.md` (G1a regression anchor / G1b
       data-transition bands / G1c sim↔production parity; universe = chapter-15 six by
       declaration). PENDING USER ADOPTION; G1c comparison script still to write.
       (c) ~~HRP-for-forecast-weights~~ DONE 2026-07-09: verdict NO CHANGE — fw_hrp −0.039,
       all fw CIs straddle zero, no fw variant wins ≥50% of walk-forward windows; two
       side-findings logged (estimated FDM cuts vol/drawdowns materially; 2020s collapse is
       instrument-axis-specific). Evidence `results/research_battery/20260709_210216/`;
       battery gained `fw_*` variants. (d) ~~stale parity JSONs~~ DONE 2026-07-09:
       `results/2024/` + `results/2025/` removed (pre-reset fork artifacts; git history keeps them).

## State (with evidence)

- [x] Fork = upstream pst-group/develop (`883c8681`) + custom commit stack, HEAD `e4cc7134`,
      pushed. Upstream drift checked 2026-07-08: zero new commits.
- [x] MACHINE MIGRATED: work now lives on the Threadripper (`jungdaesuh-playstation`,
      Ubuntu 26.04, 9970X 32c/64t, 128GB, RTX 5090 + driver 595/CUDA). Acceptance test
      passed: baseline battery reproduced reference values EXACTLY (sharpe 0.478, n=13,422).
- [x] IBKR: live account `U26413989` (Cash, USD, IBKR Pro, IB Key active); paper account
      **DUR207416** (username `hftove227`, own password after portal reset, $1M sim).
      Market-data sharing ON. Broker chain PROVEN: Gateway 10.45 (`~/ibgateway`) →
      ib_async → pysystemtrade connectionIB, read-only OFF, data farms OK.
      IB historical daily bars work WITHOUT paid subscriptions (probed: EURUSD + MES).
- [x] Data layer: Mongo 6.0.28 in Docker (`pysystemtrade-mongo`, restart-persistent,
      pymongo-3.11.3 gate PASSED); 522 parquet files seeded from repo CSVs (ends 2024-03-28),
      row-counts verified vs source; spread costs in Mongo; private config at
      `~/pysystemtrade-private/private_config.yaml` (DUR207416, port 4002).
- [x] Phase 5 attempted: machinery clean but price pull is a no-op — contract chain anchors
      on the stale multiple-prices row → fully-expired chain → nothing sampled. Blocker
      characterized to the function (`get_furthest_out_contract_date`); helper written:
      `scripts/data_utilities/bootstrap_key_contracts_from_multiple_prices.py`.
- [x] Research battery (`analysis/research_harness/run_battery.py`): variants
      (baseline/handcraft/shrinkage/hrp/equal), paired stationary block bootstrap CIs,
      `--walkforward N` regime table with n_eff≥4 CI gate, `--vol-func` estimator axis,
      curves archived per run. First campaign verdict LOGGED (DECISIONS.md): HRP +0.076
      vs baseline, 95% CI [-0.078,+0.237] → not significant; equal-weights most robust;
      all estimated variants collapse in the 2020s (open question).
- [x] `har_vol_calc` HAR estimator in `sysquant/estimators/vol.py` + `tests/test_har_vol.py`
      (7/7 with HRP tests) — strictly causal (bitwise-proven), drop-in via
      `volatility_calculation.func`, level 0.95× default. NOT wired into any live config.
- [x] HAR-vs-default campaign JUDGED 2026-07-08 (DECISIONS.md): HAR worse everywhere
      (mixed_vol_calc's 20-year slow anchor is the load-bearing part); verdict NO CHANGE.
      Cross-run comparator added: `analysis/research_harness/compare_runs.py` — paired
      bootstrap + walkforward between any two archived runs' curves.csv.
- [x] Forecast-weight campaign JUDGED 2026-07-09 (DECISIONS.md): battery gained `fw_*`
      variants (forecast-weight axis, instrument weights fixed); no fw variant beats
      fixed weights; anchor reproduced exactly through the code change. Fourth null win.
- [x] Gate 1 parity definition DRAFTED 2026-07-09 (`docs/custom/plans/
      gate1_parity_definition.md`) — awaiting user adoption; pre-reset `results/2024-2025`
      parity artifacts deleted (git history retains them).
- [x] `scripts/ib/deploy_phase1.py` — dry-run/whatIf validated against live paper gateway;
      **`--live` path UNEXERCISED** (next action 4).
- [x] Orchestrated build reviewed via crucible: 5 lenses, 6 scorers, auditor; verdict FAIL →
      2 major fixes applied (dead UNSET sentinel guard removed; walk-forward CI n_eff gate
      added) → re-audit PASS. Mistake book gained Patterns 117-118.
- [ ] Plan Phases 5-6 (first IB price pull, manual paper cycle, 10-day clean reconcile
      streak = Gate 2) — blocked on next-action 3.
- [ ] Gates: 1 (parity) needs target figures defined; 2 (paper streak) blocked on data gap;
      3 (minimum-capital report) one command, run after funding known.

## Environment & how to run

- cwd/repo/branch: `/home/jungdaesuh/code/software/trading/pysystemtrade` / jungdaesuh fork / `develop`
- Machine: `jungdaesuh-playstation` (Threadripper, Ubuntu 26.04). Git pushes via SSH (key registered).
- Base commit: `e4cc7134` (all work committed; only transient `results/research_battery/*`
  validation run dirs untracked — deliberate, selective-archival workflow).
- Env: `.venv/bin/python` for EVERYTHING (`uv venv --python 3.11 .venv && uv pip install -e '.[dev]'`;
  pandas 2.1.3 / numpy 1.26.4 / ib_async 2.1.0). `export PYSYS_PRIVATE_CONFIG_DIR="$HOME/pysystemtrade-private"`
  (also in ~/.bashrc).
- Mongo: `docker start pysystemtrade-mongo` if down; ping:
  `docker exec pysystemtrade-mongo mongosh --quiet --eval 'db.runCommand({ping:1})'`.
- Gateway: launch from the DESKTOP app menu ("IB Gateway 10.45"), NOT from a shell
  (window lands on the wrong display). Login `hftove227` + paper password + Paper toggle + IB Key.
- Tests: `.venv/bin/python -m pytest tests/test_har_vol.py tests/test_hrp.py -q` (7 expected).
- Regression anchor: `run_battery.py --variants baseline --jobs 1` must print sharpe 0.478 /
  n_days 13422 — any deviation is a regression, not a discovery.
- Quirks: miniforge base has pandas 3.x — never use. `python -m venv` fails on uv-managed
  interpreters. A pre-tool hook blocks `rm -rf`. `pkill -f <pattern>` matches your own shell's
  command line — use the bracket trick (`pgrep -f '[G]WClient'`).

## Decisions & rationale

- **Hard reset over merge/rebase** for the June upstream sync; fork's pandas patches dropped
  (they compensated for the wrong env). Do not relitigate.
- **Custom work stays a rebasable commit stack** on upstream; weekly `git fetch upstream && git rebase`.
- **Paper-first, three-gated go-live (~Sept 2026)** — commissioning, not caution.
- **Barbell policy** (portfolio_policy.md): five rules, pre-registered kill criteria; engine
  20%→35% of capital scaling +5pp/clean quarter.
- **Cost/breakeven rule**: full paid stack (~$1.5-2k/yr: data vendor, CME real-time, API,
  commissions) is justified at ≥~$50k working capital; below that run free config.
- **Research machine hosts the PAPER stack too** (pragmatic bend of research≠production;
  rule hardens again at live go-live — separate box/VM then).
- **Broker-portable code only** — user is J-1; IBKR access tied to US presence.
- **No .gitignore for battery results** — they're a deliberately-committed experiment registry;
  archive selectively.
- **Walk-forward CI gate**: below ~4 non-overlapping windows, NO CI is emitted (block bootstrap
  degenerates to mean-preserving rotations = falsely narrow). Auditor-ratified; don't "fix" it back.

## Dead ends / do NOT retry

- Installing deps into miniforge base; `python -m venv` on uv interpreters (use `uv venv`).
- Pushing `backup/pre-upstream-sync-2026-06-09` — contains `.env`. Local only, never push.
- Seeding deep history from IB directly (pacing) — repo CSVs for depth, IB for increments.
- apt/brew MongoDB on Ubuntu 26.04 (no packages) — Docker `mongo:6.0` is the blessed setup
  (pymongo 3.11.3 pin; server ≤6.0).
- Dotted directories in `PYSYS_PRIVATE_CONFIG_DIR` (`~/.config/...` silently becomes `~/config/...`).
- Launching IB Gateway via `DISPLAY=:0` from a shell — invisible window; use the app menu.
- Expecting `update_sampled_contracts` to work on stale seed data — chain anchors on the last
  multiple-prices row; requires the gap stitch or fresh data first.

## Open questions / blockers

- **Tax branch** (W-9 resident alien vs W-8BEN NRA) — never stated by user; gates XSP condors,
  IRP reallocation (PFIC/FBAR if W-9), and bond-fund selection. Ask before tax-sensitive moves.
- **Funding amount** — drives Gate 3, data decision, engine sizing. User decision.
- **Gate 1 definition** — DRAFT at `docs/custom/plans/gate1_parity_definition.md`
  (replaces figure-parity with G1a anchor / G1b bands / G1c sim↔production; declares
  the chapter-15 six as parity universe). Needs user adoption + a DECISIONS.md entry;
  then write the G1c comparison script.
- **IRP reallocation** (Korean 퇴직연금 at 3.9% guaranteed) — pending tax branch; plan is
  qualified TDF up to 100% or 70/30 index ETFs. Logged in DECISIONS.md.

## Mental model

- pysystemtrade: pst-group org, ib_async, actively maintained. Config keys string-resolved
  from YAML — never rename referenced functions. Percent curves are ADDITIVE pct-POINTS.
- Cold-start gap mechanics: production assumes continuous operation; multiple prices' last row
  is the anchor for contract chains, sampling, and rolls. Stale seed = dead pipeline until stitched.
- IBKR: one active session per account (web portal can bump Gateway); paper shares live
  password only after overnight sync (we reset to a separate one); historical daily bars are
  free, real-time needs the CME sub only at live execution.
- The knowledge loop is the product: DECISIONS.md (pre-registered, judged), learnings/
  (one rule per hard problem), battery results (experiment registry), this handoff. Reinvest
  conclusions; never re-litigate settled verdicts without new evidence.
- Market context in past conversation (KOSPI unwind, Warsh, ceasefire, BTC ~$60k) is PERISHABLE — re-verify before use.

## Pointers

- Plans: `docs/custom/plans/portfolio_policy.md` · `docs/custom/plans/ib_paper_trading_implementation_plan.md` · `docs/custom/plans/upgrade_surgical_map.md` · `TODO.md`
- Knowledge loop: `docs/custom/DECISIONS.md` · `docs/custom/learnings/README.md`
- Research notes: `docs/custom/research/order_flow_and_llm_investing.md`
- Crucible mistake book: `~/.claude/skills/crucible/shared/mistake-book.md` (Patterns 117-118 from this program)
- Assistant memory (per machine): `~/.claude/projects/-home-jungdaesuh-code-software-trading-pysystemtrade/memory/`
  (Mac twin exists under `-Users-suhjungdae-...`)
- Continuity: Claude Code runs pay-as-you-go with an API key (console.anthropic.com).
