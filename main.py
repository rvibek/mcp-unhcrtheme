import asyncio
import base64
import logging
from typing import Any, Dict

import httpx
import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
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


# Create the MCP server instance with standard variable name 'mcp'
mcp = Server("unhcr-plot")

# FastAPI server configuration
FASTAPI_BASE_URL = "https://unhcrpyplot.rvibek.com.np/"


@mcp.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
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


@mcp.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    if name == "generate_chart":
        return await _generate_chart(arguments)
    elif name == "check_fastapi_status":
        return await _check_fastapi_status()
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _generate_chart(arguments: dict) -> list[types.TextContent | types.ImageContent]:
    """Generate a chart using the FastAPI service"""
    try:
        chart_request = ChartRequest(**arguments)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FASTAPI_BASE_URL}/plot",
                json=chart_request.dict(),
                timeout=30.0
            )
            
            if response.status_code == 200:
                image_data_base64 = base64.b64encode(response.content).decode('utf-8')
                
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
                text="Error: Could not connect to FastAPI server. Make sure it's accessible at https://unhcrpyplot.rvibek.com.np/"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error generating chart: {str(e)}"
            )
        ]


async def _check_fastapi_status() -> list[types.TextContent]:
    """Check if the FastAPI server is accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/", timeout=5.0)
            
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
                text="FastAPI server is not accessible. Make sure it's accessible at https://unhcrpyplot.rvibek.com.np/"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error checking FastAPI status: {str(e)}"
            )
        ]


async def main():
    """Main entry point for the server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="unhcr-plot",
                server_version="0.1.0",
                capabilities=mcp.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
