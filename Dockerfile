# Base image
FROM python:3.13-slim

# 필수인가?
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

# 필수인가?
EXPOSE 8000

# Run entrypoint.sh
CMD ["/entrypoint.sh"]
