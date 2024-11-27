# Use Python 3.12 slim image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Set the environment variables
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project first
COPY . .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create user without root privileges
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set the port
EXPOSE 8000

# Run the application
CMD cd /app && uvicorn main:app --host 0.0.0.0 --port 8000
