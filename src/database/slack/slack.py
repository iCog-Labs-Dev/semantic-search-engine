import json
import math
from src.database.crud import CRUD as chroma
from src.database.slack.extract_data import ExtractData as extract

class Slack:

    def __init__(self, collection, slack_data_path, embedding):
        self.collection = collection
        self.slack_data_path = slack_data_path,
        self.embedding = embedding
    

    # This will fetch the metadata from the slack archive (passing an empty array will fetch all channels' metadata)
    def upsert_channels(self, channel_names=[], step=15):

        channels = extract.get_all_channels()

        if (channel_names == []):
            channel_names = channels['channel_name'].tolist()

        for idx, ch_name in enumerate(channel_names):
            print(f'Upserting channel { str(idx+1) } of { str(len(channel_names)) }: "{ch_name}" ... ')

            channel_metadata = extract.extract_channel_metadata(self.slack_data_path, ch_name)

            if (channel_metadata.empty):
                print('-> The channel is empty / doesn\'t exist!')
                continue

            no_messages = len(channel_metadata)

            for start in range(0, no_messages, step):
                end = min(no_messages, start+step)

                print(f'-> Embedding Batch { math.ceil(end/step) }/{ math.ceil(no_messages/step) } ...')

                self.upsert_channel(channel_metadata[start:end])


    def upsert_channel(self, channel_metadata_batch):
    
            channel_embeddings = self.embedding.embed_channel_messages(channel_metadata_batch['message'])

            parsed_channel_metadata = json.loads(channel_metadata_batch.to_json(orient="records")) # parse the channel metadata to json

            # create IDs for each embedding to be stored on the vector database
            # ids = [ (channel_name + str(ch)) for ch in enumerate(embeddings) ] ... [channelname_0 -> ... -> channelname_n]
            ids = [ str(hash(metadata['message'])) for metadata in parsed_channel_metadata ]

            chroma.upsert(self.collection, ids, channel_embeddings, channel_metadata_batch) # ###########################################################################################################################


        # upsert_channels() # upsert all channels

    def get_data_from_chroma(self, query, num_results, condition={}):
        print('Embedding query ...', end=' ')
        embedded_query = self.embedding.embed_query(query)
        print('Done!')
        query_response = chroma.retrieve(self.collection, embedded_query, num_results, condition)
        # documents = query_response['documents']
        scores = query_response['distances'][0]
        metadatas = query_response['metadatas'][0]

        context = ''

        for idx, metadata in enumerate(query_response['metadatas'][0]):
            context += metadata['message'] + '\n'
            metadata['score'] = 1 - scores[idx]

        # return {'context': context, 'metadata': metadatas}
        return context, metadatas



    