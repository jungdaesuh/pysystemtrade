# Research Notes — Order Flow Signals & LLMs in Investing

**Status:** Reference
**Last updated:** 2026-07-07
**Context:** Findings from literature verification, 2026-07-07 session. Backlog items only —
nothing here starts before the trading engine passes its September gates
(`docs/custom/plans/portfolio_policy.md`).

## Part 1 — Order flow (signed volume) signals

### What it is

Classify every trade by its aggressor side (the market order that crossed the spread):
buyer- vs seller-initiated. Net aggressive flow = **order flow imbalance (OFI)**. Core
empirical fact: OFI predicts short-horizon returns with roughly linear price impact.

Canonical literature: Cont–Kukanov–Stoikov (2014) "The Price Impact of Order Book
Events" (OFI); Lee–Ready (1991) trade classification; Easley–López de Prado–O'Hara
(VPIN, flow toxicity).

### The forced-vs-informed framework (the transferable idea)

Aggressive flow is either **informed** (impact persists) or **forced** (margin calls,
leveraged-ETF rebalancing, redemptions — impact REVERTS because it carries no view on
value). The systematic edge at every timescale is classifying which, and providing
liquidity against the forced kind.

Case study, market scale: KOSPI 2026-06-08 — record ₩37.7T margin debt → broker
liquidations + leveraged-ETF forced sales → −8.4% circuit-breaker day → +8.2% reversal
next session. Textbook forced-flow impact-and-reversion. The portfolio policy's
pre-committed forced-seller limit orders are the slow-clock version of a market maker's
passive bid.

### Where it fits this program

1. **Crypto perps** — the accessible venue: taker buy/sell volume + liquidation feeds
   free from every exchange API. If the niche-research track (Sharpe-2-via-breadth) ever
   starts, this is the first hunting ground. Institutional-grade data, zero cost.
2. **Daily system conditioner (weak)** — volume-confirmed trend and volume-spike
   capitulation markers as forecast modifiers; battery-testable; expect small effects.
3. **Do NOT** bolt intraday flow logic onto the daily CTA — different data, execution,
   and risk cadence. Concept transfers; implementation does not.

Futures caveat: proper aggressor-side data = CME MBO feeds (institutional pricing).
Daily volume bars retain only a shadow of the signal.

## Part 2 — LLMs in startup & equity investing (verified 2026-07-07)

### The claim "LLMs beat humans at startup picking" is substantially true

- LLM agents significantly outperformed human VC analysts across 61,814 early-stage
  ventures: [ScienceDirect 2025](https://www.sciencedirect.com/science/article/pii/S105752192500835X).
- Controlled live-venture tournament (no training-data leakage possible): frontier LLMs
  beat MBA/investor panels; adding humans to AI picks made results worse:
  [TechTimes, May 2026](https://www.techtimes.com/articles/317288/20260527/ai-predicts-startup-success-better-expert-panels-adding-humans-makes-it-worse.htm).
- Public-equity anchor: [Chicago Booth / arXiv 2407.17866](https://arxiv.org/abs/2407.17866)
  — GPT-4 on ANONYMIZED standardized financials predicted earnings direction ~60% vs
  analysts' low-50s; long-short on its predictions beat ML baselines on Sharpe/alpha.
  Anonymization defeats the memorization objection.

### The two asterisks

1. **Calibration**: [VCBench](https://arxiv.org/pdf/2509.14448) — LLMs consistently
   OVERPREDICT startup success. They rank well; their probability levels are inflated.
2. **Picking ≠ investing**: VC returns require deal access; and in public equities the
   consensus of the sober literature ([84-study review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12421730/),
   [HBR 2026 stock-picking competition](https://hbr.org/2026/03/competing-llms-were-asked-to-pick-stocks-their-choices-revealed-ais-limitations),
   [StockBench](https://arxiv.org/html/2510.02209v1)) is that LLMs are BAD at price
   prediction — direct forecasts never beat numerical quant models.

### Resolution: fundamentals-judgment ≠ price-prediction

The Booth result and the "bad at prediction" results coexist because they are different
tasks. LLMs win at judging business fundamentals from filings; they lose at forecasting
market prices. Conclusion: **the LLM is the analyst, never the portfolio manager.**

### If a value-investing track ever starts (backlog, post-September)

Edge locations, in order:
1. **Neglected text-rich corners** — small caps below analyst coverage, spinoffs,
   foreign filings. Sharpest specific: **Korean small caps** (thin coverage, live
   governance/value-up revaluation theme, Korean-language filings, user reads Korean).
2. **Forensics at scale** — quarter-over-quarter risk-factor diffs, footnote changes,
   accrual red flags, call-vs-filing inconsistencies. "Organize, don't predict."
3. **Temperament** — identical checklist on company #1 and #500.

Mandatory guardrails (from the studies' failure modes):
- Every cited number extracted by tools, never recalled (hallucinated financials).
- Every judgment = pre-registered dated prediction, scored later in
  `docs/custom/DECISIONS.md` machinery (VCBench overconfidence ⇒ calibration must be
  measured, not assumed).
- Position sizing by rules, never by model conviction.

Architecture sketch: local model (RTX 5090, vLLM) for bulk filing ingestion/extraction →
API-grade model for Booth-style fundamental judgment on structured output → quantitative
value/quality screen → journal-scored decisions.
