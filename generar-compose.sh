#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Invalid number of arguments. Expected 2: <docker-compose> <number_of_clients>"
    exit 1
fi

file=$1

cat << EOL > $file
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
EOL
      
python3 generador.py $file $2

cat << EOL >> $file

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOL