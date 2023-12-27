#!/bin/bash
# Shim to emit warning and call start-notebook.py
echo "WARNING: Use start-notebook.py instead"
source activate jupyter
exec /usr/local/bin/start-notebook.py "$@"
