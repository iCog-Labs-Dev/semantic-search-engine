import git
from config import *
repo_url = "https://github.com/TollanBerhanu/MatterMost-LLM-test-Slack-export-Jun-19-2023---Jun-20-2023.git"
# slack_data_path = '/content/drive/MyDrive/Colab Notebooks/dataset/slack-data/'

git.Repo.clone_from(repo_url, slack_data_path)