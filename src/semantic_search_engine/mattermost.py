from time import time, sleep
from sched import scheduler
import requests
import shelve

from semantic_search_engine.chroma import ChromaSingleton
from semantic_search_engine.constants import CHROMA_COLLECTION
from semantic_search_engine.constants import MM_USER_NAME, MM_PASSWORD, MM_PERSONAL_ACCESS_TOKEN, MATTERMOST_SERVER_URL

class Mattermost:

    collection = ChromaSingleton()\
        .get_connection()\
        .get_or_create_collection(CHROMA_COLLECTION)
    

    mmUrl = MATTERMOST_SERVER_URL
    
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
            return requests.post(
                self.mmUrl + "/users/login",
                json=loginData,
                headers={"Content-type": "application/json; charset=UTF-8"},
            ).headers["token"]

    def getChannels(self, authHeader):
        res = requests.get(
            self.mmUrl + "/channels",
            headers={
                "Content-type": "application/json; charset=UTF-8",
                "Authorization": authHeader,
            },
        )

        # Guard against bad requests
        if res.status_code != requests.codes.ok:
            print("Request failed with status code: ", res.status_code)
            return

        queryChannels = res.json()
        channels = []

        # Filter out the channel properties we don't want
        for channel in queryChannels:
            tempChannel = {}

            tempChannel["id"] = channel["id"]
            tempChannel["name"] = channel["name"]
            tempChannel["display_name"] = channel["display_name"]
            tempChannel["type"] = channel["type"]
            tempChannel["create_at"] = channel["create_at"]
            tempChannel["creator_id"] = channel["creator_id"]
            tempChannel["last_post_at"] = channel["last_post_at"]
            tempChannel["total_msg_count"] = channel["total_msg_count"]

            channels.append(tempChannel)
        
        totalPosts = 0
        for channel in channels:
            totalPosts += channel['total_msg_count']

        print('Total Channel: ', len(queryChannels))
        print('Total Posts: ', totalPosts)

        return channels

    def scheduleFirstEvent(self, fetchIntervalInSeconds, authHeader, channels):
        print('scheduleFirstEvent')
        # Add an event to the scheduler
        self.nextFetchScheduler.enter(
            0,
            1, # priority
            self.getPostsForAllChannels, # function to run when the event is triggered
            [fetchIntervalInSeconds, authHeader, self.nextFetchScheduler, channels] # arguments to pass to the function
        ) 

    def getPostsForAllChannels(self, fetchIntervalInSeconds, authHeader, scheduler, channels):
        print('\n')
        print('*'*50)
        print('\n')
        print('getPostsForAllChannels')

        scheduler.enter(
            fetchIntervalInSeconds, 
            1, 
            self.getPostsForAllChannels, 
            [fetchIntervalInSeconds, authHeader, scheduler, channels]
        )

        # Get the last fetch time from shelve file store
        with shelve.open(self.shelve_name) as db: # handles the closing of the shelve file automatically with context manager
            if 'lastFetchTime' in db:
                lastFetchTime = db['lastFetchTime']
            else:
                lastFetchTime = 0

        print('current time', time())
        print('lastFetchTime from store: ', lastFetchTime)

        # calculate the time passed since lastFetchTIme
        timePassedInSeconds = (time() - lastFetchTime)
        print('Time passed since last fetch SUB: ', timePassedInSeconds)

        postParams = {}

        # if timePassedInSeconds >= fetchIntervalInSeconds and lastFetchTime != 0:
        if lastFetchTime != 0:
            postParams = { 'since': int(lastFetchTime * 1000) } # convert to milliseconds
            print('get posts since last fetch time')

        # Set the last fetch time to the current time for next api call
        with shelve.open(self.shelve_name) as db:
            db['lastFetchTime'] = time()

        posts = []

        print('is channels empty: ', channels == [])
        print('postParams: ', postParams)
        for channel in channels:
            # 200 is the max number of posts per page
            # reset page to 0 for each channel
            postParams.update({'per_page': 200, 'page': 0})

            # previousPostId is used to check if there are more pages of posts
            previousPostId = ' '

            # Loop through all pages of posts for the channel
            while previousPostId != '':
                # Get the server response for each page of posts
                postsRes = requests.get(
                    self.mmUrl + "/channels/" + channel["id"] + "/posts",
                    params=postParams,
                    headers={
                        "Content-type": "application/json; charset=UTF-8",
                        "Authorization": authHeader,
                    },
                )

                # Guard against bad requests
                if postsRes.status_code != requests.codes.ok:
                    print("Request failed with status code: ", postsRes.status_code)
                    return

                # Convert the response to JSON
                postsRes = postsRes.json()

                # Loop through each post in the response in order, filter out the properties we don't want
                for postId in postsRes['order']:
                    post = {}
                    tempPost = postsRes['posts'][postId]
                    
                    # Filter out the post properties we don't want
                    post['msg_id'] = tempPost['id']
                    # post['root_id'] = tempPost['root_id']
                    post['channel_id'] = tempPost['channel_id']
                    post['create_at'] = tempPost['create_at']
                    post['update_at'] = tempPost['update_at']
                    post['type'] = tempPost['type']         # type=='' is a normal message
                    post['message'] = tempPost['message']   # any attachments will be ignored
                    post['user_id'] = tempPost['user_id']

                    # Add the filtered out post to the posts list
                    posts.append(post)
                
                # Update the page number and previousPostId for the next page of posts
                postParams['page'] += 1
                previousPostId = postsRes['prev_post_id']
        
        
        msg_ids=[post['msg_id'] for post in posts]
        messages=[post['message'] for post in posts]
        user_ids=[post['user_id'] for post in posts]
        channel_ids=[post['channel_id'] for post in posts]
        
        self.collection.add(
            ids=msg_ids,
            documents=messages,
            metadatas=[{**{'user_id': x}, **{'channel_id': y}, "platform":"mm"} for x, y in zip(user_ids, channel_ids)]
        )
        
        print('Total Posts SUB: ', len(posts))
        # print(' *************************** All POSTS *************************** \n', posts)


    def start_sync(self):
        print('Starting mattermost data sync ...')

        authHeader = "Bearer " + self.get_auth_token()
        print('\n')
        print('-'*20)
        print('-'*20)
        print('\n')
        
        channels = self.getChannels(authHeader) # get all channels
        fetchIntervalInSeconds = 3 * 60 # fetch interval in seconds  

        # Get the last fetch time from shelve file store
        with shelve.open(self.shelve_name) as db: # handles the closing of the shelve file automatically with context manager
            if 'lastFetchTime' in db:
                lastFetchTime = db['lastFetchTime']
            else:
                lastFetchTime = 0
        
        # calculate the time passed since lastFetchTIme
        timePassedInSeconds = (time() - lastFetchTime)
        print('Time passed since last fetch MAIN: ', timePassedInSeconds)

        if lastFetchTime == 0: # This are no posts in the database
            print('get all posts for the first time')
            
            self.stop_sync() # cancel all previously scheduled events
            
            self.scheduleFirstEvent(fetchIntervalInSeconds, authHeader, channels) # schedule the first event
            
            self.nextFetchScheduler.run() # run the scheduled events
        
        else: 
            print('Not the first time getting posts')

            if self.nextFetchScheduler.empty(): 
                self.scheduleFirstEvent(fetchIntervalInSeconds, authHeader, channels)
                self.nextFetchScheduler.run()   

        if timePassedInSeconds < fetchIntervalInSeconds:
            print("It's not time to fetch posts yet")
            
        return 'Synchronizing ...'


    def stop_sync(self):
        print('Stopping mattermost data sync ...')
        
        if not self.nextFetchScheduler.empty():
            for event in self.nextFetchScheduler.queue:
                # print('event: ', event)
                self.nextFetchScheduler.cancel(event)

        print('isEmpty: ', self.nextFetchScheduler.empty())
        return 'Stopped!'
    
    # Privacy Feature in Mattermost

    def get_user_teams(self, authHeader, userId):
        teamRes = requests.get(
            self.mmUrl + "/users/" + userId + "/teams",
            headers={
                "Content-type": "application/json; charset=UTF-8",
                "Authorization": authHeader,
            },
        )

        # Guard against bad requests
        if teamRes.status_code != requests.codes.ok:
            print("Get User's teams request failed with status code: ", teamRes.status_code)
            return

        return teamRes.json()

    def get_channels_for_user_team(self, authHeader, userId, teamId):
        userChannelsRes = requests.get(
            self.mmUrl + "/users/" + userId + "/teams/" + teamId + "/channels",
            headers={
                "Content-type": "application/json; charset=UTF-8",
                "Authorization": authHeader,
            },
        )

        # Guard against bad requests
        if userChannelsRes.status_code != requests.codes.ok:
            print("Get User's teams request failed with status code: ", userChannelsRes.status_code)
            return

        return userChannelsRes.json()
    
    def get_user_channels(self, user_id: str) -> [str]:
        authHeader = "Bearer " + MM_PERSONAL_ACCESS_TOKEN
        # user_id = login().json()['id']

        teams = self.get_user_teams(authHeader, user_id)

        channels = []
        for team in teams:
            channel = self.get_channels_for_user_team(authHeader, user_id, team['id'])
            channels.extend(channel)

        channels = list({v['id']:v for v in channels}.values()) # make the channels list unique

        print('Total Channels: ', len(channels))

        return channels