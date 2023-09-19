# Export env variables
set -o allexport
source .env
set +o allexport

# include the python path
export PYTHONPATH="$PYTHONPATH:./src"

# run tests
python -m unittest -v