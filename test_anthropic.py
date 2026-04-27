import asyncio
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

load_dotenv()

async def main():
    llm = ChatAnthropic(model="claude-3-haiku-20240307", stop_sequences=["[DONE]", "[QUESTION]"])
    msg = await llm.ainvoke([HumanMessage(content="Say Hello [QUESTION] World")])
    print("Content:", msg.content)
    print("Metadata:", msg.response_metadata)

asyncio.run(main())
