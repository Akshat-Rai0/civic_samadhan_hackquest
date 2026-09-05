#!/usr/bin/env bash

# Resolve directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run start.sh inside grievance-app
exec "${SCRIPT_DIR}/grievance-app/start.sh" "$@"
