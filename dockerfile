# Use the official Python image with a slim base
FROM python:3.12-slim

# Set environment variables to prevent Python from buffering and writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory in the container
WORKDIR /app

# Install system dependencies for build tools (e.g., for psycopg2 and other dependencies)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements.txt to leverage Docker's caching mechanism
COPY requirements.txt /app/

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . /app/

# Expose the port Django will run on (default: 8000)
EXPOSE 8000

# Use Gunicorn for production instead of the Django dev server
CMD ["gunicorn", "IWE.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]

