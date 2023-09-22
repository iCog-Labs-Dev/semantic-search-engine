from time import time, sleep
from sched import scheduler
import requests
import shelve

from semantic_search_engine.chroma import ChromaSingleton
from semantic_search_engine.constants import CHROMA_COLLECTION
from semantic_search_engine.constants import MM_USER_NAME, MM_PASSWORD, MM_PERSONAL_ACCESS_TOKEN, MM_SERVER_URL, MM_FETCH_INTERVAL

class Mattermost:

    collection = ChromaSingleton()\
        .get_connection()\
        .get_or_create_collection(CHROMA_COLLECTION)
    

    mm_server_url = MM_SERVER_URL
    fetchIntervalInSeconds = MM_FETCH_INTERVAL
    
    nextFetchScheduler = scheduler(time, sleep)
    shelve_name = 'last_fetch_time'

    # authenticate a user (through the MM API)
    def get_auth_token(self):
        loginData = {
                        "login_id": MM_USER_NAME,
                        "password": MM_PASSWORD
                    }
        personal_access_token = MM_PERSONAL_ACCESS_TOKEN

        if personal_access_token:
            return personal_access_token
        else:
            print('Warning: You\'re not using a Personal-Access-Token, your session might expire!')
            return requests.post(
                self.mm_server_url + "/users/login",
                json=loginData,
                headers={"Content-type": "application/json; charset=UTF-8"},
            ).headers["token"]

    def mm_api_GET(self, route: str, params={}):
        authHeader = "Bearer " + self.get_auth_token()

        res = requests.get(
            self.mm_server_url + route,
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

    @staticmethod
    def select_fields(response, fields):
        return [{field: res[field] for field in fields} for res in response]

    def get_all_channels(self, *fields: [str]):
        all_channels = self.mm_api_GET('/channels')
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
        print('\n')
        print('*'*50)
        print('\n')
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
            if 'lastFetchTime' in db:
                lastFetchTime = db['lastFetchTime']
            else:
                lastFetchTime = 0
            # Set the last fetch time to the current time for next api call
            db['lastFetchTime'] = time()
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
                postsRes = self.mm_api_GET(
                    "/channels/" + channel["id"] + "/posts",
                    params=postParams
                )

                fields = ['id', 'message', 'user_id', 'channel_id']

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
                
                if posts:
                    user_ids=[post['user_id'] for post in posts]
                    channel_ids=[post['channel_id'] for post in posts]
                    
                    self.collection.upsert(
                        ids=[post['id'] for post in posts],
                        documents=[post['message'] for post in posts],
                        metadatas=[{**{'user_id': x}, **{'channel_id': y}, "platform":"mm"} for x, y in zip(user_ids, channel_ids)]
                    )

                # Update the page number and previousPostId for the next page of posts
                postParams['page'] += 1
                previousPostId = postsRes['prev_post_id']
                no_posts += len(posts)
        
        
        print('Total posts fetched: ', no_posts)
        # print(' *************************** All POSTS *************************** \n', posts)

        '''
            {
                "id" : "message_id",

                "document" : "message",

                "metadata" : {
                    "platform": "sl / mm",
                    "access" : "pri / pub",
                    "channel_id" : "ch_sdfsa",
                    "user_id" : "usr_dfsdf",
                }
            }

            # user_id -> realname 
            # message_id -> time sent
            # channel_id -> channel name
        
        '''

    def start_sync(self):
        print('Starting mattermost data sync ...')
        
        channels = self.get_all_channels('id') # get all channels
        # self.fetchIntervalInSeconds = 3 * 60 # fetch interval in seconds  
        self.fetchIntervalInSeconds = 5 # fetch interval in seconds  

        # Get the last fetch time from shelve file store
        with shelve.open(self.shelve_name) as db: # handles the closing of the shelve file automatically with context manager
            if 'lastFetchTime' in db:
                lastFetchTime = db['lastFetchTime']
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
        user_teams = self.mm_api_GET("/users/" + user_id + "/teams")
        all_channels = []

        for team in user_teams:
            channels_in_team = self.mm_api_GET("/users/" + user_id + "/teams/" + team['id'] + "/channels")
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
        res = requests.get(
            f"{self.mm_server_url}/{entity}/{mm_id}",
            headers={
                "Content-type": "application/json; charset=UTF-8",
                "Authorization": "Bearer " + MM_PERSONAL_ACCESS_TOKEN,
            },
        )

        if res.status_code != requests.codes.ok:
            print(f"Get {entity} details request failed with status code: ", res.status_code)
            return

        details = res.json()
        filtered_details = {}

        for field in args:
            filtered_details[str(field)] = details[str(field)]

        return filtered_details
        # return details.json()

    def get_user_details(self, user_id: str, *args: [str]):
        print(self.get_details('users', user_id, args))
        return self.get_details('users', user_id, args)

    def get_channel_details(self, channel_id: str, *args: [str]):
        print(self.get_details('channels', channel_id, args))
        return self.get_details('channels', channel_id, args)
    
    def get_post_details(self, post_id: str, *args: [str]):
        print(self.get_details('posts', post_id, args))
        return self.get_details('posts', post_id, args)

"""
Mattermost().get_user_details('ioff979djbn97juwtkx9cizq9e', 'first_name', 'last_name', 'username', 'email')             # Admin
Mattermost().get_user_details('r3dhbuhw9f8gjpwyexd7ex4iuy', 'first_name', 'last_name', 'username', 'email', 'is_bot')   # Feedback-bot

Mattermost().get_channel_details('9wgspwmu53y6mg1s6dpsbjzagy', 'name', 'display_name', 'type', 'team_id')   # hyperon           (public)
Mattermost().get_channel_details('z4kqay9m1jdxipatytm7eyteur', 'name', 'display_name', 'type', 'team_id')   # icog-hyperon-team (private)

Mattermost().get_post_details('u95bn1e1kiyg8d98hor7rwupwh', 'message', 'type', 'channel_id', 'user_id')     # Hello
Mattermost().get_post_details('e68a8f4gsjya7g4isfujyej1fe', 'message', 'type', 'channel_id', 'user_id')     # Channel join

print( Mattermost().get_user_channels('ioff979djbn97juwtkx9cizq9e', 'id', 'type', 'name') )

Mattermost().get_all_channels('id', 'name', 'total_msg_count')
"""