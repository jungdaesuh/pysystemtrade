# IBKR Paper Trading & Production Pipeline Implementation Plan

**Status:** Draft
**Last updated:** 2026-07-03

## Purpose

Execution roadmap for taking this fork from research-only to a running **paper-trading production pipeline** against Interactive Brokers. Companion documents: `TODO.md` (research/parity track — runs in parallel, no broker dependency) and upstream `docs/production.md` / `docs/IB.md` (reference material this plan indexes into). This plan covers broker plumbing only; strategy work stays in `TODO.md`.

## Goals

- Verified `ib_async` connectivity from this machine to IB Gateway (paper, port 4002).
- pysystemtrade broker layer connects via private config stored **outside the repo** (`PYSYS_PRIVATE_CONFIG_DIR`).
- MongoDB + Parquet production data layer stood up and seeded for a pilot instrument universe.
- Daily price update (`update_historical_prices`) runs end-to-end: IB → pysystemtrade → Parquet.
- IB-sourced prices reconciled against repo-shipped CSVs for the pilot universe.
- One full paper trading cycle completed: price update → system backtest → order generation → stack handler → reconcile report clean.
- Minimum capital report produced for the intended universe (input to funding decision).

## Non-Goals

- Live (real-money) trading, funding amounts, or order submission to a live account.
- Korean broker adapter work (revisit only if/when IBKR access ends — see Risks).
- Strategy enhancements (HRP comparison, estimation toggles, risk overlays) — tracked in `TODO.md` Phases 2–4.
- Dedicated Linux server / hardware build — macOS is acceptable for the paper phase.
- IBC-based full automation — manual Gateway management is acceptable for the paper phase.

## Current Context

Confirmed facts as of 2026-07-03:

- `develop` = upstream `pst-group/pysystemtrade` HEAD (`883c8681`) + one custom commit (`f5640a93`: HRP optimiser, parity toolkit). Pre-reset state preserved on `backup/pre-upstream-sync-2026-06-09` (contains `.env` — **never push**).
- Pinned environment exists: `.venv` (Python 3.11, pandas 2.1.3, numpy 1.26.4, `ib_async` 2.1.0). `tests/test_hrp.py` passes; chapter-15 system smoke-tested. Do **not** use the miniforge base env (pandas 3.x, incompatible).
- IBKR live account application completed (tax certification step resolved).
- Config defaults (`sysdata/config/defaults.yaml`): `ib_ipaddress: 127.0.0.1`, `ib_port: 4001` (live; paper = 4002), `ib_idoffset: 100`, `mongo_host: 127.0.0.1`, `parquet_store` is a placeholder that must be overridden.
- `PYSYS_PRIVATE_CONFIG_DIR` env var is supported (`sysdata/config/private_config.py:11`, `docs/production.md` "Custom private directory").
- Connection smoke-test pattern documented in `docs/IB.md` (`connectionIB(client_id, ib_ipaddress=..., ib_port=..., account=...)`).
- Seeding scripts available under `sysinit/futures/`: `roll_parameters_csv_mongo.py`, `repocsv_adjusted_prices.py`, `repocsv_multiple_prices.py`, `repocsv_spotfx_prices.py`, `repocsv_spread_costs.py`, `seed_price_data_from_IB.py`, `get_prices_and_contract_details_from_ib.py`.

## Rationale

Seed the data layer from repo CSVs first and use IB only for incremental updates: it avoids IB historical-data pacing limits, gives an immediate reconciliation baseline, and matches the upstream-documented path. Private config lives outside the repo so the `develop` branch stays a pure upstream-plus-one-commit tree with zero secret-leak surface.

## Assumptions

- Paper trading account will be enabled in Client Portal and receives a `DU…` account ID (live IDs are `U…`).
- Market data: live-account CME subscription + "share market data with paper account" flag will be active before Phase 5 acceptance is judged (Phases 1–4 work without it).
- IB Gateway (stable channel) runs on this macOS/arm64 machine.
- Broker access persists for the duration of the paper phase (J-1/US-residency dependency — see Risks).

## Implementation Plan

1. **IBKR account-side configuration** (Client Portal, no code)
   - [ ] Enable paper trading account; record the `DU…` account ID.
   - [ ] Enable "Share real-time market data with paper trading account".
   - [ ] Enable two-factor authentication via IB Key.
   - [ ] After funding lands: subscribe CME Real-Time (NP, L1) on the live account. (Data fees bill against account cash.)

2. **IB Gateway install + raw connectivity**
   - [ ] Download and install IB Gateway, **stable** channel (not TWS, not latest).
   - [ ] Gateway API settings: enable ActiveX/socket clients; socket port **4002**; trusted IP `127.0.0.1`; "Read-Only API" **off**; set auto-restart time to a quiet hour.
   - [ ] Write `scripts/ib/smoke_test_ib_connection.py`: bare `ib_async` connect to `127.0.0.1:4002` with `clientId=999`, print `accountSummary()`, disconnect.
   - [ ] Run it with `.venv/bin/python`; acceptance = the `DU…` account appears in the summary.

3. **pysystemtrade private config (outside the repo)**
   - [ ] Create `~/.config/pysystemtrade-private/` and export `PYSYS_PRIVATE_CONFIG_DIR` in the shell profile.
   - [ ] Write `private_config.yaml` there: `broker_account: DU…`, `ib_ipaddress: 127.0.0.1`, `ib_port: 4002`, `ib_idoffset: 100`, `mongo_host: 127.0.0.1`, `mongo_db: production_paper`, `parquet_store: /Users/suhjungdae/data/pysystemtrade/parquet`, `csv_backup_directory: /Users/suhjungdae/data/pysystemtrade/backups_csv`.
   - [ ] Verify pysystemtrade-level connection per `docs/IB.md`: `connectionIB(999)` picks up the private config values.

4. **Production data layer (Mongo + Parquet), seeded from repo CSVs**
   - [ ] `brew install mongodb-community` and run it as a service (`brew services start mongodb-community`); create the data directories from step 3.
   - [ ] Choose the pilot instrument universe (see Open Questions; default candidate: the chapter-15 six — CORN, EUROSTX, MXP, SOFR, US10, V2X — all liquid, cheap to trade).
   - [ ] Seed per `docs/production.md` "Get all the data in": `roll_parameters_csv_mongo.py`, then `repocsv_multiple_prices.py`, `repocsv_adjusted_prices.py`, `repocsv_spotfx_prices.py`, `repocsv_spread_costs.py` (all run with `.venv/bin/python`).
   - [ ] Sanity-check: read one instrument's adjusted prices back from Parquet via a `dataBlob` and compare row count vs the repo CSV.

5. **First end-to-end IB data pull + reconciliation**
   - [ ] Run `update_sampled_contracts` then `update_historical_prices` (from `sysproduction/`) for the pilot universe against the paper gateway.
   - [ ] Acceptance: new price rows land in Parquet with no pacing-violation errors in the log.
   - [ ] Reconcile: for each pilot instrument, compare the IB-updated series against the repo CSV over the overlap window; investigate any divergence > 0.1% (record findings in `docs/custom/reports/`).

6. **Paper production cycle (manual, one full day)**
   - [ ] Run the daily sequence by hand in order: price updates → `update_system_backtests` → `update_strategy_orders` → `run_stack_handler` (bounded run) → `update_multiple_adjusted_prices`.
   - [ ] Run `reconcile_report` and `roll_report`; acceptance = no unexplained breaks between system, database, and broker state.
   - [ ] Run the minimum-capital report for the pilot universe; save output to `results/` (input to the funding decision).
   - [ ] Only after one clean manual cycle: decide the scheduling mechanism (see Open Questions) and automate the sequence.

## Validation Plan

- [ ] `.venv/bin/python scripts/ib/smoke_test_ib_connection.py` → prints `DU…` account summary (Phase 2 gate).
- [ ] `mongosh --eval 'db.runCommand({ping: 1})'` → `ok: 1` (Phase 4 gate).
- [ ] `.venv/bin/python -m pytest tests/test_hrp.py -q` still green after any config changes (no repo code should change in this plan; a failure means scope leaked).
- [ ] Parquet store contains adjusted + multiple prices for every pilot instrument; spot check one series tail against IB TWS chart.
- [ ] Reconciliation diff report exists in `docs/custom/reports/` with all divergences explained.
- [ ] `reconcile_report` after the manual paper cycle shows positions/orders consistent across DB and broker.

## Risks and Mitigations

- Risk: IB historical-data pacing violations while backfilling.
  Mitigation: seed from repo CSVs (Phase 4); IB used only for incremental updates on ≤6 instruments.
- Risk: Paper account returns delayed/garbage prices because live data sharing or the CME subscription isn't active.
  Mitigation: Phase 1 checkboxes are hard prerequisites for judging Phase 5 acceptance; verify a known price against TWS before reconciling.
- Risk: macOS sleep/energy settings kill Gateway or Mongo mid-run.
  Mitigation: `caffeinate` during manual cycles; disable system sleep for the paper phase; dedicated hardware is deliberately deferred.
- Risk: Gateway weekly restart + 2FA interrupts unattended runs.
  Mitigation: acceptable during manual paper phase; adopt IBC only when automating (explicitly out of scope now).
- Risk: clientId collisions produce confusing connection failures.
  Mitigation: smoke tests use `clientId=999`; production processes allocate from Mongo via `ib_idoffset: 100`; never run both simultaneously.
- Risk: IBKR access is tied to US presence (J-1); a future return to Korea likely forces account closure.
  Mitigation: keep all custom code behind `sysbrokers/` abstractions; no IB-specific logic in the custom layer; revisit broker portability before any live-money decision.
- Risk: Upstream drift re-accumulates while this plan executes.
  Mitigation: weekly `git fetch upstream && git rebase upstream/develop` (custom layer is one commit by design).
- Risk: Secrets leak into the repo.
  Mitigation: private config lives in `PYSYS_PRIVATE_CONFIG_DIR` outside the tree; `.env` is in `.git/info/exclude`; `backup/pre-upstream-sync-2026-06-09` is never pushed.

## Completion Criteria

- [ ] One full manual paper trading cycle completed with a clean `reconcile_report` (no unexplained breaks).
- [ ] Reconciliation report for pilot-universe prices committed to `docs/custom/reports/`.
- [ ] Minimum-capital report output saved to `results/`.
- [ ] A "runbook" section appended to this file recording the exact commands used, so the cycle is reproducible by another agent.

## Open Questions

- Pilot universe: chapter-15 six vs. a micro-contract set (MES/MYM/MGC)? Decide after the minimum-capital report.
- Account base currency: `TODO.md` parity work uses GBP (matching Rob); the live/paper account will likely be USD. Decide before Phase 6 backtest config.
- Funding amount and timing for the live account (drives market data eligibility and eventual sizing) — user decision, outside this plan.
- Scheduling mechanism when automation starts: macOS `launchd` vs cron-in-Docker vs deferring automation until a Linux box exists.
- Whether the paper-phase Mongo DB (`production_paper`) should be kept permanently separate from an eventual live DB namespace, or wiped and re-seeded at go-live.
