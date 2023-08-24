import chromadb
from src.embedding.embedding import Embedding

class CRUD:
    def upsert(self, collection, ids=[], embeddings=[], metadata=[]):
        try:
            # upsert the embeddings along with their metadata, into a Chroma collection
            collection.upsert(
                ids = ids,
                embeddings = embeddings,
                metadatas = metadata,
                # documents = channel_metadata['channel'].astype(str).tolist()
            )
        except chromadb.errors.DuplicateIDError as duplicate_err:
            print(f'This one exists already: {duplicate_err}')

        # print(collection.peek()) # returns a list of the first 10 items in the collection
        print(f'Upsert complete! \n * Total items in collection: { collection.count() }') # returns the number of items in the collection


    def retrieve(collection, embedded_query, num_results=5, condition={}):
        query_response = collection.query(
            query_embeddings = embedded_query,
            n_results = num_results, # No. of similar results retrieved
            where = condition
            # where = {"metadata_field": "is_equal_to_this"},
            # where_document={"$contains":"search_string"}
        )

        return query_response


    # get_data_from_chroma("Why was it good work?")
    # get_data_from_chroma("What did Tollan say was good work?")
    # get_data_from_chroma("What are some models that are comparable to GPT 3?")