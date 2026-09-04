FROM python:3.12-slim

LABEL maintainer="harezadmm <security@redmess.dev>"
LABEL description="RedMess BRUTAL MOD - Unrestricted Offensive Security AI"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /redmess

# Copy project files
COPY requirements.txt .
COPY setup.py .
COPY redmess/ ./redmess/
COPY README.md .
COPY LICENSE .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Install Hermes if not already a dependency
RUN pip install --no-cache-dir hermes-ai

# Create BRUTAL profile directory
RUN mkdir -p /root/.hermes/profiles/brutal

# Copy SOUL.md if exists
COPY SOUL.md /root/.hermes/profiles/brutal/SOUL.md 2>/dev/null || true

# Copy security skills if they exist
RUN mkdir -p /root/.hermes/profiles/brutal/skills/security
COPY skills/ /root/.hermes/profiles/brutal/skills/ 2>/dev/null || true

# Set environment variables
ENV HERMES_PROFILE=brutal
ENV PYTHONUNBUFFERED=1

# Expose port for web dashboard (if using)
EXPOSE 8080

# Default command
CMD ["redmess"]
