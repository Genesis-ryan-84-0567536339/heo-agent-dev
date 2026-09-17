#!/usr/bin/env bash
set -e

git config --system --add safe.directory '*' 2>/dev/null || git config --global --add safe.directory '*' 2>/dev/null || true

# Đảm bảo các thư mục dữ liệu và profile người dùng tồn tại
mkdir -p /app/data /app/workspace /app/logs /app/auth/xdg-data /app/auth/home/.gemini /app/bin
if [ -L /app/auth/gemini_profile ] && [ ! -e /app/auth/gemini_profile ]; then
    rm -f /app/auth/gemini_profile
fi
if [ ! -e /app/auth/gemini_profile ]; then
    ln -sf /app/auth/home/.gemini /app/auth/gemini_profile 2>/dev/null || mkdir -p /app/auth/gemini_profile
fi
export HOME="${HOME:-/app/auth/home}"
git config --global --add safe.directory '*' 2>/dev/null || true

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
    echo "🚀 Đang khởi chạy Heo-Agent (Bé Heo) chế độ Daemon..."
    export BASE_DIR=/app
    export WORKSPACE_DIR=/app/workspace
    export DATA_DIR=/app/data
    export LOGS_DIR=/app/logs
    export AUTH_DIR=/app/auth
    export GEMINI_DIR="${GEMINI_DIR:-/app/auth/home/.gemini}"
    export XDG_DATA_HOME=/app/auth/xdg-data
    export AGY_BIN=/app/bin/agy

    # Khởi chạy AI Engine với auto-restart supervisor
    (
        set +e
        while true; do
            python3 /app/engine/server.py >> /app/logs/engine.log 2>&1
            EXIT_C=$?
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Supervisor] 🔄 AI Engine thoát (mã $EXIT_C). Khởi động lại sau 2s..." >> /app/logs/engine.log
            sleep 2
        done
    ) &
    ENGINE_PID=$!

    # Khởi chạy Zalo Bridge với auto-restart supervisor
    (
        set +e
        cd /app/bridge
        while true; do
            node bot.js >> /app/logs/zalo.log 2>&1
            EXIT_C=$?
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Supervisor] 🔄 Zalo Bridge thoát (mã $EXIT_C). Tự động kết nối lại sau 2s..." >> /app/logs/zalo.log
            sleep 2
        done
    ) &
    BRIDGE_PID=$!

    echo "✔ AI Engine Supervisor PID: $ENGINE_PID"
    echo "✔ Zalo Bridge Supervisor PID: $BRIDGE_PID"

    trap "kill -9 $ENGINE_PID $BRIDGE_PID 2>/dev/null; pkill -f 'python3 /app/engine/server.py' 2>/dev/null; pkill -f 'node bot.js' 2>/dev/null; exit 0" SIGINT SIGTERM

    tail -f /app/logs/engine.log /app/logs/zalo.log &
    wait
fi

# Mặc định thực thi lệnh được truyền vào
exec "$@"
