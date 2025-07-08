#!/bin/bash

# Simple health check for the MCP server
# This script checks if the Python process is running

if pgrep -f "python -m awslabs.healthlake_mcp_server.server" > /dev/null; then
    exit 0
else
    exit 1
fi
