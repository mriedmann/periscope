FROM docker.io/library/python:3.9-alpine

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY periscope/ ./periscope/

ENTRYPOINT [ "python", "-m", "periscope" ]