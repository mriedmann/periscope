.PHONY: init bump bump-minor update build test build_image test_image publish
pwd = $(shell pwd)
version = $(shell poetry version -s)
short_version = $(shell poetry version -s | cut -d'+' -d'-' -f1)
helm_version = $(shell cat helm/pipecheck/Chart.yaml | yq '.version')
helm_short_version = $(shell cat helm/pipecheck/Chart.yaml | yq '.version' | cut -d'+' -d'-' -f1)

init:
	pip install poetry
	poetry self add "poetry-dynamic-versioning[plugin]"

check-bump: init
	which yq || { echo "yq not installed!"; exit 1; }
	which git || { echo "git not installed!"; exit 1; }

bump: check-bump
	poetry dynamic-versioning
	sed -i 's/appVersion: .*/appVersion: $(short_version)/' helm/pipecheck/Chart.yaml

helm-bump-major: check-bump
	$(eval helm_new_version = $(shell IFS=. read -r a b c<<<"$(helm_short_version)";echo "$$((a+1)).0.0"))
	sed -i 's/version: .*/version: $(helm_new_version)/' helm/pipecheck/Chart.yaml
	git commit -a -m "bump helm minor-version from $(helm_version) to $(helm_new_version)"

helm-bump: check-bump
	$(eval helm_new_version = $(shell IFS=. read -r a b c<<<"$(helm_short_version)";echo "$$a.$$((b+1)).0"))
	sed -i 's/version: .*/version: $(helm_new_version)/' helm/pipecheck/Chart.yaml
	git commit -a -m "bump helm minor-version from $(helm_version) to $(helm_new_version)"

helm-bump-patch: check-bump
	$(eval helm_new_version = $(shell IFS=. read -r a b c<<<"$(helm_short_version)";echo "$$a.$$b.$$((c+1))"))
	sed -i 's/version: .*/version: $(helm_new_version)/' helm/pipecheck/Chart.yaml
	git commit -a -m "bump helm minor-version from $(helm_version) to $(helm_new_version)"

release:
	git push
	poetry version -s | xargs -i gh release create v{}

update:
	poetry update
	poetry export --output requirements.txt
	poetry export --with dev --output requirements.dev.txt

install: bump
	poetry install

lint: install
	poetry run flake8 pipecheck tests --show-source --statistics --count

format: install
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
