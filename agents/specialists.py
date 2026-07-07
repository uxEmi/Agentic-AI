import os
from dataclasses import dataclass
from typing import Optional
from mcp import ClientSession
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel

import config
from schemas import ReviewResult

model = AnthropicModel("claude-sonnet-5")


@dataclass
class ReviewDeps:
    mcp_session: Optional[ClientSession] = None
    local_repo_path: Optional[str] = None
    owner: str = ""
    repo: str = ""


async def read_file(ctx: RunContext[ReviewDeps], file_path: str) -> str:
    """Read the contents of a file from the repository to get full context.

    Args:
        file_path: The relative path of the file in the repository (e.g., 'src/main.py').
    """
    if ctx.deps.local_repo_path:
        try:
            full_path = os.path.join(ctx.deps.local_repo_path, file_path)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading local file: {e}"
    elif ctx.deps.mcp_session:
        try:
            res = await ctx.deps.mcp_session.call_tool(
                "get_file_contents",
                {
                    "owner": ctx.deps.owner,
                    "repo": ctx.deps.repo,
                    "path": file_path,
                },
            )
            if res.content and len(res.content) > 0:
                return res.content[0].text
            return "File is empty."
        except Exception as e:
            return f"Error reading file via MCP: {e}"
    return "Mock content: No context source available."


async def search_code(ctx: RunContext[ReviewDeps], query: str) -> str:
    """Search for code matching a query within the repository.

    Args:
        query: The code search query terms.
    """
    if ctx.deps.local_repo_path:
        return "Code search is not available in local mode. Use read_file with a specific path instead."
    if ctx.deps.mcp_session:
        try:
            search_q = f"repo:{ctx.deps.owner}/{ctx.deps.repo} {query}"
            res = await ctx.deps.mcp_session.call_tool(
                "search_code",
                {"q": search_q},
            )
            if res.content and len(res.content) > 0:
                return res.content[0].text
            return "No matches found."
        except Exception as e:
            return f"Error searching code via MCP: {e}"
    return "Mock content: Search code is only supported in live mode."


security_agent = Agent(
    model,
    deps_type=ReviewDeps,
    output_type=ReviewResult,
    system_prompt=(
        "You are an expert security code reviewer. Your job is to review the given git diff "
        "(and fetch additional context if needed) to identify security vulnerabilities. "
        "For each vulnerability found, emit a Finding with category 'security' and severity of 'critical', 'warning', or 'info'. "
        "Provide precise file paths and line numbers from the diff. "
        "Do not report style, performance, or quality issues that do not have security implications."
    ),
    tools=[read_file, search_code],
)

quality_agent = Agent(
    model,
    deps_type=ReviewDeps,
    output_type=ReviewResult,
    system_prompt=(
        "You are an expert code quality reviewer. Your job is to review the given git diff "
        "to identify style violations, anti-patterns, readability issues, code smell, structural design flaws, or performance bottlenecks. "
        "For each issue found, emit a Finding with category 'quality' and severity of 'critical' (for major bugs/performance issues), "
        "'warning' (for code smells/anti-patterns), or 'info' (for minor style improvements). "
        "Provide precise file paths and line numbers from the diff. "
        "Do not report security vulnerabilities or testing-only issues."
    ),
    tools=[read_file, search_code],
)

tests_agent = Agent(
    model,
    deps_type=ReviewDeps,
    output_type=ReviewResult,
    system_prompt=(
        "You are an expert testing and verification reviewer. Your job is to review the given git diff "
        "to identify missing unit tests, inadequate test coverage, weak assertions, incorrect mock setups, or testing-only anti-patterns. "
        "For each issue found, emit a Finding with category 'tests' and severity of 'critical' (for critical untested paths/broken tests), "
        "'warning' (for weak assertions/missing unit tests), or 'info' (for minor test improvements). "
        "Provide precise file paths and line numbers from the diff. "
        "Do not report security or general code quality issues."
    ),
    tools=[read_file, search_code],
)


async def review_security(diff: str, deps: ReviewDeps) -> ReviewResult:
    result = await security_agent.run(diff, deps=deps)
    return result.output


async def review_quality(diff: str, deps: ReviewDeps) -> ReviewResult:
    result = await quality_agent.run(diff, deps=deps)
    return result.output


async def review_tests(diff: str, deps: ReviewDeps) -> ReviewResult:
    result = await tests_agent.run(diff, deps=deps)
    return result.output
