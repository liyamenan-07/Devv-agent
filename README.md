# DevAgent
AI-powered GitHub engineering agent that automatically analyzes issues, generates code changes with Gemini, validates them through automated testing, and creates pull requests.

# Problem Statement

Modern software teams spend significant time triaging GitHub issues, implementing fixes, running tests, and creating pull requests manually. This repetitive workflow slows development and increases engineering effort.

DevAgent automates this process by listening to GitHub issue events, securely cloning repositories, using Gemini to generate code changes, validating them through automated tests, and creating pull requests only after successful verification.

---

# Features

- GitHub webhook integration
- Automated issue processing
- AI-powered code generation using Gemini
- Repository cloning in isolated temporary workspaces
- Automated test execution
- Retry mechanism for failed tests
- Automatic Pull Request creation
- HMAC webhook verification
- Secure filesystem sandbox
- FastAPI REST service
- Modular agent architecture
- Environment-based configuration

---

# Tech Stack

## Backend

- Python
- FastAPI

## AI

- Gemini 1.5 Pro

## Version Control

- Git
- GitHub API

## Testing

- Pytest

## Security

- HMAC SHA-256 Webhook Verification

## Tools

- GitHub Webhooks
- TemporaryDirectory
- REST APIs

---

# System Architecture

```text
GitHub Issue

↓

Webhook

↓

FastAPI

↓

Webhook Verification

↓

Repository Clone

↓

Gemini Agent

↓

File Editing

↓

Run Tests

↓

Retry Failed Tests

↓

Create Pull Request
```

---

# Technical Highlights

- Implemented secure GitHub webhook verification using HMAC SHA-256 signatures.
- Built an AI-powered engineering agent using Gemini function calling.
- Executed repository operations inside isolated temporary workspaces.
- Automated testing with retry logic before pull request creation.
- Restricted file operations to sandboxed project directories.
- Designed a modular architecture separating webhook handling, agent logic, and tooling.

---

# Performance

- Automated workflows reduce manual engineering effort.
- Temporary workspaces ensure clean execution environments.
- Retry logic minimizes failures due to transient test issues.
- Modular components allow independent scaling.

---

# Security

- HMAC webhook verification
- Secure GitHub token handling
- Filesystem sandbox restrictions
- Environment variable configuration
- Restricted command execution
- Temporary workspace cleanup

---

# Future Improvements

- Multi-agent collaboration
- Support multiple LLM providers
- GitHub App authentication
- Docker sandbox execution
- Persistent job queue
- CI/CD integration
- Parallel task execution
- Slack and Discord notifications

---

# License

This project is licensed under the MIT License.