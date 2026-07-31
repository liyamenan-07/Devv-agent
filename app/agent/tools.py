"""Local workspace and GitHub tools exposed to Gemini."""
from __future__ import annotations

import subprocess
from pathlib import Path

from github import Github


class AgentTools:
    def __init__(self, workspace: Path, github_token: str, repository: str, base_branch: str, git_env: dict[str, str]):
        self.workspace = workspace.resolve()
        self.github = Github(github_token)
        self.repository = repository
        self.base_branch = base_branch
        self.git_env = git_env

    def _path(self, requested_path: str) -> Path:
        candidate = (self.workspace / requested_path).resolve()
        if candidate != self.workspace and self.workspace not in candidate.parents:
            raise ValueError("Path escapes the isolated workspace")
        return candidate

    def read_file(self, path: str) -> str:
        target = self._path(path)
        if not target.is_file():
            return f"ERROR: {path} is not a readable file"
        return target.read_text(encoding="utf-8", errors="replace")

    def write_file(self, path: str, content: str) -> str:
        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {target.relative_to(self.workspace)}"

    def run_tests(self, command: str) -> str:
        # Tool-use models must not gain a general shell. Keep this deliberately narrow.
        allowed = ("pytest", "python -m pytest", "npm test", "npm run test")
        forbidden = (";", "&", "|", ">", "<", "`", "$", "\n", "\r")
        if not command.strip().startswith(allowed) or any(char in command for char in forbidden):
            return "ERROR: only pytest or npm test commands are permitted"
        result = subprocess.run(
            command, cwd=self.workspace, shell=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600,
        )
        output = result.stdout[-20_000:]
        return f"exit_code={result.returncode}\n{output}"

    def create_pull_request(self, branch_name: str, title: str, body: str) -> str:
        safe_branch = "devagent/" + "".join(c if c.isalnum() or c in "-_/" else "-" for c in branch_name).strip("/-")
        run = lambda args: subprocess.run(args, cwd=self.workspace, env=self.git_env, check=True, capture_output=True, text=True)
        run(["git", "checkout", "-b", safe_branch])
        run(["git", "add", "-A"])
        status = run(["git", "status", "--porcelain"]).stdout
        if not status.strip():
            return "ERROR: no changes to create a pull request from"
        run(["git", "commit", "-m", title[:72]])
        run(["git", "push", "origin", safe_branch])
        pr = self.github.get_repo(self.repository).create_pull(title=title, body=body, head=safe_branch, base=self.base_branch)
        return f"Created pull request: {pr.html_url}"
