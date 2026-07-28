FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN pip install uv

# Copy dependency definitions
COPY pyproject.toml .

# Install dependencies
RUN uv sync

# Copy source code
COPY app/ ./app
COPY assets/ ./assets

# Expose dash port
EXPOSE 8042

# Run app
CMD ["uv", "run", "-m", "app.main"]
