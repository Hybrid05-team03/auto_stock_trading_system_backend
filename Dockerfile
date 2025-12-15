# Base image
FROM python:3.13-slim

WORKDIR /app

# Copy requirements.txt
COPY auto_stock/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY . /app

# Set permissions
RUN chgrp -R 0 /app && \
    chmod -R g=u /app

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Working directory
WORKDIR /app/auto_stock

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default Command
CMD ["uvicorn", "auto_stock.asgi:application", "--host", "0.0.0.0", "--port", "8000"]