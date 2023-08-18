from InstructorEmbedding import INSTRUCTOR
from langchain.embeddings import HuggingFaceInstructEmbeddings



# Load the embedding model
instructor_embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl",
                                                      model_kwargs={"device": "cuda"})


# Get the list of embeddings for all messages in a channel
def embed_channel_messages(channel_messages):
  msg_list = channel_messages.astype(str).tolist()
  return instructor_embeddings.embed_documents(msg_list)