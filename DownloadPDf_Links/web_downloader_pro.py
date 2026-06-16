import os
import re
import time
import logging
import requests
import concurrent.futures
import streamlit as st
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# ---------------------- Configuration ---------------------- #
BASE_FOLDER = "Downloaded_Documents"
os.makedirs(BASE_FOLDER, exist_ok=True)

FILE_TYPES = {
    "PDF": (".pdf",),
    "Word": (".doc", ".docx"),
    "Excel": (".xls", ".xlsx"),
    "PowerPoint": (".ppt", ".pptx"),
    "Text": (".txt", ".rtf"),
    "Zip": (".zip",),
    "Images": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"),
}

logging.basicConfig(filename="download_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# ---------------------- Utility Functions ---------------------- #
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def download_file(url, save_path):
    """Download a file with retries and streaming."""
    try:
        r = requests.get(url, stream=True, timeout=20)
        r.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return False

def extract_links(base_url, selected_exts):
    """Extract all document and image links + internal links."""
    try:
        response = requests.get(base_url, timeout=15)
        if "text/html" not in response.headers.get("content-type", ""):
            return [], []
    except Exception as e:
        logging.error(f"Error fetching {base_url}: {e}")
        return [], []

    soup = BeautifulSoup(response.text, "html.parser")

    # All internal sublinks
    sublinks = [urljoin(base_url, a.get("href")) for a in soup.find_all("a", href=True)]
    # All downloadable links (a tags + img tags)
    media_links = []
    for tag in soup.find_all(["a", "img"]):
        url_attr = tag.get("href") if tag.name == "a" else tag.get("src")
        if not url_attr:
            continue
        file_url = urljoin(base_url, url_attr)
        if file_url.lower().endswith(selected_exts):
            media_links.append(file_url)

    return sublinks, media_links

# ---------------------- Crawler ---------------------- #
def crawl_page(base_url, domain, visited, depth, max_depth, selected_exts, found_files, progress_callback):
    """Recursive page crawler."""
    if depth > max_depth or base_url in visited:
        return
    visited.add(base_url)

    sublinks, media_links = extract_links(base_url, selected_exts)
    for file_url in media_links:
        if file_url not in found_files:
            found_files.add(file_url)

    for link in sublinks:
        parsed = urlparse(link)
        if parsed.netloc == domain and link not in visited:
            crawl_page(link, domain, visited, depth + 1, max_depth, selected_exts, found_files, progress_callback)

def crawl_domain(domain_url, max_depth, selected_exts, ui_updater):
    """Main per-domain crawler with real-time progress."""
    domain = urlparse(domain_url).netloc
    visited = set()
    found_files = set()

    # Step 1: Discover all files (count first)
    ui_updater(domain, 0, 0, "🔍 Discovering files...")
    crawl_page(domain_url, domain, visited, 0, max_depth, selected_exts, found_files, None)
    total_files = len(found_files)

    if total_files == 0:
        ui_updater(domain, 0, 0, f"❌ No files found at {domain_url}")
        return 0

    # Step 2: Download with progress
    downloaded_count = 0
    ui_updater(domain, 0, total_files, f"🟡 Starting downloads...")

    def download_and_update(file_url):
        nonlocal downloaded_count
        file_path = urlparse(file_url).path
        save_path = os.path.join(BASE_FOLDER, domain, sanitize_filename(file_path.lstrip("/")))
        success = download_file(file_url, save_path)
        downloaded_count += 1
        ui_updater(domain, downloaded_count, total_files, f"{'✅' if success else '❌'} ({downloaded_count} of {total_files}) {file_url}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(download_and_update, found_files))

    ui_updater(domain, downloaded_count, total_files, f"✅ Completed {domain}: {downloaded_count}/{total_files} files downloaded.")
    logging.info(f"{domain} completed: {downloaded_count}/{total_files} files.")
    return downloaded_count

# ---------------------- Streamlit UI ---------------------- #
def main():
    st.set_page_config(page_title="⚡ Web Downloader Ultra", page_icon="🌐", layout="wide")
    st.title("🌐 Recursive Web Downloader Ultra")
    st.write("Crawl and download all documents and images from multiple sites with live progress tracking.")

    # File input
    links_file = st.file_uploader("📁 Select a links.txt file (each URL on a new line):", type=["txt"])
    if not links_file:
        st.info("Please upload your links.txt file to continue.")
        return

    urls = [u.strip() for u in links_file.read().decode("utf-8").splitlines() if u.strip()]
    if not urls:
        st.error("No valid URLs found in the uploaded file.")
        return

    # Depth selector
    max_depth = st.slider("🔍 Crawl depth", 1, 5, 2, help="Higher depth means deeper recursion (more pages crawled).")

    # File type filters
    st.subheader("📂 File Type Filters")
    selected_types = [ft for ft in FILE_TYPES if st.checkbox(ft, True)]
    selected_exts = tuple(sum((list(FILE_TYPES[t]) for t in selected_types), []))

    start_btn = st.button("🚀 Start Crawling")

    if start_btn:
        start_time = time.time()
        total_files_downloaded = 0
        progress_placeholders = {}

        # Prepare per-domain UI blocks
        for url in urls:
            domain = urlparse(url).netloc
            progress_placeholders[domain] = {
                "bar": st.progress(0),
                "status": st.empty(),
                "summary": st.empty()
            }

        def ui_updater(domain, current, total, message):
            placeholders = progress_placeholders[domain]
            if total > 0:
                progress_value = min(current / total, 1.0)
                placeholders["bar"].progress(progress_value)
            placeholders["status"].write(f"**{domain}** → {message}")

        st.info(f"🔎 Crawling started for {len(urls)} domain(s)...")

        # Process all URLs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
            futures = {executor.submit(crawl_domain, url, max_depth, selected_exts, ui_updater): url for url in urls}
            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                try:
                    count = future.result()
                    total_files_downloaded += count
                    domain = urlparse(url).netloc
                    progress_placeholders[domain]["summary"].success(f"✅ Done: {count} files downloaded.")
                except Exception as e:
                    st.error(f"❌ Error processing {url}: {e}")

        duration = time.time() - start_time
        st.success(f"🎉 All crawls complete in {duration:.2f}s. Total files downloaded: {total_files_downloaded}")
        logging.info(f"All crawls done: {total_files_downloaded} files in {duration:.2f}s")

        st.download_button("📜 Download Log File", open("download_log.txt").read(), file_name="download_log.txt")

# ----------------------------------------------------------- #
if __name__ == "__main__":
    main()
