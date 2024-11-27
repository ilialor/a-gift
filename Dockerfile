# Use Python 3.12 slim image
FROM python:3.12-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app and copy everything there
WORKDIR /app

# Copy the entire project
COPY . .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create user without root privileges
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Export Python path to include the app directory while preserving existing paths
ENV PYTHONPATH="/app:$PYTHONPATH"

# Set the port
EXPOSE 8000

# Run the application with the correct module path
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
