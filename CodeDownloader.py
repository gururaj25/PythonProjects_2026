import os
import re
import zipfile
from tkinter import *
from tkinter import filedialog, messagebox

# ==========================================
# SIMPLE AI CODE DOWNLOADER & RECONSTRUCTOR
# ==========================================

# Detect:
# File: app.py
# ```python
# code
# ```

pattern = re.compile(
    r"File:\s*(.*?)\n```.*?\n(.*?)```",
    re.DOTALL
)

def parse_and_create():
    text = input_text.get("1.0", END)

    matches = pattern.findall(text)

    if not matches:
        messagebox.showerror(
            "Error",
            "No files detected!"
        )
        return

    folder = filedialog.askdirectory(
        title="Select Output Folder"
    )

    if not folder:
        return

    project_folder = os.path.join(
        folder,
        "Generated_Project"
    )

    os.makedirs(project_folder, exist_ok=True)

    # Create files
    for filename, content in matches:

        filename = filename.strip()

        file_path = os.path.join(
            project_folder,
            filename
        )

        # Create folders automatically
        os.makedirs(
            os.path.dirname(file_path),
            exist_ok=True
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())

    # Create ZIP
    zip_path = project_folder + ".zip"

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for root, dirs, files in os.walk(project_folder):

            for file in files:

                full_path = os.path.join(root, file)

                relative_path = os.path.relpath(
                    full_path,
                    project_folder
                )

                zipf.write(
                    full_path,
                    relative_path
                )

    messagebox.showinfo(
        "Success",
        f"Project Created!\n\nZIP:\n{zip_path}"
    )

# ==========================================
# GUI
# ==========================================

root = Tk()
root.title("Simple AI Source Downloader")
root.geometry("900x600")

Label(
    root,
    text="Paste AI Generated Code Below",
    font=("Arial", 14, "bold")
).pack(pady=10)

input_text = Text(
    root,
    wrap=WORD,
    font=("Consolas", 11)
)

input_text.pack(
    fill=BOTH,
    expand=True,
    padx=10,
    pady=10
)

Button(
    root,
    text="Create Project + ZIP",
    font=("Arial", 12, "bold"),
    bg="green",
    fg="white",
    command=parse_and_create
).pack(pady=10)

root.mainloop()