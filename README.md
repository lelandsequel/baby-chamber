# baby-chamber

Pattern-extraction mini-versions of the chamber's engines — a family of tiny,
deterministic, dependency-light packages. Each demonstrates the chamber methodology
(**deterministic · receipted · refuse-or-verify**) in one domain.

**This is not production chamber software.** These are clean-room teaching artifacts
safe for open source (MIT) and Chasify (zero proprietary entanglement).

## Reference template

`strata_mini` (BabySTRATA) is the shape every baby mirrors. Originally public at
[`github.com/lelandsequel/strata-mini`](https://github.com/lelandsequel/strata-mini);
now lives in this monorepo.

## Babies

| Package | Role | Status |
|---------|------|--------|
| `strata_mini` | Deterministic semantic decision layer (template) | built |
| `vellum_mini` | Provenance envelope — no value without `{value, source, sha}` | built |
| `aurora_mini` | Verdict gate — `RELEASE` / `REFUSE` with reasons | built |
| `luna_mini` | Append-only hash-chain witness | built |
| `gavel_mini` | Citation verify-or-refuse (synthetic store) | built |
| `cipher_mini` | 5-line DCF refuse-or-verify valuation | built |
| `vantage_mini` | Deterministic code-smell flagger | built |
| `cadmus_mini` | Deterministic spec generator | built |
| `bifrost_mini` | Claim vs evidence verifier | built |
| `cosmic_mini` | Spine integration: produce → vellum → aurora → luna | built |
| `constellation_mini` | Drift distance from signed bedrock | built |
| `keystone_mini` | Upstream receipt integrity lock | built |
| `mirrorverse_mini` | — | **pending Captain** |

`mirrorverse_mini` is not built until Captain confirms its one-liner.

## Contract (every baby)

- Pipeline: `canonicalize → derive/check → score/decide → gate → receipt`
- Zero runtime deps in core (stdlib only)
- Deterministic: same input + config → same receipt hash (no random, no clock)
- `sha256` receipt (sorted keys, no timestamps)
- `REFUSED_WITH_FALLBACK` gate on invalid candidates
- Plain-`assert` tests, synthetic fixtures only

## Run all proofs

```bash
./scripts/run_all_proofs.sh
```

Per-baby:

```bash
cd vellum_mini && PYTHONPATH=. python3 tests/test_bot_basic.py
```

## Gate

Toph builds → Pan validates from artifacts (except `keystone_mini` — Toph self-gates) → Captain calls public/Chasify.

Nothing public before the gate fires.