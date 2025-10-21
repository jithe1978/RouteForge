FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY Extract_name_phone_address_toast.py .

ENV OUTPUT_DIR=/data
ENV PYTHONUNBUFFERED=1
VOLUME ["/data"]
EXPOSE 5000

# More time for big PDFs
CMD ["gunicorn", "--timeout", "180", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]