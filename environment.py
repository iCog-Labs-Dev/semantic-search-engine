import os

os.environ["TOGETHER_API_KEY"] = ""
os.environ["NGROK_AUTH_TOKEN"] = ""

os.environ["EMBEDDING_URL"] = 'https://hackingfaces.onrender.com/embed'
os.environ["EMBEDDING_MODEL_SPACE_LINK"] = 'https://huggingface.co/spaces/tollan/instructor-xl'
# os.environ["EMBEDDING_MODEL_SPACE_LINK"] = 'https://huggingface.co/spaces/tollan/sentence-transformers-embedding'