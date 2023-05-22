.PHONY: all

SHELL=/bin/bash -e

.DEFAULT_GOAL := help

DCF_LOCAL = docker-compose

build: ## build dev images
	${DCF_LOCAL} build

up: ## start docker dev environment
	${DCF_LOCAL} up -d
	${DCF_LOCAL} ps

up-no-detach: ## start docker dev environment
	${DCF_LOCAL} up

down: ## stop docker dev environment
	${DCF_LOCAL} down --remove-orphans

purge: ## stop docker dev environment and remove orphans and volumes
	${DCF_LOCAL} down --volumes --remove-orphans
