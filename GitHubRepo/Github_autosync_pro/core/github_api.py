from github import Github

class GitHubAPI:

    def __init__(self, token):
        self.github = Github(token)

    def create_repository(self, repo_name, private=True):

        user = self.github.get_user()

        repo = user.create_repo(
            name=repo_name,
            private=private,
            auto_init=True
        )

        return repo.clone_url