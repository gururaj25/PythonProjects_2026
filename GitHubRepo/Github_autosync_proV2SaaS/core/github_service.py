from github import Github

class GitHubService:

    def __init__(self, token: str):
        self.github = Github(token)

    def ensure_repo(self, repo_name: str):

        user = self.github.get_user()

        # check if repo exists
        for repo in user.get_repos():
            if repo.name == repo_name:
                return repo.clone_url

        # create repo if missing
        repo = user.create_repo(
            name=repo_name,
            private=False
        )

        return repo.clone_url