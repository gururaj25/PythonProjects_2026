import os

DEFAULT_IGNORE = """
__pycache__/
*.pyc
venv/
.env
node_modules/
dist/
build/
"""

def create_gitignore(folder_path):

    gitignore_path = os.path.join(folder_path, ".gitignore")

    if not os.path.exists(gitignore_path):

        with open(gitignore_path, "w") as f:
            f.write(DEFAULT_IGNORE)