# FROM python:alpine3.18
# FROM python:latest

FROM python:3.10.13-slim-bookworm
WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y g++ && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt

ENV MM_API_URL="http://localhost:8065/api/v4"
ENV MM_URL="http://localhost:8065"
ENV TOGETHER_API_KEY="ac17a88fb15afc19f632fc58d39d177814f3ead1d013f7adc9bce9f3ccf33580"
ENV APP_SECRET_KEY="somerandomstring"

CMD ["python", "./server.py"]
# RUN cd ./src/
# CMD ["gunicorn", "-c", "gunicorn.conf.py"]

ENV PORT=5555

EXPOSE 5555