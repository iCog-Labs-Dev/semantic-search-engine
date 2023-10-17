import os, requests, shelve
from semantic_search_engine.constants import MM_PAT_ID_SHELVE
from dotenv import load_dotenv

load_dotenv()

class MattermostAPI:

    def __init__(self, access_token: str):
        self.mm_api_url = os.getenv("MM_API_URL")
        self.access_token = access_token
    
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
        user_teams = self.mm_api_request("/users/" + user_id + "/teams")
        all_channels = []

        for team in user_teams:
            channels_in_team = self.mm_api_request(f"/users/{user_id}/teams/{team['id']}/channels")
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
        details = self.mm_api_request(f"/{entity}/{mm_id}")

        filtered_details = {}

        for field in args:
            filtered_details[str(field)] = details[str(field)]

        return filtered_details

    def get_user_details(self, user_id: str, *args: [str]):
        user_data = self.get_details('users', user_id, args)
        try:
            real_name = f"{user_data['first_name']} {user_data['last_name']}".strip()   # Just in case the user has no first and/or last names
            user_data.update({ 'name' : real_name or user_data['username'] })
        except: pass

        return user_data

    def get_channel_details(self, channel_id: str, *args: [str]):
        channel_data = self.get_details('channels', channel_id, args)
        try:
            display_name = channel_data['display_name']
            channel_data.update({ 'name' : display_name or channel_data['name'] })      # Just in case the channel has no display name
        except: pass
        return channel_data
    
    def get_team_details(self, team_id: str, *args: [str]):
        return self.get_details('teams', team_id, args)

    def get_post_details(self, post_id: str, *args: [str]):
        return self.get_details('posts', post_id, args)


    def mm_api_request(self, route: str, params={}, method='GET', data={}):
        authHeader = "Bearer " + self.access_token # authenticate a user (through the MM API)

        res = requests.request(
            method=method,
            url=self.mm_api_url + route,
            params=params,
            data=data,
            headers={
                "Content-type": "application/json; charset=UTF-8",
                "Authorization": authHeader,
            },
        )
        
        # Guard against bad requests
        if res.status_code != requests.codes.ok:
            raise Exception(f"Request to '{route}' failed with status code: ", res.status_code)
            
        return res.json()





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