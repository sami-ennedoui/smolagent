# Use a stable, lightweight Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and keep stdout unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your agent script into the container
COPY hardware_agent.py .

# Command to run when the container starts
CMD ["python", "hardware_agent.py"]
