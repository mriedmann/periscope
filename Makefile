.PHONY: init bump bump-minor update build test build_image test_image publish
pwd = $(shell pwd)
version = $(shell poetry version -s)
short_version = $(shell poetry version -s | cut -d'+' -f1)

init:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
	
bump:
	which gh || { echo "gh (github cli) not installed!"; exit 1; }
	poetry version $(shell IFS=. read -r a b c<<<"$(version)";echo "$$a.$$((b+1)).0")
	poetry version | xargs -i git commit -a -m "bump major-version from $(version) to {}"
	git push
	poetry version -s | xargs -i gh release create v{}

bump-minor:
	which gh || { echo "gh (github cli) not installed!"; exit 1; }
	poetry version $(shell IFS=. read -r a b c<<<"$(version)";echo "$$a.$$b.$$((c+1))")
	poetry version | xargs -i git commit -a -m "bump minor-version from $(version) to {}"
	git push
	poetry version -s | xargs -i gh release create v{}

update:
	poetry update
	poetry export --output requirements.txt
	poetry export --dev --output requirements.dev.txt

install: init
	poetry install

lint: install
	poetry run flake8 pipecheck tests --show-source --statistics --count

format: lint
	poetry run isort pipecheck tests
	poetry run black pipecheck tests

build: install
	poetry build

test: build
	poetry run pytest

publish:
	@poetry config pypi-token.pypi "$(PYPI_TOKEN)"
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

publish_image:
	docker tag pipecheck:$(short_version) ghcr.io/mriedmann/pipecheck:$(short_version)
	docker tag pipecheck:$(short_version) ghcr.io/mriedmann/pipecheck:latest
	docker push ghcr.io/mriedmann/pipecheck:$(short_version)
	docker push ghcr.io/mriedmann/pipecheck:latest
