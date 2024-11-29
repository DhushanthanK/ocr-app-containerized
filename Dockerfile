# Use an official Ubuntu base image
FROM ubuntu:latest

# Update and install dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /home/app

# Copy the application code into the container
COPY . /home/app

# Create and activate the virtual environment
RUN python3 -m venv myenv

# Install the required Python packages inside the virtual environment
RUN /home/app/myenv/bin/pip install --upgrade pip && \
    /home/app/myenv/bin/pip install -r /home/app/requirements.txt

# Expose the port that the app will run on
EXPOSE 5000

# Command to run the application
CMD ["bash", "-c", "source /home/app/myenv/bin/activate && python3 app.py"]