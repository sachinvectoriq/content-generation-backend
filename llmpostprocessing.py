import re
import json
from typing import Dict, Any
import logging

# Set up basic logging (optional, but good practice)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Heuristic Regex: Used to detect Synthesia Media Mapping (looks for [time – time])
# This is used to distinguish the two plain-text blocks: script vs. media mapping.
MEDIA_MAPPING_HEURISTIC = re.compile(r"\[\s*\d{1,2}:\d{2}\s*–\s*\d{1,2}:\d{2}\s*\]", re.DOTALL)


# ----------------------------------------------------------------------
# HELPER FUNCTION
# ----------------------------------------------------------------------

def clean_json_string(s: str) -> str:
    """
    Performs minor cleanup on JSON string content to handle common LLM formatting flaws
    (e.g., trailing commas, unnecessary escape sequences) before attempting parsing.
    """
    s = s.strip()

    # Robustly remove a trailing comma right before the final brace or bracket
    # This addresses a common LLM error where a trailing comma is placed before the final bracket/brace.
    if (s.endswith('},') and s.count('{') > s.count('}')) or \
            (s.endswith('],') and s.count('[') > s.count(']')):
        # Remove the comma but keep the brace/bracket
        s = s[:-2] + s[-1]

    # Clean up double backslashes often introduced by LLMs
    s = s.replace('\\\\', '\\')
    return s


# ----------------------------------------------------------------------
# CORE PARSING FUNCTION
# ----------------------------------------------------------------------

def parse_llm_output(llm_output_string: str) -> Dict[str, Any]:
    """
    Parses the raw LLM output using structure-based identification. This is resilient
    to missing blocks and handles any permutation of the five deliverables. It identifies
    each block by its language tag and unique content structure (e.g., JSON root keys).

    Args:
        llm_output_string: The raw output string from the LLM.

    Returns:
        A dictionary mapping extracted content to standardized keys.
    """

    # 1. Define the Robust Regex for capturing blocks.
    # Pattern is robust: tolerates missing 'eof' and case variation in tags.
    pattern = re.compile(
        # ^```(\w*)   -> Match start fence and capture optional language tag
        # ([\s\S]*?)  -> Capture the content (non-greedy, multi-line)
        # \n```(?:eof)?$ -> Match closing fence, optionally followed by 'eof'
        r"^```(\w*)\s*([\s\S]*?)\n```(?:eof)?$",
        re.MULTILINE | re.IGNORECASE
    )

    matches = pattern.findall(llm_output_string)
    output_data: Dict[str, Any] = {}

    if not matches:
        logger.error("Error: No fenced code blocks found in the LLM output.")
        return {}

    # 2. Iterate and map based on structure (Tag + Content Check)
    for i, (tag, content) in enumerate(matches):

        key = None
        content = content.strip()

        # 2a. Handle JSON Blocks (Identified by internal root keys)
        if tag.lower() == 'json':
            try:
                cleaned_content = clean_json_string(content)
                parsed_json = json.loads(cleaned_content)

                # Use unique root keys for reliable JSON block identification
                if "summary_table" in parsed_json:
                    key = 'summary_table'
                elif "process_description" in parsed_json:
                    key = 'process_description'

                if key:
                    output_data[key] = parsed_json
                else:
                    logger.warning(f"Unrecognized JSON structure found in block #{i + 1}. Skipping.")

            except json.JSONDecodeError as e:
                logger.error(
                    f"Error decoding JSON in block #{i + 1} (Tag: {tag}, Content Start: {content[:30]}). Error: {e}")

        # 2b. Handle XML Blocks (Always BPMN Diagram)
        elif tag.lower() == 'xml' or content.startswith('<definitions'):
            key = 'bpmn_diagram'
            output_data[key] = content

        # 2c. Handle TEXT Blocks (Distinguished by heuristic)
        elif tag.lower() == 'text' or tag.lower() == 'plain':
            # Check for timestamp pattern to identify media mapping
            if MEDIA_MAPPING_HEURISTIC.search(content):
                key = 'media_mapping'
            else:
                # Default plain text that is not a media mapping is the script
                key = 'synthesia_script'
            output_data[key] = content

        else:
            logger.warning(f"Found unknown content block with tag '{tag}' at position #{i + 1}. Skipping.")

    return output_data

if __name__ == "__main__":
    mock_input=input("provide the llm reponse as string")
    print("--- Parsing Mock LLM Output (Variable Blocks Test) ---")
    parsed_result = parse_llm_output(mock_input)

    print("\n--- Parsed Python Dictionary Structure ---", parsed_result)
    if parsed_result:
        for key, value in parsed_result.items():
            value_type = type(value).__name__
            snippet = str(value)[:50].replace('\n', ' ')
            print(f"[{key:<20}] Type: {value_type:<10} | Content snippet: {snippet}...")
    else:
        print("Parsing failed or no content extracted.")