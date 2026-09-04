#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE=(-f "$ROOT/compose.yaml" -f "$ROOT/compose.osint.yaml")
OUT="$ROOT/data/system"
TMP="$OUT/collectors.tsv"
mkdir -p "$OUT"
: > "$TMP"

capture() {
  local name="$1" image="$2"; shift 2
  local output code version
  set +e
  output="$(docker compose "${COMPOSE[@]}" run --rm "$name" "$@" 2>&1)"
  code=$?
  set -e
  version="$(printf '%s\n' "$output" | grep -Eo 'v?[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || true)"
  printf '%s\t%s\t%s\t%s\n' "$name" "$code" "$version" "$image" >> "$TMP"
}

capture bbot osint-bbot:arm64 --version
capture httpx projectdiscovery/httpx:latest -version
capture subfinder projectdiscovery/subfinder:latest -version
capture theharvester ghcr.io/laramies/theharvester:latest -h
capture maigret soxoj/maigret:latest --version
capture sherlock sherlock/sherlock:latest --version
capture holehe osint-holehe:arm64 --help

python3 - "$TMP" "$OUT/collectors.json" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
result = {}
for line in open(src, encoding='utf-8', errors='ignore'):
    name, code, version, image = line.rstrip('\n').split('\t', 3)
    result[name] = {
        'status': 'OK' if int(code) == 0 else 'ERROR',
        'version': version or None,
        'image': image,
    }
with open(dst, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(dst)
PY
rm -f "$TMP"
