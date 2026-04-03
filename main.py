import os
from dotenv import load_dotenv
from anthropic import Anthropic
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import PromptSession
from datetime import datetime, timedelta

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

async def search_emails(session, label, from_date, to_date, max_emails):
    result = await session.call_tool("search_emails", {
        "label":label,
        "after_date": from_date,
        "before_date": to_date,
        "max_results": max_emails
    })
    raw_text = result.content[0].text
    message_ids = []
    for line in raw_text.splitlines():
        if line.startswith("Message ID:"):
            message_ids.append(line.replace("Message ID:", "").strip())
    return message_ids

async def get_emails(session, message_ids):
    result = await session.call_tool("get_emails", {"message_ids":message_ids})
    return result

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

            from_date = input("Enter start date in a format YYYY/MM/DD (default to last 7 days):")
            if not from_date:
                from_date = (datetime.today() - timedelta(days=7)).strftime("%Y/%m/%d")
            else:
                from_date = datetime.strptime(from_date, "%Y/%m/%d").strftime("%Y/%m/%d")

            to_date = input("Enter end date in a format YYYY/MM/DD (default today):")
            if not to_date:
                to_date = datetime.today().strftime("%Y/%m/%d")
            else:
                to_date = datetime.strptime(to_date, "%Y/%m/%d").strftime("%Y/%m/%d")  

            max_emails = input("Enter max number of emails to consider or enter for default(20 emails):")
            if not max_emails:
                max_emails=20
            else:
                max_emails=int(max_emails)

            print(f"""
                    Initating tasks:
                        - email label: {label}
                        - start date: {from_date}
                        - end date: {to_date}
                        - max emails: {max_emails}
                  """)
            consent=input("Press Enter to confirm or type anything (No) to stop the process:")
            if consent != '':
                exit()


            email_ids = await search_emails(session, label, from_date, to_date, max_emails)
            # print(emails_raw)  # verify the output before moving to the next step
            emails_content = await get_emails(session, email_ids)
            print(emails_content)
    
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