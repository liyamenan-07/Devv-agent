from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request, Response

from app.agent.core import DevAgent
from app.config import settings
from app.webhooks import parse_opened_issue, verify_github_signature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="DevAgent", version="1.0.0")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/github", status_code=202)
async def github_webhook(request: Request) -> Response:
    raw_body = await request.body()
    verify_github_signature(settings.github_webhook_secret, raw_body, request.headers.get("X-Hub-Signature-256"))
    if request.headers.get("X-GitHub-Event") != "issues":
        return Response(status_code=202)
    try:
        issue = parse_opened_issue(await request.json())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Webhooks must return quickly; each job has its own temporary clone/workspace.
    asyncio.create_task(DevAgent(settings).handle_issue(issue))
    logger.info("Queued DevAgent job for %s#%s", issue.repository, issue.number)
    return Response(status_code=202)
