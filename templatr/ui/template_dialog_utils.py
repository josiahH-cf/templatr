"""Shared helpers for template generation/improvement dialogs."""

import re
from typing import Sequence, Set


def extract_template_content(text: str, *, tag_name: str) -> str:
    """Extract template content from a model response.

    The parser first looks for a named XML-like tag (for example,
    ``<generated_template>...</generated_template>``). If absent, it falls back
    to stripping markdown code-fence wrappers from the full response body.
    """
    pattern = rf"<{tag_name}>(.*?)</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    result = text.strip()
    if result.startswith("```"):
        lines = result.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        result = "\n".join(lines)

    return result


def is_connection_error(error: Exception) -> bool:
    """Return True if the exception represents a transient connection issue."""
    error_str = str(error).lower()
    return (
        isinstance(error, ConnectionError)
        or "cannot connect" in error_str
        or "connection refused" in error_str
        or "connection error" in error_str
    )


def extract_variables_from_content(content: str) -> Set[str]:
    """Extract variable names from ``{{variable_name}}`` placeholders."""
    pattern = r"\{\{\s*(\w+)\s*\}\}"
    matches = re.findall(pattern, content)
    return set(matches)


def sanitize_variable_name(raw_name: str) -> str:
    """Normalize user-entered variable names to lowercase ``[a-z0-9_]``."""
    return re.sub(r"[^a-zA-Z0-9_]", "", raw_name).lower()


def format_variable_warning(expected_variables: Sequence[str], content: str) -> str:
    """Return the missing/extra variable warning text for generated content.

    Returns an empty string when there is nothing to warn about.
    """
    if not expected_variables:
        return ""

    found_vars = extract_variables_from_content(content)
    expected_set = set(expected_variables)

    missing = expected_set - found_vars
    extra = found_vars - expected_set

    warnings = []
    if missing:
        warnings.append(f"Missing: {', '.join(sorted(missing))}")
    if extra:
        warnings.append(f"Extra: {', '.join(sorted(extra))}")

    return "; ".join(warnings)
