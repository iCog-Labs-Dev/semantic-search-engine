from time import time, sleep
from sched import scheduler
import requests
import shelve

from semantic_search_engine.constants import MM_USER_NAME, MM_PASSWORD, MM_PERSONAL_ACCESS_TOKEN, MM_SERVER_URL, MM_FETCH_INTERVAL, MM_SHELVE_NAME, MM_FETCH_INTERVAL

class Mattermost:

    def __init__(self, collection) -> None:
        self.collection = collection

    fetchIntervalInSeconds = MM_FETCH_INTERVAL
    
    nextFetchScheduler = scheduler(time, sleep)
    shelve_name = MM_SHELVE_NAME

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
        with shelve.open(self.shelve_name) as db: # handles the closing of the shelve file automatically with context manager
            if self.shelve_name in db:
                lastFetchTime = db[self.shelve_name]
            else:
                lastFetchTime = 0
            # Set the last fetch time to the current time for next api call
            db[self.shelve_name] = time()
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

                fields = ['id', 'message', 'user_id', 'type', 'channel_id']

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
                
                # Filter out any channel join and other type messages. Also filter out any empty string messages (only images, audio, ...)
                # TODO: filter out any stickers / emojis
                # TODO: replace user handles with their real names
                filtered_posts = []
                
                for post in posts:
                    print('POST ************** ', post)
                    if (post['type']=='') and (post['message']): # If the 'type' is empty, that means it's a normal message (instead of 'system_join_channel')
                        filtered_posts.append(post)

                if filtered_posts:   # If the channel has any posts left
                    user_ids=[post['user_id'] for post in filtered_posts]
                    channel_ids=[post['channel_id'] for post in filtered_posts]

                    '''
                        {
                            "id" : "message_id",

                            "document" : "message_text",

                            "metadata" : {
                                "platform": "sl / mm",
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
                                    "platform":"mm"}  for x, y in zip(user_ids, channel_ids)]
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
        # self.fetchIntervalInSeconds = 3 * 60 # fetch interval in seconds  
        self.fetchIntervalInSeconds = MM_FETCH_INTERVAL # fetch interval in seconds  # TODO

        # Get the last fetch time from shelve file store
        with shelve.open(self.shelve_name) as db: # handles the closing of the shelve file automatically with context manager
            if self.shelve_name in db:
                lastFetchTime = db[self.shelve_name]
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

        print('The scheduler is ', 'empty!' if self.nextFetchScheduler.empty() else 'NOT empty!')
        return 'Stopped!'



class MattermostAPI:
    
    def get_user_channels(self, user_id: str, *args: [str]) -> [str]:
        """get the channel_ids for all the channels a user is a member of

        Parameters
        ----------
        user_id : str
            the user's id for whom we are fetching the channels

        Returns
        -------
        [str]
            the list of channel ids
        """
        user_teams = mm_api_GET("/users/" + user_id + "/teams")
        all_channels = []

        for team in user_teams:
            channels_in_team = mm_api_GET(f"/users/{user_id}/teams/{team['id']}/channels")
            all_channels.extend(channels_in_team)

        all_channels = list({v['id']:v for v in all_channels}.values()) # make the channels list unique

        print('Total no. of channels: ', len(all_channels))
        
        return [ch['id'] for ch in all_channels]

    def get_details(self, entity: str, mm_id: str, args: [str]):
        """ Fetchs the details of the entity (user, channel, post) from Mattermost's API

        Parameters
        ----------
        entity : str
            the entity we want to get the details of
        mm_id : str
            the id of the entity provided by Mattermost
        args : [str]
            the list of fields we want to get from the response

        Returns
        -------
        {"field": "value"}
            _description_
        """
        details = mm_api_GET(f"/{entity}/{mm_id}")

        filtered_details = {}

        for field in args:
            filtered_details[str(field)] = details[str(field)]

        return filtered_details

    def get_user_details(self, user_id: str, *args: [str]):
        user_data = self.get_details('users', user_id, args)
        print('(*)'*40)
        try:
            real_name = f"{user_data['first_name']} {user_data['last_name']}".strip()
            user_data.update({ 'name' : real_name or user_data['username'] })
        except: pass

        return user_data

    def get_channel_details(self, channel_id: str, *args: [str]):
        print(self.get_details('channels', channel_id, args))
        return self.get_details('channels', channel_id, args)
    
    def get_post_details(self, post_id: str, *args: [str]):
        print(self.get_details('posts', post_id, args))
        return self.get_details('posts', post_id, args)

"""
    # user_id -> realname 
    # message_id -> time sent
    # channel_id -> channel name

Mattermost().get_user_details('ioff979djbn97juwtkx9cizq9e', 'first_name', 'last_name', 'username', 'email')             # Admin
Mattermost().get_user_details('r3dhbuhw9f8gjpwyexd7ex4iuy', 'first_name', 'last_name', 'username', 'email', 'is_bot')   # Feedback-bot

Mattermost().get_channel_details('9wgspwmu53y6mg1s6dpsbjzagy', 'name', 'display_name', 'type', 'team_id')   # hyperon           (public)
Mattermost().get_channel_details('z4kqay9m1jdxipatytm7eyteur', 'name', 'display_name', 'type', 'team_id')   # icog-hyperon-team (private)

Mattermost().get_post_details('u95bn1e1kiyg8d98hor7rwupwh', 'message', 'type', 'channel_id', 'user_id')     # Hello
Mattermost().get_post_details('e68a8f4gsjya7g4isfujyej1fe', 'message', 'type', 'channel_id', 'user_id')     # Channel join

print( Mattermost().get_user_channels('ioff979djbn97juwtkx9cizq9e', 'id', 'type', 'name') )

Mattermost().get_all_channels('id', 'name', 'total_msg_count')
"""

# authenticate a user (through the MM API)
def __get_auth_token():
    if MM_PERSONAL_ACCESS_TOKEN:
        return MM_PERSONAL_ACCESS_TOKEN
    else:
        print('Warning: You\'re not using a Personal-Access-Token, your session might expire!')
        return requests.post(
            MM_SERVER_URL + "/users/login",
            json={ "login_id": MM_USER_NAME,
                    "password": MM_PASSWORD },
            headers={ "Content-type": "application/json; charset=UTF-8" },
        ).headers["token"]

def mm_api_GET(route: str, params={}):
    authHeader = "Bearer " + __get_auth_token()

    res = requests.get(
        MM_SERVER_URL + route,
        params=params,
        headers={
            "Content-type": "application/json; charset=UTF-8",
            "Authorization": authHeader,
        },
    )
    
    # Guard against bad requests
    if res.status_code != requests.codes.ok:
        raise Exception(f"Request to '{route}' failed with status code: ", res.status_code)
        
    return res.json()