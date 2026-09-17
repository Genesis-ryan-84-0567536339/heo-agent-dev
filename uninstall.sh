#!/usr/bin/env bash
# ==============================================================================
# Heo-Agent (Bé Heo) — Clean & Uninstall Script
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo -e "${YELLOW}"
echo "=============================================================================="
echo " 🧹 DỌN DẸP & GỠ BỎ ZALO-AGY COPILOT (BÉ HEO)"
echo "=============================================================================="
echo -e "${NC}"

# 1. Dừng container và tiến trình
echo -e "${CYAN}>>> Bước 1: Dừng các container và tiến trình...${NC}"
./stop.sh 2>/dev/null || true

# 2. Xóa Docker containers & volumes nếu có
if command -v docker &> /dev/null; then
    echo -e "${CYAN}>>> Bước 2: Dọn dẹp Docker container và network...${NC}"
    if docker compose version &> /dev/null 2>&1; then
        docker compose down -v --remove-orphans 2>/dev/null || true
    elif sudo docker compose version &> /dev/null 2>&1; then
        sudo docker compose down -v --remove-orphans 2>/dev/null || true
    fi
fi

# Xóa podman container cũ nếu từng chạy bằng podman
if command -v podman &> /dev/null; then
    podman rm -f heo-agent-copilot zalo-agy-copilot 2>/dev/null || true
fi

# 3. Hỏi người dùng có muốn xóa Docker Image không
if [ -t 0 ]; then
    read -r -p "👉 Bạn có muốn xóa Docker Image 'heo-agent:latest' để giải phóng dung lượng không? [Y/n]: " remove_image
else
    read -r -p "👉 Bạn có muốn xóa Docker Image 'heo-agent:latest' để giải phóng dung lượng không? [Y/n]: " remove_image || remove_image="y"
fi
remove_image=${remove_image:-y}
if [[ "$remove_image" =~ ^[Yy]$ ]]; then
    echo -e "${CYAN}Đang xóa Docker Image 'heo-agent:latest' / 'zalo-agy:latest'...${NC}"
    if command -v docker &> /dev/null; then
        docker rmi -f heo-agent:latest zalo-agy:latest 2>/dev/null || sudo docker rmi -f heo-agent:latest zalo-agy:latest 2>/dev/null || true
    fi
    if command -v podman &> /dev/null; then
        podman rmi -f heo-agent:latest zalo-agy:latest 2>/dev/null || true
        podman rmi -f $(podman images -q -f "dangling=true") 2>/dev/null || true
    fi
    echo -e "${GREEN}✔ Đã xóa image.${NC}"
fi

# 4. Gỡ bỏ lệnh heo-agent & heo-zalo toàn hệ thống
echo -e "${CYAN}>>> Bước 3: Gỡ bỏ phím tắt lệnh heo-agent & heo-zalo...${NC}"
rm -f "$HOME/.local/bin/heo-agent" "$HOME/.local/bin/heo-zalo"
if sudo -n true 2>/dev/null; then
    sudo rm -f /usr/local/bin/heo-agent /usr/local/bin/heo-zalo 2>/dev/null || true
fi
echo -e "${GREEN}✔ Đã gỡ bỏ symlink heo-agent và heo-zalo.${NC}"

# 5. Dọn dẹp logs và cache
rm -rf logs/* bin/agy*
echo -e "${GREEN}✔ Đã dọn dẹp thư mục logs và bin/agy.${NC}"

# 6. Tùy chọn xóa dữ liệu xác thực
if [ -t 0 ]; then
    read -r -p "⚠️ Bạn có muốn xóa sạch phiên đăng nhập Zalo & Google (auth/)? [y/N]: " wipe_auth
else
    read -r -p "⚠️ Bạn có muốn xóa sạch phiên đăng nhập Zalo & Google (auth/)? [y/N]: " wipe_auth || wipe_auth="n"
fi
wipe_auth=${wipe_auth:-n}
if [[ "$wipe_auth" =~ ^[Yy]$ ]]; then
    rm -rf auth/*
    echo -e "${GREEN}✔ Đã xóa sạch dữ liệu đăng nhập auth/.${NC}"
else
    echo -e "${CYAN}ℹ Giữ lại dữ liệu đăng nhập trong auth/ cho lần cài đặt sau.${NC}"
fi

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}✔ HOÀN TẤT DỌN DẸP HỆ THỐNG THÀNH CÔNG!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
