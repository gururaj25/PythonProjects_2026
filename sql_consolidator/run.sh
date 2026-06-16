#!/bin/bash
echo '============================================================'
echo '  SQL QUERY CONSOLIDATION AND DEDUPLICATION TOOL'
echo '============================================================'

if ! command -v python3 &> /dev/null; then
    echo 'ERROR: Python 3 not installed'; exit 1
fi

[ ! -d venv ] && python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
mkdir -p logs output

echo '1. CLI Tool  2. Streamlit GUI  3. Sample Run  4. Tests'
read -p 'Choice: ' c

case $c in
    1) read -p 'Input dir: ' i; read -p 'Output dir: ' o; o=${o:-./output}
       python3 main.py -i "$i" -o "$o" --verbose ;;
    2) streamlit run ui/streamlit_app.py ;;
    3) python3 main.py -i ./sample_input -o ./output/sample_run --verbose ;;
    4) pytest tests/ -v ;;
    *) echo 'Invalid choice' ;;
esac
