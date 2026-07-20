#!/usr/bin/env bash
# Run the test suite with coverage. Config lives in pyproject.toml
# ([tool.coverage.*]) — source/omit list, etc.
#
# Usage:
#   ./scripts/run_coverage.sh              # full run, term + HTML report
#   ./scripts/run_coverage.sh -k webhook    # forward extra args to pytest
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

uv run pytest \
    --cov=whatsapp_assistant \
    --cov-report=term-missing \
    --cov-report=html \
    "$@"

echo
echo "HTML report: $(pwd)/htmlcov/index.html"
