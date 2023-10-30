import shelve
import os
from semantic_search_engine.constants import *
from semantic_search_engine.chroma import ChromaSingleton

collection = ChromaSingleton().get_chroma_collection()

def __set_default_shelve(shelve_name: str, default_value):
    with shelve.open( shelve_name ) as my_shelve:
        if not my_shelve.get( shelve_name, False ):
            my_shelve[ shelve_name ] = default_value

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

# Default total_posts
__set_default_shelve(
    shelve_name=TOTAL_POSTS_SHELVE,
    default_value=DEFAULT_TOTAL_POSTS
)

# Default personal_access_token_id
__set_default_shelve(
    shelve_name=MM_PAT_ID_SHELVE,
    default_value='' 
)