from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional
import json
import os
import tempfile  # NEW: Needed for creating temporary files
from pathlib import Path  # NEW: Useful for file path manipulation

from process_analyzer import AnalysisResult
from content_generation_core import ProcessAnalyzer
from file_content_extractor import extract_content  # NEW: Import the unified extractor function

from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

ANALYZER = ProcessAnalyzer(
    azure_api_key=os.getenv("Azure_Open_api_key"),
    azure_endpoint=os.getenv("Alta_Azure_end_point")
)


@router.post("/analyze")
async def analyze_process(
        # Accept selected_outputs as a string from the form data
        selected_outputs_str: str = Form(..., alias="selected_outputs"),
        # Make the file and text inputs optional
        transcript_file: Optional[UploadFile] = File(None),
        transcript_text: Optional[str] = Form(None)):

    if not transcript_file and not transcript_text:
        raise HTTPException(
            status_code=400,
            detail="Either a 'transcript_file' or 'transcript_text' must be provided."
        )

    try:
        selected_outputs: List[str] = json.loads(selected_outputs_str)
        if not all(isinstance(item, str) for item in selected_outputs):
            raise ValueError("All items in selected_outputs must be strings.")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid format for selected_outputs. Expected a JSON list of strings. Error: {str(e)}"
        )

    if transcript_file:
        temp_file_path = None
        extracted_content = None

        try:

            file_extension = Path(transcript_file.filename).suffix if transcript_file.filename else ".tmp"

            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file_path = temp_file.name

                # Read the uploaded file's content (bytes) and write it to the temporary file
                content = await transcript_file.read()
                temp_file.write(content)
                temp_file.flush()

            extracted_content = extract_content(temp_file_path)

            if extracted_content is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Failed to extract text from file: {transcript_file.filename}. Check file integrity or ensure dependencies (pypdf, python-docx) are installed."
                )
            transcript_text = extracted_content

        except HTTPException as e:
            # Re-raise explicit HTTPExceptions (like the 422 above)
            raise HTTPException(
                status_code=422,
                detail=f"Error: {str(e)}"
            )
        except Exception as e:
            print(f"File extraction error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {str(e)}")
        finally:
            # CRITICAL: Clean up the temporary file from disk immediately
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    # Check if transcript_text is still empty after processing (applies if a file was uploaded but failed extraction)
    if not transcript_text:
        raise HTTPException(
            status_code=400,
            detail="Transcript content is empty after processing the file or was not provided."
        )

    try:
        output = ANALYZER.analyze(
            selected_outputs=selected_outputs,
            transcript_text=transcript_text
        )
        return AnalysisResult(output=output)
    except Exception as e:
        print(f"Core analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
