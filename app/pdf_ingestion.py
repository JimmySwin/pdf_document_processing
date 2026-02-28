from pypdf import PdfReader
from pathlib import Path
from .config import DATA_DIR

def extract_text_from_pdf(file_path):
    """
    Reads a PDF file and extracts all text, returning a single string.
    """
    reader = PdfReader(file_path)
    pdf_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pdf_text += page_text + "\n"
    return pdf_text.strip()

def preprocess_text(text : str) -> str:
    """
    Cleans and normalises the extracted text (removes any extra whitespaces).
    """
    text = " ".join(text.split())
    return text

if __name__ == "__main__":
    """
    Testcase to make sure the the PDF ingestion and preprocessing works correctly. 
    It will print the extracted text from the PDF files in the data directory.
    """
    # Check if the data directory exists
    if not DATA_DIR.exists():
        print(f"Data directory not found at {DATA_DIR}")
    else:
        # Find all PDF files in the data dierctory
        pdf_files = list(DATA_DIR.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {DATA_DIR}")
        else:
            print(f"Found {len(pdf_files)} PDF file(s) in {DATA_DIR}")
            for pdf_file in pdf_files:

                print(f"\nProcessing PDF: {pdf_file}")
                raw_text = extract_text_from_pdf(pdf_file)
                clean_text = preprocess_text(raw_text)
                print(f"Extracted Text:\n{clean_text[:500]}...")  # Print first 500 characters