# Use a lightweight official Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app


COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy  the project files into the container
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the FastAPI server
# host 0.0.0.0 makes it reachable outside the container
# workers 1 is correct here — the pipeline runs as a thread inside the process
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]