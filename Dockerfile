# Use Python 3.12 slim image
FROM python:3.12-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# First set working directory to temporary location
WORKDIR /build

# Copy the entire project first
COPY . .

# Move the inner app directory contents to final location
RUN mkdir -p /app && \
    mv app/* /app/ && \
    mv requirements.txt /app/

# Set the final working directory
WORKDIR /app

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create user without root privileges
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set the port
EXPOSE 8000

# Run the application (now templates will be found in correct location)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
