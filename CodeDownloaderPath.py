
import os
import shutil
import zipfile
from tkinter import *
from tkinter import filedialog, messagebox

# ==========================================
# SIMPLE SOURCE CODE EXTRACTOR
# ==========================================

# Allowed source code extensions
SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".cpp", ".c",
    ".cs", ".java", ".php", ".go",
    ".rs", ".swift", ".kt",
    ".sql", ".json", ".xml",
    ".yaml", ".yml", ".md"
}

# Ignore folders
IGNORE_FOLDERS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".idea",
    ".vscode",
    "bin",
    "obj",
    "venv"
}

def extract_source():

    source_folder = filedialog.askdirectory(
        title="Select Project Folder"
    )

    if not source_folder:
        return

    output_folder = filedialog.askdirectory(
        title="Select Output Folder"
    )

    if not output_folder:
        return

    project_name = os.path.basename(source_folder)

    clean_folder = os.path.join(
        output_folder,
        project_name + "_SOURCE"
    )

    os.makedirs(clean_folder, exist_ok=True)

    # Scan project
    for root, dirs, files in os.walk(source_folder):

        # Remove ignored folders
        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_FOLDERS
        ]

        for file in files:

            ext = os.path.splitext(file)[1].lower()

            if ext in SOURCE_EXTENSIONS:

                source_path = os.path.join(root, file)

                relative_path = os.path.relpath(
                    source_path,
                    source_folder
                )

                destination_path = os.path.join(
                    clean_folder,
                    relative_path
                )

                os.makedirs(
                    os.path.dirname(destination_path),
                    exist_ok=True
                )

                shutil.copy2(
                    source_path,
                    destination_path
                )

    # Create ZIP
    zip_path = clean_folder + ".zip"

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for root, dirs, files in os.walk(clean_folder):

            for file in files:

                full_path = os.path.join(root, file)

                relative_path = os.path.relpath(
                    full_path,
                    clean_folder
                )

                zipf.write(
                    full_path,
                    relative_path
                )

    messagebox.showinfo(
        "Success",
        f"Source Extracted Successfully!\\n\\nZIP:\\n{zip_path}"
    )

# ==========================================
# GUI
# ==========================================

root = Tk()
root.title("Simple Source Code Extractor")
root.geometry("500x250")

Label(
    root,
    text="Extract Only Source Code Files",
    font=("Arial", 16, "bold")
).pack(pady=30)

Button(
    root,
    text="Select Project Folder",
    font=("Arial", 14),
    bg="green",
    fg="white",
    padx=20,
    pady=10,
    command=extract_source
).pack(pady=20)

Label(
    root,
    text="Automatically removes non-code files",
    font=("Arial", 10)
).pack()

root.mainloop()

