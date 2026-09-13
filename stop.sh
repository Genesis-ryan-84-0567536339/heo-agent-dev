#!/usr/bin/env bash
# stop.sh: Dừng an toàn toàn bộ hệ thống Zalo-AGY Copilot
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "🛑 Đang dừng Zalo-AGY Copilot..."

if command -v docker compose &> /dev/null && [[ -f "docker-compose.yml" ]]; then
    docker compose down
fi

# Dừng cả các tiến trình native nếu có
pkill -f "engine/server.py" 2>/dev/null || true
pkill -f "node bot.js" 2>/dev/null || true

echo "✔ Toàn bộ dịch vụ đã được dừng an toàn."
