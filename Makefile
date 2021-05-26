.PHONY: update_dependencies test build_image test_image
pwd = $(shell pwd)
tests = $(wildcard *.tests.py)

requirements.txt:
	python -m pip install -U --user pipreqs
	pipreqs --print ./ | sort > requirements.txt

init:
	python -m pip install -U --user -r requirements.txt

test: $(tests)
	pytest --cov=periscope ./tests

build_image:
	docker build -t periscope .

test_image: build_image
	docker run -it --rm --entrypoint '/bin/sh' -v $(pwd)/tests/:/usr/src/app/tests/:z -v $(pwd)/example.yaml:/usr/src/app/example.yaml:z periscope -c 'python -m unittest discover -v ./tests'
