# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does
A Python CLI tool that fetches emails from Gmail by label and summarises them using the Claude API (Haiku model). Built as a learning project exploring MCP and agentic AI patterns.

## Commands

```bash
# Run the app
source .venv/bin/activate
python main.py

# Debug MCP tools via inspector
npx @modelcontextprotocol/inspector .venv/bin/python run_gmail_mcp_server.py

# If inspector ports are in use
lsof -ti :6277,:6274 | xargs kill
```

## Environment
Requires a `.env` file with `ANTHROPIC_API_KEY`. Gmail OAuth credentials are stored in `credentials.json` + `token.json` (project root, or set `MCP_GMAIL_CREDENTIALS_PATH` / `MCP_GMAIL_TOKEN_PATH`).

## Versions

**V1 (complete, branch: `version_1`)** — Python drives orchestration; Claude is used only for the final summarisation step. Entry point: `main()` in `main.py`.
**V2 (current, branch: `agentic_version`)** — fully agentic: Claude drives Gmail tool calls directly in a loop via the Anthropic tools API. Entry point: `v2()` in `main.py`.

## Architecture

### Files
- `main.py` — entry points for both versions. `v2()` is the active one: collects label + freeform search request from the user, then hands off to `EmailSummaryWorkflow`. `main()` is the V1 flow (kept for reference).
- `email_summary_workflow.py` — `EmailSummaryWorkflow` class (V2). Runs the agentic loop: sends all MCP tools to Claude Haiku, then iterates `messages.create` → call MCP tool → append result until `stop_reason != "tool_use"`. Saves final summary to `summary.md`.
- `gmail_mcp_client.py` — `GmailMcpClient` async context manager. Wraps the MCP session lifecycle and exposes: `fetch_labels()`, `search_emails()`, `get_emails()`, `get_email_message()`, `list_tools()`, `use_tool()`.
- `my_email.py` — `MyEmail` dataclass used in V1. `from_mcp()` parses MCP response; `_clean_body()` strips URLs/footers via regex (~52% token reduction).
- `run_gmail_mcp_server.py` — one-liner that starts the `mcp-gmail` server as a subprocess (via `StdioServerParameters`).

### V2 agentic flow
1. `GmailMcpClient` opens MCP session → `fetch_labels()` → `prompt_toolkit` autocomplete for label selection
2. User types a freeform search request (e.g. "last 5 unread emails")
3. `EmailSummaryWorkflow.start()` builds the system prompt (injects today's date, label, and request), fetches all available MCP tools via `list_tools()`, then enters the tool-use loop
4. Loop: `messages.create` → if `stop_reason == "tool_use"`, call the MCP tool, append assistant + tool_result messages, repeat
5. Final text response is printed and written to `summary.md`

### MCP tool names (as registered on the server)
Full list: `compose_email`, `send_email`, `search_emails`, `query_emails`, `list_available_labels`, `mark_message_read`, `add_label_to_message`, `remove_label_from_message`, `get_emails`

Key tools:
- `list_available_labels` — returns `Name: <label>` lines
- `search_emails` — params: `label`, `after_date`, `before_date`, `max_results` (YYYY/MM/DD)
- `get_emails` — params: `message_ids` (list)

Resource templates (not tools, used in V1): accessible via `session.read_resource(f"gmail://messages/{id}")`

## Token / cost notes (V1 reference)
- ~52% token reduction after cleaning (88k chars raw → 41k chars)
- ~10 emails/run ≈ ~50k input tokens ≈ $0.04/run with Haiku 4.5
- Rule of thumb: 4 chars ≈ 1 token

## Key technical decisions
- `asyncio` + MCP Python SDK (`mcp` v1.27.0) for Gmail calls — avoids routing through Anthropic
- `PromptSession.prompt_async()` required (not `prompt()`) — running inside an async event loop
- MCP session kept open for entire run via `GmailMcpClient` async context manager
- In V2, `EmailSummaryWorkflow` passes all MCP tools to Claude as-is (no filtering); Claude selects which to call
- Tool result content accessed via `result.content[0].text`; email bodies must be cleared from the messages list before re-sending to Claude to reduce token usage (known TODO as of last commit)
- Do NOT name any file `email.py` — shadows Python's built-in `email` module and breaks `mcp-gmail`
- `gmail_url` constructed as `https://mail.google.com/mail/u/0/#inbox/{message_id}` from the message ID
