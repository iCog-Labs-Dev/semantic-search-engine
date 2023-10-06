from time import time, sleep
from sched import scheduler
import shelve

from semantic_search_engine.constants import FETCH_TIME_SHELVE_NAME, SETTINGS_SHELVE_NAME, CHROMA_COLLECTION
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MMApi
from semantic_search_engine.mattermost.mm_api import mm_api_GET
from datetime import datetime

class Mattermost:

    def __init__(self, collection) -> None:
        self.collection = collection

        with shelve.open(SETTINGS_SHELVE_NAME) as settings:
            if 'fetch_interval' in settings:
                self.fetchIntervalInSeconds = int(settings['fetch_interval']) or 5 
    
    nextFetchScheduler = scheduler(time, sleep)
    fetch_time_shelve = FETCH_TIME_SHELVE_NAME

    def update_fetch_interval(self, interval):
        self.fetchIntervalInSeconds = interval

    @staticmethod
    def select_fields(response, fields):
        return [{field: res[field] for field in fields} for res in response]

    def get_all_channels(self, *fields: [str]):
        all_channels = mm_api_GET('/channels')
        return self.select_fields(all_channels, fields)

    def scheduleFirstEvent(self, channels):
        print('scheduleFirstEvent')
        # Add an event to the scheduler
        self.nextFetchScheduler.enter(
            0,
            1, # priority
            self.getPostsForAllChannels, # function to run when the event is triggered
            [self.nextFetchScheduler, channels] # arguments to pass to the function
        ) 

    def getPostsForAllChannels(self, scheduler, channels):
        print(f"\n {'*'*50} \n")
        print('Fetching posts for all channels ...')

        # Register next schedule
        scheduler.enter(
            self.fetchIntervalInSeconds, 
            1, 
            self.getPostsForAllChannels, 
            [scheduler, channels]
        )

        # Get the last fetch time from shelve file store
        with shelve.open(self.fetch_time_shelve) as db: # handles the closing of the shelve file automatically with context manager
            if self.fetch_time_shelve in db:
                lastFetchTime = db[self.fetch_time_shelve]
            else:
                lastFetchTime = 0
            # Set the last fetch time to the current time for next api call
            db[self.fetch_time_shelve] = time()
        db.close()  # Close the shelve just in case

        # calculate the time passed since lastFetchTIme
        timePassedInSeconds = (time() - lastFetchTime)
        print('Time passed since last fetch: ', timePassedInSeconds)

        postParams = {}

        # if timePassedInSeconds >= self.fetchIntervalInSeconds and lastFetchTime != 0:
        if lastFetchTime != 0:
            postParams = { 'since': int(lastFetchTime * 1000) } # convert to milliseconds
            print('get posts since last fetch time')
        
        no_posts = 0

        print('Request Params: ', postParams)

        for channel in channels:
            # 200 is the max number of posts per page
            # reset page to 0 for each channel
            postParams.update({'per_page': 200, 'page': 0})

            # previousPostId is used to check if there are more pages of posts
            previousPostId = '~'

            # Loop through all pages of posts for the channel
            while previousPostId != '':
                # Get the server response for each page of posts
                postsRes = mm_api_GET(
                    "/channels/" + channel["id"] + "/posts",
                    params=postParams
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
                posts = [ { field: postsRes['posts'][postId][field] for field in fields } for postId in postsRes['order'] ]

                # try:
                # for postId in postsRes['order']:
                #     thread_res = mm_api_GET(
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
                        # post['message'] = f"{ datetime(post['update_at'] / 1000).date() } { user_details['name'] }: { post['message'] }"
                        # TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
                        post['message'] = f"{ 'date' } { user_details['name'] }: { post['message'] }"
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

                # Update the page number and previousPostId for the next page of posts
                postParams['page'] += 1
                previousPostId = postsRes['prev_post_id']
                no_posts += len(filtered_posts)
        
        print('Total posts fetched: ', no_posts)
        # print(' *************************** All POSTS *************************** \n', posts)


    def start_sync(self):
        print('Starting mattermost data sync ...')
        
        channels = self.get_all_channels('id', 'type') # get all channels

        # Get the last fetch time from shelve file store
        with shelve.open(self.fetch_time_shelve) as db: # handles the closing of the shelve file automatically with context manager
            if self.fetch_time_shelve in db:
                lastFetchTime = db[self.fetch_time_shelve]
            else:
                lastFetchTime = 0
            db.close()
        
        # calculate the time passed since lastFetchTIme
        timePassedInSeconds = (time() - lastFetchTime)
        print('Time passed since last fetch MAIN: ', timePassedInSeconds)

        if lastFetchTime == 0: # This are no posts in the database
            print('Fetching all posts for the first time...')
            
            self.stop_sync() # cancel all previously scheduled events
            
            self.scheduleFirstEvent(channels) # schedule the first event
            
            self.nextFetchScheduler.run() # run the scheduled events
        
        elif lastFetchTime != 0 and self.nextFetchScheduler.empty(): 
            self.scheduleFirstEvent(channels)
            self.nextFetchScheduler.run()   

        if timePassedInSeconds < self.fetchIntervalInSeconds:
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

            # Delete fetch time shelve store
            with shelve.open(FETCH_TIME_SHELVE_NAME) as fetch_time_shelve:
                del fetch_time_shelve[FETCH_TIME_SHELVE_NAME]    # Delete the field within the shelve store
                print('Fetch time shelve deleted!')
        except:
            print(f'No collection named { CHROMA_COLLECTION } detected!')
