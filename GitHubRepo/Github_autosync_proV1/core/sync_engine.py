import threading
from core.git_manager import GitManager

class SyncEngine:

    def __init__(self):
        self.git = GitManager()

    def sync_project(
        self,
        folder_path,
        repo_url,
        branch,
        commit_message,
        callback,
        progress_callback
    ):

        threading.Thread(
            target=self._sync_thread,
            args=(
                folder_path,
                repo_url,
                branch,
                commit_message,
                callback,
                progress_callback
            )
        ).start()

    def _sync_thread(
        self,
        folder_path,
        repo_url,
        branch,
        commit_message,
        callback,
        progress_callback
    ):

        try:

            callback("Initializing Git Repository...")
            self.git.initialize_repo(folder_path)

            progress_callback(0.2)

            callback("Adding & Committing Files...")
            self.git.commit_all(folder_path, commit_message)

            progress_callback(0.6)

            callback("Pushing to GitHub...")
            self.git.push(folder_path, repo_url, branch)

            progress_callback(1.0)

            callback("Upload Completed Successfully")

        except Exception as e:
            callback(f"ERROR: {str(e)}")