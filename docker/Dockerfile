# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container to /myapp
WORKDIR /app

# Copy the entire repo (context is the parent folder)
COPY .. .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Interactive when running the container 
CMD ["/bin/bash"]
