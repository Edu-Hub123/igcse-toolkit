import fitz  # PyMuPDF
import os

# Define input and output folders
pdf_folder = "syllabus_pdfs"
output_folder = "syllabus_texts"

# Make output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def process_all_pdfs():
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)
            text = extract_text_from_pdf(pdf_path)

            txt_filename = filename.replace(".pdf", ".txt")
            output_path = os.path.join(output_folder, txt_filename)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"✅ Extracted: {filename}")

if __name__ == "__main__":
    process_all_pdfs()

