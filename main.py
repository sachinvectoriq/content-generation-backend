from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from content_generation_prompts import router as prompt_router
from content_generation_api import router as analysis_router

app = FastAPI(title="Unified Content Generation and Analysis API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 2. Add the CORSMiddleware to the main app instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Apply the list of allowed origins
    allow_credentials=True,         # Allows cookies/authorization headers
    allow_methods=["*"],            # Allows all HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],            # Allows all headers, including custom ones like Authorization
)

# --- ADD THE CATCH-ALL OPTIONS HANDLER ---
# This must be defined on the main app instance.
@app.options("/{path:path}")
async def catch_all_options(_: str):
    """
    Handles all OPTIONS preflight requests globally.
    """
    return Response(status_code=200)

app.include_router(prompt_router)
app.include_router(analysis_router)

# Example of a simple root endpoint
@app.get("/")
async def root():
    return {"message": "API is online with CORS configured"}
