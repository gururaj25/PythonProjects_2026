import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from core.workflow_engine import WorkflowEngine


class GitHubAutoSyncApp:

    def __init__(self, root):

        self.root = root
        self.root.title("GitHub AutoSync SaaS")
        self.root.geometry("700x600")

        # ---------------- STATE ----------------
        self.folder_path = tk.StringVar()
        self.repo_name = tk.StringVar()
        self.branch = tk.StringVar(value="main")
        self.commit_message = tk.StringVar(value="Initial commit")
        self.token = tk.StringVar()

        # ---------------- UI ----------------
        self.build_ui()

    # ---------------- UI BUILDER ----------------
    def build_ui(self):

        tk.Label(self.root, text="GitHub AutoSync SaaS", font=("Arial", 18, "bold")).pack(pady=10)

        # Folder selection
        tk.Label(self.root, text="Project Folder").pack()
        tk.Entry(self.root, textvariable=self.folder_path, width=60).pack()
        tk.Button(self.root, text="Browse Folder", command=self.select_folder).pack(pady=5)

        # Repo name
        tk.Label(self.root, text="GitHub Repo Name").pack()
        tk.Entry(self.root, textvariable=self.repo_name, width=60).pack()

        # Branch
        tk.Label(self.root, text="Branch").pack()
        tk.Entry(self.root, textvariable=self.branch, width=60).pack()

        # Commit message
        tk.Label(self.root, text="Commit Message").pack()
        tk.Entry(self.root, textvariable=self.commit_message, width=60).pack()

        # Token
        tk.Label(self.root, text="GitHub Token (PAT)").pack()
        tk.Entry(self.root, textvariable=self.token, width=60, show="*").pack()

        # Upload button
        tk.Button(
            self.root,
            text="🚀 Upload to GitHub",
            bg="green",
            fg="white",
            command=self.start_upload
        ).pack(pady=10)

        # Log console
        self.log_box = scrolledtext.ScrolledText(self.root, width=80, height=15)
        self.log_box.pack(pady=10)

    # ---------------- FOLDER PICKER ----------------
    def select_folder(self):

        folder = filedialog.askdirectory()

        if folder:
            self.folder_path.set(folder)
            self.log(f"📁 Selected folder: {folder}")

    # ---------------- LOG FUNCTION ----------------
    def log(self, message):

        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.root.update()

    # ---------------- MAIN UPLOAD FLOW ----------------
    def start_upload(self):

        folder = self.folder_path.get()
        repo_name = self.repo_name.get()
        branch = self.branch.get() or "main"
        message = self.commit_message.get()
        token = self.token.get()

        # ---------------- VALIDATION ----------------
        if not folder:
            messagebox.showerror("Error", "Please select a folder")
            return

        if not repo_name:
            messagebox.showerror("Error", "Please enter repo name")
            return

        if not token:
            messagebox.showerror("Error", "Please enter GitHub token")
            return

        self.log("====================================")
        self.log("🚀 Starting Upload...")
        self.log("Initializing Workflow Engine...")

        try:
            engine = WorkflowEngine(token=token)

            engine.run_full_sync(
                folder=folder,
                repo_name=repo_name,
                branch=branch,
                message=message,
                callback=self.log
            )

            self.log("✅ Upload Completed Successfully!")

        except Exception as e:

            self.log(f"❌ ERROR: {str(e)}")
            messagebox.showerror("Upload Failed", str(e))


# ---------------- RUN APP ----------------
if __name__ == "__main__":

    root = tk.Tk()
    app = GitHubAutoSyncApp(root)
    root.mainloop()