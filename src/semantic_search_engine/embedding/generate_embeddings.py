'''
    You can run this to install Instructor-XL embeddings on your local machine.
'''

# from InstructorEmbedding import INSTRUCTOR    # To import this, you'll first need to run: `pip install -U INSTRUCTOR` 
from langchain.embeddings import HuggingFaceInstructEmbeddings



# Load the embedding model
instructor_embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl",
                                                      model_kwargs={"device": "cuda"})


# Get the list of embeddings for all messages in a channel
def embed_channel_messages(channel_messages):
  msg_list = channel_messages.astype(str).tolist()
  return instructor_embeddings.embed_documents(msg_list)
# unnessasay