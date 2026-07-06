from schemas import Finding

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def format_markdown(findings):
    if not findings:
        return "## 🤖 PR Review\n\nNo issues found."

    ordered = sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 99))

    lines = ["## 🤖 PR Review", "", f"Found {len(ordered)} issue(s):", ""]
    for f in ordered:
        lines.append(f"- **{f.severity.upper()}** `{f.file}:{f.line}` — {f.message}")
    return "\n".join(lines)
