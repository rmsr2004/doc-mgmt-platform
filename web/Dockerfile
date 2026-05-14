FROM python:3.11-slim

WORKDIR /app

RUN apt-get update -y && apt-get install libmagic1 -y && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY run.py .
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/
COPY .env .

EXPOSE 8000

CMD ["python", "run.py"]