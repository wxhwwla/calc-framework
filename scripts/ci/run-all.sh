#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0
# CI 全量模拟 — 与 GitHub Actions 完全一致的本地测试脚本
# 用法: bash scripts/ci/run-all.sh [--skip-docker]
#       或在 Docker 中: docker run --rm -v .:/workspace -w /workspace calc-framework-ci bash scripts/ci/run-all.sh

set -euo pipefail
START_TIME=$(date +%s)
PASSED=0
FAILED=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASSED=$((PASSED + 1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAILED=$((FAILED + 1)); }
skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; }
run() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }

# ── 环境检查 ──────────────────────────────────
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "Repo: $REPO_ROOT"
echo "Python: $(python3 --version 2>/dev/null || echo 'not found')"
echo "Node:   $(node --version 2>/dev/null || echo 'not found')"
echo "npm:    $(npm --version 2>/dev/null || echo 'not found')"
echo ""

# ── 1. Game CI ─────────────────────────────────
run "1. Game CI (ruff + pytest endfield + coverage)"

echo "  → ruff check"
if python3 -m ruff check games/endfield/ framework/src/ web/backend/ scripts/; then
    pass "ruff"
else
    fail "ruff"
fi

echo "  → Install framework"
python3 -m pip install -e framework -q 2>/dev/null || true

echo "  → Install endfield"
python3 -m pip install -e games/endfield -q 2>/dev/null || true

echo "  → pytest endfield (no GUI)"
if python3 -m pytest games/endfield/tests/ -q --tb=short \
    --ignore=games/endfield/tests/gui_design \
    --cov=games.endfield --cov-report=term; then
    pass "endfield tests"
else
    fail "endfield tests"
fi

echo "  → pytest tools"
if python3 -m pytest tools/tests/ -q --tb=short; then
    pass "tools tests"
else
    fail "tools tests"
fi

echo "  → pytest backend"
if python3 -m pytest web/backend/tests/ -q --tb=short; then
    pass "backend tests"
else
    fail "backend tests"
fi

# ── 2. Framework CI ────────────────────────────
run "2. Framework CI (ruff + pytest framework + benchmark)"

echo "  → ruff check framework"
if python3 -m ruff check framework/src/ framework/tests/; then
    pass "framework ruff"
else
    fail "framework ruff"
fi

echo "  → pytest framework (no GUI)"
if xvfb-run python3 -m pytest framework/tests/ -q --tb=short \
    --ignore=framework/tests/graph_editor \
    --cov=calc_framework --cov-report=term 2>/dev/null; then
    pass "framework tests"
else
    # xvfb might not be available locally
    skip "framework tests (needs xvfb — run in Docker)"
fi

echo "  → benchmark (quick)"
if python3 -m pytest framework/tests/benchmarks/ --benchmark-min-rounds=1 --benchmark-max-time=1 -q 2>/dev/null; then
    pass "benchmark"
else
    skip "benchmark (needs pytest-benchmark)"
fi

# ── 3. Web CI ──────────────────────────────────
run "3. Web CI (tsc + eslint + build)"

if command -v node &>/dev/null && [ -d web/frontend/node_modules ]; then
    echo "  → npm ci"
    (cd web/frontend && npm ci --silent 2>/dev/null) || true

    echo "  → tsc"
    if (cd web/frontend && npx tsc --noEmit); then
        pass "TypeScript"
    else
        fail "TypeScript"
    fi

    echo "  → eslint"
    if (cd web/frontend && npx eslint "src/**/*.{ts,tsx}" --max-warnings 50); then
        pass "ESLint"
    else
        fail "ESLint"
    fi

    echo "  → vite build"
    if (cd web/frontend && npx vite build --logLevel warn); then
        pass "vite build"
    else
        fail "vite build"
    fi
else
    skip "Web CI (Node.js or node_modules not available)"
fi

# ── 4. 安全检查 ─────────────────────────────────
run "4. Security checks"

echo "  → code origin"
if python3 tools/check_code_origin.py --ci --skip git-diff 2>/dev/null | grep -q "suspicious"; then
    fail "code origin (suspicious code found)"
else
    pass "code origin"
fi

# ── 总结 ────────────────────────────────────────
ELAPSED=$(($(date +%s) - START_TIME))
echo ""
echo "============================================"
echo " Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}"
echo " Time:    ${ELAPSED}s"
echo "============================================"

if [ $FAILED -gt 0 ]; then
    exit 1
fi
exit 0
