from github import Github

class GitHubAPI:

    def __init__(self, token):
        self.github = Github(token)

    def ensure_repo_exists(self, repo_name):

        user = self.github.get_user()

        # check if repo exists
        for repo in user.get_repos():
            if repo.name == repo_name:
                return repo.clone_url

        # create if not exists
        repo = user.create_repo(
            name=repo_name,
            private=False,
            auto_init=False
        )

        return repo.clone_url