#!/bin/bash

# Thin wrapper so you can run: ./run-app.sh ...
# Delegates to the main runner in ./shell/run-app.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$SCRIPT_DIR/shell/run-app.sh" "$@"
