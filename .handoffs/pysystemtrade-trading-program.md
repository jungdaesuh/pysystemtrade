# HANDOFF — Personal systematic trading program on pysystemtrade   ·   task-key: pysystemtrade-trading-program

> Updated 2026-07-06 23:20 EDT · Status: repo synced to upstream + validated; all plans/policy/tooling written, committed and pushed (HEAD `e2f7ef32` + doc-review fixes); next real-world step is IBKR paper-account activation and Phase 1 portfolio deployment.

## Goal

Build a production-grade personal systematic trading program on this pysystemtrade fork:
(a) portfolio per the barbell policy, (b) paper-trading pipeline against IBKR, (c) engine
live ~Sept 2026 if gates pass, (d) research factory on incoming Threadripper 9970X + RTX 5090.
**Done when:** engine trades live on micro futures with clean daily reconciliation, scaled per policy.

## Next actions  (start here)

1. [x] DONE 2026-07-07 (via browser automation): paper account created — account
       **DUR207416**, paper username **hftove227** (same password as live, Live/Paper toggle
       at Gateway login). Market-data sharing = Yes (shares `jungdaesuh`'s subscriptions).
       IB Key 2FA already active. Note: live and paper cannot hold sessions simultaneously.
2. [ ] **NEW — margin upgrade**: live account `U26413989` is a **Cash** account; futures
       (the engine) require margin. Portal → Settings → Account Type → upgrade before
       September go-live. Barbell ETFs work fine on Cash meanwhile.
3. [ ] Fund the live account, then deploy Phase 1 barbell per
       `docs/custom/plans/portfolio_policy.md` (55% SGOV / 35% four-asset sleeve / 10% reserve).
4. [x] DONE 2026-07-07 night: Gateway 10.45 installed at `~/ibgateway` (launch from app
       menu, NOT from a shell — window lands on wrong display otherwise). Both smoke tests
       PASSED: bare ib_async saw DUR207416 with $1M sim funds; `--pst` connected clean
       after Read-Only API unchecked (market-data + HMDS + sec-def farms all OK).
       Paper password was RESET via portal (own password now, not shared with live) —
       initial shared-password login failed, likely pre-sync. Note: paper web-portal
       sessions can collide with Gateway login (one session per account).
5. [x] DONE 2026-07-07: private config live at `~/pysystemtrade-private/` (NOT ~/.config —
       dots in path break pysystemtrade resolution, see learnings), DUR207416 configured,
       `PYSYS_PRIVATE_CONFIG_DIR` in ~/.bashrc.
6. [~] Phases 3–4 DONE (Mongo 6.0.28 in Docker `pysystemtrade-mongo`; 522 parquet files
       seeded + sanity-checked; spread costs in Mongo). Phase 5 ATTEMPTED 2026-07-08:
       sampling + price machinery run clean end-to-end, BUT price pull is a no-op —
       the contract chain anchors on the stale multiple-prices row (2024-03), so the
       generated chain is fully expired ("No contracts marked for sampling").
       **DECISION NEEDED — two ways to close the 2024-03→now gap:**
       (a) roll-forward stitch: bootstrap gap contract chain, IB fetches with
       includeExpired (most gap contracts within IB's ~2yr post-expiry window), then
       repeated roll-forwards of multiple prices per instrument — a careful session
       for the pilot six, zero cost; or (b) buy fresher seed data (Norgate/CSI/Barchart —
       importer exists at `sysinit/futures/barchart_futures_contract_prices.py`),
       ~$30-100/mo, sidesteps the stitch and buys the 100-instrument universe too.
       Helper written: `scripts/data_utilities/bootstrap_key_contracts_from_multiple_prices.py`.
7. [x] DONE 2026-07-07: bootstrap CIs shipped and run — HRP +0.076 vs baseline,
       95% CI [-0.078, +0.237] → confirmed insignificant (DECISIONS.md outcome closed).
8. [x] DONE 2026-07-08 (orchestrated build, crucible-PASSed): (a) har_vol_calc estimator
       (vol.py, +tests 7/7) — judge via `--vol-func har_vol_calc`; (b) battery walk-forward
       table (`--walkforward N`) with n_eff>=4 CI gate (no CI below ~4 independent windows —
       prevents falsely-narrow block-bootstrap CIs) + `--vol-func` axis; (c) parity runner
       audited clean, runs in 7.6s (Gate 1 gaps: target figures + tolerance undefined, stale
       results/2024-2025 parity JSONs need regeneration, universe question); (d)
       scripts/ib/deploy_phase1.py — barbell ticket machine, dry-run/whatIf validated on
       DUR207416; --live path exists but UNEXERCISED (needs one supervised paper run).
       NEXT research items: HAR vs mixed_vol campaign (bootstrap+walkforward), Gate 1
       target-figure definition, HRP-for-forecast-weights config experiment.

## State (with evidence)

- [x] Fork hard-reset onto upstream `pst-group/pysystemtrade` develop (`883c8681`) with custom
      layer re-applied as ONE commit `f5640a93` — verified: `git log --oneline -2`.
- [x] Pinned env `.venv` (uv, Python 3.11, pandas 2.1.3, numpy 1.26.4, ib_async 2.1.0) —
      verified: `tests/test_hrp.py` 3/3 pass; chapter-15 system smoke-run OK.
- [x] HRP optimiser registered — verified: `REGISTER_OF_OPTIMISERS` contains `hrp`
      (`sysquant/optimisation/optimisers/call_optimiser.py`).
- [x] Plan docs written: `/Users/suhjungdae/code/software/trading/pysystemtrade/docs/custom/plans/ib_paper_trading_implementation_plan.md`,
      `/Users/suhjungdae/code/software/trading/pysystemtrade/docs/custom/plans/portfolio_policy.md`.
- [x] Tooling written 2026-07-06: `scripts/ib/smoke_test_ib_connection.py`,
      `docs/custom/templates/private_config.yaml.example`,
      `analysis/research_harness/run_battery.py`.
- [x] `run_battery.py` baseline variant — verified end-to-end 2026-07-06: 13,422 days,
      full-period sharpe 0.478 / ann_std 32.9 pctpts (reference values, recorded in the
      script docstring; output at `results/research_battery/20260706_231411/metrics.csv`).
      Note: percent curves are additive pct-POINTS of capital (drawdowns can exceed 100).
- [ ] `run_battery.py` estimated variants (handcraft/shrinkage/hrp/equal) — **UNVERIFIED**:
      take minutes–hours each; first full run belongs on the Threadripper.
- [x] Artifacts committed & pushed: `1ca1062f` (policy, smoke test, battery, handoff)
      and `e2f7ef32` (paper plan) — verified: `git log --oneline -4`.
- [ ] IBKR paper account, IB Gateway install, Mongo/Parquet seeding — not started (need user actions).

## Environment & how to run

- cwd/repo/branch: `/Users/suhjungdae/code/software/trading/pysystemtrade` / jungdaesuh/pysystemtrade fork / `develop`
- Base commit: `f5640a93` (= upstream `883c8681` + custom layer)
- Remotes: `origin` = github.com/jungdaesuh/pysystemtrade, `upstream` = github.com/pst-group/pysystemtrade
- Env: `.venv/bin/python` for EVERYTHING (created via `uv venv --python 3.11 .venv`; recreate with
  `uv venv --clear …` then `uv pip install -e '.[dev]'`)
- Tests: `.venv/bin/python -m pytest tests/test_hrp.py -q`
- Quirks: miniforge base has pandas 3.x — incompatible, never use. `python -m venv` fails with
  the uv-managed 3.11. A pre-tool hook blocks `rm -rf`.

## Decisions & rationale

- **Hard reset over merge/rebase** for the upstream sync — local delta was 5 mostly-additive
  commits; the only code overlaps were pandas-compat patches upstream had superseded. Do not relitigate.
- **Dropped fork's pandas-2.x patches** (`vol.py`, `positionsizing.py`) — they existed only because
  the fork ran on base-env pandas 3.x; pinned env makes them unnecessary.
- **Custom work = one rebasable commit** on top of upstream, synced weekly. Never let develop drift again.
- **Paper-first, gated go-live (~Sept 2026)** — commissioning, not caution; EV math in conversation:
  6-week paper phase costs ~$1.2k expected forgone vs near-certain multi-$k first production bug.
- **Barbell policy** (see portfolio_policy.md): five rules, pre-registered kill criteria,
  engine scales +5pp/clean quarter, cap 35%.
- **Research machine ≠ production machine.** Threadripper is the factory; production stays on
  boring separate hardware/VM.
- **Broker-portable code only** — user is J-1; IBKR doesn't serve Korea residents, so access is
  tied to US presence. Nothing IB-specific outside `sysbrokers/`.

## Dead ends / do NOT retry

- Installing deps into miniforge base (downgrades global pandas; broke things originally).
- `python3.11 -m venv` with the uv-managed interpreter (`/install` prefix error). Use `uv venv`.
- Pushing branch `backup/pre-upstream-sync-2026-06-09` — it contains `.env` in its commit. Local only.
- Seeding price history from IB directly (pacing violations) — seed from repo CSVs, IB for increments.
- Plain `brew install mongodb-community` (installs 8.x) — repo pins `pymongo==3.11.3`
  (tested only to server 4.4). Use `mongodb-community@6.0` or older; see plan doc Phase 4.

## Open questions / blockers

- **Tax branch unresolved**: user is J-1 with SSN; W-9 (resident alien) vs W-8BEN (NRA) was decided
  during IBKR signup but which branch was never stated. Ask before tax-sensitive moves (XSP condors / Section 1256).
- Pilot universe (chapter-15 six vs micros) — decide after minimum-capital report.
- Account base currency (parity work uses GBP to match Rob; account likely USD).
- Funding amount — user decision; drives market-data eligibility and engine sizing.

## Mental model

- pysystemtrade moved orgs (robcarver17 → pst-group, Jan 2026) and to `ib_async` (April 2026);
  Andy Geach is primary maintainer. Upstream is actively maintained; sync before trusting numbers.
- The system: ~40 rule variations (trend/carry/MR/skew families) → capped forecasts → vol-targeted
  positions → buffered orders. Config keys are string-resolved from YAML — don't rename referenced functions.
- User's stated 2026 view: high-vol, range-bound → agreed tilt toward carry/MR over trend in the
  engine, pending walk-forward evidence from `run_battery.py`.
- Market context is PERISHABLE: all July-2026 analyses in conversation (KOSPI margin unwind, Warsh
  hawkish dots, Iran ceasefire, VIX ~16.6, BTC ~$60k) must be re-verified before use.

## Pointers

- Plans: `docs/custom/plans/ib_paper_trading_implementation_plan.md` · `docs/custom/plans/portfolio_policy.md` · `docs/custom/plans/upgrade_surgical_map.md` · `TODO.md`
- Research notes: `docs/custom/research/order_flow_and_llm_investing.md` (backlog: crypto order-flow niche, LLM value-investing analyst layer)
- Knowledge loop: `docs/custom/DECISIONS.md` · `docs/custom/learnings/`
- Session memory (assistant-side): `~/.claude/projects/-Users-suhjungdae-code-software-trading-pysystemtrade/memory/`
- Continuity: Claude Code works pay-as-you-go with an API key from console.anthropic.com — no subscription needed.
