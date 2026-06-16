import os
import re
import openpyxl
from openpyxl.styles import Font

def extract_info_from_file(file_path):
    print(f"Processing: {file_path}")  # Debugging line
    hostname = ''
    ip_address = ''
    oracle_versions = []
    oracle_present = 'No'

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

            # Extract Hostname
            hostname_match = re.search(r'Hostname:\s*(\S+)', content)
            if hostname_match:
                hostname = hostname_match.group(1).strip()
            else:
                print(f"⚠️ Hostname not found in {file_path}")

            # Extract IP Address
            ip_match = re.search(r'IP Address:\s*(\S+)', content)
            if ip_match:
                ip_address = ip_match.group(1).strip()
            else:
                print(f"⚠️ IP Address not found in {file_path}")

            # Extract ORACLE_HOME versions
            matches = re.findall(r'ORACLE_HOME\s+REG_SZ\s+.*?product\\([\d\.]+)\\', content)
            if matches:
                oracle_versions = list(set(matches))
                oracle_present = 'Yes'
            else:
                print(f"ℹ️ No Oracle versions found in {file_path}")

    except Exception as e:
        print(f"❌ Failed to read file: {file_path}\nError: {e}")

    return {
        'Hostname': hostname,
        'IP Address': ip_address,
        'Oracle Present': oracle_present,
        'Oracle Versions': ':'.join(sorted(oracle_versions, reverse=True))
    }

def scan_directories(base_folder):
    result = []
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file.lower() == "oracle_info.txt":
                file_path = os.path.join(root, file)
                data = extract_info_from_file(file_path)
                result.append(data)
    return result

def save_to_excel(data_list, output_file):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Oracle Report"

    headers = ['Hostname', 'IP Address', 'Oracle Present', 'Oracle Versions']
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for data in data_list:
        ws.append([
            data['Hostname'],
            data['IP Address'],
            data['Oracle Present'],
            data['Oracle Versions']
        ])

    wb.save(output_file)
    print(f"✅ Excel saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    BASE_DIR = r"D:\Projects_2025\Oracle_Projects_BidP"  # Update this path to your root folder
    OUTPUT_FILE = "Oracle_System_Report.xlsx"

    if not os.path.exists(BASE_DIR):
        print(f"❌ Base folder does not exist: {BASE_DIR}")
    else:
        all_data = scan_directories(BASE_DIR)
        if not all_data:
            print("⚠️ No data extracted. Check folder structure or file contents.")
        else:
            save_to_excel(all_data, OUTPUT_FILE)

