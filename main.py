import asyncio
from dotenv import load_dotenv
from gmail_mcp_client import GmailMcpClient
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import PromptSession
from email_summary_workflow import EmailSummaryWorkflow

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
        If a date range is not specified we will consider emails in the last 3 days.
              """)
        search_request=input(">")

        workflow = EmailSummaryWorkflow(label, search_request, client)
        await workflow.start()



if __name__ == "__main__":
    asyncio.run(v2())