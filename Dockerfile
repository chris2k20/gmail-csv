# Use an official Python runtime with Debian as a parent image
FROM python:slim-buster

# Set an environment variable with the default value
ARG SOURCE_COMMIT
ENV SOURCE_COMMIT="${SOURCE_COMMIT}"

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' worker

# Install necessary packages
# USER root
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends gcc libc6-dev linux-headers-amd64 python3-dev make g++ wkhtmltopdf \
#     && rm -rf /var/lib/apt/lists/*

# Switch back to the non-root user
USER worker
WORKDIR /home/worker

# Install pipenv or just pip based on your preference
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir --user pipenv

# Ensure scripts in .local are usable
ENV PATH="/home/worker/.local/bin:${PATH}"

# Copy the current directory contents into the container at /home/worker
COPY --chown=worker:worker . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# Make port 8080 available to the outside world
EXPOSE 8080

# Define environment variable to specify that the application is running in production
ENV FLASK_ENV=production

# Run the application with Gunicorn
CMD ["gunicorn", "-c", "gunicorn.config.py", "--bind", "0.0.0.0:8080", "app:app"]
