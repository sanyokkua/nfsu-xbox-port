#!/bin/bash
# upstream/ = antoxa2584x/nfsu1-sw (main) at BASE + patches/*.patch (git am).
# The base is not ours and is not copied into this repo. mirror/nfsu1-sw.bundle (local) is the fallback.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
URL=https://github.com/antoxa2584x/nfsu1-sw.git
BASE=d597e08f
D="$ROOT/upstream"
[[ -e "$D" ]] && { echo "upstream/ exists; remove it to fetch again"; exit 1; }
if ! git clone -q "$URL" "$D" 2>/dev/null; then
  [[ -f "$ROOT/mirror/nfsu1-sw.bundle" ]] || { echo "fetch: clone failed and no mirror bundle"; exit 1; }
  git clone -q "$ROOT/mirror/nfsu1-sw.bundle" "$D"
fi
git -C "$D" checkout -q -B clean "$BASE"
shopt -s nullglob; P=("$ROOT"/patches/*.patch)
(( ${#P[@]} )) && git -C "$D" -c user.name=build -c user.email=build@localhost am -q "${P[@]}"
echo "upstream/ = nfsu1-sw $BASE + ${#P[@]} patches ($(git -C "$D" rev-parse --short HEAD))"
