import os
import re
import time
import logging
import requests
import streamlit as st
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm

# Supported extensions
DOC_EXTENSIONS = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".rtf", ".zip")
IMG_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")

# Folder to save downloads
BASE_FOLDER = "Downloaded_Documents"
os.makedirs(BASE_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(filename="download_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def download_file(url, save_path):
    try:
        r = requests.get(url, stream=True, timeout=20)
        r.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded: {url}")
        return True
    except Exception as e:
        logging.error(f"Failed to download {url} - {e}")
        return False

def crawl_page(base_url, visited, total_files, progress_callback):
    domain = urlparse(base_url).netloc
    if base_url in visited:
        return
    visited.add(base_url)

    try:
        response = requests.get(base_url, timeout=15)
        if "text/html" not in response.headers.get("content-type", ""):
            return
    except Exception as e:
        logging.error(f"Error fetching {base_url}: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    links = [urljoin(base_url, a.get("href")) for a in soup.find_all("a", href=True)]
    media_links = []

    # Extract document and image links
    for tag in soup.find_all(["a", "img"]):
        if tag.name == "a" and tag.get("href"):
            file_url = urljoin(base_url, tag["href"])
        elif tag.name == "img" and tag.get("src"):
            file_url = urljoin(base_url, tag["src"])
        else:
            continue

        if file_url.lower().endswith(DOC_EXTENSIONS + IMG_EXTENSIONS):
            media_links.append(file_url)

    # Download files
    for idx, file_url in enumerate(media_links, start=1):
        file_path = urlparse(file_url).path
        save_path = os.path.join(BASE_FOLDER, domain, sanitize_filename(file_path.lstrip("/")))
        if not os.path.exists(save_path):
            success = download_file(file_url, save_path)
            total_files[0] += 1
            if progress_callback:
                progress_callback(file_url, idx, total_files[0], success)

    # Crawl internal links recursively (same domain only)
    for link in links:
        parsed_link = urlparse(link)
        if parsed_link.netloc == domain and link not in visited:
            crawl_page(link, visited, total_files, progress_callback)

def main():
    st.set_page_config(page_title="Recursive Web Downloader", page_icon="🌐", layout="wide")
    st.title("🌐 Recursive Web Downloader")
    st.write("Automatically crawl websites and download all document and image files recursively.")

    if not os.path.exists("links.txt"):
        st.warning("⚠️ Please create a 'links.txt' file with one or more URLs (each on a new line).")
        return

    urls = [u.strip() for u in open("links.txt") if u.strip()]
    if not urls:
        st.error("No valid URLs found in links.txt")
        return

    start_btn = st.button("🚀 Start Download")

    if start_btn:
        total_files = [0]
        visited = set()
        progress_area = st.empty()
        log_area = st.empty()
        start_time = time.time()

        def update_progress(file_url, idx, count, success):
            status = "✅" if success else "❌"
            progress_area.write(f"{status} ({count}) Downloading: {file_url}")

        for url in urls:
            st.info(f"🌍 Crawling: {url}")
            crawl_page(url, visited, total_files, update_progress)

        duration = time.time() - start_time
        summary = f"\nCrawl completed in {duration:.2f} seconds. Total files downloaded: {total_files[0]}"
        logging.info(summary)
        st.success(summary)
        st.download_button("📜 Download Log File", open("download_log.txt", "r").read(), file_name="download_log.txt")

if __name__ == "__main__":
    main()
