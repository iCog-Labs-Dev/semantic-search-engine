#!/bin/bash

export PYTHONPATH="$PYTHONPATH:./src"

script_path="src/semantic_search_engine/db.py"

if [ $# -eq 0 ]; then
    python $script_path --help
else
    python $script_path "$@"
fi