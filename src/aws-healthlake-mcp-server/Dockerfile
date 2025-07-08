FROM python:3.10-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -e .

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "/app/docker-healthcheck.sh" ]

ENTRYPOINT [ "python", "-m", "awslabs.healthlake_mcp_server.server" ]
