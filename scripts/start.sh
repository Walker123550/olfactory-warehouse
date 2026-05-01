#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PYTHONPATH="${PWD}/src"

echo "Starting olfactory warehouse at http://127.0.0.1:8765"
python3 -m olfactory_warehouse
