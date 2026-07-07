import asyncio
import sys

import github_client
from agents.orchestrator import route_specialists
from agents.specialists import ReviewDeps, review_security, review_quality, review_tests
from agents.verifier import verify_findings
from agents.aggregator import format_markdown


async def review_pr_async(
    owner: str,
    repo: str,
    pr_number: int,
    diff: str = None,
    local_repo_path: str = None,
    post_to_github: bool = True,
) -> str:
    
    if diff is None:
        diff = github_client.get_pr_diff(owner, repo, pr_number)

    selected_specialists = await route_specialists(diff)

    if not selected_specialists:
        comment = format_markdown([])
        if post_to_github:
            github_client.post_comment(owner, repo, pr_number, comment)
        return comment

    async with github_client.github_mcp_session() as mcp_session:
        deps = ReviewDeps(
            mcp_session=mcp_session,
            local_repo_path=local_repo_path,
            owner=owner,
            repo=repo,
        )

        tasks = []
        if "security" in selected_specialists:
            tasks.append(review_security(diff, deps))
        if "quality" in selected_specialists:
            tasks.append(review_quality(diff, deps))
        if "tests" in selected_specialists:
            tasks.append(review_tests(diff, deps))

        results = await asyncio.gather(*tasks)

        all_findings = []
        for res in results:
            all_findings.extend(res.findings)

        verified_result = await verify_findings(diff, all_findings, deps)

    comment = format_markdown(verified_result.findings)

    if post_to_github:
        github_client.post_comment(owner, repo, pr_number, comment)

    return comment


def review_pr(owner: str, repo: str, pr_number: int):
    return asyncio.run(review_pr_async(owner, repo, pr_number))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python review.py <owner> <repo> <pr_number>")
        sys.exit(1)

    review_pr(sys.argv[1], sys.argv[2], int(sys.argv[3]))
