# September 2026 Roll Playbook — first rolls of the program

> Written 2026-08-21. SSOT for the September contract rolls. The first roll is a
> commissioning milestone: the machinery (`interactive_update_roll_status` +
> stack-handler roll orders + adjusted-price rolling) has NEVER been exercised.
> Execute the first one (MXP) supervised, with the user aware.

## The calendar (from IB expiries, checked 08-17)

| Instrument | Priced contract | Expires | Position | Roll decision due |
|---|---|---|---|---|
| MXP | 20260900 | 2026-09-14 | -2 | **week of 08-24 (NOW)** |
| EUROSTX | 20260900 | 2026-09-18 | +6 | week of 08-31 |
| US10 | 20260900 | 2026-09-21 | -2 | week of 08-31 (liquidity moves ~09-01) |
| V2X | 20261000 | 2026-10-21 | -83 | mid-September |
| CORN | 20261200 | 2026-12-14 | -20 | November |
| SOFR | 20290600 | 2029 | -6 | n/a |

Rule of thumb: roll when the forward contract's volume overtakes the priced
contract (typically 1-3 weeks before expiry; for US10, the quarterly roll is
concentrated ~3 weeks out).

## Roll states (sysobjects/production/roll_state.py)

- **No_Roll** — normal trading in the priced contract.
- **Passive** — closing trades execute in the priced contract, opening trades
  in the forward: position migrates naturally with the system's own orders.
  Slowest, cheapest, fine for small positions with time to spare.
- **Force** — roll ASAP using a calendar SPREAD order (one order, both legs).
  Preferred for prompt migration; spread book is usually liquid at roll time.
- **Force_Outright** — roll ASAP with two outright orders. Fallback if the
  spread book is dead (V2X may need this — check spread quotes first).
- **Roll_Adjusted** — position fully in the forward: roll the multiple/adjusted
  price panama-stitch and promote forward -> priced. Terminal step.

## The procedure (per instrument)

1. **Pre-checks (read-only):** forward contract sampled and priced (daily
   cycle samples it); forward volume >= priced volume at IB; stacks empty;
   zero position break; Gateway stable.
2. **Set state** via `interactive_update_roll_status` (interactive; run in a
   supervised session): No_Roll -> Force (MXP/US10: small positions, spread
   order trivially sized; EUROSTX likewise).
3. **Execute:** the stack handler's roll path spawns the roll order(s) in the
   next pass INSIDE the instrument's trading window (MXP/US10: 10:00-15:00
   EDT pass; EUROSTX: morning pass before 10:00). Watch fills, verify zero
   break after.
4. **Finalize:** when position is fully in the forward, set Roll_Adjusted in
   the same tool -> multiple/adjusted prices roll (panama stitch), forward
   becomes priced. Verify: `get_priced_contract_id` returns the new contract;
   adjusted price series continuous (no jump beyond the roll differential);
   G1b-style sanity on the stitched series tail.
5. **Record** in DECISIONS.md: state transitions, fills, differentials, any
   surprises. First roll = extra detail for the playbook's next revision.

## Schedule

- **Tue 08-25 or Wed 08-26:** MXP roll (Force), in the midday US-window pass.
  Smallest position (-2), most time-critical expiry, ideal first exercise.
- **Week of 08-31:** EUROSTX (+6, morning pass) and US10 (-2, midday pass).
- **Mid-September:** V2X (-83 — the big one; by then we'll have three
  rehearsals; check spread liquidity, consider Passive across several days
  or staged Force clips; decide with the user).

## Known risks

- Roll orders are a NEW code path (spread orders at IB, parent/child links,
  fill booking across two contracts). Treat the first like Day-1: small,
  watched, verified. Any defect found voids nothing (rolls are not Gate 2p
  day-criteria) but must be root-fixed before the next roll.
- The trading-hours frame fix (07-27) has never been tested against spread
  orders — verify the roll order respects the same windows.
- V2X spread liquidity is thin; do NOT assume Force works there because it
  worked on MXP/US10.
- If a roll stalls half-migrated, positions sit in two contracts — the
  reconcile check must compare BOTH; zero-break logic already does
  (contract-level), but eyeball it.
