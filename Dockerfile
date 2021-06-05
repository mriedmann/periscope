FROM docker.io/library/python:3.9-alpine

ARG VERSION=0.1.0

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir "pipecheck==${VERSION}"

ENTRYPOINT [ "python", "-m", "pipecheck" ]