FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy dependency definitions
COPY pyproject.toml .

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy source code
COPY app/ ./app
COPY utils ./utils
COPY assets/ ./assets

# Expose dash port
EXPOSE 8042

# Activate venv & run app
CMD ["uv", "run", "-m", "app.main"]
