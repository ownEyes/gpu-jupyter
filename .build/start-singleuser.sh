#!/bin/bash
# Shim to emit warning and call start-singleuser.py
echo "WARNING: Use start-singleuser.py instead"
# Activate the Conda environment
source activate jupyter
exec /usr/local/bin/start-singleuser.py "$@"
