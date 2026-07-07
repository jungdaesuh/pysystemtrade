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
