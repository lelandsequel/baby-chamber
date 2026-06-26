# STRATA-mini (BabySTRATA)

Part of the [`baby-chamber`](../) monorepo. A tiny, deterministic **semantic decision layer**
for CodeComp-style bot decisions.

This is a *pattern extraction* of STRATA — **not** production STRATA, and it
contains none of its internals. It exists to show the shape clearly:

```
raw tick → canonical state → semantic facts → scoring → policy → gate → receipt → action
```

- **No LLMs at runtime.** Pure deterministic Python.
- **No secrets, tokens, cloud config, customer data, or internal infrastructure.**
- **Same input + same config ⇒ same facts, same mode, same action, same receipt hash.**
- The `strata_mini` package has **zero runtime dependencies** (stdlib only). Only
  the optional REST server (`app.py`) and the tests need extras.

## The flow (and the files)

| Stage | File | Job |
|---|---|---|
| canonicalize | `canonical.py` | defensive parse of any tick shape → `CanonicalState` / `Entity` |
| facts | `facts.py` | derive deterministic semantic facts (`AT_ASTEROID`, `ENERGY_CRITICAL`, …) from `CONFIG` |
| scoring | `scoring.py` | score asteroids / posts; deterministic exploration direction |
| policy | `policy.py` | the priority ladder → pick a **mode**, then an action |
| gate | `gate.py` | validate the candidate; **release or refuse-with-fallback** |
| receipts | `receipts.py` | auditable receipt + `sha256` hash (no timestamps in the hash) |
| bot | `bot.py` | `choose_action(raw)` wires it all together + prints the receipt |

## Strategy (v1 priority ladder)

1. destroyed → `RESPAWN`
2. recharging & energy < target → `WAIT`
3. recharging & energy ≥ target → `RECHARGE_END`
4. energy critical → `RECHARGE`
5. meaningful cargo & at a trading post → `SELL`
6. meaningful cargo & a post is visible → `MOVE` toward best post
7. on a nutrinium asteroid & cargo not near full → `MINE`
8. asteroid visible → `MOVE` toward best asteroid
9. otherwise → deterministic exploration `MOVE`

Combat is **placeholder-only** in v1 (`HOSTILE_NEARBY` fact; `ATTACK` is refused by the gate).

## Coordinate convention

`NORTH = +y`, `SOUTH = -y`, `EAST = +x`, `WEST = -x`. Direction order is always
`NORTH, EAST, SOUTH, WEST`. Exploration = `(tick + sha256(position)) % 4` — varied
but fully deterministic.

## Run the tests

```bash
cd strata_mini
pip install pytest && python3 -m pytest -q          # the normal path
```

No pytest? The tests are plain `assert` functions, so the stdlib runs them too:

```bash
PYTHONPATH=.:tests python3 -c "
import io, contextlib, test_bot_basic as T
for n in sorted(x for x in dir(T) if x.startswith('test_')):
    with contextlib.redirect_stdout(io.StringIO()): getattr(T, n)()
    print('PASS', n)"
```

Proven: same input → same output; destroyed → RESPAWN; low energy → RECHARGE/WAIT;
at asteroid → MINE; near-full cargo + post → MOVE (SELL_RUN); an invalid MINE is
refused with a fallback; receipt hash is stable.

## Run the local REST server

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8099
curl -s -X POST localhost:8099/action -H 'content-type: application/json' \
  -d @tests/fixtures/sample_tick_at_asteroid.json
```

## Placeholder schema — replace with the real CodeComp Action Request

The fixtures in `tests/fixtures/` use a **placeholder** tick schema (clearly
marked here). `canonicalize()` is deliberately defensive — it uses `.get()`-style
lookups, accepts alternative field names, and never crashes on missing optionals.

Assumed input shape (yours may differ — that's fine):

```json
{
  "tick": 3,
  "ship": {
    "id": "ship_1",
    "position": { "x": 5, "y": 5 },
    "energy": 90, "max_energy": 100,
    "cargo": { "nutrinium": 10, "capacity": 50 },
    "destroyed": false, "recharging": false, "health": 100
  },
  "visible": {
    "asteroids":      [{ "id": "ast_1", "position": {"x":5,"y":5}, "nutrinium": 40, "density": 1.2 }],
    "trading_posts":  [{ "id": "tp_1",  "position": {"x":0,"y":0} }],
    "ships": [], "wreckage": []
  }
}
```

**To plug in the real schema:** edit only `canonicalize()` in `canonical.py`
(map the official field names into `CanonicalState` / `Entity`) and adjust the
five fixture JSONs. Everything downstream — facts, scoring, policy, gate,
receipts — stays the same. Then map `final.to_response()` (in `gate.py`) onto the
official Action Response shape.

## Output

`choose_action()` returns the action response and prints a deterministic receipt:

```json
{ "action": "MINE", "payload": {}, "mode": "MINE_LOCAL", "reason": "mining local asteroid", "verdict": "RELEASED" }
```

The receipt records: tick, ship, position, sorted facts, mode, scores summary,
candidate vs final action, `RELEASED`/`REFUSED_WITH_FALLBACK`, and the
`deterministic_receipt_hash`.

— STRATA-mini · deterministic, receipted, refusal-first.
