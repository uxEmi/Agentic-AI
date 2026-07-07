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

quality_agent = Agent(
    "anthropic:claude-sonnet-5",
    output_type=list[Finding],
    system_prompt=(
        "You are a code quality reviewer. Review the given git diff and report "
        "real bugs, correctness problems, and maintainability or readability "
        "issues as findings. For each finding set category to 'quality' and a "
        "severity of low, medium, high, or critical. Use the file path and line "
        "number from the diff. Do not report security or test-coverage issues."
    ),
)

tests_agent = Agent(
    "anthropic:claude-sonnet-5",
    output_type=list[Finding],
    system_prompt=(
        "You are a test coverage reviewer. Review the given git diff and report "
        "changed code that lacks adequate test coverage as findings. For each "
        "finding set category to 'tests' and a severity of low, medium, high, or "
        "critical. Use the file path and line number from the diff. Do not report "
        "security or general quality issues."
    ),
)


async def review_security(diff):
    result = await security_agent.run(diff)
    return result.output


async def review_quality(diff):
    result = await quality_agent.run(diff)
    return result.output


async def review_tests(diff):
    result = await tests_agent.run(diff)
    return result.output
