import json
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def generate_reports(duplicates):

    rows = []

    for group in duplicates:
        for file in group["files"]:

            rows.append({
                "Hash": group["hash"],
                "File": file["name"],
                "Path": file["path"],
                "Size": file["size"]
            })

    df = pd.DataFrame(rows)

    df.to_csv(OUTPUT_DIR / "duplicate_report.csv", index=False)
    df.to_excel(OUTPUT_DIR / "duplicate_report.xlsx", index=False)

    with open(OUTPUT_DIR / "duplicate_report.json", "w") as f:
        json.dump(rows, f, indent=4)

    with open(OUTPUT_DIR / "duplicate_report.txt", "w") as f:
        for row in rows:
            f.write(str(row) + "\n")