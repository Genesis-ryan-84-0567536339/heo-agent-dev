#!/usr/bin/env bash
# start.sh: Khởi động nhanh hệ thống Heo-Agent (Bé Heo)
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
    elif podman-compose version &> /dev/null 2>&1; then
        echo "podman-compose"
    elif podman compose version &> /dev/null 2>&1; then
        echo "podman compose"
    elif sudo -n docker compose version &> /dev/null 2>&1; then
        echo "sudo docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif sudo -n command -v docker-compose &> /dev/null; then
        echo "sudo docker-compose"
    else
        echo "docker compose"
    fi
}

DOCKER_COMPOSE="$(get_docker_compose)"

# Tự động cấu hình alias cho Podman để tránh hỏi lựa chọn Registry
if command -v podman &>/dev/null; then
    mkdir -p "$HOME/.config/containers/registries.conf.d" 2>/dev/null || true
    # Dọn dẹp alias sai cú pháp có chứa tag (:latest) gây lỗi Podman daemon
    if [ -f "$HOME/.config/containers/registries.conf.d/shortnames.conf" ]; then
        sed -i '/:latest/d' "$HOME/.config/containers/registries.conf.d/shortnames.conf" 2>/dev/null || true
    fi
    if [ ! -f "$HOME/.config/containers/registries.conf.d/shortnames.conf" ] || ! grep -q '"heo-agent"' "$HOME/.config/containers/registries.conf.d/shortnames.conf" 2>/dev/null; then
        cat << 'EOF_REG' > "$HOME/.config/containers/registries.conf.d/shortnames.conf" 2>/dev/null || true
[aliases]
"heo-agent" = "localhost/heo-agent"
EOF_REG
    fi
fi

open_web_ui() {
    local url="http://localhost:5066"
    local lock="/tmp/.heo_agent_web_open.lock"
    local now
    now=$(date +%s 2>/dev/null || echo 0)
    if [ -f "$lock" ]; then
        local last
        last=$(cat "$lock" 2>/dev/null || echo 0)
        if [ $((now - last)) -lt 4 ]; then
            return 0
        fi
    fi
    echo "$now" > "$lock" 2>/dev/null || true

    for i in {1..15}; do
        if curl -s -m 1 "$url" >/dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
    if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
        if command -v xdg-open &>/dev/null; then
            xdg-open "$url" >/dev/null 2>&1 &
        elif command -v google-chrome &>/dev/null; then
            google-chrome "$url" >/dev/null 2>&1 &
        elif command -v firefox &>/dev/null; then
            firefox "$url" >/dev/null 2>&1 &
        elif command -v gio &>/dev/null; then
            gio open "$url" >/dev/null 2>&1 &
        fi
    elif command -v wslview &>/dev/null; then
        wslview "$url" >/dev/null 2>&1 &
    elif command -v open &>/dev/null; then
        open "$url" >/dev/null 2>&1 &
    fi
}

if [[ "$MODE" == "--tui" || "$MODE" == "tui" ]]; then
    echo "🖥️ Đang khởi chạy giao diện TUI..."
    (sleep 2 && open_web_ui) &
    if [[ -f "docker-compose.yml" ]] && command -v docker &> /dev/null; then
        $DOCKER_COMPOSE run --rm app tui
    else
        python3 cli/tui.py
    fi
else
    echo "🚀 Đang khởi chạy Heo-Agent (Bé Heo) chế độ nền (Daemon 24/7)..."
    if [[ -f "docker-compose.yml" ]] && command -v docker &> /dev/null; then
        $DOCKER_COMPOSE up -d
        echo "✔ Đã khởi động Docker container! Xem log bằng lệnh: heo-agent logs hoặc $DOCKER_COMPOSE logs -f"
    else
        echo "ℹ Khởi chạy chế độ Native Daemon..."
        mkdir -p logs
        python3 engine/server.py >> logs/engine.log 2>&1 &
        (cd bridge && node bot.js >> ../logs/zalo.log 2>&1 &)
        echo "✔ Đã khởi chạy các dịch vụ Native! Xem log tại logs/"
    fi
    open_web_ui
    echo "🌐 Đã tự động mở Web Dashboard tại: http://localhost:5066"
fi
