# Semaintic Search Engine

>This repo contains an API for semantically searching exported slack data. The API has the following endpoints:
-  **Root endpoint** `/` : Get some documentation about the endpoints
-  **Root endpoint** `/pull` : Pull / clone the repo containing the exported slack data
-  **Root endpoint** `/upsert` : Upsert exported slack data to the vector database
-  **Root endpoint** `/togetherai/start` : Start running the togeher.ai model
-  **Root endpoint** `/search` : Semantically search the exported slack messages
-  **Root endpoint** `/togetherai/stop` : Stop running the togeher.ai model

**Note: All `GET` requests to the above URLs show the structure of the `POST` requests you should be sending.**

>**It's best to follow these steps if you are running the API for the first time.**

#### 1. Starting the model on together.ai
* **URL:** `/togetherai/start`
* **Method:** `POST`
```sh
{
	"together_api_key": "---------------------------",
	"model_name": "togethercomputer/llama-2-70b-chat"
}
```

### Prompting the semantic-search-engine
* **URL:** `/search`
* **Method:** `POST`
```sh
{
	"query" : "What did someone say about something?",
	"together_api_key": "---------------------------",
	"together_model_name": "togethercomputer/llama-2-70b-chat",
	"embedding_model_hf": "https://huggingface.co/spaces/tollan/instructor-xl",
	"embedding_api_url": "https://hackingfaces.onrender.com/embed"
}
```