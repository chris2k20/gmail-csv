.DEFAULT_GOAL := build
GIT_HASH ?= $(shell git log --format="%h" -n 1)
DOCKER_USERNAME ?= user2k20
APPLICATION_NAME ?= gsheets-wtime
REGISTRY ?= registry.cs95.de

test:
	pylint app.py

build:
	docker build --build-arg "SOURCE_COMMIT=${GIT_HASH}" --tag ${REGISTRY}/${DOCKER_USERNAME}/${APPLICATION_NAME}:${GIT_HASH} .

push:
	docker push ${REGISTRY}/${DOCKER_USERNAME}/${APPLICATION_NAME}:${GIT_HASH}

release:
	docker pull ${REGISTRY}/${DOCKER_USERNAME}/${APPLICATION_NAME}:${GIT_HASH}
	docker tag  ${REGISTRY}/${DOCKER_USERNAME}/${APPLICATION_NAME}:${GIT_HASH} ${REGISTRY}/${DOCKER_USERNAME}/${APPLICATION_NAME}:latest
	docker push ${REGISTRY}/${DOCKER_USERNAME}/${APPLICATION_NAME}:latest

all : build push release

# Thx to Kasper Siig (Source: https://earthly.dev/blog/docker-and-makefiles/)
