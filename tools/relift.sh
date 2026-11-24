#!/bin/bash
# Relift the disc in game/extracted into engine/gen (full disasm -> recomp, after a seed or lifter change), check
# that no lifter stub is real code (tools/stubcheck.py), then rebuild build/release.   tools/relift.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
export PATH="$ROOT/.venv/bin:/opt/homebrew/bin:$PATH"
mkdir -p build
NFSU1_XBE="$ROOT/game/extracted/default.xbe" NFSU1_GEN_DIR="$ROOT/engine/gen" bash engine/tools/regen.sh \
  > build/regen.log 2>&1 || { tail -20 build/regen.log; exit 1; }
grep -E "Translating|unresolved" build/regen.log || true
python3 tools/stubcheck.py > build/stubcheck.log 2>&1 || { tail -12 build/stubcheck.log; exit 1; }   # a real-code stub is a silent bug
tail -1 build/stubcheck.log
cmake --build build/release > build/build.log 2>&1 || { grep -E "error" build/build.log | head; exit 1; }
echo "build OK"
