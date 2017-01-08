FROM gliderlabs/alpine:3.4

ENV AWS_ACCESS_KEY_ID=AKIAJ4RBE2DG3IFNHBEA
ENV AWS_SECRET_ACCESS_KEY=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
ENV AWS_DEFAULT_REGION=eu-west-1
ENV AWS_SNS_TOPIC_ARN=arn:aws:sns:eu-west-1:236205202378:Alexa-Chromecast
ENV CHROMECAST_NAME=Front Room

RUN apk add --update --no-cache python python-dev py-pip build-base linux-headers

RUN mkdir /app
WORKDIR /app

ADD requirements.txt /app
RUN pip install -r requirements.txt

ADD *.py /app

ENTRYPOINT ['python', 'main.py']
