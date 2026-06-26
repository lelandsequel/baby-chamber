#!/usr/bin/env bash
# Farm-fence leak scan — no secrets, tokens, LLM refs, CAPITAL, LUMEN
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PATTERNS=(
  'sk-[a-zA-Z0-9]{20,}'
  'OPENAI_API_KEY'
  'ANTHROPIC_API_KEY'
  'CourtListener'
  'CAPITAL'
  'LUMEN'
  'chasify'
  'northpole'
  'gpt-4'
  'claude-'
)

FOUND=0
for pkg in strata_mini vellum_mini aurora_mini luna_mini gavel_mini cipher_mini vantage_mini cadmus_mini bifrost_mini cosmic_mini constellation_mini keystone_mini; do
  while IFS= read -r -d '' f; do
    for pat in "${PATTERNS[@]}"; do
      if grep -qiE "$pat" "$f" 2>/dev/null; then
        echo "LEAK? $f matches /$pat/"
        FOUND=1
      fi
    done
  done < <(find "$pkg" -type f \( -name '*.py' -o -name '*.json' -o -name '*.md' \) ! -path '*/.git/*' -print0)
done

if [[ $FOUND -eq 0 ]]; then
  echo "LEAK_SCAN: CLEAN"
  exit 0
fi
echo "LEAK_SCAN: ISSUES FOUND"
exit 1