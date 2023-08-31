import git

class FetchFromRepo:
    def __init__(self, repo_url):
        self.repo_url = repo_url

    def fetch_slack_export_from_github(self, slack_data_path='./src/database/slackdata/'):
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