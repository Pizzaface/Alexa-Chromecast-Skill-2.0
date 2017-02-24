FROM gliderlabs/alpine:3.4

RUN apk update
RUN apk add python python-dev
RUN apk add py-pip
RUN apk add build-base
RUN apk add linux-headers
RUN apk add bsd-compat-headers
RUN apk add libffi-dev

RUN mkdir /app
WORKDIR /app

ADD ./src/local/requirements.txt /app/
RUN pip install -r requirements.txt

ADD ./src/local/*.py /app/

ENTRYPOINT ["python", "main.py"]
