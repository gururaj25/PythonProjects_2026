import os
from git import Repo


class GitManager:

    def initialize_repo(self, folder_path):

        if not os.path.exists(os.path.join(folder_path, ".git")):
            Repo.init(folder_path)

    def commit_all(self, folder_path, message):

        repo = Repo(folder_path)

        # Add all files
        repo.git.add(A=True)

        # Commit only if changes exist
        if repo.is_dirty(untracked_files=True):

            repo.index.commit(message)

        # Ensure branch exists
        try:
            repo.git.branch("-M", "main")

        except Exception as e:
            print(e)

    def push(self, folder_path, repo_url, branch):

        repo = Repo(folder_path)

        # Create remote if missing
        if "origin" not in [r.name for r in repo.remotes]:
            repo.create_remote("origin", repo_url)

        # Checkout/Create branch
        try:
            repo.git.checkout(branch)

        except:
            repo.git.checkout("-b", branch)

        # Push branch
        origin = repo.remote(name="origin")

        origin.push(
            refspec=f"{branch}:{branch}",
            set_upstream=True
        )