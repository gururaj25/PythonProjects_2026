import os
import re
import time
import logging
import requests
import tempfile
import streamlit as st
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# ------------------------
# Supported document extensions
# ------------------------
DOC_EXTENSIONS = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".rtf", ".zip")

# Globals
visited_links = set()
downloaded_files = set()

# ------------------------
# Streamlit setup
# ------------------------
st.set_page_config(page_title="Document Crawler & Downloader", layout="wide")
st.title("📥 Website Document Crawler & Downloader")

# Log setup
LOG_FILE = os.path.join(tempfile.gettempdir(), "crawler_log.txt")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ------------------------
# Helper functions
# ------------------------
def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def sanitize_path_component(component):
    """Make folder names safe for filesystem."""
    return re.sub(r"[^a-zA-Z0-9._-]", "_", component)

def get_save_path(file_url, base_output):
    """Generate folder structure based on domain and path"""
    parsed = urlparse(file_url)
    domain = parsed.netloc.split('.')[-2] if len(parsed.netloc.split('.')) >= 2 else parsed.netloc
    domain = sanitize_path_component(domain)

    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) > 1:
        folder_path = os.path.join(base_output, domain, *[sanitize_path_component(p) for p in path_parts[:-1]])
        filename = sanitize_path_component(path_parts[-1])
    else:
        folder_path = os.path.join(base_output, domain)
        filename = sanitize_path_component(path_parts[0]) if path_parts else "unknown_file"

    os.makedirs(folder_path, exist_ok=True)
    return os.path.join(folder_path, filename)

def get_all_links(url, session, depth, max_depth, log_area=None):
    """Recursively collect all links from a given URL."""
    if depth > max_depth or url in visited_links:
        return []

    visited_links.add(url)
    links = []

    try:
        response = session.get(url, timeout=10)
        if "text/html" not in response.headers.get("Content-Type", ""):
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            full_link = urljoin(url, a_tag["href"])
            if is_valid_url(full_link):
                links.append(full_link)
    except Exception as e:
        logging.warning(f"Failed to fetch links from {url}: {e}")
        if log_area:
            log_area.write(f"⚠️ Failed to fetch {url}: {e}")
        return []

    # Recursively get sub-links
    sub_links = []
    for link in links:
        if urlparse(link).netloc == urlparse(url).netloc:
            sub_links.extend(get_all_links(link, session, depth + 1, max_depth, log_area))

    return links + sub_links

def download_file(file_url, output_folder, session, counter, total, log_area):
    """Download a single file into structured folder path."""
    local_path = get_save_path(file_url, output_folder)
    local_filename = os.path.basename(local_path)

    if local_path in downloaded_files:
        return False

    downloaded_files.add(local_path)

    try:
        response = session.get(file_url, timeout=15)
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(response.content)
            log_area.write(f"✅ ({counter}/{total}) {local_filename} → {os.path.dirname(local_path)}")
            logging.info(f"Downloaded: {file_url} -> {local_path}")
            return True
        else:
            log_area.write(f"⚠️ Failed: {local_filename} (HTTP {response.status_code})")
            logging.error(f"Failed to download {file_url}: {response.status_code}")
            return False
    except Exception as e:
        log_area.write(f"❌ Error: {local_filename} ({e})")
        logging.error(f"Error downloading {file_url}: {e}")
        return False

def crawl_and_download(base_urls, output_folder, max_depth, selected_types, log_area, progress_bar, status_placeholder):
    """Main crawl + download function."""
    os.makedirs(output_folder, exist_ok=True)
    session = requests.Session()
    all_doc_links = set()

    log_area.write("🔍 Scanning all links for downloadable documents...")
    for base_url in base_urls:
        logging.info(f"Scanning base URL: {base_url}")
        links = get_all_links(base_url, session, 0, max_depth, log_area)
        for link in links:
            if link.lower().endswith(selected_types):
                all_doc_links.add(link)

    total_files = len(all_doc_links)
    log_area.write(f"📄 Found {total_files} documents.\n")

    if total_files == 0:
        return 0, 0, 0

    downloaded_count = 0
    failed_count = 0

    for i, doc_url in enumerate(all_doc_links, start=1):
        progress = i / total_files
        progress_bar.progress(progress)
        status_placeholder.metric("Processed", f"{i} / {total_files}")
        success = download_file(doc_url, output_folder, session, i, total_files, log_area)
        if success:
            downloaded_count += 1
        else:
            failed_count += 1
        status_placeholder.metric("Downloaded", downloaded_count)
        status_placeholder.metric("Failed", failed_count)

    summary = f"""
===== DOWNLOAD COMPLETED =====
Total Files Found: {total_files}
Total Files Downloaded: {downloaded_count}
Total Failed: {failed_count}
Log generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
==============================
"""
    log_area.write(summary)
    logging.info(summary)
    return downloaded_count, failed_count, total_files

# ------------------------
# Main Streamlit App
# ------------------------
def main():
    uploaded_file = st.file_uploader("📂 Upload your links.txt file", type=["txt"])
    depth = st.slider("🔁 Recursion Depth", 1, 4, 2)
    output_folder = st.text_input("💾 Output Folder", "Downloaded_Documents")
    selected_types = st.multiselect("📄 Select file types to download", options=list(DOC_EXTENSIONS), default=list(DOC_EXTENSIONS))
    start_button = st.button("🚀 Start Crawling & Downloading")

    if start_button:
        if not uploaded_file:
            st.error("Please upload a text file containing URLs.")
            return

        urls = [line.strip() for line in uploaded_file.read().decode("utf-8").splitlines() if line.strip()]
        if not urls:
            st.error("No valid URLs found in the uploaded file.")
            return

        st.info("⏳ Process started. Please wait...")
        progress_bar = st.progress(0)
        status_placeholder = st.container()
        log_area = st.empty()

        try:
            downloaded_count, failed_count, total_files = crawl_and_download(
                urls, output_folder, depth, tuple(selected_types), log_area, progress_bar, status_placeholder
            )

            st.success(f"✅ All downloads completed! ({downloaded_count}/{total_files} successful, {failed_count} failed)")
            with open(LOG_FILE, "r") as f:
                st.download_button("📜 Download Log File", data=f.read(), file_name="crawler_log.txt")
        except Exception as e:
            st.error(f"Error during process: {e}")

if __name__ == "__main__":
    main()
