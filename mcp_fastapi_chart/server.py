import asyncio
import base64
import logging
import os
import tempfile
from typing import Any, Dict, Optional

import httpx
import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fastapi-chart-server")


class ChartRequest(BaseModel):
    """Request model for chart generation"""
    chart_type: str
    title: str
    subtitle: str
    data: Dict[str, Any]
    x_label: str
    y_label: str


class FastAPIChartServer:
    def __init__(self):
        logger.info("Initializing FastAPIChartServer")
        self.server = Server("fastapi-chart")
        
        # FastAPI server configuration
        self.fastapi_base_url = "http://localhost:8000"
        logger.info(f"FastAPI server URL configured: {self.fastapi_base_url}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="generate_chart",
                    description="Generate a chart using the FastAPI chart generation service",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "chart_type": {
                                "type": "string",
                                "description": "Type of chart to generate (line, bar, scatter, etc.)",
                                "enum": ["line", "bar", "scatter", "pie"]
                            },
                            "title": {
                                "type": "string",
                                "description": "Main title of the chart"
                            },
                            "subtitle": {
                                "type": "string",
                                "description": "Subtitle of the chart"
                            },
                            "x_label": {
                                "type": "string",
                                "description": "Label for the X-axis"
                            },
                            "y_label": {
                                "type": "string",
                                "description": "Label for the Y-axis"
                            },
                            "data": {
                                "type": "object",
                                "description": "Chart data with labels and values",
                                "properties": {
                                    "labels": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Labels for data points"
                                    },
                                    "values": {
                                        "type": "array",
                                        "items": {"type": "number"},
                                        "description": "Values for data points"
                                    }
                                },
                                "required": ["labels", "values"]
                            }
                        },
                        "required": ["chart_type", "title", "subtitle", "x_label", "y_label", "data"]
                    }
                ),
                types.Tool(
                    name="check_fastapi_status",
                    description="Check if the FastAPI server is running and accessible",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str,
            arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            if name == "generate_chart":
                return await self._generate_chart(arguments)
            elif name == "check_fastapi_status":
                return await self._check_fastapi_status()
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _generate_chart(self, arguments: dict) -> list[types.TextContent | types.ImageContent]:
        """Generate a chart using the FastAPI service"""
        try:
            # Validate and prepare the request
            chart_request = ChartRequest(**arguments)
            
            # Send request to FastAPI server
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.fastapi_base_url}/plot",
                    json=chart_request.dict(),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    # Create a temporary file to save the image
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                        temp_file.write(response.content)
                        temp_file_path = temp_file.name
                    
                    # Encode the image data as base64 for ImageContent
                    image_data_base64 = base64.b64encode(response.content).decode('utf-8')
                    
                    # Return both text confirmation and the image
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Chart generated successfully: {chart_request.title}"
                        ),
                        types.ImageContent(
                            type="image",
                            data=image_data_base64,
                            mimeType="image/png"
                        )
                    ]
                else:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Error generating chart: {response.status_code} - {response.text}"
                        )
                    ]
                    
        except httpx.ConnectError:
            return [
                types.TextContent(
                    type="text",
                    text="Error: Could not connect to FastAPI server. Make sure it's running on localhost:8000"
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error generating chart: {str(e)}"
                )
            ]
    
    async def _check_fastapi_status(self) -> list[types.TextContent]:
        """Check if the FastAPI server is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.fastapi_base_url}/", timeout=5.0)
                
                if response.status_code == 200:
                    return [
                        types.TextContent(
                            type="text",
                            text="FastAPI server is running and accessible"
                        )
                    ]
                else:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"FastAPI server responded with status: {response.status_code}"
                        )
                    ]
                    
        except httpx.ConnectError:
            return [
                types.TextContent(
                    type="text",
                    text="FastAPI server is not accessible. Make sure it's running on localhost:8000"
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error checking FastAPI status: {str(e)}"
                )
            ]


# Create a global server instance for FastMCP
server = FastAPIChartServer()

async def main():
    logger.info("Starting FastAPI Chart MCP server")
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP stdio server started")
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fastapi-chart",
                server_version="0.1.0",
                capabilities=server.server.get_capabilities(
                    notification_options=mcp.server.models.ServerCapabilities(
                        tools_changed=False
                    ),
                    experimental_capabilities=None,
                )
            ),
        )


if __name__ == "__main__":
    logger.info("Running server as main module")
    asyncio.run(main())
