from pathlib import Path

OUTPUT_DIR = Path("generated_projects")

def reconstruct_project(data):
    project_name = data.get("project_name", "generated_project")
    files = data.get("files", [])

    root = OUTPUT_DIR / project_name
    root.mkdir(parents=True, exist_ok=True)

    for file in files:
        file_path = root / file["filename"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file["content"], encoding="utf-8")

    return {
        "status": "success",
        "project_path": str(root)
    }