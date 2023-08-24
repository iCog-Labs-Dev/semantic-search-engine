import chromadb

class Chroma:

  def __init__(self, path_to_db):
    self.path = path_to_db  # "./chroma_db"

  # This will return an instance of an existing collection or create a new one if it doesn't exist
  def get_collection(self, collection_name):
    client = chromadb.PersistentClient(self.path)

    collection = client.get_or_create_collection(     # Get a collection object from an existing collection, by name. If it doesn't exist, create one.
      name= collection_name,
      metadata= {"hnsw:space": "cosine"},
      # embedding_function= instructor_embeddings     # The default embedding model is 'all-MiniLM-L6-V2'
    )
    return collection