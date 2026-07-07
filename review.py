import asyncio

import github_client
from agents.specialists import review_security, review_quality, review_tests
from agents.aggregator import format_markdown


async def review_pr(owner, repo, pr_number):
    diff = github_client.get_pr_diff(owner, repo, pr_number)
    results = await asyncio.gather(
        review_security(diff),
        review_quality(diff),
        review_tests(diff),
    )
    findings = [f for group in results for f in group]
    comment = format_markdown(findings)
    github_client.post_comment(owner, repo, pr_number, comment)
    return comment


if __name__ == "__main__":
    import sys

    asyncio.run(review_pr(sys.argv[1], sys.argv[2], int(sys.argv[3])))
