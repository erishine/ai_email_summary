from anthropic import Anthropic
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from gmail_mcp_client import GmailMcpClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from my_email import MyEmail
import os
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import PromptSession
import json
from email_summary_workflow import EmailSummaryWorkflow

load_dotenv()

async def main():
    email_list = []

    async with GmailMcpClient() as client:
        labels = await client.fetch_labels()
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
        email_ids = await client.search_emails(label, from_date, to_date, max_emails)
        #result = await client.list_tools()
        #print([t.name for t in result.tools])
        print(f"\nFetching {len(email_ids)} emails.")
        for id in email_ids:
            email_data = await client.get_email_message(id)
            email = MyEmail.from_mcp(id, email_data)
            #print(email.clean_body,"\n\n")
            email_list.append(email)

    client = Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )

    prompt = """
        You are summarising emails and newsletters. For each email below, provide a brief summary of the key topics covered.
        """
          
    for email in email_list:
        email_info = f"""----
                      Subject:{email.subject}
                      Body:{email.clean_body}
                      """
        prompt += email_info

    print(f"The prompt contains {len(prompt)} characters. It will be capped to 400k characters if greater.")

    prompt = prompt[:400_000]


    message = client.messages.create(
        max_tokens=4096,
        messages = [
            {
                "role":"user",
                "content":prompt,
            }
        ],
        model="claude-haiku-4-5-20251001"
    )

    summary = message.content[0].text
    print(summary)
    with open('summary.md', 'w') as f:
        f.write(summary)

async def v2():
    async with GmailMcpClient() as client:
        # no worth having Claude to trigger this call
        labels = await client.fetch_labels()
        label_completer = WordCompleter(labels, ignore_case=True)
        session_pt = PromptSession()
        label = await session_pt.prompt_async("Select Gmail label: ", completer=label_completer)
        print(f"We will summarise only emails with label '{label}'")
        print(f"""
        Now tell Claude which emails you want to summarise. For example:
              `All the emails in the last 7 days`
              `3 emails from last Friday`
              `emails with "MCP" in the subject`
              `Last 7 unread emails`
        If date is not specified we will consider emails in the last 3 days.
              """)
        search_request=input(">")

        workflow = EmailSummaryWorkflow(label, search_request, client)
        await workflow.start()



if __name__ == "__main__":
    asyncio.run(v2())