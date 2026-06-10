# Hybrid Mini‑CTA + ML/Sentiment Equity Tilt — Production Plan

Owner: SJD  
Date: 2025‑10‑30  
Status: Production Plan v1

## Bottom Line

- Keep pysystemtrade, but run it as a small, conservative “mini‑CTA” sleeve and pair it with a simple ML+sentiment, long‑biased ETF tilt. Start tiny, prove edge, then scale.

## Scope

- Two sleeves: (A) futures “mini‑CTA” using pysystemtrade; (B) equity ETF “active buy‑and‑hold tilt” driven by ML forecasts and LLM sentiment.  
- Environments: dev → staging (paper) → prod (live). Strict separation of keys, DBs, and brokers.  
- Backtest locally (bundled futures CSVs), then stage, then small live capital with rollback.

## Repository Pointers (What Matters)

- Futures system entry: `systems/provided/futures_chapter15/basesystem.py`  
- Futures config: `systems/provided/futures_chapter15/futuresconfig.yaml`  
- Futures data: `data/futures/adjusted_prices_csv/`  
- Costs/accounting: `systems/accounts/` (e.g., `account_subsystem.py`)  
- Guides: `docs/backtesting.md`, `README.md`, `TODO.md`

## Environments & Dependencies

- Python 3.10+. Install: `python -m pip install -e '.[dev]'` or `python -m pip install -r requirements.txt`.  
- Equity tilt extras: `xgboost`, `lightgbm`, `pandas`, `pyarrow`, `yfinance` (or vendor). Add to requirements when wiring the tilt service.

## Capital Profiles

- Test: $1,000 (analytical backtest using SR‑costs and fractional positions).  
- Small live: ₩10M (70% equity tilt, 30% macro via micros/ETFs).  
- Target: ₩50M+ (use full futures where margin permits).

## Portfolio Design

### Sleeve A — Macro (Mini‑CTA)

- Universe: 8–12 highly liquid futures/micros spanning Rates, Equity Index, FX, Gold, Crude. If margin tight, swap to ETFs (IEF/TLT, SPY/QQQ, GLD, USO, UUP).  
- Rules: EWMAC trend, Carry, and one cross‑sectional relative momentum.  
- Parameters: vol target 8–10%, forecast cap 10, diversification multiplier ≈2.0.  
- Risk overlay tightened (see Config Tweaks).

### Sleeve B — Equity Tilt (Active Buy‑and‑Hold)

- Core long basket: SPY, QQQ, IWM, EFA, EEM, TLT, HYG, GLD.  
- Monthly tilts per ETF ±0–3% around benchmark weights.  
- ML: XGBoost/LightGBM on 4‑week excess returns with features: 12‑1 momentum, short/long vol, breadth, macro proxy (term spread/VIX), and sentiment.

### Sentiment (LLM)

- GPT‑5 primary + DeepSeek secondary on headlines/filings/transcripts.  
- Output: probability in [0,1] per ticker; z‑score standardized.  
- Use as features and as confidence scaler; strong disagreement halves tilt size.

## Configuration Tweaks (pysystemtrade)

- `forecast_cap: 10`  
- `percentage_vol_target: 10.0`  
- Restrict to EWMAC+Carry+RelMom rules; prune `trading_rules` and `forecast_weights`.  
- Risk overlay:  
  - `max_risk_fraction_normal_risk: 1.2`  
  - `max_risk_fraction_stdev_risk: 3.0`  
  - `max_risk_limit_sum_abs_risk: 3.0`  
  - `max_risk_leverage: 6.0–8.0`  
- Turn off estimator flags you won’t maintain; refresh forecast scalars quarterly.

Example override snippet:

```python
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system
from sysdata.config.configdata import Config

data = csvFuturesSimData()
cfg = Config('systems.provided.futures_chapter15.futuresconfig.yaml')
cfg.forecast_cap = 10
cfg.percentage_vol_target = 10.0
cfg.instrument_div_multiplier = 2.0
cfg.risk_overlay = {
  'max_risk_fraction_normal_risk': 1.2,
  'max_risk_fraction_stdev_risk': 3.0,
  'max_risk_limit_sum_abs_risk': 3.0,
  'max_risk_leverage': 6.0,
}
cfg.instrument_weights = {'SOFR':0.2,'US10':0.2,'EUROSTX':0.2,'GOLD_micro':0.2,'CRUDE_W':0.2}
sys = futures_system(data=data, config=cfg)
print(sys.accounts.portfolio().percent.sharpe())
```

## Production Architecture

- Environments: dev (local), staging (paper), prod (live); isolated secrets and DBs.  
- Services: Research/Backtest, Live Signal Engine, Sentiment Service, OMS/Execution, Risk Service, Dashboard/API.  
- Data: Object storage (Parquet) + Postgres (configs/results) + Redis cache; immutable, append‑only, versioned datasets.

## Operations (Production)

- Orchestration: Prefect flows with retries and SLAs; idempotent runs.  
- Packaging: Docker images with pinned deps; docker‑compose acceptable for single VM; health checks per service.  
- Secrets & RBAC: secrets manager; least‑privilege roles; per‑environment API keys.  
- Execution: IBKR Gateway primary; ETF‑only fallback venue for DR. OMS handles throttles, child‑orders, cancel/replace, and persistent order/exec ledger.  
- Monitoring: Prometheus/Grafana for metrics; Loki/ELK for logs; Sentry for traces/exceptions.

## Backtesting — Run Now

Smoke test:

```bash
python - <<'PY'
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system
from sysdata.config.configdata import Config
data = csvFuturesSimData(); cfg = Config('systems.provided.futures_chapter15.futuresconfig.yaml')
sys = futures_system(data=data, config=cfg)
print('INSTR:', sys.get_instrument_list()[:6]); print(sys.accounts.portfolio().head(3).to_string())
PY
```

$1k analysis run (fractional SR‑costs):

```bash
python - <<'PY'
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system
from sysdata.config.configdata import Config
data = csvFuturesSimData(); cfg = Config('systems.provided.futures_chapter15.futuresconfig.yaml')
cfg.notional_trading_capital = 1_000; cfg.percentage_vol_target = 10.0; cfg.use_SR_costs = True
cfg.instrument_weights = {'SOFR':0.25,'US10':0.25,'EUROSTX':0.25,'CORN':0.25}
sys = futures_system(data=data, config=cfg)
curve = sys.accounts.portfolio()
print('Ann vol:', curve.percent.ann_std()); print('Sharpe:', curve.percent.sharpe()); print('Worst DD:', curve.percent.worst_drawdown())
PY
```

## Equity Tilt — Production‑Grade Implementation

- Data: vendor‑grade EOD OHLCV with calendars and corporate actions; Parquet with dataset versioning and write‑audit logs.  
- Features: deterministic jobs (12‑1 momentum, 20/60d vol, breadth proxy, macro proxy, sentiment) with Great Expectations quality suite.  
- Sentiment service (FastAPI): GPT‑5 primary, DeepSeek secondary; `/score` batch endpoint, `/healthz`, `/metrics`; Redis cache (TTL+LRU), rate‑limits, cost budget guard; prompt/model versioning; nightly backfill.  
- Model: XGBoost/LightGBM + MLflow registry; monthly walk‑forward retrain; calibration (ECE); promotion gate IR>0.4, turnover<50%/yr, stability by sector.  
- Rebalance: monthly cut‑over; T‑cost penalty; ±3% per‑ETF tilt; asset‑class caps; persist decisions with model/data/sentiment hashes.

Directory layout:

```
systems/provided/equity_tilt/
  __init__.py
  data_loader.py         # read/write ETF OHLCV
  features.py            # factor & sentiment features
  model.py               # XGBoost/LightGBM train/infer, MLflow integration
  run_tilt.py            # monthly rebalance; writes target weights
  config.yaml            # ETF list, limits, penalties
services/sentiment/
  server.py              # FastAPI; GPT‑5 + DeepSeek (fallbacks, budget guard)
  cache.py               # Redis helpers
  requirements.txt
```

## Daily Runbook (Prod)

1) Pre‑open: update prices, compute features, refresh sentiment cache.  
2) Generate mini‑CTA signals and ETF tilts; persist pre‑trade snapshots.  
3) Pre‑trade checks: exposure/VAR, concentration, cash/margin; block+alert on failure.  
4) Apply overlays/kill‑switches; if guardrails trigger, auto‑reduce gross and require manual re‑arm.  
5) Route orders (IBKR); enforce throttles; capture slippage/rejects; reconcile positions vs broker.  
6) EOD: persist curves, risk, attribution; rotate logs/metrics; send daily report; open incidents for anomalies.

## Rollout Phases (₩50M example)

- Phase 1 (paper, 2–4 weeks): 100% paper for both sleeves.  
- Phase 2 (live small): ₩10M live — 70% equity tilt, 30% macro (micros/ETFs).  
- Phase 3 (scale): Double only after 3 positive months and max DD < 5%.

## Success Criteria (First 6 Months)

- Beat 60/40 by ≥1% annualised with vol ≤12% and max DD ≤10%.  
- Tilt hit ratio >52% and information ratio >0.4.  
- Execution slippage ≤10 bps per ETF trade; futures within expected ticks.

## Testing & CI/CD

- Tests: unit (≥80% coverage core libs), integration (data→signals→orders), E2E paper‑trade replay; property‑based tests for sizing/buffers; golden‑file regression for backtests.  
- Static checks: mypy, ruff/black, bandit, pip‑audit.  
- CI: PR pipeline must pass; CD: tag→staging→5 trading‑day parity→prod; rollback to last tag on breach.

## Observability & Alerts

- SLIs/SLOs: signal timeliness p95 < 5m post‑close; OMS error rate <0.1%; sentiment p95 latency <800ms, success >99%; data freshness by 07:00 local; inference completeness 100% tracked symbols.  
- Alerts: data freshness/pre‑trade failures, kill‑switch triggers, broker rejects above threshold, SLO breaches.

## Risk, Limits, and Compliance

- Pre/intra/post‑trade: gross/net, VAR, per‑asset caps, daily loss, and DD stops.  
- Audit: immutable logs (inputs, model/prompt versions, outputs).  
- Security/DR: encryption at rest/in‑flight; key rotation; nightly snapshots; RPO 24h, RTO 4h.

## Dashboard (Prod)

- Streamlit or Grafana: portfolio curve, rolling vol/DD, turnover, slippage, exposures, sentiment dispersion, model confidence; staging/prod toggle.

## Work Breakdown (Weeks 1–4)

Week 1: Data quality (GE), mini‑CTA config hardening, CI/observability baseline.  
Week 2: Sentiment service (caching, budget guard) + eval harness; model registry wired; first calibrated XGBoost.  
Week 3: OMS risk gates; E2E paper trading; SLO alerting.  
Week 4: Staging soak (5 trading days), parity report, prod cutover with rollback.

