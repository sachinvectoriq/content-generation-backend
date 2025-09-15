import os
import psycopg2
import psycopg2.extras
import logging
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "settings_db"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

logger = logging.getLogger("prompt_repository")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)


def _get_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise Exception("Failed to connect to database.")


def get_core_prompt() -> str:
    """
    Fetch the core prompt (prompt_id = 0).
    """
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("SELECT content FROM content_generation_prompts WHERE prompt_id = 0;")
        result = cur.fetchone()

        if not result:
            logger.error("Core prompt with prompt_id=0 not found in DB.")
            raise Exception("Core prompt (prompt_id=0) not found.")

        return result[0]

    except psycopg2.Error as e:
        logger.error(f"Database query error while fetching core prompt: {str(e)}")
        raise Exception("Error querying database for core prompt.")

    finally:
        try:
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Error closing database connection: {str(e)}")


def get_modular_prompts(selected_names: List[str]) -> Dict[str, str]:
    """
    Fetch modular prompts filtered by their names (list of names).
    Returns: {name: content}
    """
    if not selected_names:
        return {}

    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
            SELECT name, content FROM content_generation_prompts
            WHERE name = ANY(%s) AND prompt_id != 0;
        """, (selected_names,))

        rows = cur.fetchall()
        if not rows:
            logger.warning(f"No matching modular prompts found for names: {selected_names}")
            return {}

        return {row["name"]: row["content"] for row in rows}

    except psycopg2.Error as e:
        logger.error(f"Database query error while fetching modular prompts: {str(e)}")
        raise Exception("Error querying database for modular prompts.")

    finally:
        try:
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Error closing database connection: {str(e)}")