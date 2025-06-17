# Use a lightweight Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including ffmpeg for whisper
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY Core/requirements.txt ./Core/
RUN pip install --no-cache-dir -r ./Core/requirements.txt

# Copy the entire application code
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=web_app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose the port Flask runs on
EXPOSE 5000

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "web_app:app"] 