import os
import re
import json
from typing import List
from typing import Optional
import requests
import logging
from sasurldownload import download_file_from_blob
from prompt_repository import get_core_prompt, get_modular_prompts

logger = logging.getLogger("process_analysis_service")


class ProcessAnalyzer:
    def __init__(self, azure_api_key: str, azure_endpoint: str):
        self.azure_api_key = azure_api_key
        self.azure_endpoint = azure_endpoint
        self.max_tokens = 4000

    # This method is now simplified to only accept and process raw text
    def load_transcript(self, transcript_text: str) -> List[str]:
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

    # This method is now simplified to only accept transcript_text
    def analyze(self, selected_outputs: List[str], transcript_text: str) -> str:
        print("transcript_text:", transcript_text)

        transcript_lines = self.load_transcript(transcript_text=transcript_text)
        cleaned_lines = self.light_cleanup(transcript_lines)
        raw_text = " ".join(cleaned_lines)

        CORE_PROMPT = get_core_prompt()
        PROMPTS = get_modular_prompts(selected_outputs)

        deliverables_prompt = "\n".join([PROMPTS[o] for o in selected_outputs])
        final_prompt = (
                CORE_PROMPT
                + "\n\n-----------------------\nEXPECTED OUTPUTS\n-----------------------\n"
                + deliverables_prompt
        )

        full_prompt = final_prompt + f"\n\n---TRANSCRIPT START---\n{raw_text}\n---TRANSCRIPT END---"
        print(full_prompt)

        logger.info(f"Sending analysis prompt to LLM...{full_prompt}")
        return self.call_llm(full_prompt)
