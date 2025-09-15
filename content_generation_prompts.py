import os
import psycopg2
import psycopg2.extras
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
from fastapi import APIRouter

# -------------------------------
# Load ENV
# -------------------------------
load_dotenv()

# -------------------------------
# Logging Config
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("prompt_api")

# -------------------------------
# DB Config
# -------------------------------
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "settings_db"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

# -------------------------------
# Data Models
# -------------------------------
class Prompt(BaseModel):
    prompt_id: int
    name: str
    description: Optional[str]
    content: str
    updated_at: Optional[datetime]

class PromptCreate(BaseModel):
    name: str
    description: Optional[str]
    content: str

class PromptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None

# -------------------------------
# Repository Class
# -------------------------------
class PromptOperation:
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_conn(self):
        return psycopg2.connect(**self.db_config)

    def get_all(self) -> List[Prompt]:
        try:
            conn = self._get_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT prompt_id, name, description, content, updated_at 
                FROM content_generation_prompts
                ORDER BY prompt_id;
            """)
            rows = cur.fetchall()
            return [Prompt(**row) for row in rows]
        except Exception as e:
            logger.error("Error fetching prompts: %s", str(e))
            raise
        finally:
            cur.close()
            conn.close()

    def create(self, prompt: PromptCreate) -> Prompt:
        try:
            conn = self._get_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute("""
                INSERT INTO content_generation_prompts (name, description, content)
                VALUES (%s, %s, %s)
                RETURNING prompt_id, name, description, content, updated_at;
            """, (prompt.name, prompt.description, prompt.content))

            new_prompt = cur.fetchone()
            conn.commit()
            return Prompt(**new_prompt)
        except Exception as e:
            logger.error("Error creating prompt: %s", str(e))
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def delete(self, prompt_id: int):
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM content_generation_prompts WHERE prompt_id = %s;", (prompt_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Prompt not found")
            conn.commit()
        except Exception as e:
            logger.error("Error deleting prompt: %s", str(e))
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def update(self, prompt_id: int, prompt_update: PromptUpdate) -> Prompt:
        try:
            conn = self._get_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Build dynamic SET clause
            update_fields = []
            values = []

            if prompt_update.name is not None:
                update_fields.append("name = %s")
                values.append(prompt_update.name)
            if prompt_update.description is not None:
                update_fields.append("description = %s")
                values.append(prompt_update.description)
            if prompt_update.content is not None:
                update_fields.append("content = %s")
                values.append(prompt_update.content)

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields provided for update.")

            values.append(prompt_id)  # For WHERE clause

            update_query = f"""
                UPDATE content_generation_prompts
                SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE prompt_id = %s
                RETURNING prompt_id, name, description, content, updated_at;
            """

            cur.execute(update_query, values)
            updated_prompt = cur.fetchone()

            if not updated_prompt:
                raise HTTPException(status_code=404, detail="Prompt not found.")

            conn.commit()
            return Prompt(**updated_prompt)

        except Exception as e:
            logger.error(f"Error updating prompt {prompt_id}: {str(e)}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

# -------------------------------
# FastAPI App
# -------------------------------
from fastapi import APIRouter

router = APIRouter()

repo = PromptOperation(DB_CONFIG)

@router.get("/prompts")
def get_prompts(request: Request):
    user = request.headers.get("X-User", "system")
    logger.info("GET /prompts triggered by %s", user)
    try:
        return repo.get_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompts", response_model=Prompt)
def add_prompt(prompt: PromptCreate, request: Request):
    user = request.headers.get("X-User", "system")
    logger.info("POST /prompts triggered by %s", user)
    try:
        return repo.create(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/prompts/{prompt_id}")
def delete_prompt(prompt_id: int, request: Request):
    user = request.headers.get("X-User", "system")
    logger.info("DELETE /prompts/%d triggered by %s", prompt_id, user)
    try:
        repo.delete(prompt_id)
        return {"message": f"Prompt {prompt_id} deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/prompts/{prompt_id}", response_model=Prompt)
def update_prompt(prompt_id: int, prompt_update: PromptUpdate, request: Request):
    user = request.headers.get("X-User", "system")
    logger.info(f"PATCH /prompts/{prompt_id} triggered by {user}")
    try:
        return repo.update(prompt_id, prompt_update)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("content_generation_prompts:app", host="0.0.0.0", port=8001, reload=True)
