FROM gliderlabs/alpine:3.4

RUN apk add --update --no-cache python python-dev py-pip build-base linux-headers bsd-compat-headers

RUN mkdir /app
WORKDIR /app

ADD requirements.txt /app/
RUN pip install -r requirements.txt

ADD *.py /app/

ENTRYPOINT ["python", "main.py"]
