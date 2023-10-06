from semantic_search_engine.slack.models import *
import json
from datetime import datetime
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH


temp_slack_path: str = TEMP_SLACK_DATA_PATH

def save_users_data():
    """reads users' relevant info from users.json and save it to Sqlite db
    """
    # Create a User table if it doesn't exist
    User.create_table()
    
    with open(temp_slack_path + 'users.json') as json_file:
        users_json = json.load(json_file) 
    users = []
    for user in users_json:
        user_instance = User(
            user_id=user['id'],
            name=user['name'],
            real_name=user['profile']['real_name'],
            email=user['profile']['email'],
            is_bot=user['is_bot'],
            avatar=user['profile']['image_192']
        )
        users.append(user_instance)

    # TODO: should update the users if they already exist
    User.bulk_create(users)

def save_channels_data(public: bool = True):
    """reads users' relevant info from users.json and save it to Sqlite db
    """
    # Create a User table if it doesn't exist
    Channel.create_table()
    file_name = 'channels.json' if public else 'groups.json'
    
    with open(file=temp_slack_path + file_name) as json_file:
        channels_json = json.load(json_file) 

    channels = []
    for channel in channels_json:
        channel_instance = Channel(
            channel_id=channel['id'],
            name=channel['name'],
            access='pub' if public else 'pri',
            purpose=channel['purpose']['value']
        )
        channels.append(channel_instance)

    # TODO: should update the channels if they already exist
    Channel.bulk_create(channels)


def save_channel_messages(channel_id: str, collection):
    """ Reads messages from a single channel file and saves the relevant info to Sqlite and Chroma.

    Parameters
    ----------
    channel_id : str
        the channel id of the channel where the messages belong
    Returns
    -------
    [str]
        extracted list of message ids from a single channel file
    """
    # Create a Message table if it doesn't exist
    Message.create_table()
    
    # Get Channel details from channel_id
    channel = Channel.select().where(Channel.channel_id==channel_id)
    channel_folder = temp_slack_path + channel[0].name
    access = channel[0].access

    # Get all files in the channel's folder (each file correspond to daily messages)
    all_files = os.listdir(channel_folder)
    for file_name in all_files:
        # Read the content of the file (all messages sent in that channel in one day)
        with open(file=channel_folder + '/' + file_name) as json_file:
            messages_json = json.load(json_file)

        messages = []
        ids = []
        documents = []
        metadatas = []

        for message in messages_json:
            # subtype == channel_join is a system message that tells a users has joined a channel, not really necessary
            # Check if 'client_msg_id' and 'text' exists/aren't empty in the json file, or else return False
            if not (message.get("client_msg_id", False) and message.get("text", False)): 
                continue

            date_time = datetime.utcfromtimestamp( float(message['ts']) )

            message_instance = Message(
                message_id=message['client_msg_id'],
                user_id=message['user'],
                channel_id=channel_id,
                text=message['text'],
                time=date_time
            )
            messages.append(message_instance)

            ids.append(message['client_msg_id'])
            # TODO: each message should be embedded with the name of the user and the date / time
            documents.append(f"({date_time.date()}) { message['user_profile']['real_name'] }: { message['text'] }")
            metadatas.append({
                "user_id" : message['user'],
                "channel_id" : channel_id,
                "access" : access,
                "source" : 'sl',
            })

        print(f'Saving channel "{ channel[0].name }" ...', end=' ')
        # TODO: should update the messages if they already exist
        if messages:
            # Use insert_many with replace=True to insert new messages and update existing ones
            # with db.atomic():
            #     Message.insert_many(messages).on_conflict_replace().execute()
            Message.bulk_create(messages)

            # Upsert messages to chroma
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print('Done!')
        else: print('The channel is empty!')

