FROM python:3.7.3
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

RUN mkdir /app
WORKDIR /app

ADD ./src/local/requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

ADD ./src/local /app/local

ENTRYPOINT ["python3", "-m", "local.main"]
