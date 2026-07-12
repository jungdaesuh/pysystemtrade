# Learnings

One note per non-trivially solved problem: the dead ends, the working approach, why it
worked, and ONE reusable rule. A solved problem without a note here is unfinished work —
the rediscovery cost is the tax this directory eliminates.

Consumed by: quarterly reviews, annual policy review, and any future AI session
(see `.handoffs/pysystemtrade-trading-program.md`).

Seed entries (from the 2026-07 setup sessions):

- **pandas-version trap** — fork carried compat patches only because it ran on base-env
  pandas 3.x; upstream pins 2.1.3. Rule: never diagnose "bugs" before confirming the
  pinned environment (`.venv/bin/python`, never miniforge base).
- **uv-managed interpreters** — `python -m venv` fails on them (`/install` prefix error).
  Rule: `uv venv --python 3.11` for env creation in this repo, always.
- **MongoDB driver pin** — repo pins `pymongo==3.11.3` (tested to server 4.4); plain
  `brew install mongodb-community` installs 8.x. Rule: check driver pins before
  installing any server-side dependency; install `mongodb-community@6.0` or older here.
- **Fork drift** — 176 commits behind upstream included order-rejection parsing and FX
  inversion fixes that would have cost real money. Rule: custom work = ONE rebasable
  commit; sync upstream weekly; never trust numbers from an unsynced fork.
- **pysystemtrade percent curves** — additive percent-of-capital POINTS, not compounded
  returns; drawdowns can exceed 100. Rule: label such metrics `_pctpts` and never read
  them as compounded percentages.
- **No dots in PYSYS_PRIVATE_CONFIG_DIR** (found 2026-07-07) — private config resolution
  goes through `resolve_path_and_filename_for_package`, which converts dots to path
  separators: `~/.config/x` silently becomes `~/config/x`. Rule: dot-free directories
  only (we use `~/pysystemtrade-private`).
- **pymongo 3.11.3 ↔ MongoDB 6.0 gate PASSED** (2026-07-07) — server 6.0.28 in Docker,
  insert/find/list/drop verified; spread-cost seeding ran clean. Rule: Mongo 6.0 via
  `docker run mongo:6.0` is the blessed setup on modern Ubuntu (apt packages don't
  support 24.04+; Docker pins the version anyway).
- **Seeding scripts have HIDDEN prompts** — `repocsv_spread_costs.py` calls
  `true_if_answer_is_yes` from `syscore.interactive.input`, invisible to a grep for
  `input(` in the script file. Rule: grep the imported helpers too, or pipe `yes n`
  for bulk operations.
- **roll_parameters_csv_mongo.py is an empty stub** — upstream production now reads roll
  parameters directly from CSV (`production_data_objects.py:72`, `csvRollParametersData`).
  Rule: no Mongo seeding step for roll params; docs mentioning it are stale.
- **Shipped price data ends 2024-03-28** — the gap to the present must come from IB
  incremental updates (fine going forward) or a paid backfill; expired-contract history
  for the gap may need Barchart/Norgate. Known task, not a bug.
- **IB historical daily bars work WITHOUT market-data subscriptions** (probed 2026-07-08
  on paper: EURUSD and MES/CME both served daily bars, no CME subscription, unfunded
  account). Rule: the daily production cycle is unblocked pre-funding; the paid CME
  subscription is only required for real-time streaming at live execution time.
- **Contract sampling anchors on the multiple-prices current row** (2026-07-08):
  `get_furthest_out_contract_date` reads the LAST multiple-prices row, so a cold start
  from stale CSVs (ours end 2024-03) generates an already-expired chain → "No contracts
  marked for sampling" → price pull is a silent no-op. Also: sampling's final check
  crashes if the row's key contracts aren't in the contract DB — fixed by
  `scripts/data_utilities/bootstrap_key_contracts_from_multiple_prices.py`. Rule: after
  seeding stale data, Phase 5/6 REQUIRE the roll-forward stitch (multiple rolls across
  the gap, IB `includeExpired` fetches for gap contracts — most are within IB's ~2yr
  post-expiry window) OR a fresher commercial seed (Norgate/CSI/Barchart), which
  sidesteps the stitch entirely.
- **Headless IB Gateway = IBC + Xvfb, never the desktop** (2026-07-10) — GNOME's RDP
  desktop-sharing dies with "Failed to record monitor: Unknown monitor" whenever no
  physical display is active (sharing mode can only mirror real hardware), which makes
  any desktop-dependent Gateway launch fragile on a remote/monitor-less box. IBC
  (~/opt/ibc) + Xvfb + `~/ibc/gatewaystart-headless.sh` auto-logs-in with zero GUI.
  Bonus root-cause from the same session: a dual-boot machine is TWO tailscale nodes —
  clients paired to the Windows boot's identity can never reach the Linux boot. Rule:
  services must never depend on a physical display or a saved desktop session; give
  every GUI-dependent daemon its own virtual display and scripted login.
- **IB expired-futures history: anchor endDateTime at EXPIRY, not now** (2026-07-10) —
  IB serves expired contracts ~2y post-expiry, but a request anchored at `now` with
  duration 1y (what `sysbrokers` production code does) returns only bars inside
  [now-1y, now] — EMPTY for anything older. `endDateTime=expiry+1d, duration 2Y`
  returns the contract's real final two years. Alive contracts needing deep history
  want `3 Y` from now. Rule: when fetching historical bars for a dead contract,
  anchor the request at the END of its life.
- **Dual-listed products hide their history under the legacy symbol** (2026-07-10) —
  CME peso resolves under both `6M` (new, recent contracts only) and `MXP` (legacy,
  holds the expired history); pysystemtrade's config symbol may be the wrong one for
  old data, and a resolution that "works" can still be the data-poor listing. Rule:
  fetch under every candidate symbol and keep the longest series; never trust the
  first successful resolution. Bonus: IB peso data has a genuine product-wide hole
  2025-03-17..2025-05-19 (symbology migration) — no listing covers it.
- **IB Gateway exits itself daily at 23:45 ET** (2026-07-10) — the "Exit Session
  Setting" shuts the session down every night even in headless mode; IBC logs a clean
  exit and the API port drops. Rule: anything scheduled against the Gateway must
  ensure-and-relaunch first, never assume it is still up — `daily_cycle_pilot.py`
  self-heals (port probe → relaunch via `~/ibc/gatewaystart-headless.sh` → wait for
  4002), validated end-to-end with the Gateway genuinely down.
- **Gates are closed by their adopted text, not by a passing script** (2026-07-12,
  from a validated external audit) — the G1b checker tested a weaker criterion than
  the adopted document (portfolio calendar vs per-instrument 5-bd gaps) and printed
  PASS while MXP sat 44 business days in violation; separately, strategy process
  config was written to private_config.yaml when the scheduling code reads
  private_control_config.yaml — it "worked" only via a bypass script. Rule: before
  declaring any gate/config done, (1) re-read the adopted criterion and diff it
  against what the checker actually computes, and (2) verify config through the
  CONSUMING code path (call the reader, not just the writer).
