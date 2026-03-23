from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict | list:
    """Extract JSON from a Claude response that may contain markdown code blocks."""
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code blocks
    for pattern in [
        r"```json\s*\n(.*?)\n\s*```",
        r"```json\s*(.*?)```",
        r"```\s*\n(.*?)\n\s*```",
        r"```\s*(.*?)```",
    ]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    # Find first { or [ and try parsing from there
    for start_char in ["{", "["]:
        idx = text.find(start_char)
        if idx == -1:
            continue
        # Try parsing from this position — json.loads will stop at the right place
        # Try increasingly large substrings from the end
        for end_idx in range(len(text), idx, -1):
            candidate = text[idx:end_idx].rstrip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract JSON from response: {text[:200]}...")
