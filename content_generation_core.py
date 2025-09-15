import os
import re
import json
from typing import List
from typing import Optional
import requests
import logging

logger = logging.getLogger("process_analysis_service")

class ProcessAnalyzer:
    def __init__(self, azure_api_key: str, azure_endpoint: str):
        #print(azure_endpoint,azure_api_key)
        self.azure_api_key = azure_api_key
        self.azure_endpoint = azure_endpoint
        self.max_tokens = 4000

    def load_transcript(self, file_path: Optional[str] = None, docx=None, transcript_text: Optional[str] = None) -> List[str]:
        # Load .txt, .docx, .pdf
        print(file_path,type(file_path),transcript_text)
        if (file_path != None):
            if file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f if line.strip()]
            elif file_path.endswith(".docx"):
                from docx import Document
                doc = Document(file_path)
                return [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            elif file_path.endswith(".pdf"):
                import pdfplumber
                lines = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            lines.extend([l.strip() for l in text.splitlines() if l.strip()])
                return lines
            else:
                raise ValueError("Unsupported file format.")
        else:
            return [line.strip() for line in transcript_text.splitlines() if line.strip()]

    def light_cleanup(self, transcript_lines: List[str]) -> List[str]:
        cleaned = []
        for line in transcript_lines:
            if ":" in line:
                _, utterance = line.split(":", 1)
            else:
                utterance = line
            utterance = re.sub(r"\[\d{2}:\d{2}(?::\d{2})?\]", "", utterance).strip()
            utterance = re.sub(r"\s+", " ", utterance).strip()
            if utterance:
                cleaned.append(utterance)
        return cleaned

    def call_llm(self, prompt: str) -> str:
        headers = {"api-key": self.azure_api_key, "Content-Type": "application/json"}
        body = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": 0.0
        }
        response = requests.post(self.azure_endpoint, headers=headers, json=body)
        if not response.ok:
            logger.error(f"Azure API call failed: {response.status_code} {response.text}")
            raise Exception(f"Azure API Error: {response.text}")

        return response.json()['choices'][0]['message']['content']

    def analyze(self, transcript_path: Optional[str], selected_outputs: List[str], transcript_text: Optional[str] = None) -> str:
        print("transcript path:",transcript_path,type(transcript_path),"transcript_text:",transcript_text)
        if (transcript_path != None):
            transcript_lines = self.load_transcript(transcript_path)
            cleaned_lines = self.light_cleanup(transcript_lines)
            raw_text = " ".join(cleaned_lines)

            from prompt_repository import get_core_prompt,get_modular_prompts   # Ideally stored in DB or config
            CORE_PROMPT=get_core_prompt()
            PROMPTS=get_modular_prompts(selected_outputs)

            deliverables_prompt = "\n".join([PROMPTS[o] for o in selected_outputs])
            final_prompt = (
                CORE_PROMPT
                + "\n\n-----------------------\nEXPECTED OUTPUTS\n-----------------------\n"
                + deliverables_prompt
            )

            full_prompt = final_prompt + f"\n\n---TRANSCRIPT START---\n{raw_text}\n---TRANSCRIPT END---"

            logger.info("Sending analysis prompt to LLM...")
            return self.call_llm(full_prompt)
        elif (transcript_text != None):
            transcript_lines = self.load_transcript(transcript_text=transcript_text)
            cleaned_lines = self.light_cleanup(transcript_lines)
            raw_text = " ".join(cleaned_lines)

            from prompt_repository import get_core_prompt, get_modular_prompts  # Ideally stored in DB or config
            CORE_PROMPT = get_core_prompt()
            PROMPTS = get_modular_prompts(selected_outputs)

            deliverables_prompt = "\n".join([PROMPTS[o] for o in selected_outputs])
            final_prompt = (
                    CORE_PROMPT
                    + "\n\n-----------------------\nEXPECTED OUTPUTS\n-----------------------\n"
                    + deliverables_prompt
            )

            full_prompt = final_prompt + f"\n\n---TRANSCRIPT START---\n{raw_text}\n---TRANSCRIPT END---"

            logger.info("Sending analysis prompt to LLM...")
            return self.call_llm(full_prompt)

