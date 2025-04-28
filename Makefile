.PHONY: build run clean logs exec setup generate

# Default target
all: build run

# Build Docker image
build:
	docker-compose build

# Run the application
run:
	docker-compose up

# Run in background
run-detached:
	docker-compose up -d

# Stop and remove containers
stop:
	docker-compose down

# Stop and remove containers, images, and volumes
clean:
	docker-compose down -v --rmi all

# View logs
logs:
	docker-compose logs -f

# Execute a command in the running container
exec:
	docker-compose exec resumemaker bash

# Setup input files from examples
setup:
	@if [ ! -f input/job_description.txt ]; then \
		echo "Creating input/job_description.txt from example"; \
		cp input/job_description.txt.example input/job_description.txt; \
	fi
	@if [ ! -f input/config.json ]; then \
		echo "Copy your resume.pdf to the input directory"; \
		echo "Edit input/config.json with your LinkedIn and GitHub details"; \
	fi

# Generate resume (shortcut)
generate:
	docker-compose up 