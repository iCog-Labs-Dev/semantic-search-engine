# FROM python:alpine3.18
# FROM python:latest

FROM python:3.10.13-slim-bookworm
WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y g++ && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt

# CMD ["python", "./server.py"]
# RUN cd ./src/
CMD ["gunicorn", "-c", "gunicorn.conf.py"]

ENV PORT=5555

EXPOSE 5555