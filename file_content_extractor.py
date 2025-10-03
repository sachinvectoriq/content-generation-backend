import os
from pathlib import Path
from typing import Optional
from pypdf import PdfReader
from docx import Document

# --- Required External Libraries ---
# You need to install these libraries to run this code:
# pip install pypdf python-docx


def extract_text_from_pdf(file_path: Path) -> Optional[str]:
    text = ""
    try:
        reader = PdfReader(file_path)
        # Iterate over all pages and accumulate text
        for page in reader.pages:
            # page.extract_text() returns None if no text is found, so we handle that
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF '{file_path.name}': {e}")
        return None


def extract_text_from_docx(file_path: Path) -> Optional[str]:
    print("file made it to docx extraction function")
    text = []
    try:
        document = Document(file_path)
        print("file made it to docx extraction function22")
        # Read all paragraphs and join them with newlines
        for paragraph in document.paragraphs:
            text.append(paragraph.text)

        print("file made it to docx extraction function33")

        return "\n".join(text).strip()
    except Exception as e:
        print(f"Error extracting text from DOCX '{file_path.name}': {e}")
        return None


def extract_text_from_txt(file_path: Path) -> Optional[str]:
    try:
        # Use 'utf-8' encoding which is standard for most text files
        return file_path.read_text(encoding='utf-8').strip()
    except Exception as e:
        print(f"Error reading TXT file '{file_path.name}': {e}")
        return None


def extract_content(file_path_str: str) -> Optional[str]:
    file_path = Path(file_path_str)

    if not file_path.exists():
        print(f"File not found: {file_path_str}")
        return None

    # Determine file extension and call the appropriate extractor
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif extension == ".docx":
        return extract_text_from_docx(file_path)
    elif extension == ".txt":
        return extract_text_from_txt(file_path)
    else:
        # This handles cases where FastAPI saves a file with an extension
        # that the extractor doesn't support.
        print(f"Unsupported file type: {extension}")
        return None


def main():
    print("--- Setting up Test Files ---")
    # 1. Create a dummy TXT file for easy testing
    txt_file = "sample_process.txt"
    Path(txt_file).write_text("This is the transcript content from a simple text file.", encoding='utf-8')
    print(f"Created dummy file: {txt_file}")

    # 2. Define paths for external files (REPLACE THESE WITH REAL FILE PATHS TO TEST)
    pdf_file = "sample_document.pdf"
    docx_file = "process_flow.docx"
    unsupported_file = "unsupported_file.csv"

    test_files = [txt_file, pdf_file, docx_file, unsupported_file]

    print("\n--- Starting File Content Extraction Test ---")

    for file_name in test_files:
        print(f"\nProcessing: {file_name}")

        # Check for existence of external files and skip if not found
        if (file_name.endswith(".pdf") or file_name.endswith(".docx")) and not Path(file_name).exists():
            print(f"Skipping {file_name}: Please place an actual test file in the directory to complete this test.")
            continue

        content = extract_content(file_name)

        if content:
            print(f"Successfully Extracted Text (First 100 chars):\n---")
            print(content[:100].replace('\n', ' ') + ('...' if len(content) > 100 else ''))
            print("---\n")
        elif content is None:
            print("Extraction failed or file type is unsupported.")

    # Clean up the created test file
    if Path(txt_file).exists():
        os.remove(txt_file)
        print(f"\nCleaned up {txt_file}.")


if __name__ == "__main__":
    main()
