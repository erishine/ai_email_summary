from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

class MessagesState(TypedDict):
    messages: Annotated[list, add_messages]

class EmailSummaryWorkflow:
    def __init__(self, search_request, client):
        self.user_search_request = search_request
        self.mcp_client = client

        # Initialize the LangChain LLM
        self.llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            max_tokens=8096,
            stop_sequences=["[DONE]", "[QUESTION]"]
        )

    def _prepare_messages_for_api(self, messages):
        """
        Prunes the content of older get_emails tool calls to save context window.
        """
        cleaned = []
        for i, message in enumerate(messages):
            is_last = (i == len(messages) - 1)
            
            if isinstance(message, ToolMessage):
                if message.name == "get_emails" and not is_last:
                    cleaned.append(ToolMessage(
                        content="[email bodies removed from history]",
                        tool_call_id=message.tool_call_id,
                        name=message.name,
                        id=message.id 
                    ))
                else:
                    cleaned.append(message)
            else:
                cleaned.append(message)
                
        return cleaned

    async def agent_node(self, state: MessagesState):
        messages = state["messages"]
        pruned_messages = self._prepare_messages_for_api(messages)
        
        response = await self.llm_with_tools.ainvoke(pruned_messages)
        return {"messages": [response]}

    async def tools_node(self, state: MessagesState):
        last_message = state["messages"][-1]
        tool_results = []
        
        for tool_call in last_message.tool_calls:
            result = await self.mcp_client.use_tool(tool_call["name"], tool_call["args"])
            tool_content = result.content[0].text if result.content else ""
            
            tool_results.append(ToolMessage(
                content=tool_content,
                tool_call_id=tool_call["id"],
                name=tool_call["name"]
            ))
            
        return {"messages": tool_results}

    def human_node(self, state: MessagesState):
        last_message = state["messages"][-1]
        
        if isinstance(last_message.content, list):
            for block in last_message.content:
                if block.get("type") == "text":
                    print(block["text"])
        elif isinstance(last_message.content, str):
            print(last_message.content)
            
        user_input = input(">")
        return {"messages": [HumanMessage(content=user_input)]}

    def should_continue(self, state: MessagesState):
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
            
        stop_reason = last_message.response_metadata.get("stop_reason")
        stop_sequence = last_message.response_metadata.get("stop_sequence")
        
        if stop_reason == "stop_sequence":
            if stop_sequence == "[DONE]":
                return END
            if stop_sequence == "[QUESTION]":
                return "human"
                
        content = ""
        if isinstance(last_message.content, list):
             for block in last_message.content:
                 if block.get("type") == "text":
                     content += block["text"]
        else:
             content = str(last_message.content)
             
        if "[DONE]" in content:
            return END
        if "[QUESTION]" in content:
            return "human"
            
        return END

    async def start(self):
        mcp_tools_res = await self.mcp_client.list_tools()
        lc_tools = []
        for t in mcp_tools_res.tools:
            lc_tools.append({
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema
            })
            
        self.llm_with_tools = self.llm.bind_tools(lc_tools)

        workflow = StateGraph(MessagesState)
        
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tools", self.tools_node)
        workflow.add_node("human", self.human_node)
        
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", self.should_continue)
        workflow.add_edge("tools", "agent")
        workflow.add_edge("human", "agent")
        
        self.app = workflow.compile()

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

        initial_state = {"messages": [HumanMessage(content=first_message)]}
        
        final_state = await self.app.ainvoke(initial_state)
        
        last_ai_msg = None
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage):
                last_ai_msg = msg
                break
                
        if last_ai_msg:
            content = ""
            if isinstance(last_ai_msg.content, list):
                for block in last_ai_msg.content:
                    if block.get("type") == "text":
                        content += block["text"]
            else:
                content = str(last_ai_msg.content)
                
            date_time = datetime.today().strftime('%Y%m%d_%H%M%S')
            with open(f"summary_{date_time}.md", 'w') as file:
                file.write(content)
