FROM python:3.14

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install the dependencies first so they cache independently of source changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy the application into the container.
COPY . /app

# Expose HTTP and DNS ports.
EXPOSE 8000
EXPOSE 53/udp

# Set DNS to run on privileged port inside container.
ENV DNS_PORT=53

# Run the application.
CMD ["/app/.venv/bin/fastapi", "run", "-e", "app.main:app", "--host", "0.0.0.0"]
