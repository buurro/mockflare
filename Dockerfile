FROM python:3.14

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

# Expose HTTP and DNS ports.
EXPOSE 8000
EXPOSE 53/udp

# Set DNS to run on privileged port inside container.
ENV DNS_PORT=53

# Run the application.
CMD ["/app/.venv/bin/fastapi", "run", "-e", "app.main:app", "--host", "0.0.0.0"]
