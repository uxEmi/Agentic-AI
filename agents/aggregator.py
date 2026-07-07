from schemas import Finding

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "warning": 2,
    "medium": 3,
    "low": 4,
    "info": 5,
}


def format_markdown(findings: list[Finding]) -> str:
    """Concatenates, dedupes, sorts findings by severity, and formats to markdown."""
    if not findings:
        return "## PR Review\n\nNo issues found."

    seen = set()
    deduped = []
    for f in findings:
        key = (f.file, f.line, f.message.strip())
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    def sort_key(f: Finding):
        sev_val = SEVERITY_ORDER.get(f.severity.lower(), 99)
        line_val = f.line if f.line is not None else -1
        return (sev_val, f.file, line_val)

    ordered = sorted(deduped, key=sort_key)

    lines = ["## PR Review", "", f"Found {len(ordered)} issue(s):", ""]
    for f in ordered:
        line_str = f"L{f.line}" if f.line is not None else "File-level"
        lines.append(f"- **[{f.severity.upper()}]** `{f.file}:{line_str}` ({f.category}) — {f.message}")

    return "\n".join(lines)
