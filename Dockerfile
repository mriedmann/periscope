FROM docker.io/library/python:3.9-alpine

WORKDIR /usr/src/app

COPY requirements*.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY pipecheck/ /usr/src/app/pipecheck/

ENTRYPOINT [ "python", "-m", "pipecheck" ]