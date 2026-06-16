import customtkinter as ctk
from tkinter import filedialog
from core.sync_engine import SyncEngine
from core.logger import logger

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GitHubAutoSyncApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("GitHub AutoSync Pro")
        self.geometry("1200x800")

        self.sync_engine = SyncEngine()

        self.create_widgets()

    def create_widgets(self):

        self.folder_label = ctk.CTkLabel(self, text="Project Folder")
        self.folder_label.pack(pady=10)

        self.folder_entry = ctk.CTkEntry(self, width=700)
        self.folder_entry.pack()

        self.browse_btn = ctk.CTkButton(
            self,
            text="Browse Folder",
            command=self.select_folder
        )
        self.browse_btn.pack(pady=10)

        self.repo_entry = ctk.CTkEntry(
            self,
            width=700,
            placeholder_text="GitHub Repository URL"
        )
        self.repo_entry.pack(pady=10)

        self.branch_entry = ctk.CTkEntry(
            self,
            width=300,
            placeholder_text="Branch Name"
        )
        self.branch_entry.pack(pady=10)

        self.commit_entry = ctk.CTkEntry(
            self,
            width=700,
            placeholder_text="Commit Message"
        )
        self.commit_entry.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self, width=700)
        self.progress.pack(pady=20)
        self.progress.set(0)

        self.push_btn = ctk.CTkButton(
            self,
            text="Upload to GitHub",
            command=self.start_upload
        )
        self.push_btn.pack(pady=20)

        self.log_box = ctk.CTkTextbox(self, width=1000, height=300)
        self.log_box.pack(pady=10)

    def select_folder(self):
        folder = filedialog.askdirectory()
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, folder)

    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def start_upload(self):

        folder = self.folder_entry.get()
        repo = self.repo_entry.get()
        branch = self.branch_entry.get()
        commit = self.commit_entry.get()

        self.log("Starting Upload...")

        self.sync_engine.sync_project(
            folder_path=folder,
            repo_url=repo,
            branch=branch,
            commit_message=commit,
            callback=self.log,
            progress_callback=self.progress.set
        )


if __name__ == "__main__":
    app = GitHubAutoSyncApp()
    app.mainloop()