# FROM python:alpine3.18
FROM python:latest
WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install virtualenv
RUN source venv/bin/activate
# RUN pip freeze
# RUN pip install -r requirements.txt
RUN ./install.sh

CMD ["python", "./server.py"]

# ENV PORT=5000

EXPOSE 5000