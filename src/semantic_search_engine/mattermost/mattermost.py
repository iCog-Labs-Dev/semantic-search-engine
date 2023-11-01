import shelve
from time import time, sleep
from sched import scheduler

from semantic_search_engine.constants import DEFAULT_LAST_FETCH_TIME, DEFAULT_TOTAL_POSTS, LAST_FETCH_TIME_SHELVE, MM_PAT_ID_SHELVE, TOTAL_POSTS_SHELVE
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MMApi
from semantic_search_engine.mattermost.fetch_mm_data import FetchMMData
from . import collection

class Mattermost:

    def __init__(self) -> None:

        self.next_fetch_scheduler = scheduler(time, sleep)

    # For real-time update of the fetch interval (without reinstantiating the 'Mattermost' Class)
    # def update_fetch_interval(self, interval):
    #     self.fetch_interval_in_seconds = interval


    # def schedule_first_event(self, channels):
    #     # Add an event to the scheduler
    #     self.next_fetch_scheduler.enter(
    #         0,
    #         1, # priority
    #         get_posts_for_all_channels, # function to run when the event is triggered
    #         [channels] # arguments to pass to the function
    #     ) 
   

    def create_new_pat(self, temp_access_token: str) -> str:
        mm_api = MMApi(access_token=temp_access_token)
        print(temp_access_token)

        with shelve.open( MM_PAT_ID_SHELVE ) as pat_id:
            authHeader = "Bearer " + temp_access_token # authenticate a user (through the MM API)
            
            if pat_id.get( MM_PAT_ID_SHELVE, False ):
                # Delete the prev pat
                res = mm_api.mm_api_request(
                    route='/users/tokens/revoke',
                    method='POST',
                    data={ 'token_id': pat_id[ MM_PAT_ID_SHELVE ] }
                )
                if not res.get('status') == 'OK':
                    print("Failed to delete previous personal access token!")
                
            # Create a new personal_access_token
            res = mm_api.mm_api_request(
                route='/users/me/tokens',
                method='POST',
                data={ 'description': 'Mattermost Semantic Search' }
            )
            print(res)
            if not (res.get('id') or res.get('token')):
                raise Exception('Failed to create a new personal access token!')
            
            # Update the personal_access_token's id in shelve
            pat_id[ MM_PAT_ID_SHELVE ] = res['id']

        return res['token']

    def start_sync(self, temp_access_token: str) -> None:

        # Get the last fetch time from shelve file store
        with shelve.open(LAST_FETCH_TIME_SHELVE) as db: # handles the closing of the shelve file automatically with context manager
            if LAST_FETCH_TIME_SHELVE in db:
                last_fetch_time = db[LAST_FETCH_TIME_SHELVE]
            else:
                last_fetch_time = 0

        if last_fetch_time == 0: # No posts have been fetched before
            self.stop_sync() # cancel any previously scheduled events
            print('Fetching all posts for the first time...')

        if self.is_syncing(): 
            print('Sync has already started!')
            return

        # Delete the previous and create a new personal access token for the Admin
        personal_access_token = self.create_new_pat(temp_access_token=temp_access_token)
        # Set the global MMApi instance with the new pat of the Admin
        get_posts_for_all_channels = FetchMMData(
            access_token=personal_access_token,
            next_fetch_scheduler=self.next_fetch_scheduler
            ).get_posts_for_all_channels
        # all_channels = self.get_all_channels('id', 'type', 'total_msg_count', 'display_name') # get all channels' id and type

        # Add an event to the scheduler
        self.next_fetch_scheduler.enter(
            0,
            1, # priority
            get_posts_for_all_channels, # function to run when the event is triggered
            # [] # arguments to pass to the function
        ) 
        # self.schedule_first_event(all_channels) # schedule the first event
        self.next_fetch_scheduler.run() # run the scheduled events


    def stop_sync(self) -> None:

        if not self.next_fetch_scheduler.empty():
            for event in self.next_fetch_scheduler.queue:
                # print('event: ', event)
                self.next_fetch_scheduler.cancel(event) # Cancel each event in the scheduler queue

        print('Not Syncing!')
        # TODO: SSE to indicate that syncing has stopped

    def is_syncing(self):
        return not self.next_fetch_scheduler.empty()

    def reset_mattermost(self):
        self.stop_sync()
        try:
            collection.delete(
                where={"source" : "mm"}
            )

            # Reset last_fetch_time in shelve store
            with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time:
                last_fetch_time[LAST_FETCH_TIME_SHELVE] = DEFAULT_LAST_FETCH_TIME
                self.last_fetch_time = DEFAULT_LAST_FETCH_TIME
                print('Last fetch time reset!')
                
            with shelve.open(TOTAL_POSTS_SHELVE) as total_posts:
                total_posts[TOTAL_POSTS_SHELVE] = DEFAULT_TOTAL_POSTS
                self.prev_total_posts = DEFAULT_TOTAL_POSTS
                print('Total posts reset!')
        except:
            print('No Chroma Collection!')
