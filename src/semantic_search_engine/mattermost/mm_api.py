import os, requests, json
from semantic_search_engine.constants import MM_PAT_ID_SHELVE
from dotenv import load_dotenv

load_dotenv()

class MattermostAPI:

    def __init__(self, access_token: str):
        self.mm_api_url = os.getenv("MM_API_URL")
        self.access_token = access_token


    def mm_api_request(self, route: str, params: dict={}, method: str='GET', data: dict={}):
        authHeader = "Bearer " + self.access_token # authenticate a user (through the MM API)

        try:
            res = requests.request(
                method=method,
                url=self.mm_api_url + route,
                params=params,
                data=json.dumps(data),
                headers={
                    "Content-type": "application/json; charset=UTF-8",
                    "Authorization": authHeader,
                },
            )
        except Exception as err:
            raise Exception(f"Request to Mattermost's API failed: ", err)
        
        # Guard against bad requests
        if res.status_code != requests.codes.ok:
            raise Exception(f"Request to '{route}' failed with status code: ", res.status_code)
            
        return res.json()
