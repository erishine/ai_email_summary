import os
from dotenv import load_dotenv
from anthropic import Anthropic
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import PromptSession

load_dotenv()

async def fetch_labels(session):
    result = await session.call_tool("list_available_labels", {})
    # result.content is a list of content blocks, first one is the text
    raw_text = result.content[0].text
    # parse out the Name: lines
    labels = []
    for line in raw_text.splitlines():
        if line.startswith("Name:"):
            labels.append(line.replace("Name:", "").strip())
    return labels

##asynch def search_emails(sesion, label, from_date):

async def main():
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=["run_gmail_mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            labels = await fetch_labels(session)
            label_completer = WordCompleter(labels, ignore_case=True)
            session_pt = PromptSession()
            label = await session_pt.prompt_async("Enter Gmail label: ", completer=label_completer)

    print(f"Summarising the emails with label '{label}'")
    
    
    """
    
    print(\"""
        Gmail emails summary:\n
          Specify the Gmail label associated to the emails and the number of days to consider:
          \n\n
          \""")
    label = input("Enter the Gmail label:")
    days = int(input("Enter the days:"))

    consent=input("Enter Y to confirm or N to stop the process:")
    if consent.lower() != 'y':
        exit()

    print(f"Summarising the emails with label {label} received in the last {days} days")


    client = Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )

    message = client.messages.create(
        max_tokens=1024,
        messages = [
            {
                "role":"user",
                "content":"hello Claude",
            }
        ],
        model="claude-haiku-4-5-20251001"
    )

    print(message.content[0].text)
"""


if __name__ == "__main__":
    asyncio.run(main())