from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class GmailMcpClient:
    
    async def __aenter__(self):
        server_params = StdioServerParameters(
            command=".venv/bin/python",
            args=["run_gmail_mcp_server.py"]
        )
        self._stdio = stdio_client(server_params)
        read, write = await self._stdio.__aenter__()
        self._session = ClientSession(read, write)
        self.session = await self._session.__aenter__()
        await self.session.initialize()
        return self

    async def __aexit__(self, *args):
        await self._session.__aexit__(*args)
        await self._stdio.__aexit__(*args)

    async def fetch_labels(self):
        result = await self.session.call_tool("list_available_labels", {})
        # result.content is a list of content blocks, first one is the text
        raw_text = result.content[0].text
        # parse out the Name: lines
        labels = []
        for line in raw_text.splitlines():
            if line.startswith("Name:"):
                labels.append(line.replace("Name:", "").strip())
        return labels

    async def search_emails(self, label, from_date, to_date, max_emails):
        result = await self.session.call_tool("search_emails", {
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

    async def get_emails(self, message_ids):
        result = await self.session.call_tool("get_emails", {"message_ids":message_ids})
        return result
    
    async def get_email_message(self, message_id):
        result = await self.session.read_resource(f"gmail://messages/{message_id}")
        return result
    
    async def list_tools(self):
        return await self.session.list_tools()
    
    async def use_tool(self, tool_name, tool_input):
        return await self.session.call_tool(tool_name, tool_input)
    
    async def list_resource_templates(self):
        return await self.session.list_resource_templates()
