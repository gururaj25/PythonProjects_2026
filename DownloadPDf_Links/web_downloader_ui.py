# web_downloader_ui.py
import streamlit as st
import subprocess
import tempfile
import os

st.title("JS Recursive Downloader (Windows Safe)")

links_file = st.file_uploader("Upload links.txt", type=["txt"])
max_depth = st.slider("Crawl Depth", 1, 5, 2)
file_types = st.multiselect("File Types", ["Documents","Spreadsheets","Presentations","Images"], default=["Documents","Images"])
output_dir = st.text_input("Output Folder", "Downloaded_Documents")

if st.button("Start Crawl") and links_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(links_file.getvalue())
        tmp_path = tmp.name

    cmd = [
        "python", "web_downloader_crawler.py",
        "--links_file", tmp_path,
        "--output_dir", output_dir,
        "--max_depth", str(max_depth),
        "--types"
    ] + file_types

    st.info("Crawling started. See logs below...")
    log_area = st.empty()

    # Run crawler as a separate process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1
    )

    # Read output in real-time
    for line in process.stdout:
        log_area.text(line.strip())

    process.wait()
    st.success("Crawling Completed!")

    # Download log file
    if os.path.exists("logs/download_log.txt"):
        with open("logs/download_log.txt", encoding="utf-8") as f:
            st.download_button("Download Log File", f.read(), file_name="download_log.txt")
