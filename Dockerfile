# Use the custom base image
FROM lukerobertson19/base-os:latest

# OCI labels for the image
LABEL org.opencontainers.image.title="AI Assistant Web Interface"
LABEL org.opencontainers.image.description="The web interface for the AI assistant. Provides a user-friendly interface for interacting with the AI assistant to configure and manage the system, as well as view live alerts"
LABEL org.opencontainers.image.base.name="lukerobertson19/base-os:latest"
LABEL org.opencontainers.image.source="https://github.com/LukeRoberson/Web-Service"
LABEL org.opencontainers.image.version="1.0.0"

# The health check URL for the service
LABEL net.networkdirection.healthz="http://localhost:5100/api/health"

# The name of the service, as it should appear in the compose file
LABEL net.networkdirection.service.name="web-interface"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install procps, which includes sysctl
# RUN apk add --no-cache procps

# Set the somaxconn value in sysctl.conf (increase maximum listners for uWSGI)
# RUN echo "net.core.somaxconn=1024" >> /etc/sysctl.conf

# Copy the rest of the application code
COPY . .

# Start the application using uWSGI
CMD ["uwsgi", "--ini", "uwsgi.ini"]
