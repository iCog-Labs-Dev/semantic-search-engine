import shelve
import os
from semantic_search_engine.constants import *

def __set_default_shelve(shelve_name: str, default_value):
    with shelve.open( shelve_name ) as fetch_interval:
        if not fetch_interval.get( shelve_name, False ):
            fetch_interval[ shelve_name ] = default_value

# Create the shelve directory if it doesn't exist
os.makedirs(SHELVE_PATH, exist_ok=True)

# Set default values for the following shelves if they don't exist

# Default fetch_interval
__set_default_shelve(
    shelve_name=FETCH_INTERVAL_SHELVE,
    default_value=DEFAULT_FETCH_INTERVAL 
)

# Default last_fetch_time
__set_default_shelve(
    shelve_name=LAST_FETCH_TIME_SHELVE,
    default_value=DEFAULT_LAST_FETCH_TIME 
)

# Default fetch_interval
__set_default_shelve(
    shelve_name=CHROMA_N_RESULTS_SHELVE,
    default_value=DEFAULT_CHROMA_N_RESULTS 
)