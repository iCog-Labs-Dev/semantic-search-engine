from time import time, sleep
from sched import scheduler
import shelve

from semantic_search_engine.constants import DEFAULT_LAST_FETCH_TIME, FETCH_INTERVAL_SHELVE, LAST_FETCH_TIME_SHELVE, MM_PAT_SHELVE
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MMApi
from datetime import datetime

class Mattermost:

    def __init__(self, collection) -> None:
        self.collection = collection

        with shelve.open(FETCH_INTERVAL_SHELVE) as fetch_interval:
            self.fetch_interval_in_seconds = int(fetch_interval[FETCH_INTERVAL_SHELVE])

        with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time:
            self.last_fetch_time = int(last_fetch_time[LAST_FETCH_TIME_SHELVE])
    
    nextFetchScheduler = scheduler(time, sleep)
    LAST_FETCH_TIME_SHELVE = LAST_FETCH_TIME_SHELVE

    # For real-time update of the fetch interval (without reinstantiating the 'Mattermost' Class)
    def update_fetch_interval(self, interval):
        self.fetch_interval_in_seconds = interval

    @staticmethod
    def select_fields(response, fields):
        return [{field: res[field] for field in fields} for res in response]

    def get_all_channels(self, *fields: [str]):
        all_channels = MMApi().mm_api_GET('/channels')
        return self.select_fields(all_channels, fields)

    def scheduleFirstEvent(self, channels):
        print('scheduleFirstEvent')
        # Add an event to the scheduler
        self.nextFetchScheduler.enter(
            0,
            1, # priority
            self.get_posts_for_all_channels, # function to run when the event is triggered
            [self.nextFetchScheduler, channels] # arguments to pass to the function
        ) 

    def get_posts_for_all_channels(self, scheduler, channels):
        print(f"\n {'*'*50} \n")
        print('Fetching posts for all channels ...')

        # Register next schedule
        scheduler.enter(
            self.fetch_interval_in_seconds, 
            1, 
            self.get_posts_for_all_channels, 
            [scheduler, channels]
        )

        # calculate the time passed since lastFetchTIme
        time_passed_in_seconds = (time() - self.last_fetch_time)
        print('Time passed since last fetch: ', time_passed_in_seconds)

        post_params = {}

        # if time_passed_in_seconds >= self.fetch_interval_in_seconds and last_fetch_time != 0:
        if self.last_fetch_time != 0:
            post_params = { 'since': int(self.last_fetch_time * 1000) } # convert to milliseconds
            print('get posts since last fetch time')
        

        # Save the current time (before requesting the API)
        current_time = time()
        no_posts = 0

        for channel in channels:
            # 200 is the max number of posts per page
            # reset page to 0 for each channel
            post_params.update({'per_page': 200, 'page': 0})

            # previous_post_id is used to check if there are more pages of posts
            previous_post_id = '~'

            # Loop through all pages of posts for the channel
            while previous_post_id != '':
                # Get the server response for each page of posts
                posts_res = MMApi().mm_api_GET(
                    "/channels/" + channel["id"] + "/posts",
                    params=post_params
                )

                fields = ['id', 'message', 'user_id', 'type', 'update_at', 'delete_at', 'channel_id']

                # Get the ids for all posts in the 'order' field and filter out each fields we want for each post
                '''
                This is the schema for the response:
                    {
                        "order": [ ...list of post_ids... ],
                        "posts": {
                            ...."post_id_1": { ...1st post details... },
                                "post_id_2": { ...2nd post details... }...  }
                    }
                '''
                posts = [ { field: posts_res['posts'][postId][field] for field in fields } for postId in posts_res['order'] ]

                # try:
                # for postId in posts_res['order']:
                #     thread_res = MMApi().mm_api_GET(
                #         f"/posts/{postId}/thread"
                #     )
                #     thread = ''
                #     for thread_post_id in thread_res['order']:
                #         # '\n'.join( [thread_res['posts'][thread_post_id][field] for field in fields] )
                #         thread_post = thread_res['posts'][thread_post_id]
                #         post_user = self.get_user_details(thread_post['user_id'], 'first_name', 'last_name', 'username')
                #         post_time = self.get_post_details(thread_post_id, 'time')
                #         message = f"({ post_time['time'] }) { post_user['name'] }: { thread_post['user_id'] }"
                #         thread += message + '\n'

                #     print(thread)
                # except: print('^'*60)


                access = ''
                
                # Get the channel's access restriction (private / public)
                if channel["type"] == 'O':  access = 'pub'
                elif channel["type"] == 'P':  access = 'pri'
                else: continue
                
                # TODO: filter out any stickers / emojis
                # TODO: replace user handles with their real names
                filtered_posts = []
                
                for post in posts:
                    print('POST ************** ', post)
                    if post['delete_at'] > 0:
                        self.collection.delete(ids=[post['id']])    # Delete the message from Chroma
                        print('Message deleted!')
                    # Filter out any channel join and other type messages. Also filter out any empty string messages (only images, audio, ...)
                    elif (post['type']=='' and post['message']): # If the 'type' is empty, that means it's a normal message (instead of 'system_join_channel')
                        user_details = MMApi().get_user_details(post['user_id'], 'first_name', 'last_name', 'username')
                        post['message'] = f"({ datetime.utcfromtimestamp(post['update_at'] / 1000).date() }) { user_details['name'] }: { post['message'] }"
                        filtered_posts.append(post)

                if filtered_posts:   # If the channel has any posts left
                    user_ids=[post['user_id'] for post in filtered_posts]
                    channel_ids=[post['channel_id'] for post in filtered_posts]

                    '''
                        {
                            "id" : "message_id",

                            "document" : "(date) User: message_text",

                            "metadata" : {
                                "source": "sl / mm",
                                "access" : "pri / pub",
                                "channel_id" : "ch_sdfsa",
                                "user_id" : "usr_dfsdf",
                            }
                        }
                    '''

                    self.collection.upsert(
                        ids=[post['id'] for post in filtered_posts],
                        documents=[post['message'] for post in filtered_posts],
                        metadatas=[{**{'user_id': x}, 
                                    **{'channel_id': y},
                                    "access": access,
                                    "source":"mm"}  for x, y in zip(user_ids, channel_ids)]
                    )

                # Update the page number and previous_post_id for the next page of posts
                post_params['page'] += 1
                previous_post_id = posts_res['prev_post_id']
                no_posts += len(filtered_posts)
        
        print('Total posts fetched: ', no_posts)

        # Update last_fetch_time in shelve store
        with shelve.open(LAST_FETCH_TIME_SHELVE) as db: # handles the closing of the shelve file automatically with context manager
            # Set the last fetch time to the current time for next api call
            db[LAST_FETCH_TIME_SHELVE] = current_time
            
        # Update global last_fetch_time
        self.last_fetch_time = current_time


    def start_sync(self):
        print('Starting mattermost data sync ...')
        
        # Get the last fetch time from shelve file store
        with shelve.open(LAST_FETCH_TIME_SHELVE) as db: # handles the closing of the shelve file automatically with context manager
            if LAST_FETCH_TIME_SHELVE in db:
                last_fetch_time = db[LAST_FETCH_TIME_SHELVE]
            else:
                last_fetch_time = 0
            db.close()
        
        # calculate the time passed since lastFetchTIme
        time_passed_in_seconds = (time() - last_fetch_time)
        print('Time passed since last fetch MAIN: ', time_passed_in_seconds)

        all_channels = self.get_all_channels('id', 'type') # get all channels' id and type

        if last_fetch_time == 0: # This are no posts in the database
            print('Fetching all posts for the first time...')
            
            self.stop_sync() # cancel all previously scheduled events
            
            self.scheduleFirstEvent(all_channels) # schedule the first event
            
            self.nextFetchScheduler.run() # run the scheduled events
        
        elif last_fetch_time != 0 and self.nextFetchScheduler.empty(): 
            self.scheduleFirstEvent(all_channels)
            self.nextFetchScheduler.run()   

        if time_passed_in_seconds < self.fetch_interval_in_seconds:
            print("It's not time to fetch posts yet")

        return 'Synchronizing ...'


    def stop_sync(self):
        print('Stopping mattermost data sync ...')
        
        if not self.nextFetchScheduler.empty():
            for event in self.nextFetchScheduler.queue:
                # print('event: ', event)
                self.nextFetchScheduler.cancel(event)

        print('The scheduler is', 'empty!' if self.nextFetchScheduler.empty() else 'NOT empty!')
        return 'Stopped!'

    def is_syncing(self):
        return not self.nextFetchScheduler.empty()

    def reset_mattermost(self):
        self.stop_sync()
        try:
            self.collection.delete(
                where={"source" : "mm"}
            )

            # Reset last_fetch_time in shelve store
            with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time:
                last_fetch_time[LAST_FETCH_TIME_SHELVE] = DEFAULT_LAST_FETCH_TIME
                print('Last fetch time reset!')
        except:
            print('No Chroma Collection!')
