import re

CODE_BLOCK_PATTERN = re.compile(
    r"(?:File:|###)?\s*([\\w/\\.-]+)\s*```(?:\\w+)?\\n(.*?)```",
    re.DOTALL
)

def extract_files_from_text(text: str):
    matches = CODE_BLOCK_PATTERN.findall(text)
    files = []

    for filename, content in matches:
        files.append({
            "filename": filename.strip(),
            "content": content.strip()
        })

    return files