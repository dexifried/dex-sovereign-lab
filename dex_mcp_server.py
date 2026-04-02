import os
import httpx
import logging
import uvicorn
import json
from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types

# --- 📊 TELEMETRY ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Dex-Sovereign-MCP")

# --- 🛰️ DEX LABORATORY CONFIG ---
GATEKEEPER_URL = "http://localhost:8000/execute"

# 1. Create the Low-Level MCP Server
server = Server("Dex_Sovereign_Lab")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Exposes Dex's capabilities to the ElevenLabs/Gemini 2.5 Brain."""
    return [
        types.Tool(
            name="interrogate_dex",
            description="Master interface for Dex Lab. Use for code surgery (Aider), strategy, or images.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Command for the lab"}
                },
                "required": ["prompt"],
            },
        ),
        types.Tool(
            name="check_lab_status",
            description="Retrieves current lab status and recent surgical ledger entries.",
            inputSchema={"type": "object", "properties": {}},
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Routes voice-to-text commands to your local ModernBERT matrix."""
    if name == "interrogate_dex":
        prompt = arguments.get("prompt")
        logger.info(f"🎙️ Voice Command: {prompt}")
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(GATEKEEPER_URL, json={"prompt": prompt})
            result = response.text
            if "AGENT:" in result: result = result.split("\n", 1)[-1]
            return [types.TextContent(type="text", text=f"[LAB]: {result.strip()}")]
            
    elif name == "check_lab_status":
        ledger_path = os.path.expanduser("~/dex-local/surgical_ledger.md")
        status = "Dex Matrix Online. Router Active."
        if os.path.exists(ledger_path):
            with open(ledger_path, "r") as f:
                return [types.TextContent(type="text", text=f"{status}\n\nLast Surgery:\n{f.read()[-800:]}")]
        return [types.TextContent(type="text", text=status)]

# 2. Setup the SSE Transport
sse = SseServerTransport("/sse/messages")

# 3. Raw ASGI Application Logic
# This prevents the 'NoneType' and 'Already completed' lifecycle crashes
async def app(scope, receive, send):
    path = scope["path"]
    
    if path == "/sse" or path == "/sse/":
        logger.info("📡 SSE Handshake Initiated")
        async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
            
    elif path == "/sse/messages":
        await sse.handle_post_message(scope, receive, send)
        
    elif path == "/health":
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": json.dumps({"status": "online"}).encode(),
        })
        
    else:
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({"type": "http.response.body", "body": b"Not Found"})

if __name__ == "__main__":
    # Explicitly binding to port 8001 to sit next to the Gatekeeper
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

