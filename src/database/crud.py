import chromadb

class CRUD:

    def __init__(self, collection):
        self.collection = collection

    def upsert(self, ids=[], embeddings=[], metadata=[]):
        
        try:
            # upsert the embeddings along with their metadata, into a Chroma collection
            self.collection.upsert(
                ids = ids,
                embeddings = embeddings,
                metadatas = metadata,
                # documents = channel_metadata['channel'].astype(str).tolist()
            )
        except chromadb.errors.DuplicateIDError as duplicate_err:
            print(f'This one exists already: {duplicate_err}')
        except:
            print('Something went wrong!')

        # print(self.collection.peek()) # returns a list of the first 10 items in the collection
        print(f'Upsert complete! \n * Total items in collection: { self.collection.count() }') # returns the number of items in the collection


    def retrieve(self, embedded_query, num_results=5, condition={}):
        query_response = self.collection.query(
            query_embeddings = embedded_query,
            n_results = num_results, # No. of similar results retrieved
            where = condition
            # where = {"metadata_field": "is_equal_to_this"},
            # where_document={"$contains":"search_string"}
        )

        return query_response