# Semaintic Search Engine

This repo contains an API for semantically searching exported slack data. The API has the following endpoints:
>**URL:** https://semantic-search.onrender.com
>**Note:** All `GET` requests show the structure of the `POST` requests you should be sending.
-  **Root endpoint** `/` : Get some documentation about the endpoints
-  **Pull endpoint** `/pull` : Pull / clone the repo containing the exported slack data
-  **Upsert endpoint** `/upsert` : Upsert exported slack data to the vector database
-  **Start endpoint** `/togetherai/start` : Start running the togeher.ai model
-  **Search endpoint** `/search` : Semantically search the exported slack messages
-  **Stop endpoint** `/togetherai/stop` : Stop running the togeher.ai model


### It's best to follow these steps if you are running the API for the first time.
>**Prerequisite:** You should have your own together.ai API key

#### 1. Pulling Slack data from GitHub
* **URL:** `/pull`
* **Method:** `POST`
```sh
{
    "repo_url": "https://github.com/iCog-Labs-Dev/slack-export-data.git"
}
```
#### 2. Upserting Slack data to the vector database
* **URL:** `/upsert`
* **Method:** `POST`
```sh
{
    "channel_names": "['random', 'test', 'general']"
}
```
#### 3. Starting the model on together.ai
* **URL:** `/togetherai/start`
* **Method:** `POST`
```sh
{
	"together_api_key": "---------------------------"
}
```
#### 4. Prompting the semantic-search-engine
* **URL:** `/search`
* **Method:** `POST`
```sh
{
	"query" : "What did someone say about something?",
	"together_api_key": "---------------------------"
}
```
#### 5. Stopping the model on together.ai
* **URL:** `/togetherai/stop`
* **Method:** `POST`
```sh
{
	"together_api_key": "---------------------------"
}
```