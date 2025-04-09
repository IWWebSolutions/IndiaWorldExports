# Use the official Python image with a slim base
FROM python:3.12-slim

# Set environment variables to prevent Python from buffering and writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory in the container
WORKDIR /app

# Install dependencies
# First, copy only requirements.txt to leverage Docker's caching mechanism
COPY requirements.txt /app/

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . /app/

# Expose the port Django will run on (default: 8000)
EXPOSE 8000

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
