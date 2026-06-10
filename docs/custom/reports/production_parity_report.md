# Production Parity Report (2024 vs 2025)

Generated: 2025-09-22

## Run Parameters
- Entry point: `production_classic_futures_system`
- Config base: `systems/provided/futures_chapter15/futuresconfig.yaml`
- Base currency: GBP
- Notional capital: £1,000,000
- Capital multiplier: `syscore.capital.full_compounding`
- Costs: spread, roll and slippage enabled with `vol_normalise_currency_costs=True`
- Data source: CSV bundle under `data/futures/adjusted_prices_csv/` (no `_CLEAN` proxies)

## Output Artefacts
- 2024 daily returns: `results/2024/production_parity_2024_percent.csv`
- 2024 daily value terms: `results/2024/production_parity_2024_value_terms.csv`
- 2025 daily returns: `results/2025/production_parity_2025_percent.csv`
- 2025 daily value terms: `results/2025/production_parity_2025_value_terms.csv`
- Metrics snapshots: `results/2024/production_parity_2024_metrics.json`, `results/2025/production_parity_2025_metrics.json`

## Performance Summary
| Year | Window | Realised Vol (ann.) | Annualised Return | Total Return | Sharpe | Worst DD | Turnover |
|------|--------|--------------------|-------------------|--------------|--------|----------|----------|
| 2024 | 2024-01-01 → 2024-12-31 | 12.48% | 21.58% | 23.72% | 1.73 | -5.30% | 18.79 |
| 2025 | 2025-01-01 → 2025-08-19 | 170.90% | -116.86% | -85.66% | -0.68 | -86.78% | 0.00 |

## Observations
- 2024 export matches the CSV stack expectations: business-day index, percentage returns (percentage points), and non-zero turnover.
- 2025 data currently stops on 19 August 2025 and shows extreme swings because buffered positions appear to zero-out while P&L remains noisy. We need to reconcile this with Rob Carver’s published parity numbers once the reference figures and date window are confirmed.
- Blog comparison columns are intentionally omitted for now; add them in a follow-up revision together with commentary on any discrepancies once the source metrics are collected.

## Next Actions
1. Pull Rob Carver’s blog figures for the same windows and append "Blog" and "Delta" columns to the table.
2. Investigate the 2025 turnover collapse and confirm instrument coverage matches the production report.
3. Wire these parity exports into a regression harness so future runs flag divergences automatically.
