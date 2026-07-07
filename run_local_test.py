import asyncio
import os
import sys

# Ensure project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from review import review_pr_async


async def main():
    diff_path = "tests/sample_diff.txt"
    local_repo = "tests/mock_repo"

    if not os.path.exists(diff_path):
        print(f"Error: Diff file not found at {diff_path}")
        return

    print("Reading sample diff...")
    with open(diff_path, "r", encoding="utf-8") as f:
        diff_content = f.read()

    print("Running multi-agent PR review locally (post_to_github=False)...")
    try:
        comment = await review_pr_async(
            owner="mock_owner",
            repo="mock_repo",
            pr_number=1,
            diff=diff_content,
            local_repo_path=local_repo,
            post_to_github=False,
        )

        print("\n=== Review Markdown Comment ===")
        print(comment)
        print("===============================")
    except Exception as e:
        print(f"\nExecution failed: {e}")
        print("\nEnsure that you have set valid keys in your .env file.")


if __name__ == "__main__":
    asyncio.run(main())
