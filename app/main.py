"""
AI-Assisted Document Processing Pipeline

Usage Examples:
  python app/main.py                                          # Process all PDFs in data directory with multi_call method
  python app/main.py --method single_call                     # Process all PDFs in data directory with single_call method (faster)
  python app/main.py --input-dir /path/to/folder              # Process PDFs from custom folder
  python app/main.py --input-dir /path/to/folder --method single_call  # Custom folder with single_call
"""

import argparse
import sys
from pathlib import Path
from pdf_ingestion import extract_text_from_pdf, preprocess_text
from extractor import extract_metadata_multi_call, extract_metadata_single_call
from db import init_db, save_result, generate_request_id
from email_drafter import generate_email_draft
from config import DATA_DIR, DB_PATH

def process_pdfs(input_dir, extraction_method: str = "multi_call"):
    """
    Process all PDFs in a directory and save results to the database.
    """

    init_db(DB_PATH)
    print(f"Database initialized at: {DB_PATH}")
    pdf_files = list(input_dir.glob("*.pdf"))# Find all PDFs in the input directory
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return
    print(f"Found {len(pdf_files)} PDF file(s)\n")
    
    if extraction_method == "single_call":
        extract_func = extract_metadata_single_call
    else:
        extract_func = extract_metadata_multi_call
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        
        try:
            raw_text = extract_text_from_pdf(pdf_file) # Extract text
            clean_text = preprocess_text(raw_text)
            result = extract_func(clean_text)# Extract metadata
            request_id = generate_request_id()# Generate a request ID
            
            # Save result to database
            document_id = save_result(
                db_path=DB_PATH,
                filename=pdf_file.name,
                request_id=request_id,
                extraction_method=extraction_method,
                result=result
            )
            
            print(f"Saved to database with ID: {document_id}")
            print(f"Request ID: {request_id}")
            print(f"Time taken: {result.get('elapsed_seconds')}s")
            
            if result.get("rejected"):
                print(f"Document rejected: {result.get('message')}")
            else:
                metadata = result.get("metadata", {})
                print(f"Extracted {len(metadata)} fields")
                email_draft = generate_email_draft(metadata, request_id, pdf_file.name)
                print("\nGenerated Email Draft:\n")
                print(email_draft)
            
            print()
        
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Process PDFs and extract metadata using AI"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DATA_DIR,
        help=f"Directory containing PDF files (default: {DATA_DIR})"
    )
    parser.add_argument(
        "--method",
        choices=["multi_call", "single_call"],
        default="multi_call",
        help="Extraction method: multi_call (multiple API calls) or single_call (one API call)"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not args.input_dir.exists():
        print(f"Error: Input directory '{args.input_dir}' does not exist.")
        sys.exit(1)
    
    print(f"Using extraction method: {args.method}")
    print(f"Processing PDFs from: {args.input_dir}\n")
    
    # Process PDFs
    process_pdfs(args.input_dir, extraction_method=args.method)
    
    print(f"\nDone! Results saved to: {DB_PATH}")

if __name__ == "__main__":
    main()