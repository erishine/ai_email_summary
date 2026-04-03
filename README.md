# AI Newsletter Summary

A Python CLI tool that fetches newsletter emails from Gmail by label and summarises them using the Claude API (Haiku model).

## How it works

1. Prompts for a Gmail label and number of days to look back
2. Fetches matching emails via the Gmail MCP server
3. Sends the email content to Claude Haiku for summarisation
4. Prints a digest to the terminal

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

You will need an account on [Claude platform](https://platform.claude.com/) with some token credits.

### Gmail MCP server
#### Set Up Google Cloud Project
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project.
- Navigate to "APIs & Services" > "Library" and enable the Gmail API.
- Generate OAuth Credentials
- Go to "APIs & Services" > "Credentials".
- Click "Create Credentials" > "OAuth client ID".
- Choose "Desktop application" (or Web application) and download the credentials.json file.
- install the mcp server for example by using `pip install mcp-gmail`
- once installed you should be able to run the mcp server for example `python -m mcp_gmail.server` which will open a browser to complete the authentication flow.  This will also create a token.json in your current folder.

## Usage

```bash
python main.py
```

The script will prompt for:
- **Gmail label** — e.g. `Data Science`
- **Days** — how many days back to look, e.g. `7`
