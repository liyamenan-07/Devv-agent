"""GitHub event validation and small, explicit payload parser."""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from fastapi import HTTPException


@dataclass(frozen=True)
class IssueOpened:
    repository: str
    number: int
    title: str
    body: str
    html_url: str


def verify_github_signature(secret: str, raw_body: bytes, signature: str | None) -> None:
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing GitHub signature")
    expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")


def parse_opened_issue(payload: dict) -> IssueOpened:
    if payload.get("action") != "opened":
        raise ValueError("Only the opened action is eligible")
    issue = payload.get("issue") or {}
    repo = payload.get("repository") or {}
    full_name = repo.get("full_name")
    if not full_name or not issue.get("number") or not issue.get("title"):
        raise ValueError("Malformed issues payload")
    return IssueOpened(
        repository=full_name,
        number=int(issue["number"]),
        title=str(issue["title"]),
        body=str(issue.get("body") or ""),
        html_url=str(issue.get("html_url") or ""),
    )
