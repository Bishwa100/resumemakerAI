FROM python:3.11-slim AS builder

WORKDIR /app

# Copy only requirements files first to leverage Docker cache
COPY requirements.txt pyproject.toml ./

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install -e .

# Final stage
FROM python:3.11-slim

# Add metadata
LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="ATS-friendly resume maker powered by OpenRouter API"
LABEL version="1.0"

# Install LaTeX and required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    latexmk \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/

# Create required directories
RUN mkdir -p /app/output \
    /app/src/resumemaker/crews/poem_crew/resume_templates

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run as non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Run the application
ENTRYPOINT ["python", "-m", "resumemaker.main"]
CMD ["kickoff"] 