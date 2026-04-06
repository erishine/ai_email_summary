from anthropic import Anthropic
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

class EmailSummaryWorkflow:

    
    def __init__(self, email_label, search_request, client):
        self.email_label = email_label
        self.user_search_request = search_request
        self.mcp_client = client

        client = Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        self.antropic_client = client

    def tool_data(self, claude_response):
        for block in claude_response.content:
            if block.type == "tool_use":
                return block.name, block.input, block.id

    async def start(self):
        messages = []
        today = datetime.today().strftime("%Y/%m/%d")
        first_message=f"""
            You are an email summarisation assistant. Your only task is to fetch and summarise emails from Gmail using the available tools.
            You will be given a Gmail label and a search criteria from the user. Use the Gmail tools to fetch the emails matching those criteria and summarise them.
            Today's date is {today}. If no date range is specified, you must default to only search emails received in the last 3 days.
            Cap the total number of emails to summarise to 5.
            If the user asks anything unrelated to fetching and summarising emails, respond with a plain text message explaining you can only help with email summarisation and do not call any tools.
            
            <gmail_label>
            {self.email_label}
            </gmail_label>

            <user_search_crieria>
            {self.user_search_request}
            </user_search_crieria>
        """

        user_message = {
            "role":"user",
            "content":first_message
        }

        messages.append(user_message)

        mcp_tools = await self.mcp_client.list_tools()

        #print(type(mcp_tools))
        #print(mcp_tools)

        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in mcp_tools.tools
        ]

        message = None

        while True:

            message = self.antropic_client.messages.create(
                max_tokens=4096,
                messages=messages,
                tools = tools,
                model="claude-haiku-4-5-20251001",
            )

            print(message.content[0].text)

        
            if message.stop_reason != "tool_use":
                break
        
            tool_name, tool_input, tool_use_id= self.tool_data(message)

            result = await self.mcp_client.use_tool(tool_name, tool_input)

            messages.append({"role": "assistant", "content": message.content})

            messages.append({
                "role":"user",
                "content": [
                    {
                        "type":"tool_result",
                        "tool_use_id":tool_use_id,
                        "content":result.content[0].text
                    }
                ]
            })

        if message:
            print(message.content[0].text)

        with open('summary.md', 'w') as f:
            f.write(message.content[0].text)


