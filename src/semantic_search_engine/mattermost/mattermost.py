import shelve
from time import time, sleep
from sched import scheduler
from json import dumps as to_json

from semantic_search_engine.constants import DEFAULT_LAST_FETCH_TIME, DEFAULT_TOTAL_POSTS, FETCH_INTERVAL_SHELVE, LAST_FETCH_TIME_SHELVE, MM_PAT_ID_SHELVE, TOTAL_POSTS_SHELVE
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MMApi
from datetime import datetime

class Mattermost:

    def __init__(self, collection) -> None:
        self.collection = collection

        with shelve.open(FETCH_INTERVAL_SHELVE) as fetch_interval:
            self.fetch_interval_in_seconds = int(fetch_interval[FETCH_INTERVAL_SHELVE])

        with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time:
            self.last_fetch_time = int(last_fetch_time[LAST_FETCH_TIME_SHELVE])

        with shelve.open(TOTAL_POSTS_SHELVE) as total_posts:
            self.prev_total_posts = int(total_posts[TOTAL_POSTS_SHELVE])
    
    next_fetch_scheduler = scheduler(time, sleep)
    sync_in_progress = False
    sync_percentage = 0

    # For real-time update of the fetch interval (without reinstantiating the 'Mattermost' Class)
    def update_fetch_interval(self, interval):
        self.fetch_interval_in_seconds = interval

    def get_all_channels(self,  *fields: [str]):
        all_channels = self.mm_api.mm_api_request('/channels')
        channel_fields = [{field: res[field] for field in fields} for res in all_channels]
        return channel_fields

    def schedule_first_event(self, channels):
        # Add an event to the scheduler
        self.next_fetch_scheduler.enter(
            0,
            1, # priority
            self.get_posts_for_all_channels, # function to run when the event is triggered
            [channels] # arguments to pass to the function
        ) 

    def get_posts_for_all_channels(self, channels):
        print(f"\n {'*'*50} \n")
        print('Fetching posts for all channels ...')
        self.sync_in_progress = True

        # calculate the time passed since lastFetchTIme
        time_passed_in_seconds = (time() - self.last_fetch_time)
        print('Time passed since last fetch: ', time_passed_in_seconds)

        post_params = {}

        # if time_passed_in_seconds >= self.fetch_interval_in_seconds and last_fetch_time != 0:
        if self.last_fetch_time != 0 and self.prev_total_posts != 0:
            post_params = { 'since': int(self.last_fetch_time * 1000) } # convert to milliseconds
        
        current_total_posts = sum( [int(channel['total_msg_count']) for channel in channels] )

        # Get the total number of posts since last sync
        total_posts = current_total_posts - self.prev_total_posts

        # Save the current time (before requesting the API)
        current_time = time()
        no_posts = 0
        no_filtered_posts = 0

        for channel in channels:
            # 200 is the max number of posts per page
            # reset page to 0 for each channel
            post_params.update({'per_page': 10, 'page': 0})

            # previous_post_id is used to check if there are more pages of posts
            previous_post_id = '~'

            # Loop through all pages of posts for the channel
            while previous_post_id != '':
                # Get the server response for each page of posts
                posts_res = self.mm_api.mm_api_request(
                    "/channels/" + channel["id"] + "/posts",
                    params=post_params
                )

                fields = ['id', 'message', 'user_id', 'type', 'update_at', 'delete_at', 'channel_id']

                # Get the ids for all posts in the 'order' field and filter out each post_detail_fields we want for each post
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
                #     thread_res = self.mm_api.mm_api_request(
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
                        total_posts-=1    # Deleted messages don't decrease the total_message_count from the API
                        self.collection.delete(ids=[post['id']])    # If the post has been deleted, also delete the message from Chroma
                        print('Message deleted!')
                    # Filter out any channel join and other type messages. Also filter out any empty string messages (only images, audio, ...)
                    elif (post['type']=='' and post['message']): # If the 'type' is empty, that means it's a normal message (instead of 'system_join_channel')
                        user_details = self.mm_api.get_user_details(post['user_id'], 'first_name', 'last_name', 'username')
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
                no_filtered_posts += len(filtered_posts)
                no_posts += len(posts)
                    
                # TODO: yield with progress on every batch of posts fetched from MM's API
                if total_posts != 0:
                    # yield f'data: { round(no_posts / (total_posts-9), 3) }\n\n'
                    self.sync_percentage = round(no_posts / (total_posts), 3)
                    print('Sync Progress: ', self.sync_percentage )
            # TODO: yield to indicate channel is complete
            # yield f'data: { channel["display_name"] }\n\n'
        
        print('Total posts: ', total_posts)
        print('Total posts fetched: ', no_posts)
        self.sync_in_progress = False

        # Register next schedule
        # scheduler.enter(
        #     self.fetch_interval_in_seconds, 
        #     1, 
        #     self.get_posts_for_all_channels, 
        #     [channels]
        # )

        # Update last_fetch_time in shelve store
        with shelve.open(LAST_FETCH_TIME_SHELVE) as db: # handles the closing of the shelve file automatically with context manager
            # Set the last fetch time to the current time for next api call
            db[LAST_FETCH_TIME_SHELVE] = current_time
        # Update global last_fetch_time
        self.last_fetch_time = current_time

        with shelve.open(TOTAL_POSTS_SHELVE) as db:
            db[TOTAL_POSTS_SHELVE] = total_posts + no_posts
        self.prev_total_posts = total_posts + no_posts

        # Register next schedule
        self.next_fetch_scheduler.enter(
            self.fetch_interval_in_seconds, 
            # 5,
            1, 
            self.get_posts_for_all_channels, 
            [channels]
        )
        self.next_fetch_scheduler.run()


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
        self.mm_api = MMApi(access_token=personal_access_token)
        
        all_channels = self.get_all_channels('id', 'type', 'total_msg_count', 'display_name') # get all channels' id and type

        # yield from self.get_posts_for_all_channels(all_channels)
        self.schedule_first_event(all_channels) # schedule the first event
        self.next_fetch_scheduler.run() # run the scheduled events

        # TODO: SSE to indicate that syncing is complete


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
            self.collection.delete(
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
