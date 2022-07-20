#!/bin/bash

set -eo pipefail

for v in 3.7 3.8 3.9 3.10; do
    podman build -f Dockerfile.ci --build-arg python_version=$v -t pipecheck-ci:$v .
    podman run --rm -t --name pipecheck-ci-$v -v "$PWD":/usr/src/app:z pipecheck-ci:$v
done