from semantic_search_engine.db import db
from semantic_search_engine.chroma import ChromaSingleton
from semantic_search_engine.constants import CHROMA_COLLECTION


class CRUD():

    collection = ChromaSingleton()\
        .get_connection()\
        .get_or_create_collection(CHROMA_COLLECTION)
    
    def read(self):
        pass