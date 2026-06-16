import os
import re
import time
import logging
import streamlit as st
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
import requests

# ---------------- Config ---------------- #
BASE_FOLDER_DEFAULT = "Downloaded_Documents"
os.makedirs(BASE_FOLDER_DEFAULT, exist_ok=True)

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".zip"],
    "Spreadsheets": [".xls", ".xlsx"],
    "Presentations": [".ppt", ".pptx"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"]
}

# Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(filename="logs/download_log.txt", level=logging.INFO,
                    format="%(asctime)s - %(message)s")


# ---------------- Utilities ---------------- #
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def fetch_page_sync(playwright, url):
    """Fetch page content using Playwright sync API (handles JS)"""
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


def download_file_sync(file_url, save_path):
    """Download file synchronously"""
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        r = requests.get(file_url, stream=True, timeout=60)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            logging.info(f"Downloaded {file_url} → {save_path}")
    except Exception as e:
        logging.error(f"Failed to download {file_url}: {e}")


# ---------------- Crawler ---------------- #
def crawl_domain_sync(playwright, start_url, selected_exts, max_depth, domain_progress, overall_progress, output_dir):
    """Crawl a single domain recursively and download files"""
    visited = set()
    queue = [(start_url, 0)]
    parsed_domain = urlparse(start_url).netloc
    domain_folder = os.path.join(output_dir, parsed_domain)
    os.makedirs(domain_folder, exist_ok=True)

    total_found = 0
    total_downloaded = 0

    while queue:
        url, level = queue.pop(0)
        if url in visited or level > max_depth:
            continue
        visited.add(url)

        html = fetch_page_sync(playwright, url)
        soup = BeautifulSoup(html, "html.parser")

        # Extract file links & internal links
        file_links = []
        for tag in soup.find_all(["a", "img"], href=True) + soup.find_all("img", src=True):
            href = tag.get("href") or tag.get("src")
            if not href:
                continue
            full_url = urljoin(url, href)
            if any(full_url.lower().endswith(ext) for ext in selected_exts):
                file_links.append(full_url)
            elif urlparse(full_url).netloc == parsed_domain:
                queue.append((full_url, level + 1))

        total_found += len(file_links)

        # Download files
        for file_url in file_links:
            filename = os.path.basename(urlparse(file_url).path)
            save_path = os.path.join(domain_folder, sanitize_filename(filename))
            if not os.path.exists(save_path):
                download_file_sync(file_url, save_path)
                total_downloaded += 1
                if total_found > 0:
                    domain_progress.progress(min(total_downloaded / total_found, 1.0))
                overall_progress.text(f"({total_downloaded} of {total_found}) Downloading {filename}")

    domain_progress.progress(1.0)
    overall_progress.text(f"✅ Completed {parsed_domain}: {total_downloaded} files downloaded.")
    return total_downloaded


# ---------------- Streamlit App ---------------- #
def main():
    st.set_page_config(page_title="🌐 JS Recursive Downloader", page_icon="⚡", layout="wide")
    st.title("⚡ Advanced Recursive Web Downloader (Sync Playwright)")

    # File uploader
    links_file = st.file_uploader("📂 Upload links.txt", type=["txt"])
    max_depth = st.slider("🔍 Crawl Depth", 1, 5, 2)
    selected_types = st.multiselect("📁 File Types", list(SUPPORTED_EXTENSIONS.keys()),
                                    default=["Documents", "Images"])
    output_dir = st.text_input("💾 Output Folder", BASE_FOLDER_DEFAULT)

    if st.button("🚀 Start Crawling") and links_file:
        urls = [line.strip() for line in links_file.read().decode().splitlines() if line.strip()]
        selected_exts = [ext for t in selected_types for ext in SUPPORTED_EXTENSIONS[t]]

        total_downloaded = 0
        start_time = time.time()

        with sync_playwright() as p:
            overall_progress = st.empty()
            for url in urls:
                domain_name = urlparse(url).netloc
                st.subheader(f"🌍 {domain_name}")
                domain_progress = st.progress(0)
                downloaded = crawl_domain_sync(p, url, selected_exts, max_depth, domain_progress, overall_progress, output_dir)
                total_downloaded += downloaded

        elapsed = time.time() - start_time
        st.success(f"🎉 Completed in {elapsed:.2f}s. Total files downloaded: {total_downloaded}")
        logging.info(f"SUMMARY: Downloaded {total_downloaded} files from {len(urls)} domains in {elapsed:.2f}s")
        st.download_button("📜 Download Log File", open("logs/download_log.txt").read(), file_name="download_log.txt")


if __name__ == "__main__":
    main()
