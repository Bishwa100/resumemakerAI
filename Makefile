.PHONY: build run clean logs exec

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