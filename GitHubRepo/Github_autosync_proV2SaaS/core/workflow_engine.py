import os
from core.git_manager import GitManager
from core.github_api import GitHubAPI

class WorkflowEngine:

    def __init__(self, token):
        self.git = GitManager()
        self.github = GitHubAPI(token)

    def run_full_sync(self, folder, repo_name, branch, message, callback):

        callback("🔍 Checking folder...")

        # 1. Ensure folder exists
        if not os.path.exists(folder):
            raise Exception("Folder not found")

        # 2. Init git if needed
        callback("📦 Checking Git repository...")
        self.git.ensure_repo(folder)

        # 3. Commit safety check
        callback("📝 Adding & committing files...")
        self.git.safe_commit(folder, message)

        # 4. Create GitHub repo if missing
        callback("☁️ Checking GitHub repository...")

        repo_url = self.github.ensure_repo_exists(repo_name)

        # 5. Link remote safely
        callback("🔗 Linking remote repository...")
        self.git.set_remote(folder, repo_url)

        # 6. Push
        callback("🚀 Pushing to GitHub...")
        self.git.safe_push(folder, branch)

        callback("✅ Upload Completed Successfully!")