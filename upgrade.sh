#!/bin/bash

# Ensure required files are up to date (manually handled if needed)

# Pull new images
docker-compose pull || { echo "Error: Failed to pull images."; exit 1; }

# Pull new base images
docker-compose build --pull || { echo "Error: Failed to pull base images."; exit 1; }

# Bring up updated services
docker-compose up -d --build || { echo "Error: Failed to bring up services."; exit 1; }

# Clean up old Docker resources
docker system prune -f

# Done
echo "Upgrade completed."
