from core.git_service import GitService
from core.github_service import GitHubService

class SyncEngine:

    def __init__(self, token: str):
        self.git = GitService()
        self.github = GitHubService(token)

    def run_sync(self, folder: str, repo_name: str, branch: str = "main"):

        # 1. Ensure git repo
        self.git.init_repo(folder)

        # 2. Commit changes
        self.git.commit_all(folder, "Auto Sync Commit")

        # 3. Create GitHub repo if not exists
        repo_url = self.github.ensure_repo(repo_name)

        # 4. Link remote
        self.git.set_remote(folder, repo_url)

        # 5. Push
        self.git.push(folder, branch)

        return {
            "status": "success",
            "repo_url": repo_url
        }