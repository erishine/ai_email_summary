from anthropic import Anthropic
from datetime import datetime
from dotenv import load_dotenv
from headroom import compress
import os

load_dotenv()

class EmailSummaryWorkflow:

    
    def __init__(self, search_request, client):
        self.user_search_request = search_request
        self.mcp_client = client

        client = Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        self.antropic_client = client

    def _prepare_messages_for_api(self, messages):
        cleaned = []
        for i, message in enumerate(messages):
            is_last = (i == len(messages) - 1)
            if message["role"] == "user" and isinstance(message["content"], list):
                cleaned_blocks = []
                for block in message["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        clean_block = {
                            "type": "tool_result",
                            "tool_use_id": block["tool_use_id"],
                            "content": (
                                block["content"]  # keep full body
                                if is_last
                                else (
                                    "[email bodies removed from history]"
                                    if block.get("_tool_name") == "get_emails"
                                    else block["content"]
                                )
                            )
                        }
                        # never pass _tool_name to the API
                        cleaned_blocks.append(clean_block)
                    else:
                        cleaned_blocks.append(block)
                cleaned.append({**message, "content": cleaned_blocks})
            else:
                cleaned.append(message)
        return cleaned

    async def start(self):
        messages = []
        today = datetime.today().strftime("%Y/%m/%d")
        first_message = f"""
            You are an email summarisation assistant. Your only task is to fetch and summarise emails from Gmail using the available tools.

            Today's date is {today}.

            ## Rules

            1. Use the Gmail tools to fetch emails matching the user's search request and summarise them.
            2. If no date range is specified, default to emails received in the last 3 days.
            3. Cap the total number of emails to summarise to a maximum of 20.
            4. If the user asks anything unrelated to fetching and summarising emails, explain you can only help with email summarisation and do not call any tools.
            5. When searching for emails received on a specific day, set after_date to that day and before_date to the following day.
            
            ## Mandatory output rules — follow these without exception

            - Any time you want to ask the user something or need their input — including confirmations, clarifications, or corrections — you MUST output [QUESTION] immediately after your question. No exceptions.
            - You MUST NOT end a turn with a question unless you have output [QUESTION] first.
            - Once you have delivered the final summary and have no further questions, you MUST output [DONE] on its own line. Do not output [DONE] at any other point.

            ## Workflow

            1. Search for emails matching the user's request using the available tools.
            2. After identifying the matching emails, always summarise what you found and confirm with the user how to proceed before doing anything further. Output [QUESTION] after this confirmation request.
            3. Once confirmed, fetch the emails and produce the summary.
            4. Output [DONE] after the summary.


            <search_request>
            {self.user_search_request}
            </search_request>

            ## Email summary result
            - Format as Markdown
            - For each email, follow this exact process:
            - For each email:
                1. Copy the exact section headings or titles as they appear in the email body 
                   (e.g. "MCP", "PYTHON", "DEEP DIVE" — use the actual words, not paraphrases)
                2. Write one bullet per heading
                3. If you cannot find a literal heading, note "no section headings" and summarise 
       paragraphs as separate bullets instead
            - Header format: Subject - [Sender](https://mail.google.com/mail/u/0/#inbox/message_id)
            - Do NOT derive topics from the subject line — derive them from the body sections
            - At the end, summarise the main trends across all retrieved emails
            """

        user_message = {
            "role":"user",
            "content":first_message
        }

        messages.append(user_message)
        
        mcp_tools = await self.mcp_client.list_tools()

        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in mcp_tools.tools
        ]

        response = None

        while True:
            result = compress(messages, model="claude-haiku-4-5-20251001")

            print(f"----\nSaved {result.tokens_saved} tokens ({result.compression_ratio:.0%})\n-----")
            
            #messages=self._prepare_messages_for_api(result.messages),

            response = self.antropic_client.messages.create(
                max_tokens=8096,
                messages=self._prepare_messages_for_api(result.messages),
                tools = tools,
                stop_sequences=["[DONE]", "[QUESTION]"],
                model="claude-haiku-4-5-20251001",
            )

            if response.content[0].type == "text":
                print(response.content[0].text)

            if response.stop_reason == "stop_sequence":
                if response.stop_sequence == "[DONE]":
                    break
                if response.stop_sequence == "[QUESTION]":
                    messages.append({"role": "assistant", "content": response.content}) 
                    user_input = input(">")
                    messages.append({"role": "user", "content": user_input})
                    continue
            elif response.stop_reason == "tool_use":
                tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

                tool_results = []
                for block in tool_use_blocks:
                    result = await self.mcp_client.use_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result.content[0].text,
                        "_tool_name": block.name  # private tag for pruning
                    })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue
            else:
                break

        if response:
            # Find the last text block
            text_blocks = [b for b in response.content if hasattr(b, 'text')]
            if text_blocks:
                date_time = datetime.today().strftime('%Y%m%d_%H%M%S')
                with open(f"summary_{date_time}.md", 'w') as file:
                    file.write(text_blocks[-1].text)
