import glob
import json
import pandas as pd
# from src.database.slack.pull_from_repo import FetchFromRepo

class ExtractData:

    def __init__(self, slack_data_path):
        self.slack_data_path = slack_data_path


    # Return the metadata of each message in the channel
    def extract_channel_metadata(self, channel_name):

        daily_json_files = glob.glob(self.slack_data_path + channel_name + '/*.json')  # use glob to get all the json files in the folder

        if not daily_json_files:  # return if the channel doesn't exist (or hasn't been exported yet)
            return

        metadata = pd.DataFrame(columns = ['message', 'channel', 'date', 'time', 'user_id', 'user_name'])

        # loop over the list of json files (each json file includes every message in that channel for a single day)
        for f in daily_json_files:
            with open(f, 'r') as file:  # open the daily json file
                data = file.read()  # Read the contents
                today_data = json.loads(data) # Parse the JSON data

            today_date = f.split("/")[-1]  # 'f' is the full file path and file name
            print('Extracting...', today_date) # the file name is the date

            # iterate through all the messages of the day
            for msg_data in today_data:
                # Skip if its a "channel_join" type message or if the actual message content is empty
                if ('subtype' in msg_data) or (msg_data['text'] == "") or (msg_data['type'] != 'message'):
                    continue
                    # TODO: filter out any links, stickers, and other junk
                    # TODO: replace @Member references with their real names

                metadata.loc[len(metadata)] = {
                        'message': msg_data['user_profile']['first_name'] + ': ' + msg_data['text'],
                        'channel': channel_name,
                        'date': today_date.split(".json")[0], # omit the file extension '.json'
                        'time': msg_data['ts'],
                        'user_id': msg_data['user'],
                        'user_name': msg_data['user_profile']['real_name'] # We can use 'first_name' to get the first name and 'real_name' to get the full name of the user
                }

        return metadata

    # extract_channel_metadata(slack_data_path, 'test')


    def get_all_channels(self):
        df = pd.read_json(self.slack_data_path + 'channels.json')

        channel_ids = [id for id in df['id']]
        channel_names = [ name for name in df['name']]

        return pd.DataFrame({ 'channel_id': channel_ids, 'channel_name': channel_names } )

    # channels = get_all_channels(slack_data_path)