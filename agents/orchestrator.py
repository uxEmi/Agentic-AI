import os
import re


def route_specialists(diff: str) -> list[str]:
    """Inspects the git diff and determines which specialist agents to run.

    If the changes are only documentation or non-code files, skips all specialists.
    """
    # Extract changed files from the diff
    # Matches 'diff --git a/path/to/file b/path/to/file'
    pattern = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)
    changed_files = [match.group(2) for match in pattern.finditer(diff)]

    if not changed_files:
        # Fallback check for '+++ b/file_path' lines
        fallback_pattern = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
        changed_files = [match.group(1).strip() for match in fallback_pattern.finditer(diff)]

    if not changed_files:
        # If we cannot parse any files, default to running all specialists to be safe
        return ["security", "quality", "tests"]

    # Non-code/documentation file extensions
    docs_extensions = {
        ".md",
        ".txt",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".pdf",
        ".gitignore",
        ".LICENSE",
        "license",
    }

    only_docs = True
    for file_path in changed_files:
        _, ext = os.path.splitext(file_path.lower())
        # If file doesn't have extension and is not license/gitignore, treat as code/config
        if ext not in docs_extensions and os.path.basename(file_path).lower() not in docs_extensions:
            only_docs = False
            break

    if only_docs:
        return []

    return ["security", "quality", "tests"]
