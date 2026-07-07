from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

import config

model = AnthropicModel("claude-sonnet-5")

SpecialistName = Literal["security", "quality", "tests"]

orchestrator_agent = Agent(
    model,
    output_type=list[SpecialistName],
    system_prompt=(
        "You are a review orchestrator. Given a git diff, decide which specialist "
        "reviewers are relevant for it: 'security', 'quality', 'tests'. "
        "Return only the specialists worth running for this diff. "
        "If the diff is documentation-only or trivial, return an empty list. "
        "Run 'security' when the diff touches authentication, input handling, secrets, "
        "network calls, or data access. Run 'tests' when it changes logic that should be "
        "covered by tests or touches test files. Run 'quality' for non-trivial code changes. "
        "Prefer running a specialist when in doubt."
    ),
)


async def route_specialists(diff: str) -> list[str]:
    result = await orchestrator_agent.run(diff)
    return result.output
