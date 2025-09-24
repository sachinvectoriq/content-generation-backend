from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional
import json

from process_analyzer import AnalysisResult
from content_generation_core import ProcessAnalyzer
import os
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
        transcript_text: Optional[str] = Form(None)
):
    """
    Analyzes an uploaded transcript file or text based on selected outputs.
    """
    # 1. Validate that at least one input type is provided
    if not transcript_file and not transcript_text:
        raise HTTPException(
            status_code=400,
            detail="Either a 'transcript_file' or 'transcript_text' must be provided."
        )

    # 2. Parse the selected outputs string into a Python list
    try:
        selected_outputs: List[str] = json.loads(selected_outputs_str)
        if not all(isinstance(item, str) for item in selected_outputs):
            raise ValueError("All items in selected_outputs must be strings.")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid format for selected_outputs. Expected a JSON list of strings. Error: {str(e)}"
        )

    # 3. Handle the two different input types
    if transcript_file:
        # Read the uploaded file's content as bytes and then decode to a string
        try:
            transcript_bytes = await transcript_file.read()
            transcript_text = transcript_bytes.decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read and decode file: {str(e)}")

    # The transcript_text variable now holds the content, regardless of the input type

    # 4. Call the core logic
    try:
        output = ANALYZER.analyze(
            selected_outputs=selected_outputs,
            transcript_text=transcript_text
        )
        return AnalysisResult(output=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
