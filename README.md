# AI Gmail Emails Summary
A Python CLI tool that fetches emails from Gmail by label and summarises them using the Claude API (Haiku model).

I built this to stop context-switching into my inbox to keep up with data science newsletters. I get a clean digest in seconds, saved to a markdown file I can read at my own pace.

It's also a learning project — specifically an exploration of the Model Context Protocol (MCP) and agentic AI workflow patterns using the Anthropic API.

## How it works

1. Fetches your Gmail labels via the Gmail MCP server and prompts you to pick one using an autocomplete dropdown
2. Prompts for a date range and optional email cap (with sensible defaults)
3. Confirms the search criteria before proceeding
4. Fetches matching emails, cleans the content (strips URLs, footers, boilerplate) to reduce token usage
5. Sends the cleaned content to Claude Haiku for summarisation
6. Prints the summary to the terminal and saves it to summary markdown file.

## Architecture

The app has three main components:

- **`gmail_mcp_client.py`** — async context manager wrapping the MCP `ClientSession`. Handles all Gmail tool calls (`list_available_labels`, `search_emails`, `get_emails`) and parses raw MCP responses
- **`my_email.py`** — dataclass representing a single email. Handles parsing of MCP response text and cleaning of email body content via regex
- **`main.py`** — orchestrates the full flow: label selection, date input, email fetching, prompt assembly, and Claude API call

This is a V1 implementation where the Python code drives the orchestration and Claude is used only for the final summarisation step. **A V2 refactor is planned to shift to a fully agentic architecture where Claude drives the tool calls directly.**

## Cost

Running costs are low and limited to Claude API usage (the Gmail MCP is free for personal use). Based on typical usage:

- Email cleaning reduces token count by ~52% (raw content ~88k chars → ~41k chars cleaned)
- ~10 emails/run ≈ ~50k input tokens ≈ **$0.04/run** with Claude Haiku 4.5
- A hard cap of 400k characters (~100k tokens) is applied before sending the prompt to Claude

You can keep costs predictable by setting a low `max_emails` value when prompted.

## Setup

### Prerequisites

- Python 3.10+
- Node.js (required to run the Gmail MCP server)
- A Google Cloud project with the Gmail API enabled and OAuth 2.0 credentials
- An Anthropic API key

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd ai_newsletter_summary

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
```

You will need an account on [Claude platform](https://platform.claude.com/) with some token credits.  Check out the "Cost" section for an idea of how much it will cost to run this and what you can do to keep the cost down.

### Gmail MCP server

#### Set Up Google Cloud Project
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project.
- Navigate to "APIs & Services" > "Library" and enable the Gmail API.
- Generate OAuth Credentials
- Go to "APIs & Services" > "Credentials".
- Click "Create Credentials" > "OAuth client ID".
- Choose "Desktop application" and download the credentials.json file.
- Activate the venv (`source .venv/bin/activate`) then install the mcp server: `pip install mcp-gmail`
- Once installed you should be able to run the mcp server: `.venv/bin/python -m mcp_gmail.server`. On the first run (when no `token.json` exists) this will open a browser to complete the authentication flow and create a `token.json` in your current folder.

You will need the `credential.json` and `token.json` either in the current root folder or set `MCP_GMAIL_CREDENTIALS_PATH` and `MCP_GMAIL_TOKEN_PATH` in your `.env` file if stored somewhere else.

Once the server is installed and authenticated correctly you'll be able to open the MCP tool inspector.  I had some issue starting the gmail mcp server so I wrapped in a small script and used 
```
npx @modelcontextprotocol/inspector .venv/bin/python run_gmail_mcp_server.py
```
The inspector server will start automatically on localhost and once connected it allow you to browse and try the available tools.

#### Install and authenticate

```bash
# Activate the venv first
source .venv/bin/activate

# Install the Gmail MCP server
pip install mcp-gmail

# Run once to trigger the OAuth browser flow and generate token.json
.venv/bin/python -m mcp_gmail.server
```

Place `credentials.json` and `token.json` in the project root, or set the following in your `.env` file if stored elsewhere:

```
MCP_GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
MCP_GMAIL_TOKEN_PATH=/path/to/token.json
```

#### Verify with the MCP inspector

If you want to confirm the server is working before running the app:

```bash
npx @modelcontextprotocol/inspector .venv/bin/python run_gmail_mcp_server.py
```

The inspector runs on localhost and lets you browse available tools and test parameters. Click **Connect** first.

If the inspector ports are already in use:

```bash
lsof -ti :6277,:6274 | xargs kill
```

## Usage

```bash
python main.py
```

You will be prompted for:

- **Gmail label** — autocomplete dropdown populated from your account, e.g. `Data Science`
- **Start date** — `YYYY/MM/DD` format, defaults to 7 days ago
- **End date** — `YYYY/MM/DD` format, defaults to today
- **Max emails** — defaults to 20

The tool will confirm your criteria before fetching. The summary is printed to the terminal and saved to `summary.md`.

## Known limitations

- Email cleaning is regex-based and works well for newsletters but may miss edge cases in less structured emails
- `main.py` currently handles orchestration, input, and the Claude call in a single function — a refactor is planned for V2
- No retry logic if the Gmail MCP server or Claude API call fails

## Roadmap

- **V2:** Shift to a fully agentic architecture where Claude drives the Gmail tool calls, with natural language criteria input and a confirmation step before fetching
- **V3:** Browser-based interface