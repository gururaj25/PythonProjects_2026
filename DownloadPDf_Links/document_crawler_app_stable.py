# document_crawler_app_stable.py
import os
import re
import time
import logging
import requests
import tempfile
import streamlit as st
from collections import deque
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup

# Supported extensions (documents only, same as yours)
DOC_EXTENSIONS = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".rtf", ".zip")

# Streamlit setup
st.set_page_config(page_title="Document Crawler & Downloader (Stable)", layout="wide")
st.title("📥 Website Document Crawler & Downloader — Stable (Folder-wise)")

# Log setup (temp file)
LOG_FILE = os.path.join(tempfile.gettempdir(), "crawler_log.txt")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------------
# Helper utilities
# -------------------------
def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False

def normalize_url(u: str) -> str:
    """Normalize a URL for comparison: strip fragments, remove trailing slash, lower scheme/host."""
    try:
        p = urlparse(u)
        scheme = p.scheme.lower()
        netloc = p.netloc.lower()
        path = p.path or ""
        # remove duplicate slashes
        path = re.sub(r"/+", "/", path)
        # remove trailing slash except for root
        if path.endswith("/") and len(path) > 1:
            path = path.rstrip("/")
        query = p.query or ""
        # keep query (some sites serve different content per query) but strip tracking params? (not now)
        normalized = f"{scheme}://{netloc}{path}"
        if query:
            normalized = normalized + "?" + query
        return normalized
    except Exception:
        return u

def sanitize_path_component(component):
    """Make folder names safe for filesystem."""
    return re.sub(r"[^a-zA-Z0-9._-]", "_", component)

def get_save_path(file_url, base_output):
    """
    Minimal-change folder path generation:
    base_output/<second-level-domain or host>/<path dirs>/<filename>
    """
    parsed = urlparse(file_url)
    # domain base: second-level if possible e.g., gurukul.iskcondesiretree.com -> iskcondesiretree
    parts = parsed.netloc.split(".")
    if len(parts) >= 2:
        domain_base = parts[-2]
    else:
        domain_base = parsed.netloc
    domain_base = sanitize_path_component(domain_base)
    # path parts
    path = parsed.path.lstrip("/")
    path_parts = [sanitize_path_component(p) for p in path.split("/") if p]
    if path_parts:
        folder_parts = [base_output, domain_base] + path_parts[:-1]
        filename = path_parts[-1]
    else:
        folder_parts = [base_output, domain_base]
        filename = sanitize_path_component(parsed.query or "file")
    folder_path = os.path.join(*folder_parts)
    os.makedirs(folder_path, exist_ok=True)
    # decode filename from URL encoding when possible
    filename = unquote(filename)
    if not filename:
        filename = "unknown_file"
    return os.path.join(folder_path, filename)

# -------------------------
# Crawling (iterative BFS)
# -------------------------
def collect_links_bfs(start_url, session, max_depth=2, max_pages=1000, same_domain=True, log_writer=None):
    """
    Iterative BFS link collector that returns a set of candidate document links.
    - avoids revisiting normalized URLs
    - respects same-domain
    - caps pages visited to max_pages
    """
    file_links = set()
    visited = set()
    queue = deque()
    queue.append((start_url, 0))
    base_netloc = urlparse(start_url).netloc

    pages_visited = 0

    while queue and pages_visited < max_pages:
        url, depth = queue.popleft()
        norm = normalize_url(url)
        if norm in visited or depth > max_depth:
            continue
        visited.add(norm)
        pages_visited += 1
        if log_writer:
            log_writer.write(f"Scanning: {url}")

        try:
            resp = session.get(url, timeout=30)
        except Exception as e:
            logging.warning(f"Failed GET {url}: {e}")
            if log_writer:
                log_writer.write(f"⚠️ Failed GET {url}: {e}")
            continue

        # quick check: if response Content-Type suggests a file, treat URL as file link
        ct = resp.headers.get("Content-Type", "").lower()
        if any(ext.strip(".") in ct for ext in [e.strip(".") for e in DOC_EXTENSIONS]) or "application/pdf" in ct:
            file_links.add(resp.url)  # final redirected URL
            continue

        # only parse HTML further
        if "text/html" not in ct:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # collect hrefs
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href:
                continue
            full = urljoin(url, href)
            if not is_valid_url(full):
                continue
            # normalize to compare domain if required
            if same_domain and urlparse(full).netloc != base_netloc:
                continue
            # if link ends with doc extension (or before query) treat as file link
            path_part = urlparse(full).path.lower()
            # check extension either in path or directly followed by query (e.g., file.pdf?dl=1)
            if any(path_part.endswith(ext) for ext in DOC_EXTENSIONS) or re.search(r'\.(' + '|'.join([e.strip('.') for e in DOC_EXTENSIONS]) + r')($|\?)', full, re.IGNORECASE):
                file_links.add(full)
            else:
                # schedule for BFS
                nfull = normalize_url(full)
                if nfull not in visited:
                    queue.append((full, depth + 1))

        # small polite sleep to avoid hammering server
        time.sleep(0.05)

    if log_writer:
        log_writer.write(f"Pages visited: {pages_visited} (max_pages={max_pages})")
    return file_links

# -------------------------
# Download helper
# -------------------------
def download_file(file_url, output_folder, session, counter, total, log_area):
    """Download a single file into structured folder path."""
    local_path = get_save_path(file_url, output_folder)
    local_filename = os.path.basename(local_path)
    # prevent double-download per run
    if os.path.exists(local_path):
        log_area.write(f"Exists: {local_filename} -> {os.path.dirname(local_path)}")
        return True
    try:
        # stream to avoid memory spikes
        with session.get(file_url, timeout=60, stream=True) as r:
            if r.status_code != 200:
                log_area.write(f"⚠️ ({counter}/{total}) Failed: {local_filename} (HTTP {r.status_code})")
                logging.error(f"Failed to download {file_url}: HTTP {r.status_code}")
                return False
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        # decode display name for friendly log (unquote)
        display_name = unquote(local_filename)
        log_area.write(f"✅ ({counter}/{total}) {display_name} → {os.path.dirname(local_path)}")
        logging.info(f"Downloaded: {file_url} -> {local_path}")
        return True
    except Exception as e:
        log_area.write(f"❌ ({counter}/{total}) Error: {local_filename} ({e})")
        logging.error(f"Error downloading {file_url}: {e}")
        return False

# -------------------------
# Main crawling + download orchestrator
# -------------------------
def crawl_and_download(base_urls, output_folder, max_depth, selected_types, log_area, progress_bar, status_placeholder):
    """
    Minimal-change orchestration that:
    - resets state per run
    - uses BFS collector per base URL
    - downloads collected files into folder structure
    """
    # reset per-run state
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/120.0.0.0 Safari/537.36"
    })

    all_doc_links = set()
    max_pages_per_site = 800  # safe cap to avoid infinite scanning; adjust if needed

    log_area.write("🔍 Scanning all links for downloadable documents...")
    for base_url in base_urls:
        logging.info(f"Scanning base URL: {base_url}")
        # collect links (BFS)
        try:
            found = collect_links_bfs(base_url, session, max_depth=max_depth, max_pages=max_pages_per_site, same_domain=True, log_writer=log_area)
            # filter found by selected_types (tuple of extensions)
            for f in found:
                # check extension in path or before query
                if any(urlparse(f).path.lower().endswith(ext) for ext in selected_types) or re.search(r'\.(' + '|'.join([e.strip('.') for e in selected_types]) + r')($|\?)', f, re.IGNORECASE):
                    all_doc_links.add(f)
        except Exception as e:
            logging.exception(f"Error collecting links for {base_url}: {e}")
            log_area.write(f"⚠️ Error collecting links for {base_url}: {e}")

    total_files = len(all_doc_links)
    log_area.write(f"📄 Found {total_files} documents.\n")

    if total_files == 0:
        progress_bar.progress(1.0)
        return 0, 0, 0

    downloaded_count = 0
    failed_count = 0

    # iterate through files in stable sorted order to keep logs reproducible
    for i, doc_url in enumerate(sorted(all_doc_links), start=1):
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

    # completion summary
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

# -------------------------
# Streamlit UI wiring (kept minimal)
# -------------------------
def main():
    uploaded_file = st.file_uploader("📂 Upload your links.txt file", type=["txt"])
    depth = st.slider("🔁 Crawl Depth", 0, 5, 1)
    output_folder = st.text_input("💾 Output Folder", "Downloaded_Documents")
    # allow user to pick from ext list; default all
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

        st.info("⏳ Crawling started. See logs below...")
        progress_bar = st.progress(0)
        status_placeholder = st.container()
        log_area = st.empty()

        try:
            downloaded_count, failed_count, total_files = crawl_and_download(
                urls, output_folder, int(depth), tuple(selected_types), log_area, progress_bar, status_placeholder
            )

            st.success(f"✅ All downloads completed! ({downloaded_count}/{total_files} successful, {failed_count} failed)")
            # provide the temp log as download
            try:
                with open(LOG_FILE, "r") as f:
                    st.download_button("📜 Download Log File", data=f.read(), file_name="crawler_log.txt")
            except Exception:
                pass
        except Exception as e:
            st.error(f"Error during process: {e}")
            logging.exception("Unhandled exception in main crawl")

if __name__ == "__main__":
    main()
