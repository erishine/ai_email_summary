# AI Newsletter Summary — Project Context

## What this project does
A Python CLI tool that fetches newsletter emails from Gmail by label and summarises them using the Claude API (Haiku model).

## Current state
- Gmail OAuth authenticated (`credentials.json` + `token.json` present)
- MCP Gmail server working — run with:
  ```bash
  npx @modelcontextprotocol/inspector .venv/bin/python run_gmail_mcp_server.py
  ```
- If inspector ports are in use: `lsof -ti :6277,:6274 | xargs kill`
- `main.py` has: async MCP client setup, label fetching, `prompt_toolkit` autocomplete for label selection
- Old Anthropic placeholder code is commented out at the bottom of `main.py`

## Pipeline (agreed, not yet fully implemented)
1. `list_available_labels` → fetch labels, user picks one via `prompt_toolkit` autocomplete
2. User inputs date range and optional email cap (with defaults)
3. `search_emails` (MCP tool) → returns email IDs + metadata, filtered by label and date
4. Read tool (exact name TBC — check inspector, likely `get_email` or `read_message`) → called once per email ID to get body
5. `clean_email()` — strip URLs, image references, normalise whitespace (~52% token reduction observed)
6. Accumulate cleaned bodies, slice at hard token cap before sending to Claude
7. Send to Claude Haiku for summarisation

## User inputs and defaults
- `label` — selected via `prompt_toolkit` autocomplete (no default)
- `from_date` — default: today minus 7 days (format: YYYY/MM/DD for `search_emails`)
- `to_date` — default: today
- `max_emails` — default: 20, user can override

## Hard caps (non-negotiable, not shown to user)
- `max_results=20` passed to `search_emails` (or user value if lower)
- Cleaned email content sliced at 400k chars (~100k tokens) before sending to Claude
- No warning shown when cap is hit — silent truncation for now

## Token / cost notes
- 3 sample emails = ~88k chars raw → ~41k chars cleaned (~22k → ~10k tokens, 52% reduction)
- Expected ~10 emails per run ≈ ~50k input tokens
- Cost: ~$0.04/run with Haiku 4.5 ($0.80/1M tokens)
- Haiku 4.5 context window: 200k tokens
- Planned cap: ~100k tokens input (400k chars) as a safeguard
- Token estimate rule of thumb: 4 chars ≈ 1 token

## Key technical decisions
- Using `asyncio` + MCP Python SDK (`mcp` package v1.27.0) to call Gmail MCP tools directly — avoids going through Anthropic for the Gmail calls
- `prompt_toolkit` for label autocomplete (`PromptSession.prompt_async()` required — not `prompt()` — because we're inside an async event loop)
- MCP server name in code: `list_available_labels` (not `gmail_list_labels`)
- Keep the MCP `session` open for the entire run — reuse it for all tool calls

## Dependencies
- `anthropic`
- `python-dotenv`
- `mcp-gmail`
- `prompt_toolkit`

## Running the app
```bash
source .venv/bin/activate
python main.py
```
