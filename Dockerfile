FROM gliderlabs/alpine:3.4

RUN apk add --update --no-cache python python-dev py-pip build-base linux-headers bsd-compat-headers libffi-dev youtube-dl

RUN mkdir /app
WORKDIR /app

ADD ./src/local/requirements.txt /app/
RUN pip install -r requirements.txt

ADD ./src/local/*.py /app/

ENTRYPOINT ["python", "main.py"]
