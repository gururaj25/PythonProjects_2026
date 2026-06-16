# create_structure.py

import os

# Input text file
INPUT_FILE = "structure.txt"

# Output directory
OUTPUT_DIR = "output"

# Create base output folder
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    for line in file:
        path = line.strip()

        # Skip empty lines
        if not path:
            continue

        # Normalize slashes
        path = path.replace("\\", "/")

        # Full path
        full_path = os.path.join(OUTPUT_DIR, path)

        # Detect directory
        is_directory = (
            path.endswith("/") or
            "." not in os.path.basename(path)
        )

        # =========================
        # HANDLE DIRECTORIES
        # =========================
        if is_directory:

            # If folder exists and is NOT empty → skip
            if os.path.exists(full_path) and os.path.isdir(full_path):
                if os.listdir(full_path):
                    print(f"[SKIP DIR ] Already exists and not empty: {full_path}")
                    continue

            os.makedirs(full_path, exist_ok=True)
            print(f"[DIR      ] Created: {full_path}")

        # =========================
        # HANDLE FILES
        # =========================
        else:

            # Create parent folders
            parent = os.path.dirname(full_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            # If file exists and size > 0 → skip
            if os.path.exists(full_path) and os.path.isfile(full_path):
                if os.path.getsize(full_path) > 0:
                    print(f"[SKIP FILE] Already exists with content: {full_path}")
                    continue

            # Create empty file
            with open(full_path, "w", encoding="utf-8") as f:
                pass

            print(f"[FILE     ] Created: {full_path}")

print("\nProject structure creation completed.")