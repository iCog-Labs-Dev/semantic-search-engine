import json
import math
from semantic_search_engine.database.crud import CRUD
from semantic_search_engine.database.slack.extract_data import ExtractData

class Slack:
    """
    A class for managing and querying Slack data in a semantic search engine.

    This class provides methods for importing Slack data, embedding messages, and querying
    Slack data using embeddings.

    Attributes:
        collection (str): The name of the collection to store Slack data in.
        slack_data_path (str): The path to the directory containing Slack data export files.
        embedding: An instance of an embedding model for text data.
    """

    def __init__(self, collection, slack_data_path, embedding):
        """
        Initializes a new Slack instance.

        Args:
            collection (str): The name of the collection to store Slack data in.
            slack_data_path (str): The path to the directory containing Slack data export files.
            embedding: An instance of an embedding model for text data.
        """
        self.collection = collection
        self.embedding = embedding
        self.slack_data_path = slack_data_path
        self.crud = CRUD(
            collection=collection
        )
    

    # This will fetch the metadata from the slack archive (passing an empty array will fetch all channels' metadata)
    def upsert_channels(self, channel_names=[], step=15):
        """
        Upserts Slack channel data into the collection.

        This method fetches metadata from Slack channels and upserts it into the collection.
        If `channel_names` is empty, metadata for all channels is upserted.

        Args:
            channel_names (list, optional): A list of channel names to upsert metadata for.
                Default is an empty list, which upserts metadata for all channels.
            step (int, optional): The batch size for embedding and upserting metadata.
                Default is 15.

        Returns:
            str: A message indicating the upsert process's completion.
        """

        extract = ExtractData( slack_data_path=self.slack_data_path )

        channels = extract.get_all_channels()

        if (channel_names == []):
            channel_names = channels['channel_name'].tolist()

        for idx, ch_name in enumerate(channel_names):
            print(f'Upserting channel { str(idx+1) } of { str(len(channel_names)) }: "{ch_name}" ... ')

            channel_metadata = extract.extract_channel_metadata(ch_name)

            if (channel_metadata.empty):
                print('-> Err: The channel is either empty or it doesn\'t exist!')
                continue

            no_messages = len(channel_metadata)

            for start in range(0, no_messages, step):
                end = min(no_messages, start+step)

                print(f'-> Embedding Batch { math.ceil(end/step) }/{ math.ceil(no_messages/step) } ...')

                self.upsert_channel(channel_metadata[start:end])
        
        return 'Upsert Complete!'


    def upsert_channel(self, channel_metadata_batch):
        """
        Upserts a batch of channel metadata into the collection.

        Args:
            channel_metadata_batch (pandas.DataFrame): A DataFrame containing channel message metadata.

        Returns:
            None
        """
    
        channel_embeddings = self.embedding.embed_channel_messages(channel_metadata_batch['message'])

        parsed_channel_metadata = json.loads(channel_metadata_batch.to_json(orient="records")) # parse the channel metadata to json

        # create IDs for each embedding to be stored on the vector database
        ids = [ str(hash(metadata['message'])) for metadata in parsed_channel_metadata ]
        
        self.crud.upsert(ids=ids, embeddings=channel_embeddings, metadata=parsed_channel_metadata) # ###########################################################################################################################


        # upsert_channels() # upsert all channels

    def get_data_from_chroma(self, query, num_results, condition={}):
        """
        Retrieves Slack data using a semantic query.

        This method embeds the query, retrieves matching Slack data, and returns context and metadata.

        Args:
            query (str): The query string.
            num_results (int): The number of results to retrieve.
            condition (dict, optional): Additional query conditions. Default is an empty dictionary.

        Returns:
            tuple: A tuple containing the context (concatenated messages) and metadata of the retrieved data.
        """
        print('Embedding query ...', end=' ')
        embedded_query = self.embedding.embed_query(query)
        print('Done!')
        query_response = self.crud.retrieve(embedded_query, num_results, condition)
        # documents = query_response['documents']
        scores = query_response['distances'][0]
        metadatas = query_response['metadatas'][0]

        context = ''

        for idx, metadata in enumerate(query_response['metadatas'][0]):
            context += metadata['message'] + '\n'
            metadata['score'] = 1 - scores[idx]

        # return {'context': context, 'metadata': metadatas}
        return context, metadatas



    