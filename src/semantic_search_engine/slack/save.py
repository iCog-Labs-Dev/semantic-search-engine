import os, json
from datetime import datetime
from semantic_search_engine.slack.models import User, Channel, ChannelMember, Message
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH


def save_users_data() -> None:
    """reads users' relevant info from users.json and save it to Sqlite db
    """
    # Create a User table if it doesn't exist
    User.create_table()
    
    with open(os.path.join(TEMP_SLACK_DATA_PATH, 'users.json')) as json_file:
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

def save_channels_data(channel_ids: [str]) -> [dict]:
    """reads channels' relevant info from channels.json and save it to Sqlite db
    """
    # Create 'Channel' and 'ChannelMember' tables if they don't exist
    Channel.create_table()
    ChannelMember.create_table()

    file_names = ['channels.json', 'groups.json']   # Files that hold data for public and private channels
    saved_channels = []

    for file_name in file_names:
        access = 'pub' if file_name == 'channels.json' else 'pri'
        try:
            with open(file=os.path.join(TEMP_SLACK_DATA_PATH, file_name)) as json_file:
                channels_json = json.load(json_file) 
        except FileNotFoundError:
            print(f'"{ file_name }" doesn\'t exist in "{ TEMP_SLACK_DATA_PATH }"')
            continue

        channels = []
        channel_members = []
        for channel in channels_json:
            # Check if the channel_id is in the list of selected channels
            if channel['id'] not in channel_ids:
                continue

            channel_instance = Channel(
                channel_id=channel['id'],
                name=channel['name'],
                access=access,
                purpose=channel['purpose']['value']
            )
            channels.append(channel_instance)
            
            channel_member_instance = ChannelMember(
                channel_id=channel['id'],
                user_ids=json.dumps( channel['members'] ),
                no_members=len( channel['members'] )
            )
            channel_members.append(channel_member_instance)

            saved_channels.append({
                'id': channel['id'],
                'name': channel['name'],
                'access': access
            })

        # TODO: should update the channels if they already exist
        Channel.bulk_create(channels)
        ChannelMember.bulk_create(channel_members)

    return saved_channels


def save_channel_messages(collection, saved_channels: [dict], channel_specs: [dict]):
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

    for channel in saved_channels:
    
        # Get the directory where the channel data is stored
        channel_folder = os.path.join(TEMP_SLACK_DATA_PATH, channel['name'])
        channel_id = channel['id']
        spec = channel_specs[channel_id]

        if spec['store_none']:  # This is shouldn't happen because the channels are already filtered in 'slack.py'
            continue
        elif spec['store_all']:
            start_date = datetime.utcfromtimestamp(0).date()
            end_date = datetime.now().date()
        else:
            start_date = datetime.utcfromtimestamp(float(spec['start_date']) / 1000).date()
            end_date = datetime.utcfromtimestamp(float(spec['end_date']) / 1000).date()
            if start_date >= end_date: 
                print('Start date cannot be larger that end date!')
                continue

        # Get all files in the channel's folder (each file correspond to daily messages)
        all_files = os.listdir(channel_folder)
        for file_name in all_files:

            # Get the date from the filename and check whether it's in the range provided
            date_str = file_name.split('.json')[0]  # The files are stored as YYYY-mm-dd.json
            file_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Don't save the files that are out of the specified date range
            if start_date > file_date or end_date < file_date:
                continue

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
                # Each message is embedded with the name of the user and the date / time
                documents.append(f"({date_time.date()}) { message['user_profile']['real_name'] }: { message['text'] }")
                metadatas.append({
                    "user_id" : message['user'],
                    "channel_id" : channel_id,
                    "access" : channel['access'],
                    "source" : 'sl',
                })

            print(f"Saving channel \"{ channel['name'] }\" ...", end=' ')
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

