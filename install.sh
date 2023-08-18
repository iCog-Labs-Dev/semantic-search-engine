pip install gitpython
#Install dependencies for Llama 2
pip -q install git+https://github.com/huggingface/transformers # need to install transformers from github
pip install -q datasets loralib sentencepiece
pip -q install bitsandbytes accelerate xformers einops
# Install Instructor Embedding and Chroma
pip -q install langchain chromadb sentence_transformers InstructorEmbedding
# Install ngrok to host an api endpoint from colab
pip install pyngrok