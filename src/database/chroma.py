import chromadb
from ..util.get_channels import *
from ..util.extract_channel_metadata import *
from ..embedding.generate_embeddings import *
from ..util.config import *


client = chromadb.PersistentClient(path="/content/chroma_db")


# Get a collection object from an existing collection, by name. If it doesn't exist, create one.
collection = client.get_or_create_collection(
      name= "slack_collection",
      metadata= {"hnsw:space": "cosine"},
      # embedding_function= instructor_embeddings       # The default embedding model is 'all-MiniLM-L6-V2'
    )

def upsert_channel_embeddings(channel_name, channel_embeddings, channel_metadata):

  # parse the channel metadata to json
  parsed_channel_metadata = json.loads(channel_metadata.to_json(orient="records"))

  # create IDs for the embeddings ... [channelname_0 -> ... -> channelname_..]
  ids = [ (channel_name + str(ch)) for ch in enumerate(channel_embeddings) ]

  # upsert the embeddings along with their metadata, into a Chroma collection
  collection.upsert(
    ids = ids,
    embeddings = channel_embeddings,
    metadatas = parsed_channel_metadata,
    # documents = channel_metadata['channel'].astype(str).tolist()
  )

  print(collection.peek()) # returns a list of the first 10 items in the collection
  print(collection.count()) # returns the number of items in the collection

# Upsert every channel's data into the vector db
def upsert_all_channels():
  channel_names = channels['channel_name'].tolist()
  for channel_name in channel_names:
    print('Upserting ' + channel_name + ' ... ')

    channel_metadata = extract_channel_metadata(slack_data_path, channel_name)

    if (not channel_metadata.empty):

      channel_embeddings = embed_channel_messages(channel_metadata['message'])

      upsert_channel_embeddings(channel_name, channel_embeddings, channel_metadata)

# Upsert just one channel's data
def upsert_one_channel(channel_name):
  print('Upserting ' + channel_name + ' ... ')

  channel_metadata = extract_channel_metadata(slack_data_path, channel_name)

  if (not channel_metadata.empty):

    channel_embeddings = embed_channel_messages(channel_metadata['message'])

    upsert_channel_embeddings(channel_name, channel_embeddings, channel_metadata)
upsert_all_channels()
# upsert_one_channel('random')  # general, random, gptgenerated



def get_data_from_chroma(query):
  # Generate embeddings for the query
  embedded_query = instructor_embeddings.embed_query(query)

  query_response = collection.query(
      query_embeddings = embedded_query,
      n_results = 5,
      # where = {"metadata_field": "is_equal_to_this"},
      where = {
          # "channel": {"$eq": "general"}
          # "user_id": {"$in": ["U05D1SQDNSH", "U05DHDPL4FK", "U05CQ93C3FZ", "U05D4M7RGQ3"]}
      }
      # where_document={"$contains":"search_string"}
  )

  # documents = query_response['documents']
  scores = query_response['distances'][0]
  metadatas = query_response['metadatas'][0]

  context = ''

  for idx, metadata in enumerate(query_response['metadatas'][0]):
    context += metadata['message'] + '\n'
    metadata['score'] = 1 - scores[idx]

  return {'context': context, 'metadata': metadatas}

# get_data_from_chroma("Why was it good work?")
get_data_from_chroma("What did Tollan say was good work?")
# get_data_from_chroma("What are some models that are comparable to GPT 3?")