# MCP FastAPI Chart Server

An MCP (Model Context Protocol) server that interacts with a FastAPI service to generate matplotlib charts.

## Overview

This MCP server provides tools to:
- Generate charts using your FastAPI chart generation service
- Check the status of your FastAPI server
- Return chart images directly to the client

## Prerequisites

- Python 3.8+
- Your FastAPI server running on `localhost:8000` with the `/plot` endpoint

## Installation

1. Install the package:
```bash
pip install -e .
```

## Configuration

### For Claude Desktop

Add the following to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fastapi-chart": {
      "command": "python",
      "args": ["-m", "mcp_fastapi_chart.server"]
    }
  }
}
```

### For Other MCP Clients

Configure your MCP client to run:
```bash
python -m mcp_fastapi_chart.server
```

## Available Tools

### 1. `generate_chart`

Generate a chart using the FastAPI chart generation service.

**Parameters:**
- `chart_type` (string): Type of chart to generate - "line", "bar", "scatter", or "pie"
- `title` (string): Main title of the chart
- `subtitle` (string): Subtitle of the chart  
- `x_label` (string): Label for the X-axis
- `y_label` (string): Label for the Y-axis
- `data` (object): Chart data with labels and values
  - `labels` (array of strings): Labels for data points
  - `values` (array of numbers): Values for data points

**Example Usage:**
```json
{
  "chart_type": "line",
  "title": "Asylum Applications Trend",
  "subtitle": "Monthly applications received (2023-2024)",
  "x_label": "Month",
  "y_label": "Applications Received",
  "data": {
    "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "values": [15400, 16800, 14200, 18900, 17600, 19500, 20300, 18700, 17400, 16200, 15800, 14900]
  }
}
```

### 2. `check_fastapi_status`

Check if the FastAPI server is running and accessible.

**Parameters:** None

## FastAPI Server Requirements

Your FastAPI server should have an endpoint at `/plot` that accepts POST requests with the following JSON structure:

```json
{
  "chart_type": "string",
  "title": "string", 
  "subtitle": "string",
  "data": {
    "labels": ["string"],
    "values": [number]
  },
  "x_label": "string",
  "y_label": "string"
}
```

And should return a PNG image as the response.

## Development

To run the server directly for testing:

```bash
python -m mcp_fastapi_chart.server
```

## Cloud Deployment

When you move your FastAPI server to the cloud, update the `fastapi_base_url` in `mcp_fastapi_chart/server.py`:

```python
self.fastapi_base_url = "https://your-cloud-domain.com"
```

## Troubleshooting

1. **Connection Errors**: Make sure your FastAPI server is running on `localhost:8000`
2. **Chart Generation Errors**: Verify your FastAPI `/plot` endpoint is working correctly
3. **MCP Connection Issues**: Check your Claude Desktop configuration file syntax

## License

MIT
