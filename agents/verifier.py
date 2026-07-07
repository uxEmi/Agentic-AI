import json
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

import config
from schemas import ReviewResult, Finding
from agents.specialists import ReviewDeps, read_file

# Initialize the model. Since config.py loads the env variables, AnthropicModel will automatically pick up ANTHROPIC_API_KEY.
model = AnthropicModel("claude-3-5-sonnet-latest")

# Verifier Agent definition
verifier_agent = Agent(
    model,
    deps_type=ReviewDeps,
    output_type=ReviewResult,
    system_prompt=(
        "You are an expert evaluator and reflexion agent. Your job is to verify a set of "
        "proposed findings (issues found during a code review) against the actual code. "
        "You will receive the git diff and a list of proposed findings. "
        "For each finding, you MUST check the cited file using the `read_file` tool to inspect "
        "the actual code at the cited line number. "
        "Keep only findings that are fully grounded in the actual code and represent a real issue. "
        "If a proposed finding is a hallucination (the code doesn't contain the issue described, "
        "or the cited line number/file doesn't exist, or the finding is a false positive), discard it. "
        "Do not invent new findings."
    ),
    tools=[read_file],
)


async def verify_findings(diff: str, findings: list[Finding], deps: ReviewDeps) -> ReviewResult:
    """Evaluates the proposed findings, checking them against source code, and filters hallucinations."""
    if not findings:
        return ReviewResult(findings=[])

    findings_data = [f.model_dump() for f in findings]
    findings_json = json.dumps(findings_data, indent=2)

    prompt = (
        f"Git Diff:\n{diff}\n\n"
        f"Proposed Findings to Verify:\n{findings_json}\n\n"
        "Verify each proposed finding against the actual repository files using the `read_file` tool. "
        "Return the verified list of findings."
    )

    result = await verifier_agent.run(prompt, deps=deps)
    return result.data
