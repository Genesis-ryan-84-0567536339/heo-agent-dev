#!/usr/bin/env bash
# start.sh: Khởi động nhanh hệ thống Zalo-AGY Copilot
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

MODE="${1:-daemon}"

if [[ "$MODE" == "--tui" || "$MODE" == "tui" ]]; then
    echo "🖥️ Đang khởi chạy giao diện TUI..."
    if command -v docker compose &> /dev/null && [[ -f "docker-compose.yml" ]]; then
        docker compose run --rm -it app tui
    else
        python3 cli/tui.py
    fi
else
    echo "🚀 Đang khởi chạy Zalo-AGY Copilot chế độ nền (Daemon 24/7)..."
    if command -v docker &> /dev/null && docker compose version &> /dev/null && [[ -f "docker-compose.yml" ]]; then
        docker compose up -d
        echo "✔ Đã khởi động Docker container! Xem log bằng lệnh: docker compose logs -f"
    else
        echo "ℹ Khởi chạy chế độ Native Daemon..."
        mkdir -p logs
        python3 engine/server.py >> logs/engine.log 2>&1 &
        (cd bridge && node bot.js >> ../logs/zalo.log 2>&1 &)
        echo "✔ Đã khởi chạy các dịch vụ Native! Xem log tại logs/"
    fi
fi
