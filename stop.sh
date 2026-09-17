#!/usr/bin/env bash
# stop.sh: Dừng an toàn toàn bộ hệ thống Zalo-AGY Copilot
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
BASE_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
cd "$BASE_DIR"

echo "🛑 Đang dừng Zalo-AGY Copilot..."

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

if [[ -f "docker-compose.yml" ]] && command -v docker &> /dev/null; then
    $DOCKER_COMPOSE down 2>/dev/null || true
fi

# Dừng các container podman cũ nếu có
if command -v podman &> /dev/null; then
    podman stop heo-agent-copilot zalo-agy-copilot 2>/dev/null || true
    podman rm heo-agent-copilot zalo-agy-copilot 2>/dev/null || true
fi

# Dừng cả các tiến trình native nếu có
pkill -f "engine/server.py" 2>/dev/null || true
pkill -f "node bot.js" 2>/dev/null || true

echo "✔ Toàn bộ dịch vụ đã được dừng an toàn."
