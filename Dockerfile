FROM node:20-bookworm

LABEL maintainer="Genesis <contact@genesis.local>"
LABEL description="Heo-Agent (Bé Heo) - Full Executive Assistant Suite"

# Cài đặt Python 3, ffmpeg, sox, audio codecs và các công cụ cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    sox \
    libsox-fmt-all \
    curl \
    ca-certificates \
    git \
    procps \
    tar \
    gzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cài đặt npm dependencies cho Zalo bridge
COPY bridge/package*.json ./bridge/
RUN cd bridge && npm install --production --no-audit --no-fund
ENV NODE_PATH=/app/bridge/node_modules

# Cài đặt Python dependencies cho AI Engine và Terminal UI
COPY engine/requirements.txt ./engine/
COPY cli/requirements.txt ./cli/
RUN pip3 install --no-cache-dir --break-system-packages -r engine/requirements.txt -r cli/requirements.txt

# Sao chép toàn bộ mã nguồn và tài nguyên
COPY bridge/ ./bridge/
COPY engine/ ./engine/
COPY scripts/ ./scripts/
COPY workspace/ ./workspace/
COPY skills/ ./skills/
COPY config/ ./config/
COPY cli/ ./cli/
COPY data/beats/ ./data/beats/
COPY entrypoint.sh ./
COPY start.sh ./
COPY stop.sh ./
COPY DISCLAIMER.md ./

# Cấp quyền thực thi cho các script
RUN chmod +x entrypoint.sh start.sh stop.sh engine/agy_exec.sh scripts/*.py cli/tui.py

# Cổng dịch vụ
EXPOSE 5051 5066

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["tui"]
