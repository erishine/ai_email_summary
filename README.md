# AI Gmail Emails Summary
A Python CLI tool that fetches emails from Gmail by label and summarises them using the Claude API (Haiku model).

I built this to stop context-switching into my inbox to keep up with data science newsletters. I get a clean digest in seconds, saved to a markdown file I can read at my own pace.

It's also a learning project — specifically an exploration of the Model Context Protocol (MCP) and agentic AI workflow patterns using the Anthropic API.

## How it works

1. Accepts a freeform natural language search request (e.g. *"last 5 unread emails"*, *"emails about MCP from last Friday"*)
2. Hands the request to Claude Haiku, which drives the Gmail tool calls directly — searching for matching emails and confirming with you before fetching
3. Prints the summary to the terminal and saves it to `summary.md`

## Architecture

The app has three main components:

- **`gmail_mcp_client.py`** — async context manager wrapping the MCP `ClientSession`. Handles the MCP session lifecycle and exposes `list_tools()` and `use_tool()` for direct tool dispatch
- **`email_summary_workflow.py`** — drives the agentic loop: sends all available Gmail MCP tools to Claude Haiku, handles tool calls, and uses stop sequences (`[DONE]`, `[QUESTION]`) to manage completion and mid-run user confirmations
- **`main.py`** — entry point. Collects the freeform search request and starts the workflow

This is a V2 implementation where Claude drives the Gmail tool calls directly via the Anthropic tools API. Python handles only the initial user input and session lifecycle.

## Cost

Running costs are low and limited to Claude API usage (the Gmail MCP is free for personal use). A cap of 10 emails per run is enforced. Costs will vary with email length but are typically in the range of **$0.01–0.05/run** with Claude Haiku 4.5.

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

- **Search request** — freeform natural language, e.g. `last 5 unread emails` or `emails about Python from this week`

Claude will search for matching emails, confirm with you before fetching, then print a summary to the terminal and save it to `summary.md`.

## Known limitations

- No retry logic if the Gmail MCP server or Claude API call fails

## Roadmap

**V1** *(available on branch `version_1`)* — Python drove the full orchestration: label picker, structured date and email cap prompts, fetching and cleaning emails via regex (~52% token reduction), then a single Claude API call for summarisation. Claude was used only for the final step.

**V2** *(current)* — fully agentic. Claude drives the Gmail tool calls directly using the Anthropic tools API. The user provides a freeform natural language search request; Claude decides which tools to call and in what order.

**Future improvements:**
- Prompt engineering to make summary output more consistent and structured
- Ability to email the summary directly and make the search interaction more conversational
- A better UI (web or desktop) to replace the terminal prompt