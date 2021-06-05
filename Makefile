.PHONY: init update build test build_image test_image publish
pwd = $(shell pwd)
version = $(shell poetry version -s)
short_version = $(shell poetry version -s | cut -d'+' -f1)

init:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
	python -m pip install --user -U poetry-dynamic-versioning

update:
	poetry update
	poetry-dynamic-versioning
	poetry export --output requirements.txt
	poetry export --dev --output requirements.dev.txt

install: init
	poetry install

format: install
	poetry run isort pipecheck tests
	poetry run black pipecheck tests

lint: format
	poetry run flake8 pipecheck tests --show-source --statistics --count

build: lint
	poetry build

test: build
	poetry run pytest

publish:
	poetry publish

build_image:
	docker build -t pipecheck:$(short_version) .

test_image: build_image
	docker run --rm --entrypoint '/bin/sh' \
	-v $(pwd)/tests/:/usr/src/app/tests/:z \
	-v $(pwd)/example.yaml:/usr/src/app/example.yaml:z \
	pipecheck:$(short_version) \
	-c '\
		apk add --no-cache musl-dev python3-dev gcc && \
		python -m pip install -r requirements.dev.txt && \
		pytest -v -x ./tests -k "not ping" \
	'

publish_image: test_image
	docker tag pipecheck:$(version) docker.io/mriedmann/pipecheck:$(version)
	docker tag pipecheck:$(version) docker.io/mriedmann/pipecheck:latest
	docker push docker.io/mriedmann/pipecheck:$(version)
	docker push docker.io/mriedmann/pipecheck:latest
