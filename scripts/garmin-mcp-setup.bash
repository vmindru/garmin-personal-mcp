#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
venv_dir="$project_dir/.local/garmin/mcp-venv"
python3 -m venv --without-pip "$venv_dir"
# Debian's base Python has pip but may omit ensurepip/python3-venv.
python3 -m pip --python "$venv_dir/bin/python" install -r "$project_dir/scripts/garmin-mcp-requirements.txt"
printf '%s\n' 'Garmin MCP dependencies installed. See README.md to connect Claude Code.'
