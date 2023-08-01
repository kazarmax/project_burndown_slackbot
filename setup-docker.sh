#!/bin/bash

#Remove existing containers with burndown and redis
docker rm -f burndown
#docker rm -f redis

#Remove existing images for burndown and redis
docker rmi -f python
docker rmi -f burndown
docker rmi -f redis

#Build the burndown container
docker build -t burndown:latest .

#Create the network
#docker network create maxinet

#Start burndown container
docker run --restart always -dp 8009:8009 --net maxinet --name burndown burndown:latest

#Start redis container
#docker run --restart always -dp 6379:6379 --net maxinet --name redis redis:latest redis-server
