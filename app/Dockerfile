FROM python:3.11-slim-bullseye
RUN apt update
RUN apt upgrade -y
RUN apt install -y build-essential
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]