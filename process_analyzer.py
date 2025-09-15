from pydantic import BaseModel
from typing import List, Optional

class AnalysisRequest(BaseModel):
    transcript_path: Optional[str] = None
    selected_outputs: List[str]  # E.g., ["summary", "bpmn", "process_description"]
    transcript_text: Optional[str] = None

class AnalysisResult(BaseModel):
    output: str
