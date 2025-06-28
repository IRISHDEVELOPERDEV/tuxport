#!/bin/bash
# Custom script to run TuxPort

DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/main.py" "$@"
