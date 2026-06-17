import os

IGNORE_FOLDERS = {
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    "bin",
    "obj"
}

def scan_directories(paths):
    files = []

    for root_path in paths:
        for root, dirs, filenames in os.walk(root_path):

            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]

            for file in filenames:
                try:
                    full_path = os.path.join(root, file)
                    stat = os.stat(full_path)

                    files.append({
                        "name": file,
                        "path": full_path,
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })

                except Exception:
                    pass

    return files