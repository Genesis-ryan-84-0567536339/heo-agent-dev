#!/usr/bin/env bash
# start.sh: Khởi động nhanh hệ thống Zalo-AGY Copilot
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
BASE_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
cd "$BASE_DIR"

MODE="${1:-daemon}"

# Tự động xác định lệnh docker compose chuẩn
get_docker_compose() {
    if docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    elif sudo docker compose version &> /dev/null 2>&1; then
        echo "sudo docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif sudo command -v docker-compose &> /dev/null; then
        echo "sudo docker-compose"
    else
        echo "docker compose"
    fi
}

DOCKER_COMPOSE="$(get_docker_compose)"

if [[ "$MODE" == "--tui" || "$MODE" == "tui" ]]; then
    echo "🖥️ Đang khởi chạy giao diện TUI..."
    if [[ -f "docker-compose.yml" ]] && command -v docker &> /dev/null; then
        $DOCKER_COMPOSE run --rm app tui
    else
        python3 cli/tui.py
    fi
else
    echo "🚀 Đang khởi chạy Zalo-AGY Copilot chế độ nền (Daemon 24/7)..."
    if [[ -f "docker-compose.yml" ]] && command -v docker &> /dev/null; then
        $DOCKER_COMPOSE up -d
        echo "✔ Đã khởi động Docker container! Xem log bằng lệnh: heo-zalo logs hoặc $DOCKER_COMPOSE logs -f"
    else
        echo "ℹ Khởi chạy chế độ Native Daemon..."
        mkdir -p logs
        python3 engine/server.py >> logs/engine.log 2>&1 &
        (cd bridge && node bot.js >> ../logs/zalo.log 2>&1 &)
        echo "✔ Đã khởi chạy các dịch vụ Native! Xem log tại logs/"
    fi
fi
