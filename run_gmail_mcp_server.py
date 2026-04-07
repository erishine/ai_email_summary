import logging
logging.disable(logging.CRITICAL)

from mcp_gmail.server import mcp
mcp.run()