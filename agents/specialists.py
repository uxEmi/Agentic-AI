from pydantic_ai import Agent

import config
from schemas import Finding

security_agent = Agent(
    "anthropic:claude-sonnet-5",
    output_type=list[Finding],
    system_prompt=(
        "You are a security code reviewer. Review the given git diff and report "
        "real security vulnerabilities as findings. For each finding set category "
        "to 'security' and a severity of low, medium, high, or critical. Use the "
        "file path and line number from the diff. Do not report style or "
        "non-security issues."
    ),
)


def review_security(diff):
    result = security_agent.run_sync(diff)
    return result.output
