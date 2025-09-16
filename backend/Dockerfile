# Python base with bash available via apt
FROM python:3.12-slim


# Install bash (and any native deps you need later)
RUN apt-get update \
&& apt-get install -y --no-install-recommends bash \
&& rm -rf /var/lib/apt/lists/*


WORKDIR /app


# Copy and install deps first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Copy application code (Flask app + your extractor)
COPY app.py ./
COPY Extract_name_phone_address_toast.py ./


# Declare a data volume inside the container
VOLUME ["/data"]


EXPOSE 5000


# Use Gunicorn in the container
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]