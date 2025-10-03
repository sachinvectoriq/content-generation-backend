from pydantic import BaseModel
from typing import Optional, Dict, Any

# This model is used to define the structure of the API's response.
class AnalysisResult(BaseModel):
    output: Dict[str, Any]
