import os
from git import Repo

class GitService:

    def init_repo(self, folder):

        if not os.path.exists(os.path.join(folder, ".git")):
            Repo.init(folder)

    def commit_all(self, folder, message):

        repo = Repo(folder)
        repo.git.add(A=True)

        if repo.is_dirty(untracked_files=True):
            repo.index.commit(message)

    def set_remote(self, folder, url):

        repo = Repo(folder)

        if "origin" in [r.name for r in repo.remotes]:
            repo.delete_remote("origin")

        repo.create_remote("origin", url)

    def push(self, folder, branch):

        repo = Repo(folder)

        try:
            repo.git.checkout(branch)
        except:
            repo.git.checkout("-b", branch)

        origin = repo.remote("origin")
        origin.push(refspec=f"{branch}:{branch}", set_upstream=True)