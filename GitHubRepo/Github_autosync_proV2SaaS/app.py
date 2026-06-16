import tkinter as tk
from gui.main_window import GitHubAutoSyncApp

if __name__ == "__main__":

    print("===================================")
    print("Starting GitHub AutoSync Pro")
    print("===================================")

    root = tk.Tk()
    app = GitHubAutoSyncApp(root)
    root.mainloop()