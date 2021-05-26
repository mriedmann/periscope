.PHONY: update_dependencies test build_image test_image
tests = $(wildcard *.tests.py)

requirements.txt:
	python -m pip install -U --user pipreqs
	pipreqs --force ./

update_dependencies: requirements.txt
	python -m pip install -U --user -r requirements.txt

test: $(tests)
	python -m unittest discover -v --pattern=*_tests.py

build_image:
	docker build -t periscope .

test_image: build_image
	docker run -it --rm --entrypoint '/bin/sh' periscope -c 'cd /usr/src/app/ && python -m unittest discover -v --pattern=*_tests.py'
