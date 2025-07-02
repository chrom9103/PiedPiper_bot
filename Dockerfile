FROM python:3.12.11-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["./start.sh"]

RUN apt-get install -y tzdata && \ ln -sf /usr/share/zoneinfo/Asia/Tokyo/etc/localtime