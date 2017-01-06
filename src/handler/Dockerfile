FROM gliderlabs/alpine:3.4
RUN apk add --update --no-cache python python-dev py-pip build-base linux-headers
RUN pip install --upgrade pip
RUN pip install pymysql
RUN pip install pychromecast
ADD youtube.py /root
