from pathlib import Path
import zipfile

project_folder = Path("duplicate_finder_project")
zip_file = "duplicate_finder_project.zip"

with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
    for file in project_folder.rglob("*"):
        if file.is_file():
            zf.write(file, file.relative_to(project_folder.parent))

print(f"ZIP created: {zip_file}")