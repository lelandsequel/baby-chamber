# VELLUM-mini

A tiny, deterministic **provenance envelope** layer — pattern extraction of VELLUM,
**not** production VELLUM, and it contains none of its internals.

No value is emitted without `{value, source, sha}`. Unsourced or sha-mismatched
fields are refused.

```
raw record → canonicalize → facts → scoring → policy → gate → receipt → envelope
```

- **No LLMs at runtime.** Pure deterministic Python (stdlib only in core).
- **Same input + same config ⇒ same facts, same outcome, same receipt hash.**
- Synthetic fixtures only. No secrets, tokens, or internal refs.

## Run tests

```bash
cd vellum_mini
PYTHONPATH=. python3 tests/test_bot_basic.py
```

## Plug a real schema

Edit `canonicalize()` in `canonical.py` to map your field names into `ValueField`.
Adjust fixtures. Downstream modules stay the same.

## Output

`envelope(raw)` returns the gated outcome and prints a deterministic receipt with
`deterministic_receipt_hash` (sha256, sorted keys, no timestamps).

— VELLUM-mini · deterministic, receipted, refusal-first.