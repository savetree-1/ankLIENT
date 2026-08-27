import re
from typing import List, Dict

def extract_variables(template: str) -> List[str]:
    """Finds all {{var}} placeholders."""
    matches = re.findall(r'\{\{([^}]+)\}\}', template)
    return [m.strip() for m in matches]

def render_template(template: str, variables: Dict[str, str]) -> str:
    """Replaces {{var}} with the provided values."""
    result = template
    for key, value in variables.items():
        # simple replacement
        result = re.sub(r'\{\{\s*' + re.escape(key) + r'\s*\}\}', value, result)
    return result
