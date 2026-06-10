# 2025 Pysystemtrade Plan

Status: Draft (v0.1)
Owner: SJD
Updated: 2025-09-22

Goal
- Achieve production-methodology parity with Rob Carver’s reports using full futures data, then iterate with controlled enhancements and rigorous validation.

Quick Start (for any AI agent)
- Python: 3.10+ recommended. Install deps: `pip install -e '.[dev]'` or `pip install -r requirements.txt`.
- Fast smoke test: `python - <<'PY'\nfrom sysdata.sim.csv_futures_sim_data import csvFuturesSimData\nfrom systems.provided.futures_chapter15.basesystem import futures_system\nfrom sysdata.config.configdata import Config\n\ndata = csvFuturesSimData()\nsystem = futures_system(data=data, config=Config('systems.provided.futures_chapter15.futuresconfig.yaml'))\nprint('INSTRUMENTS', system.get_instrument_list()[:6])\nprint('PANDL HEAD', system.accounts.portfolio().head(3).to_string())\nPY`
- Run 2025 prod test (current custom script): `python analysis/production/production_backtest_2025.py` → writes `production_backtest_2025_results.csv` in CWD.
- Inspect existing results: `results/2025/production_2025_clean_results.csv`, `results/2024/production_2024_clean_results.csv`.

Repo Snapshot (what matters)
- Data: futures CSVs under `data/futures/adjusted_prices_csv/`. Prefer long history `SP500.csv` / `*_SYNTH.csv`. Avoid `_CLEAN` for production parity.
- Config: `systems/provided/futures_chapter15/futuresconfig.yaml` (rules, weights, vol target, instruments).
- System wiring: `systems/provided/futures_chapter15/basesystem.py` (creates System DAG).
- Accounts/metrics: use `system.accounts.portfolio()` then `.percent`, `.ann_std()`, `.sharpe()`, `.worst_drawdown()`.
- Costs: spread/roll/slippage pipeline in `systems/accounts/pandl_calculators/` and `sysdata/csv/csv_spread_costs.py`.
- Production entry: `sysproduction/strategy_code/run_system_classic.py` (helper: `production_classic_futures_system`).

Conventions (do/don’t)
- Don’t rename functions referenced by YAML (e.g., `syscore.capital.fixed_capital`). They’re string-resolved.
- Prefer built-in metrics over manual `pct_change()`. Use `accountCurve` methods.
- Keep changes surgical; avoid broad refactors. Add behind config flags when enhancing.
- Keep BDay frequency for curves; avoid weekend stamps in exports.

Next 1–2 Actions
- [ ] Switch runs to production entrypoint with full futures, GBP base, full compounding, realistic costs.
- [ ] Export 2024 and 2025 parity results and generate a parity report (vol, Sharpe, DD) against blog figures.

Scope & Assumptions
- Use `systems/provided/futures_chapter15/basesystem.py` and `sysproduction/strategy_code/run_system_classic.py`.
- Full futures data from `data/futures/adjusted_prices_csv` (no `_CLEAN` proxies).
- Costs on (spread/slippage/roll) with vol-normalised currency costs.
- Metrics from `system.accounts.portfolio().percent` (built-ins for vol, Sharpe, DD).

Phase 0 — Environment & Data Readiness
- [ ] Verify FX config and headers (DATETIME present).
- [ ] Sanity-check adjusted futures files load; spot-check a few series (e.g., SP500, US10, GOLD, MXP).
- [ ] Confirm spread cost table reads (sysdata/csv/csv_spread_costs.py).

Phase 1 — Production Parity Baseline
- [ ] Build via `production_classic_futures_system` with:
  - [ ] `base_currency: GBP`
  - [ ] `capital_multiplier: syscore.capital.full_compounding`
  - [ ] Default futures universe from `futuresconfig.yaml` (no `_CLEAN`).
  - [ ] Costs on; `vol_normalise_currency_costs: True`.
- [ ] Export daily `percent` and `value_terms` to `results/2024/` and `results/2025/`.
- [ ] Keep BDay index; eliminate weekend stamps.

Phase 1.5 — Blog Alignment & Parity Report
- [ ] Align date windows to blog publish dates.
- [ ] Compute realized vol (`ann_std()`), Sharpe (`sharpe()`), worst DD, turnover.
- [ ] Parity report: explain any gaps (currency, costs, universe, rule sets).

Phase 2 — Portfolio Enhancements (Optional, behind flag)
- [ ] Add HRP allocator as optional optimiser; config toggle.
- [ ] Compare against fixed/IDM on walk-forward; record stability improvements.

Phase 3 — Forecast/Weight Estimation (Cautious)
- [ ] Enable estimated rule/instrument weights with shrinkage and WF.
- [ ] Keep fixed baseline for control; attribute differences.

Phase 4 — Risk/Execution Enhancements
- [ ] Add class caps and drawdown-aware scalar overlay (configurable).
- [ ] Execution R&D: adverse selection heuristics (kept out of baseline backtest; ensure cost model consistency).

Validation & Controls
- [ ] Walk-forward OOS evaluation (e.g., 1y rolling windows 2010–2025).
- [ ] Cost sensitivity ±25% spread; FX translation sanity.
- [ ] Report realized vs target vol; DM/weights effect on turnover and costs.

Deliverables
- [ ] Parity runner script (CLI) producing 2024/2025 outputs.
- [ ] Parity report (markdown) with metrics tables and commentary.
- [ ] Config toggles for GBP/compounding/allocator selection.
- [ ] HRP module and minimal tests.

Timeline (suggested)
- Week 1: Phase 0–1 parity + parity report.
- Week 2: HRP prototype + WF comparison.
- Week 3: Estimation toggles + WF; validation suite.
- Week 4: Risk overlays + finalize docs.

Risks & Mitigations
- Data/proxy mismatch → Use full futures only for parity; label any “clean” runs.
- Estimation overfit → Strict WF, shrinkage, maintain fixed baseline.
- Cost model drift → Lock spread table snapshot; run sensitivity.

Notes
- Keep enhancements behind config flags; never replace the baseline pipeline.

Appendix — How to run parity via production entry (template)
- Build system with overrides:
  - Use: `from sysproduction.strategy_code.run_system_classic import production_classic_futures_system`
  - `system = production_classic_futures_system(data, 'systems.provided.futures_chapter15.futuresconfig.yaml', base_currency='GBP', notional_trading_capital=1_000_000)`
  - To switch compounding: edit YAML or set `config.capital_multiplier = {'func': 'syscore.capital.full_compounding'}` after loading `Config` (be careful: string-resolved).
- Export metrics:
  - `curve = system.accounts.portfolio()`
  - Daily percent: `curve.percent.to_frame(name='daily_%')`
  - Realized vol: `curve.percent.ann_std()`; Sharpe: `curve.percent.sharpe()`; Worst DD: `curve.percent.worst_drawdown()`
- File outputs:
  - Write CSVs to `results/<year>/` with columns: `date, account_value, daily_return` or separate `percent` and `value_terms` files.

Common pitfalls (avoid)
- Passing volatility series as `Lfast`/`Lslow` to EWMAC (must be ints). Use standard EWMAC with vol from `rawdata.daily_returns_volatility` only when function signature expects it.
- Using `_CLEAN`/ETF proxies for production parity (carry/roll won’t match futures).
- Refactoring names/paths used by YAML (e.g., `syscore.capital.fixed_capital`).
- Calculating metrics via raw `pct_change()` on account values instead of `accountCurve` methods.
