# Dockerfile for Connect Four Game Server + Redis
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc redis-server && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server/ ./server/

# Expose ports (game server default 5001, redis 6379)
EXPOSE 5001 6379

# Start both Redis and game server using supervisord
RUN pip install supervisor
COPY supervisord.conf ./

CMD ["supervisord", "-c", "./supervisord.conf"]
