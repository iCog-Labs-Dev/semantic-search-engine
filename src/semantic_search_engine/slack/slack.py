from peewee import *
from zipfile import ZipFile
from semantic_search_engine.slack.save import *
from semantic_search_engine.slack.models import *
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH
import os

class Slack:

    def __init__(self, collection):
        self.collection = collection


    def extract_zip(self, file : str) -> None:
        """extract from a zip file this will be used to easily upload export 
        data and be able to process it

        Parameters
        ----------
        file : any
            the zip file to open
        """
        with ZipFile(file, 'r') as zObject:
            zObject.extractall(path=TEMP_SLACK_DATA_PATH)

    def reset_slack(self):
        """ deletes all slack data from SQLite and Chroma
        """
        # Delete all data from SQL database
        Message.delete().execute()
        Channel.delete().execute()
        User.delete().execute()

        # Delete all Chroma entries for Slack
        self.collection.delete(
            where={"source" : "sl"}
        )

    def import_slack_data(self):
        """ loads the extracted file from directory and saves everything to Sqlite and Chroma
        """
        try:
            save_users_data()
            save_channels_data()
        except: print('Users and channels are already exported!')
            
        rows=Channel.select()
        for row in rows:
            # print ("name: {} id: {}".format(row.name, row.channel_id))
            save_channel_messages(channel_id=row.channel_id, collection=self.collection)
    
    @staticmethod
    def get_channel_details(channel_id: str):
        return Channel.select().where( Channel.channel_id==channel_id ).dicts().get()

    @staticmethod
    def get_user_details(user_id: str):
        return User.select().where( User.user_id==user_id ).dicts().get()

    @staticmethod
    def get_message_details(message_id: str):
        return Message.select().where( Message.message_id==message_id ).dicts().get()