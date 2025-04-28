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

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create output directory
RUN mkdir -p /app/output

# Run as non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Run the application
ENTRYPOINT ["python", "-m", "resumemaker.main"]
CMD ["kickoff"] 