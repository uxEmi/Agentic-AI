from schemas import Finding

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _dedupe(findings):
    best = {}
    for f in findings:
        key = (f.file, f.line)
        if key not in best or SEVERITY_ORDER.get(f.severity, 99) < SEVERITY_ORDER.get(best[key].severity, 99):
            best[key] = f
    return list(best.values())


def format_markdown(findings):
    if not findings:
        return "## PR Review\n\nNo issues found."

    deduped = _dedupe(findings)
    ordered = sorted(deduped, key=lambda f: SEVERITY_ORDER.get(f.severity, 99))

    lines = ["## PR Review", "", f"Found {len(ordered)} issue(s):", ""]
    for f in ordered:
        lines.append(f"- **{f.severity.upper()}** `{f.file}:{f.line}` — {f.message}")
    return "\n".join(lines)
