import git

class FetchFromRepo:
    """
    A class for fetching slack data export from a git repository 

    This class provides methods to clone or pull a git repository containing slack data.
    exports to specific directory


    Attributes:
           repo_url (str): The URL of the Git repository containg slack data exports.
    """
    def __init__(self, repo_url):
        """
        Initializes a new FetchFromRepo Instance.

        Args:
            repo_url (str): The URL of the Git repository containing slack data exports
        """
        self.repo_url = repo_url

    def fetch_slack_export_from_github(self, slack_data_path='./src/database/slackdata/'):
        """
        Fetches slack data export from git repository.

        This method either clone the git repository if it doesn't exist in the specified path 
        or pulls the lattest changes if the repository already exists.

        Args:
            slack_data_path (str, optional): The path where the slack data export repository 
            should be cloned or pulled. Default is './src/database/slackdata/'

        Returns: 
            str: A message indicating whether the repository was cloned or pulled successfully.
        """
        # repo_url = "https://github.com/TollanBerhanu/MatterMost-LLM-test-Slack-export-Jun-19-2023---Jun-20-2023.git"
        repo_exists = False

        try:
            git.Repo.clone_from(self.repo_url, slack_data_path)
            
        except git.exc.GitCommandError:
            repo_exists = True
            repo = git.Repo(slack_data_path)
            repo.remotes.origin.pull()

        except:
            return 'Something went wrong! Check if the repo is correct'

        return  ('Pulled' if repo_exists else 'Cloned') + ' repo to: ' + slack_data_path