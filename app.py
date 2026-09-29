import streamlit as st
import os
import re
import shutil
from pathlib import Path
import pandas as pd

# =====================================================
# STREAMLIT UI CONFIGURATION
# =====================================================
st.set_page_config(page_title="Untranslated Chinese Finder", page_icon="🕵️‍♂️", layout="centered")

st.title("🕵️‍♂️ Untranslated Chinese Text Finder")
st.write("Upload your translated `.txt` chapter files. The app will scan them for stray Chinese characters outside of footnotes and brackets, and present a detailed report.")

# =====================================================
# FILE UPLOADERS
# =====================================================
st.subheader("Upload Chapter Text Files")
uploaded_files = st.file_uploader("Upload `.txt` chapter files", type=["txt"], accept_multiple_files=True)

# =====================================================
# PROCESSING LOGIC
# =====================================================
def scan_untranslated_chinese(files):
    input_dir = Path("temp_input")
    
    if input_dir.exists():
        shutil.rmtree(input_dir)
    input_dir.mkdir(exist_ok=True)
    
    # Save uploaded files locally
    for file in files:
        with open(input_dir / file.name, "wb") as f:
            f.write(file.getbuffer())
            
    txt_files = list(input_dir.rglob("*.txt"))
    
    # Regex patterns from original script
    chinese_pattern = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]+")
    brackets_pattern = re.compile(r"\([^)]*\)|\[[^\]]*\]")
    
    footnote_patterns = [
        re.compile(r"^\s*\[\d+\]"),
        re.compile(r"^\s*\(\d+\)"),
        re.compile(r"^\s*[\u00b2\u00b3\u00b9\u2070-\u207f\d]+"),
        re.compile(r"^\s*\("),
        re.compile(r"^\s*(?:Сноска|Примечание|Прим\.)", re.IGNORECASE)
    ]

    report_data = []
    total_files_with_issues = 0

    for file_path in txt_files:
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            file_matches = []
            inside_final_footnotes = False

            for index, line in enumerate(lines, start=1):
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                if re.match(r"^\s*(?:Примечания|Сноски):", stripped_line, re.IGNORECASE):
                    inside_final_footnotes = True
                    continue
                
                if inside_final_footnotes:
                    continue

                is_footnote = any(pattern.match(line) for pattern in footnote_patterns)
                if is_footnote:
                    continue

                line_to_check = brackets_pattern.sub("", line)
                matches = chinese_pattern.findall(line_to_check)
                if matches:
                    file_matches.append({
                        "Line Number": index,
                        "Found Characters": ", ".join(matches),
                        "Full Line Text": line.strip()
                    })

            if file_matches:
                total_files_with_issues += 1
                for match in file_matches:
                    report_data.append({
                        "File Name": file_path.name,
                        "Line": match["Line Number"],
                        "Chinese Text": match["Found Characters"],
                        "Line Context": match["Full Line Text"]
                    })

        except Exception as e:
            report_data.append({
                "File Name": file_path.name,
                "Line": "-",
                "Chinese Text": f"Error: {e}",
                "Line Context": "Could not read file"
            })

    return report_data, total_files_with_issues

# =====================================================
# MAIN ACTION BUTTON
# =====================================================
if st.button("Scan for Untranslated Text"):
    if not uploaded_files:
        st.error("Please upload at least one `.txt` file.")
    else:
        with st.spinner("Scanning files for Chinese characters..."):
            try:
                report_data, issue_count = scan_untranslated_chinese(uploaded_files)
                
                if issue_count == 0 and not report_data:
                    st.success("Scan complete! No untranslated Chinese text found outside footnotes/brackets.")
                else:
                    st.warning(f"Scan complete. Found issues in {issue_count} file(s).")
                    df = pd.DataFrame(report_data)
                    st.dataframe(df, use_container_width=True)
                    
            except Exception as e:
                st.error(f"An error occurred during scanning: {e}")