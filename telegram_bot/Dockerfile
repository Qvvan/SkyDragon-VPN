FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Создаем директорию для SSH ключей
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y iputils-ping

COPY . /app/

CMD ["python", "main.py"]
