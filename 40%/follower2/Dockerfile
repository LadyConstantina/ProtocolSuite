# syntax=docker/dockerfile:1

FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine

WORKDIR /flask-follower2
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD [ "python", "main.py"]