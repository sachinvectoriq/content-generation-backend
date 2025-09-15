from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from typing import Optional
from fastapi import APIRouter


from process_analyzer import AnalysisRequest, AnalysisResult
from content_generation_core import ProcessAnalyzer

load_dotenv()


router = APIRouter()
ANALYZER = ProcessAnalyzer(
    azure_api_key=os.getenv("Azure_Open_api_key"),
    azure_endpoint=os.getenv("Alta_Azure_end_point")
)
print(os.getenv("Azure_Open_api_key"),os.getenv("Alta_Azure_end_point"))
@router.post("/analyze")
def analyze_process(request: AnalysisRequest):
    try:
        output = ANALYZER.analyze(
            transcript_path=request.transcript_path,
            selected_outputs=request.selected_outputs,
            transcript_text=request.transcript_text
        )
        return AnalysisResult(output=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("content_generation_api:app", host="0.0.0.0", port=8001, reload=True)
