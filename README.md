# My Dockerized Application

This repository contains a Dockerized version of my application. You can easily pull the image from Docker Hub and run it on your local machine or any server with Docker installed.

## Prerequisites

- Docker installed on your machine. You can install Docker from [here](https://www.docker.com/get-started).

## Pulling the Image

1. **Log in to Docker Hub** (if not already logged in):

```bash
docker login
```

2. **Pull the Docker image:**

```bash
docker pull dhushanthan/heuristic_kilby:latest
```

3. **Run the Docker container:**

```bash
docker run -p 8080:5000 dhushanthan/heuristic_kilby:latest
```

4. **Access the running container:**

```bash
docker exec -it heuristic_kilby /bin/bash
```

5. **Navigate to the application directory:**

```bash
cd /home/ocr_app/app
```

6. **Run the application:**

```bash
python3 app.py
```