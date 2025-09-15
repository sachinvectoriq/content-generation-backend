from fastapi import FastAPI
from content_generation_prompts import router as prompt_router
from content_generation_api import router as analysis_router

app = FastAPI(title="Unified Content Generation and Analysis API")

app.include_router(prompt_router)
app.include_router(analysis_router)

