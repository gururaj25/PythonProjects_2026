from collections import defaultdict
from scanner.hash_engine import calculate_hash

def find_duplicates(files):
    grouped = defaultdict(list)

    for file in files:
        key = (file["name"], file["size"])
        grouped[key].append(file)

    duplicates = []

    for _, items in grouped.items():
        if len(items) > 1:

            hash_map = defaultdict(list)

            for item in items:
                file_hash = calculate_hash(item["path"])

                if file_hash:
                    hash_map[file_hash].append(item)

            for h, matched in hash_map.items():
                if len(matched) > 1:
                    duplicates.append({
                        "hash": h,
                        "files": matched
                    })

    return duplicates