FROM debian:latest

RUN apt-get update -y && apt-get upgrade && apt-get install -y python3-pip

RUN apt-get install -y python3 python-is-python3

RUN pip install --break-system-packages --upgrade Flask

RUN apt-get install -y npm


