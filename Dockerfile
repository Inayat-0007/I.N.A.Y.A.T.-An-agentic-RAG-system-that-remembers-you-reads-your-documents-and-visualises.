# Use official lightweight Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Set env variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install system dependencies (includes tini for proper signal forwarding)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser

# Copy dependency specifications
COPY requirements.txt constraints.txt ./

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -c constraints.txt

# Copy project files
COPY . .

# Set ownership to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8501

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Use tini as init process for proper signal forwarding
ENTRYPOINT ["tini", "--"]

# Run the app
CMD ["streamlit", "run", "app.py"]
