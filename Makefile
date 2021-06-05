.PHONY: init update build test build_image test_image publish
pwd = $(shell pwd)
version = $(shell poetry version -s)

init:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
	python -m pip install --user -U poetry-dynamic-versioning

update:
	poetry update

install:
	poetry install

build: install
	poetry-dynamic-versioning
	poetry export -f requirements.txt --output requirements.txt
	poetry build

format: build
	poetry run isort pipecheck tests
	poetry run black pipecheck tests

lint: format
	poetry run flake8 pipecheck tests --show-source --statistics --count

test: lint
	poetry run pytest

publish:
	poetry publish

build_image:
	docker build --build-arg VERSION=$(version) -t pipecheck:$(version) .

test_image: build_image
	docker run -it --rm --entrypoint '/bin/sh' -v $(pwd)/tests/:/usr/src/app/tests/:z -v $(pwd)/example.yaml:/usr/src/app/example.yaml:z pipecheck -c 'python -m unittest discover -v ./tests'

publish_image: test_image
	docker tag pipecheck:$(version) docker.io/mriedmann/pipecheck:$(version)
	docker tag pipecheck:$(version) docker.io/mriedmann/pipecheck:latest
	docker push docker.io/mriedmann/pipecheck:$(version)
	docker push docker.io/mriedmann/pipecheck:latest
