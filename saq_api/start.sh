#!/bin/bash

# Save the current directory
CUR_DIR=$(pwd)

# Change to the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Run the commands
opam install --deps-only --yes .
dune exec --root . ./server.exe

# Return to the original directory
cd "$CUR_DIR"
