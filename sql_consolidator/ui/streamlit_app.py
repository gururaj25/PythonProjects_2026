"""
Streamlit GUI for SQL Query Consolidation Tool
Run with: streamlit run ui/streamlit_app.py
"""

import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import load_config, run_consolidation


def main():
    st.set_page_config(
        page_title="SQL Consolidator",
        page_icon="\U0001f5c4",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    config = load_config("config/config.yaml")

    # Sidebar
    st.sidebar.title("Configuration")
    st.sidebar.markdown("---")

    input_dir = st.sidebar.text_input("Input Directory", placeholder="/path/to/sql/files")
    output_dir = st.sidebar.text_input("Output Directory", value="./output")

    extensions = st.sidebar.multiselect(
        "Include Extensions",
        options=[".sql", ".txt", ".log", ".bak", ".csv", ".json"],
        default=[".sql", ".txt", ".log"],
    )

    keyword_input = st.sidebar.text_area(
        "Keyword Filter (one per line)", placeholder="production\ncritical"
    )
    keywords = (
        [k.strip() for k in keyword_input.split("\n") if k.strip()]
        if keyword_input.strip() else None
    )

    skip_dedup = st.sidebar.checkbox("Skip Deduplication", value=False)
    min_complexity = st.sidebar.slider("Min Complexity Score", 0, 50, 0)
    min_importance = st.sidebar.slider("Min Importance Score", 0, 30, 0)

    st.sidebar.markdown("---")
    gen_sql = st.sidebar.checkbox("Generate .sql", value=True)
    gen_txt = st.sidebar.checkbox("Generate .txt", value=True)
    gen_docx = st.sidebar.checkbox("Generate .docx", value=True)
    gen_xlsx = st.sidebar.checkbox("Generate .xlsx", value=True)

    # Main content
    st.title("SQL Query Consolidation and Deduplication Tool")
    st.markdown(
        "Scan multiple files and directories to extract, deduplicate, "
        "and consolidate SQL queries into a single clean master document."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.info("Multi-file Scanning")
    col2.info("Smart Deduplication")
    col3.info("SQL Formatting")
    col4.info("Risk Analysis")

    st.markdown("---")

    if st.button("Start SQL Consolidation", type="primary", use_container_width=True):
        if not input_dir:
            st.error("Please specify an input directory")
            return
        if not os.path.exists(input_dir):
            st.error(f"Input directory not found: {input_dir}")
            return

        config["output"] = {
            "generate_sql": gen_sql,
            "generate_txt": gen_txt,
            "generate_docx": gen_docx,
            "generate_xlsx": gen_xlsx,
        }

        with st.spinner("Processing SQL files..."):
            try:
                results = run_consolidation(
                    input_dir=input_dir,
                    output_dir=output_dir,
                    config=config,
                    extensions=extensions,
                    keywords=keywords,
                    skip_dedup=skip_dedup,
                    min_complexity=min_complexity,
                    min_importance=min_importance,
                )
                if results:
                    st.success("Consolidation completed successfully!")
                    st.session_state["results"] = results
                else:
                    st.warning("No queries found in the specified directory")
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
                st.exception(e)

    if "results" in st.session_state:
        results = st.session_state["results"]
        dedup = results["dedup_result"]
        analysis = results["analysis_report"]

        st.markdown("---")
        st.subheader("Results Overview")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Files Scanned", results["scan_result"].total_files_scanned)
        c2.metric("Queries Found", len(results["all_queries"]))
        c3.metric("Unique Queries", dedup.total_unique,
                  delta=f"-{dedup.total_duplicates} dupes")
        c4.metric("Critical Risks", analysis.risk_summary.get("CRITICAL", 0))
        c5.metric("Time", f"{results.get('elapsed_seconds', 0):.1f}s")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Analytics", "Query Browser", "Risk Analysis", "Downloads"
        ])

        with tab1:
            if analysis.query_type_distribution:
                st.subheader("Query Type Distribution")
                df = pd.DataFrame(
                    list(analysis.query_type_distribution.items()),
                    columns=["Query Type", "Count"]
                ).sort_values("Count", ascending=False)
                st.bar_chart(df.set_index("Query Type"))

            if analysis.most_common_tables:
                st.subheader("Most Referenced Tables")
                tdf = pd.DataFrame(
                    analysis.most_common_tables, columns=["Table", "References"]
                )
                st.bar_chart(tdf.set_index("Table"))

        with tab2:
            st.subheader("Query Browser")
            queries = results["unique_queries"]
            type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + list(set(q.query_type.value for q in queries))
            )
            risk_filter = st.selectbox(
                "Filter by Risk", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
            )
            filtered = [
                q for q in queries
                if (type_filter == "All" or q.query_type.value == type_filter)
                and (risk_filter == "All" or q.risk_level == risk_filter)
            ]
            st.caption(f"Showing {len(filtered)} of {len(queries)} queries")
            if filtered:
                data = [{
                    "Type": q.query_type.value,
                    "Risk": q.risk_level,
                    "Complexity": q.complexity_score,
                    "Importance": q.importance_score,
                    "Tables": ", ".join(q.table_names[:3]),
                    "File": Path(q.source_file).name,
                    "SQL Preview": q.raw_sql[:120].replace("\n", " "),
                } for q in filtered[:500]]
                st.dataframe(pd.DataFrame(data), use_container_width=True, height=350)

                idx = st.selectbox(
                    "Select Query to View",
                    range(min(len(filtered), 500)),
                    format_func=lambda i: (
                        f"[{filtered[i].query_type.value}] "
                        f"{filtered[i].raw_sql[:60]}..."
                    )
                )
                ca, cb = st.columns([2, 1])
                with ca:
                    st.code(filtered[idx].raw_sql, language="sql")
                with cb:
                    q = filtered[idx]
                    st.json({
                        "Type": q.query_type.value,
                        "Risk": q.risk_level,
                        "Complexity": q.complexity_score,
                        "JOINs": q.has_joins,
                        "Subquery": q.has_subquery,
                        "CTE": q.has_cte,
                        "WHERE": q.has_where_clause,
                        "Tables": q.table_names,
                    })

        with tab3:
            st.subheader("Risk Analysis")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("CRITICAL", analysis.risk_summary.get("CRITICAL", 0))
            r2.metric("HIGH", analysis.risk_summary.get("HIGH", 0))
            r3.metric("MEDIUM", analysis.risk_summary.get("MEDIUM", 0))
            r4.metric("LOW", analysis.risk_summary.get("LOW", 0))

            if analysis.high_risk_queries:
                st.warning(f"Found {len(analysis.high_risk_queries)} HIGH/CRITICAL queries!")
                with st.expander("View High Risk Queries"):
                    rdata = [{
                        "Risk Level": q.risk_level,
                        "Query Type": q.query_type.value,
                        "File": Path(q.source_file).name,
                        "Line": q.line_number_start,
                        "SQL": q.raw_sql[:200].replace("\n", " "),
                    } for q in analysis.high_risk_queries[:20]]
                    st.dataframe(pd.DataFrame(rdata), use_container_width=True)

            if analysis.recommendations:
                st.subheader("Recommendations")
                for rec in analysis.recommendations:
                    if "CRITICAL" in rec:
                        st.error(rec)
                    elif "HIGH" in rec or "risk" in rec.lower():
                        st.warning(rec)
                    else:
                        st.info(rec)

        with tab4:
            st.subheader("Download Reports")
            output_files = results.get("output_files", {})
            mime_map = {
                ".sql": "text/plain",
                ".txt": "text/plain",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
            cols = st.columns(min(len(output_files), 3))
            for i, (rtype, fpath) in enumerate(output_files.items()):
                with cols[i % 3]:
                    if os.path.exists(fpath):
                        with open(fpath, "rb") as f:
                            data = f.read()
                        ext = Path(fpath).suffix
                        st.download_button(
                            label=f"Download {rtype.replace('_', ' ').title()}",
                            data=data,
                            file_name=Path(fpath).name,
                            mime=mime_map.get(ext, "application/octet-stream"),
                            use_container_width=True,
                        )


if __name__ == "__main__":
    main()
