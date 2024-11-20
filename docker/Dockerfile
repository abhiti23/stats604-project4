# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt first (for caching purposes)
COPY docker/requirements.txt /app/requirements.txt

# Install any dependencies that are in the requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Now copy the entire repository into the image
COPY . /app

# Interactive when running the container 
CMD ["/bin/bash"]
