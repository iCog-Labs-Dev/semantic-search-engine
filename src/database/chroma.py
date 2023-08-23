import chromadb
from ..util.get_channels import *
from ..util.extract_channel_metadata import *
from ..embedding.generate_embeddings import *
from ..util.config import *
import math


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

step = 15

# Upsert channel's data to the vector db
def upsert_channels(channel_names=[]):
  if (channel_names == []):
    channel_names = channels['channel_name'].tolist()

  for idx, ch_name in enumerate(channel_names):
    print(f'Upserting channel { str(idx+1) } of { str(len(channel_names)) }: "{ch_name}" ... ')

    channel_metadata = extract_channel_metadata(slack_data_path, ch_name)

    if (channel_metadata.empty):
      print('-> The channel is empty / doesn\'t exist!')
      continue

    no_messages = len(channel_metadata)

    for start in range(0, no_messages, step):

      end = min(no_messages, start+step)
      channel_metadata_batch = channel_metadata[start:end]

      print(f'-> Embedding Batch { math.ceil(end/step) }/{ math.ceil(no_messages/step) } ...')
      # print(str(channel_metadata_batch['message']))

      channel_embeddings = embed_channel_messages(channel_metadata_batch['message'])

      upsert_channel_embeddings(channel_embeddings[start:end], channel_metadata_batch)

# upsert_channels() # upsert all channels


def get_data_from_chroma(query):
  # Generate embeddings for the query
  embedded_query = embed_query(query)

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
# get_data_from_chroma("What did Tollan say was good work?")
# get_data_from_chroma("What are some models that are comparable to GPT 3?")