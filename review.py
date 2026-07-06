import github_client
from agents.specialists import review_security
from agents.aggregator import format_markdown


def review_pr(owner, repo, pr_number):
    diff = github_client.get_pr_diff(owner, repo, pr_number)
    findings = review_security(diff)
    comment = format_markdown(findings)
    github_client.post_comment(owner, repo, pr_number, comment)
    return comment


if __name__ == "__main__":
    import sys

    review_pr(sys.argv[1], sys.argv[2], int(sys.argv[3]))
