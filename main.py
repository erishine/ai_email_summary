import asyncio
from dotenv import load_dotenv
from gmail_mcp_client import GmailMcpClient
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import PromptSession
from email_summary_workflow import EmailSummaryWorkflow

async def v2():
    async with GmailMcpClient() as client:
        search_request=input("Tell Claude which emails you want to summarise :>")

        workflow = EmailSummaryWorkflow(search_request, client)
        await workflow.start()



if __name__ == "__main__":
    asyncio.run(v2())