import difflib
import os
# List the specific file paths you want to compare
file_paths = [
    r"D:\Projects_2025\MSE8\Projects\AutoCal_Source\PF33_Client_2016_64ADLINK_RP\AutoCALClient\DlgLoadPrg.cpp",
    r"D:\Projects_2025\MSE8\Projects\AutoCal_Source\2019\PF33_Client_2016_64ADLINK_RP\AutoCALClient\DlgLoadPrg.cpp",
    r"D:\Projects_2025\MSE8\Projects\AutoCal_Source\OTHERS\REPEATED\LatestClient\PF33Client\AutoCALClient\DlgLoadPrg.cpp",
    r"D:\Projects_2025\MSE8\Projects\AutoCal_Source\OTHERS\REPEATED\PF33_64Bit\PF33_Client_2016_64\AutoCALClient\DlgLoadPrg.cpp"
]

# === OUTPUT FILE ===
output_file = "comparison_report.txt"

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()
    except FileNotFoundError:
        return [f"❌ File not found: {file_path}\n"]

def compare_files(file1_path, file2_path, out):
    lines1 = read_file(file1_path)
    lines2 = read_file(file2_path)

    diff = list(difflib.unified_diff(
        lines1, lines2,
        fromfile=file1_path,
        tofile=file2_path,
        lineterm=""
    ))

    out.write(f"\n=== Differences between ===\n{file1_path}\nand\n{file2_path}\n")

    if diff:
        out.write("\n".join(diff) + "\n")
    else:
        out.write("✅ No differences found.\n")

def main():
    with open(output_file, 'w', encoding='utf-8') as out:
        n = len(file_paths)
        for i in range(n):
            for j in range(i + 1, n):
                compare_files(file_paths[i], file_paths[j], out)

    print(f"\n✅ Comparison completed. Report saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
