#!/usr/bin/env bash
set -e

# Đảm bảo các thư mục dữ liệu tồn tại
mkdir -p /app/data /app/workspace /app/logs /app/auth/gemini_profile /app/auth/xdg-data /app/bin

# Kiểm tra và giải nén AGY CLI binary nếu có file lưu trữ nén
if [ ! -f /app/bin/agy ] && [ -f /app/bin/agy.tar.gz ]; then
    echo "📦 Đang giải nén AGY CLI binary từ /app/bin/agy.tar.gz..."
    tar -xzf /app/bin/agy.tar.gz -C /app/bin
    chmod +x /app/bin/agy
fi

# Nếu chạy chế độ TUI
if [ "$1" = "tui" ]; then
    exec python3 /app/cli/tui.py
fi

# Nếu chạy chế độ Daemon ngầm
if [ "$1" = "daemon" ]; then
    echo "🚀 Đang khởi chạy Zalo-AGY Copilot chế độ Daemon..."
    export BASE_DIR=/app
    export WORKSPACE_DIR=/app/workspace
    export DATA_DIR=/app/data
    export LOGS_DIR=/app/logs
    export AUTH_DIR=/app/auth
    export GEMINI_DIR=/app/auth/gemini_profile
    export XDG_DATA_HOME=/app/auth/xdg-data
    export AGY_BIN=/app/bin/agy

    python3 /app/engine/server.py >> /app/logs/engine.log 2>&1 &
    ENGINE_PID=$!

    cd /app/bridge
    node bot.js >> /app/logs/zalo.log 2>&1 &
    BRIDGE_PID=$!

    echo "✔ AI Engine PID: $ENGINE_PID"
    echo "✔ Zalo Bridge PID: $BRIDGE_PID"

    trap "kill $ENGINE_PID $BRIDGE_PID; exit 0" SIGINT SIGTERM

    tail -f /app/logs/engine.log /app/logs/zalo.log &
    wait
fi

# Mặc định thực thi lệnh được truyền vào
exec "$@"
