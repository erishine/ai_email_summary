# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does
A Python CLI tool that fetches emails from Gmail and summarises them using the Claude API (Haiku model). Built as a learning project exploring MCP and agentic AI patterns.

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
- `main.py` — entry point. `v2()` prompts for a freeform search request and hands off to `EmailSummaryWorkflow`.
- `email_summary_workflow.py` — `EmailSummaryWorkflow` class. Runs the agentic loop: sends all MCP tools to Claude Haiku, handles `tool_use` (parallel) and `stop_sequence` (`[DONE]`/`[QUESTION]`) responses. `_prepare_messages_for_api()` strips `get_emails` bodies from all but the most recent tool result in history (the last one is preserved for summarisation). Saves final summary to a timestamped file (`summary_YYYYMMDD_HHMMSS.md`).
- `gmail_mcp_client.py` — `GmailMcpClient` async context manager. Wraps the MCP session lifecycle; exposes `list_tools()` and `use_tool()`. Also has `fetch_labels()` (parses `Name:` lines from `list_available_labels`) but it is not currently called.
- `run_gmail_mcp_server.py` — one-liner that starts the `mcp-gmail` server as a subprocess (via `StdioServerParameters`).

### V2 agentic flow
1. User types a freeform search request (e.g. "last 5 unread emails")
2. `EmailSummaryWorkflow.start()` builds the system prompt (injects today's date and search request), fetches all MCP tools via `list_tools()`, enters the loop
3. Loop: `_prepare_messages_for_api()` strips email bodies from history → `messages.create` with `stop_sequences=["[DONE]", "[QUESTION]"]`
4. On `tool_use`: execute all tool_use blocks in parallel, append results tagged with `_tool_name` for later pruning, continue
5. On `[QUESTION]` stop sequence: append assistant message, collect user input, continue
6. On `[DONE]` stop sequence: break, write final response to `summary.md`

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
- MCP session kept open for entire run via `GmailMcpClient` async context manager
- All MCP tools passed to Claude as-is (no filtering); Claude selects which to call
- Tool result content accessed via `result.content[0].text`
- `_tool_name` is a private field tagged onto tool result dicts (not sent to API); `_prepare_messages_for_api()` uses it to identify and strip `get_emails` bodies from history — all except the most recent message, which is kept intact so Claude can summarise the email content
- Stop sequences `[DONE]` and `[QUESTION]` are used instead of relying on `stop_reason == "end_turn"` — gives Claude a structured way to signal completion or request user input mid-run
- Do NOT name any file `email.py` — shadows Python's built-in `email` module and breaks `mcp-gmail`
- `gmail_url` constructed as `https://mail.google.com/mail/u/0/#inbox/{message_id}` from the message ID
