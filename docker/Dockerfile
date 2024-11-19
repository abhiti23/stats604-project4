# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container to /myapp
WORKDIR /app

# Copy the entire repo from the build context (root of the repo) into the container
COPY .. /app

# Install dependencies (requirements.txt is inside the docker/ folder)
RUN pip install --no-cache-dir -r /app/docker/requirements.txt

# Interactive when running the container 
CMD ["/bin/bash"]
