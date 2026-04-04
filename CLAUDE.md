# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does
A Python CLI tool that fetches newsletter emails from Gmail by label and summarises them using the Claude API (Haiku model).

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

## Architecture

`main.py` is the entire application — one async `main()` function that opens an MCP `ClientSession` and keeps it open for all tool calls. `run_gmail_mcp_server.py` is a one-liner that starts the `mcp-gmail` server; it's launched as a subprocess by `main.py` via `StdioServerParameters`.

Flow inside `main()`:
1. Open MCP session → call `list_available_labels` → `prompt_toolkit` autocomplete for label selection
2. Prompt for date range and email cap (with defaults)
3. Call `search_emails` → parse `Message ID:` lines from response text
4. Call `get_emails` with the list of IDs → raw email content returned

**Not yet implemented:** `clean_email()`, token-capping, and sending to Claude Haiku. The old Anthropic client code is still in `main.py` as a commented-out block at the bottom.

## MCP tool names (as registered on the server)
- `list_available_labels` — returns label list with `Name: <label>` lines
- `search_emails` — params: `label`, `after_date`, `before_date`, `max_results` (YYYY/MM/DD format)
- `get_emails` — params: `message_ids` (list)

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
- MCP session kept open for entire run; all tool calls reuse it
