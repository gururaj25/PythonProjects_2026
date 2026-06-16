import fitz  # PyMuPDF
from docx import Document
from langdetect import detect
import re

def is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return False

def extract_numbered_english_lines_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    english_lines = []
    current_number = None

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        for line in text.split('\n'):
            line = line.strip()

            # Check if line starts with a number (e.g., 54.)
            match = re.match(r'^(\d{1,3})[\.\)]\s*(.*)', line)
            if match:
                current_number = match.group(1)
                rest = match.group(2)
                if is_english(rest):
                    english_lines.append(f"{current_number}. {rest}")
            else:
                # No serial number, check if it's a continuation or a plain English question
                if is_english(line):
                    if current_number:
                        english_lines.append(f"{current_number}. {line}")
                    else:
                        english_lines.append(line)
    return english_lines

def save_text_to_docx(text_list, output_docx):
    doc = Document()
    for line in text_list:
        doc.add_paragraph(line)
    doc.save(output_docx)

if __name__ == "__main__":
    pdf_file = r"D:\Gururaj\Learning\Python\5.ReadPDFFiles\CBAQuestionsTotal.pdf"
    output_docx = r"D:\Gururaj\Learning\Python\5.ReadPDFFiles\CBA_Questions_EnglishWithNumbers.docx"

    english_lines = extract_numbered_english_lines_from_pdf(pdf_file)
    save_text_to_docx(english_lines, output_docx)

    print(f"Numbered English questions saved to {output_docx}")
