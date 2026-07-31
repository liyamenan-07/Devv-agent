"""Gemini native function-calling loop, isolated to one issue clone."""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import google.generativeai as genai

from app.agent.tools import AgentTools
from app.webhooks import IssueOpened

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are DevAgent, a careful autonomous software engineer. Work only on the reported issue.
Inspect relevant files before editing. Use read_file and write_file. Run tests after every meaningful edit.
If tests fail, diagnose and correct them; you have at most three failed test cycles. When tests pass,
call create_pull_request exactly once. Do not call tools outside this workflow and never expose secrets."""

TOOL_DECLARATIONS = [
    {"function_declarations": [
        {"name": "read_file", "description": "Read a UTF-8 file relative to the isolated repository.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
        {"name": "write_file", "description": "Create or replace a file relative to the isolated repository.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
        {"name": "run_tests", "description": "Run pytest or npm test and return output.", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
        {"name": "create_pull_request", "description": "Commit, push, and open a PR after tests pass.", "parameters": {"type": "object", "properties": {"branch_name": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}}, "required": ["branch_name", "title", "body"]}},
    ]}
]


class DevAgent:
    def __init__(self, settings):
        self.settings = settings

    async def handle_issue(self, issue: IssueOpened) -> None:
        await asyncio.to_thread(self._run, issue)

    def _run(self, issue: IssueOpened) -> None:
        with tempfile.TemporaryDirectory(prefix="devagent-") as temp_dir:
            workspace = Path(temp_dir) / "repo"
            # Git consumes the authorization header from its process environment,
            # keeping the token out of the remote URL and argument list.
            git_env = {
                **os.environ,
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.extraheader",
                "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: bearer {self.settings.github_token}",
            }
            repo_url = f"https://github.com/{issue.repository}.git"
            subprocess.run(["git", "clone", "--depth", "1", repo_url, str(workspace)], env=git_env, check=True, capture_output=True, text=True)
            subprocess.run(["git", "config", "user.name", "DevAgent"], cwd=workspace, env=git_env, check=True)
            subprocess.run(["git", "config", "user.email", "devagent@users.noreply.github.com"], cwd=workspace, env=git_env, check=True)
            base = subprocess.run(["git", "branch", "--show-current"], cwd=workspace, env=git_env, check=True, capture_output=True, text=True).stdout.strip() or "main"
            tools = AgentTools(workspace, self.settings.github_token, issue.repository, base, git_env)
            self._tool_loop(issue, tools)

    def _tool_loop(self, issue: IssueOpened, tools: AgentTools) -> None:
        genai.configure(api_key=self.settings.google_api_key)
        model = genai.GenerativeModel(self.settings.gemini_model, tools=TOOL_DECLARATIONS, system_instruction=SYSTEM_PROMPT)
        chat = model.start_chat(enable_automatic_function_calling=False)
        prompt = f"Repository: {issue.repository}\nIssue #{issue.number}: {issue.title}\nDescription:\n{issue.body}\nURL: {issue.html_url}"
        response = chat.send_message(prompt)
        failures = 0
        tests_passing = False
        for _ in range(30):
            calls = [p.function_call for p in response.candidates[0].content.parts if getattr(p, "function_call", None)]
            if not calls:
                logger.info("DevAgent stopped without another tool call for %s#%s", issue.repository, issue.number)
                return
            parts = []
            for call in calls:
                name, args = call.name, dict(call.args)
                if name == "run_tests":
                    result = tools.run_tests(**args)
                    tests_passing = "exit_code=0" in result
                    if not tests_passing:
                        failures += 1
                        if failures >= 3:
                            result += "\nSTOP: test retry limit reached; do not create a PR."
                elif name == "create_pull_request" and not tests_passing:
                    result = "ERROR: current changes have not passed tests; fix and run a passing test before opening a PR"
                else:
                    try:
                        result = getattr(tools, name)(**args)
                    except (AttributeError, OSError, subprocess.SubprocessError, ValueError) as exc:
                        result = f"ERROR: {type(exc).__name__}: {exc}"
                parts.append({"function_response": {"name": name, "response": {"result": result}}})
            response = chat.send_message(parts)
            if failures >= 3:
                return
        logger.warning("DevAgent reached tool-call safety limit for %s#%s", issue.repository, issue.number)
