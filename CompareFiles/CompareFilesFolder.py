import os
import difflib

# List of folders to compare
FOLDERS = [
    "D:\Projects_2025\MSE8\Projects\AutoCal_Source\PF33_Client_2016_64ADLINK_RP\AutoCalClient",
    "D:\Projects_2025\MSE8\Projects\AutoCal_Source\2019\PF33_Client_2016_64ADLINK_RP\AutoCalClient",
    "D:\Projects_2025\MSE8\Projects\AutoCal_Source\OTHERS\REPEATED\LatestClient\PF33Client\AutoCalClient",
    "D:\Projects_2025\MSE8\Projects\AutoCal_Source\OTHERS\REPEATED\PF33_64Bit\PF33_Client_2016_64\AutoCalClient"
]

# Output file for differences (optional)
OUTPUT_FILE = "file_differences_report.txt"

def read_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()

def compare_files_across_folders(common_filename):
    print(f"\n--- Comparing file: {common_filename} ---")
    with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
        out.write(f"\n\n=== File: {common_filename} ===\n")

        for i in range(len(FOLDERS)):
            for j in range(i + 1, len(FOLDERS)):
                file1 = os.path.join(FOLDERS[i], common_filename)
                file2 = os.path.join(FOLDERS[j], common_filename)

                if os.path.exists(file1) and os.path.exists(file2):
                    lines1 = read_file(file1)
                    lines2 = read_file(file2)

                    diff = list(difflib.unified_diff(
                        lines1, lines2,
                        fromfile=f"{FOLDERS[i]}/{common_filename}",
                        tofile=f"{FOLDERS[j]}/{common_filename}",
                        lineterm=""
                    ))

                    if diff:
                        diff_text = "\n".join(diff)
                        print(diff_text)
                        out.write(diff_text + "\n")
                    else:
                        print(f"No differences between {FOLDERS[i]} and {FOLDERS[j]} for {common_filename}")
                else:
                    print(f"File missing in one of the folders: {file1} or {file2}")

def main():
    # Collect all common file names
    all_files = set()
    for folder in FOLDERS:
        files = os.listdir(folder)
        all_files.update(files)

    # Compare only files that exist in at least two folders
    for file_name in sorted(all_files):
        folder_count = sum(1 for folder in FOLDERS if os.path.exists(os.path.join(folder, file_name)))
        if folder_count >= 2:
            compare_files_across_folders(file_name)

if __name__ == "__main__":
    main()
