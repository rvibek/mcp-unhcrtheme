import asyncio
import base64
import logging
from typing import Any, Dict

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fastapi-chart-server")

# Create the FastMCP server instance
mcp = FastMCP("unhcr-plot")

class ChartRequest(BaseModel):
    """Request model for chart generation"""
    chart_type: str
    title: str
    subtitle: str
    data: Dict[str, Any]
    x_label: str
    y_label: str

# FastAPI server configuration
FASTAPI_BASE_URL = "https://unhcrpyplot.rvibek.com.np/"

@mcp.tool()
def generate_chart(
    chart_type: str,
    title: str,
    subtitle: str,
    x_label: str,
    y_label: str,
    data: Dict[str, Any]
) -> str:
    """Generate a chart using the FastAPI chart generation service"""
    try:
        chart_request = ChartRequest(
            chart_type=chart_type,
            title=title,
            subtitle=subtitle,
            x_label=x_label,
            y_label=y_label,
            data=data
        )
        
        # This is a synchronous wrapper for the async function
        return asyncio.run(_generate_chart_async(chart_request.dict()))
        
    except Exception as e:
        return f"Error generating chart: {str(e)}"

@mcp.tool()
def check_fastapi_status() -> str:
    """Check if the FastAPI server is running and accessible"""
    try:
        return asyncio.run(_check_fastapi_status_async())
    except Exception as e:
        return f"Error checking FastAPI status: {str(e)}"

async def _generate_chart_async(chart_request_data: dict) -> str:
    """Generate a chart using the FastAPI service (async version)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FASTAPI_BASE_URL}/plot",
                json=chart_request_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                image_data_base64 = base64.b64encode(response.content).decode('utf-8')
                
                return f"Chart generated successfully: {chart_request_data['title']}\n\n![Chart](data:image/png;base64,{image_data_base64})"
            else:
                return f"Error generating chart: {response.status_code} - {response.text}"
                
    except httpx.ConnectError:
        return "Error: Could not connect to FastAPI server. Make sure it's accessible at https://unhcrpyplot.rvibek.com.np/"
    except Exception as e:
        return f"Error generating chart: {str(e)}"

async def _check_fastapi_status_async() -> str:
    """Check if the FastAPI server is accessible (async version)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/", timeout=5.0)
            
            if response.status_code == 200:
                return "FastAPI server is running and accessible"
            else:
                return f"FastAPI server responded with status: {response.status_code}"
                
    except httpx.ConnectError:
        return "FastAPI server is not accessible. Make sure it's accessible at https://unhcrpyplot.rvibek.com.np/"
    except Exception as e:
        return f"Error checking FastAPI status: {str(e)}"

if __name__ == "__main__":
    mcp.run()
