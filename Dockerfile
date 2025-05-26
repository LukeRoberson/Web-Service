# Use the official Python image from the Docker Hub
# 3.12 is required for now to support Alpine's uwsgi-python3 package
# This tag is the latest Alpine with the latest Python 3.12
# https://pkgs.alpinelinux.org/package/edge/main/x86/uwsgi-python3
FROM python:3.12-alpine
LABEL description="The web-interface service for the AI assistant"
LABEL version="1.0.0"

# Create non-root user with no password
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Set the working directory in the container
WORKDIR /app

# Install uWSGI
RUN apk add --no-cache uwsgi-python3

# Install cURL (for health checks)
RUN apk --no-cache add curl

# Copy the rest of the application code
COPY . .

# Change ownership of the application code to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Create a folder for config files
RUN mkdir -p /app/config

# Start the application using uWSGI
CMD ["uwsgi", "--ini", "uwsgi.ini"]
