import hashlib
import hmac
import os
import sys

from fastapi import BackgroundTasks, FastAPI, Request, Response

from review import review_pr_async

app = FastAPI()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
MENTION = "@myagent"


def verify_signature(body: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        return True
    if not signature:
        return False
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def run_review(owner: str, repo: str, pr_number: int):
    try:
        await review_pr_async(owner, repo, pr_number)
    except Exception as e:
        print(f"Review failed for {owner}/{repo}#{pr_number}: {e}", file=sys.stderr)


@app.get("/")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(body, signature):
        return Response(status_code=401)

    if request.headers.get("X-GitHub-Event") != "issue_comment":
        return {"status": "ignored"}

    payload = await request.json()

    if payload.get("action") != "created":
        return {"status": "ignored"}

    issue = payload.get("issue", {})
    if "pull_request" not in issue:
        return {"status": "ignored"}

    comment_body = payload.get("comment", {}).get("body", "")
    if MENTION not in comment_body:
        return {"status": "ignored"}

    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    pr_number = issue["number"]

    background_tasks.add_task(run_review, owner, repo, pr_number)
    return {"status": "review_started", "pr": pr_number}
