# web_downloader_crawler.py
import os
import re
import sys
import time
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--links_file", required=True)
parser.add_argument("--output_dir", default="Downloaded_Documents")
parser.add_argument("--max_depth", type=int, default=2)
parser.add_argument("--types", nargs="+", default=["Documents","Images"])
args = parser.parse_args()

# ---------------- Config ---------------- #
os.makedirs(args.output_dir, exist_ok=True)
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/download_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"  # important for Unicode-safe logging
)

SUPPORTED_EXTENSIONS = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".zip"],
    "Spreadsheets": [".xls", ".xlsx"],
    "Presentations": [".ppt", ".pptx"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"]
}
selected_exts = [ext for t in args.types for ext in SUPPORTED_EXTENSIONS.get(t,[])]

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def fetch_page(playwright, url):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    try:
        page.goto(url, timeout=60000)
        html = page.content()
    except Exception as e:
        logging.error(f"Error loading {url}: {e}")
        html = ""
    browser.close()
    return html

def download_file(file_url, save_path):
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        r = requests.get(file_url, stream=True, timeout=60)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            logging.info(f"Downloaded {file_url} -> {save_path}")
    except Exception as e:
        logging.error(f"Failed to download {file_url}: {e}")

def crawl_domain(playwright, start_url, max_depth, output_dir):
    visited = set()
    queue = [(start_url, 0)]
    parsed_domain = urlparse(start_url).netloc
    domain_folder = os.path.join(output_dir, parsed_domain)
    os.makedirs(domain_folder, exist_ok=True)

    total_downloaded = 0

    while queue:
        url, level = queue.pop(0)
        if url in visited or level > max_depth:
            continue
        visited.add(url)

        html = fetch_page(playwright, url)
        soup = BeautifulSoup(html, "html.parser")

        file_links = []
        for tag in soup.find_all(["a","img"], href=True) + soup.find_all("img", src=True):
            href = tag.get("href") or tag.get("src")
            if not href:
                continue
            full_url = urljoin(url, href)
            if any(full_url.lower().endswith(ext) for ext in selected_exts):
                file_links.append(full_url)
            elif urlparse(full_url).netloc == parsed_domain:
                queue.append((full_url, level + 1))

        for file_url in file_links:
            filename = os.path.basename(urlparse(file_url).path)
            save_path = os.path.join(domain_folder, sanitize_filename(filename))
            if not os.path.exists(save_path):
                download_file(file_url, save_path)
                total_downloaded += 1
                # print to stdout for Streamlit to read
                print(f"{total_downloaded} Downloading: {filename}", flush=True)

    print(f"Completed {parsed_domain}: {total_downloaded} files downloaded.", flush=True)
    return total_downloaded

def main():
    with sync_playwright() as p:
        with open(args.links_file, encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        total_downloaded = 0
        start_time = time.time()
        for url in urls:
            crawl_domain(p, url, args.max_depth, args.output_dir)
        elapsed = time.time() - start_time
        print(f"All domains completed in {elapsed:.2f}s", flush=True)

if __name__ == "__main__":
    main()
