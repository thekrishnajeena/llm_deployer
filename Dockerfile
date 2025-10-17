# Use lightweight Python image
FROM python:3.12-slim

# Prevent Python from buffering output (helps with logs)
ENV PYTHONUNBUFFERED=1

# Install git (important for your app)
RUN apt-get update && apt-get install -y git && apt-get clean

# Set working directory
WORKDIR /app

# Copy everything
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for FastAPI
EXPOSE 7860

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
