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

**V1 (current)** — Python drives orchestration; Claude is used only for the final summarisation step.
**V2 (planned)** — fully agentic: Claude drives the Gmail tool calls directly, with natural language input and a confirmation step before fetching.

## Architecture (V1)

- `main.py` — async `main()` orchestration, prompt loop, user inputs, Claude API call
- `gmail_mcp_client.py` — `GmailMcpClient` async context manager. Manages the MCP session lifecycle via `__aenter__`/`__aexit__` and exposes `fetch_labels()`, `search_emails()`, `get_emails()`
- `my_email.py` — `MyEmail` dataclass. `from_mcp(email_id, email_data)` classmethod parses MCP response text into fields; `_clean_body()` strips URLs, footers, and boilerplate via regex
- `run_gmail_mcp_server.py` — one-liner that starts the `mcp-gmail` server; launched as a subprocess by `GmailMcpClient` via `StdioServerParameters`

Flow inside `main()`:
1. `GmailMcpClient` opens MCP session → `fetch_labels()` → `prompt_toolkit` autocomplete
2. Prompt for date range and email cap (with defaults), confirm before proceeding
3. `search_emails()` → list of message IDs
4. `get_emails([id])` called once per ID (single-item list) → `MyEmail.from_mcp()` builds one object per email
5. Assemble prompt: instructions header + per-email `Subject`/`Body` blocks, sliced at 400k chars
6. Send to Claude Haiku → print summary + save to `summary.md`

## MCP tool names (as registered on the server)
Full list: `compose_email`, `send_email`, `search_emails`, `query_emails`, `list_available_labels`, `mark_message_read`, `add_label_to_message`, `remove_label_from_message`, `get_emails`

Used in V1:
- `list_available_labels` — returns label list with `Name: <label>` lines
- `search_emails` — params: `label`, `after_date`, `before_date`, `max_results` (YYYY/MM/DD format)
- `get_emails` — params: `message_ids` (list); called with single-item list per email. Response text starts with headers (`From:`, `Subject:`, `Date:`) then a blank line then body

Resource templates (not tools): `get_email_message`, `get_email_thread` — accessible via `session.read_resource(f"gmail://messages/{id}")`

## Pipeline (agreed, partially implemented)
1. `list_available_labels` → label picker
2. User inputs date range + optional email cap
3. `search_emails` → email IDs
4. `get_emails` → raw bodies (one call, batch)
5. `clean_email()` — strip URLs, image refs, normalise whitespace (~52% token reduction)
6. Accumulate cleaned bodies, slice at 400k chars hard cap (silent truncation)
7. Send to Claude Haiku for summarisation

## User inputs and defaults
- `label` — `prompt_toolkit` autocomplete, no default
- `from_date` — default: today − 7 days (`YYYY/MM/DD`)
- `to_date` — default: today
- `max_emails` — default: 20

## Hard caps (not shown to user)
- `max_results=20` (or lower user value) passed to `search_emails`
- Cleaned content sliced at 400k chars (~100k tokens) before sending to Claude

## Token / cost notes
- ~52% token reduction after cleaning (88k chars raw → 41k chars)
- ~10 emails/run ≈ ~50k input tokens ≈ $0.04/run with Haiku 4.5
- Haiku 4.5 context: 200k tokens; planned input cap: ~100k tokens
- Rule of thumb: 4 chars ≈ 1 token

## Key technical decisions
- `asyncio` + MCP Python SDK (`mcp` v1.27.0) for Gmail calls — avoids routing through Anthropic
- `PromptSession.prompt_async()` required (not `prompt()`) — running inside an async event loop
- MCP session kept open for entire run via `GmailMcpClient` async context manager
- `get_emails` returns a `CallToolResult`; use `.content[0].text` for the text, `.model_dump()` to serialise to JSON
- `get_emails` called with a single-item list per email (not batched) — avoids fragile string splitting of concatenated responses
- Do NOT name any file `email.py` — shadows Python's built-in `email` module and breaks `mcp-gmail`
- `gmail_url` constructed as `https://mail.google.com/mail/u/0/#inbox/{message_id}` from the message ID
