import re

def extract_code_block(content: str, language: str) -> str: 
    try:
        match = re.search(rf'```{language}(.*?)```', content, re.DOTALL)
        extracted_code = match.group(1)
    except Exception:
        extracted_code = content.replace(f"```{language}", "")

    return extracted_code
