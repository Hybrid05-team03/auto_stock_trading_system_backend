# Base image
FROM python:3.13-slim

# Working directory
WORKDIR /app

# Set requirements.txt
COPY /auto_stock/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
  && pip install -r /app/requirements.txt


# Copy source code
COPY . /app

# Copy entrypoint.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run entrypoint.sh
CMD ["/entrypoint.sh"]
