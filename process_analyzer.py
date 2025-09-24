from pydantic import BaseModel
from typing import Optional

# This model is used to define the structure of the API's response.
class AnalysisResult(BaseModel):
    output: str
