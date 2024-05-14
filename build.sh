#!/bin/bash

container_name="road-helper"
port=8080

docker stop $container_name 2>/dev/null || true
docker rm $container_name 2>/dev/null || true

sudo pkill -f "docker-proxy"

docker build -t $container_name .

echo "Starting new container on port $port..."
docker run -d -p $port:$port --name ${container_name} $container_name

echo "Done!"
