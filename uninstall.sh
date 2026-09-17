#!/usr/bin/env bash
# ==============================================================================
# Heo-Agent (Bé Heo) — Clean & Uninstall Script
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Banner nhận diện Heo-Agent kèm Mascot Đầu Heo 3D
echo -e "${MAGENTA}     ( \\___/ )         ${CYAN}_    _                  _                         _   "
echo -e "${MAGENTA}     /       \\        ${CYAN}| |  | |                / \\                       | |  "
echo -e "${MAGENTA}    |  ●   ●  |       ${CYAN}| |__| | ___  ___ ____ / _ \\   __ _  ___ _ __  ___| |_ "
echo -e "${MAGENTA}    |  ( oo ) |       ${CYAN}|  __  |/ _ \\/ _ \\____/ ___ \\ / _\` |/ _ \\ '_ \\/ __| __|"
echo -e "${MAGENTA}     \\   ──  /        ${CYAN}| |  | |  __/ (_) |  / /   \\ \\ (_| |  __/ | | \\__ \\ |_ "
echo -e "${MAGENTA}      \`-----\x27         ${CYAN}|_|  |_|\\___|\\___/  /_/     \\_\\__, |\\___|_| |_|___/\\__|"
echo -e "${YELLOW}   [ Bé Heo 3D ]                                    ${CYAN}|___/                    ${NC}"
echo -e ""
echo -e " 🐷 ${BOLD}${MAGENTA}HEO-AGENT (BÉ HEO) — TRÌNH DỌN DẸP & GỠ BỎ HỆ THỐNG${NC}"
echo -e " ${DIM}──────────────────────────────────────────────────────────────────────────────${NC}"

# Xác định cấp độ dọn dẹp qua tham số dòng lệnh hoặc tương tác
DO_FACTORY_RESET=0
DO_SOFT_CLEAN=0

ARG_CLEAN="${1:-}"
if [[ "$ARG_CLEAN" =~ ^(--all|-y|--clean|--force|--factory-reset|all|clean)$ ]]; then
    DO_FACTORY_RESET=1
elif [ -t 0 ]; then
    echo -e "Bạn muốn chọn cấp độ dọn dẹp nào?"
    echo -e "  ${BOLD}${GREEN}[1] Khôi phục cài đặt gốc 100% (Khuyến nghị để cài mới từ đầu)${NC}"
    echo -e "      • Dừng & xóa container, volumes, networks & Docker image"
    echo -e "      • Xóa sạch 100% phiên Zalo (data/zalo_session.json, profile, lịch sử chat)"
    echo -e "      • Xóa sạch mã PIN bảo mật & hủy ghép nối Sếp (Boss UID)"
    echo -e "      • Xóa sạch phiên xác thực Google AGY Core Agent (auth/)"
    echo -e "      • Gỡ bỏ phím tắt lệnh heo-agent & heo-zalo toàn hệ thống"
    echo -e "  ${YELLOW}[2] Gỡ bỏ nhẹ (Giữ lại phiên Zalo & cấu hình PIN/Boss/Google Auth)${NC}"
    echo -e "      • Dừng container, gỡ lệnh hệ thống, giữ nguyên data/ và config.json"
    echo -e "  ${RED}[3] Hủy thao tác (Thoát)${NC}"
    echo ""
    read -r -p "👉 Nhập lựa chọn [1/2/3] (Mặc định: 1): " user_choice
    user_choice=${user_choice:-1}
    case "$user_choice" in
        1)
            DO_FACTORY_RESET=1
            ;;
        2)
            DO_SOFT_CLEAN=1
            ;;
        *)
            echo -e "\n${YELLOW}Đã hủy thao tác. Hệ thống được giữ nguyên.${NC}\n"
            exit 0
            ;;
    esac
else
    # Môi trường non-interactive (script/CI): Mặc định khôi phục gốc 100% để đảm bảo sạch sẽ
    DO_FACTORY_RESET=1
fi

if [ "$DO_FACTORY_RESET" -eq 1 ]; then
    echo -e "\n${CYAN}>>> Bước 1/6: Dừng container và tiến trình chạy nền...${NC}"
    ./stop.sh 2>/dev/null || true
    if command -v docker &> /dev/null; then
        if docker compose version &> /dev/null 2>&1; then
            docker compose down -v --remove-orphans 2>/dev/null || true
        elif sudo docker compose version &> /dev/null 2>&1; then
            sudo docker compose down -v --remove-orphans 2>/dev/null || true
        elif command -v docker-compose &> /dev/null; then
            docker-compose down -v --remove-orphans 2>/dev/null || sudo docker-compose down -v --remove-orphans 2>/dev/null || true
        fi
    fi
    if command -v podman &> /dev/null; then
        podman rm -f heo-agent-copilot zalo-agy-copilot 2>/dev/null || true
    fi
    if command -v fuser &> /dev/null; then
        fuser -k 5051/tcp 5066/tcp 2>/dev/null || true
    fi
    echo -e "${GREEN}✔ Đã dừng toàn bộ dịch vụ và container.${NC}"

    echo -e "\n${CYAN}>>> Bước 2/6: Xóa Docker Image 'heo-agent:latest' & giải phóng ổ đĩa...${NC}"
    if command -v docker &> /dev/null; then
        docker rmi -f heo-agent:latest zalo-agy:latest 2>/dev/null || sudo docker rmi -f heo-agent:latest zalo-agy:latest 2>/dev/null || true
    fi
    if command -v podman &> /dev/null; then
        podman rmi -f heo-agent:latest zalo-agy:latest 2>/dev/null || true
        podman rmi -f $(podman images -q -f "dangling=true") 2>/dev/null || true
    fi
    echo -e "${GREEN}✔ Đã xóa Docker Image heo-agent:latest.${NC}"

    echo -e "\n${CYAN}>>> Bước 3/6: Gỡ bỏ phím tắt lệnh heo-agent & heo-zalo...${NC}"
    rm -f "$HOME/.local/bin/heo-agent" "$HOME/.local/bin/heo-zalo"
    if sudo -n true 2>/dev/null; then
        sudo rm -f /usr/local/bin/heo-agent /usr/local/bin/heo-zalo 2>/dev/null || true
    fi
    echo -e "${GREEN}✔ Đã gỡ bỏ symlink lệnh khỏi hệ thống.${NC}"

    echo -e "\n${CYAN}>>> Bước 4/6: Xóa sạch phiên kết nối Zalo, mã PIN và liên kết Sếp (Factory Reset)...${NC}"
    rm -rf data/* data/.* 2>/dev/null || true
    mkdir -p data/beats
    touch data/.gitkeep data/beats/.gitkeep
    if [ -f "config/config.example.json" ]; then
        cp config/config.example.json config/config.json
    else
        cat << 'EOF' > config/config.json
{
  "boss_uid": "",
  "boss_name": "Sếp",
  "boss_caller_name": "Sếp",
  "bot_name": "Bé Heo",
  "model": "Gemini 3.8 Flash (High)",
  "bridge_port": 5051,
  "engine_port": 5066,
  "pin_hash": "",
  "auto_claim_boss": true,
  "disclaimer_accepted": false
}
EOF
    fi
    echo -e "${GREEN}✔ Đã xóa sạch phiên Zalo (data/zalo_session.json) & reset cấu hình config/config.json (PIN, Boss UID rỗng, disclaimer=false).${NC}"

    echo -e "\n${CYAN}>>> Bước 5/6: Xóa sạch dữ liệu xác thực Google Core Agent (auth/)...${NC}"
    rm -rf auth/* auth/.* 2>/dev/null || true
    mkdir -p auth/xdg-data auth/home/.gemini
    ln -sf home/.gemini auth/gemini_profile 2>/dev/null || true
    touch auth/.gitkeep
    echo -e "${GREEN}✔ Đã làm sạch toàn bộ thư mục auth/.${NC}"

    echo -e "\n${CYAN}>>> Bước 6/6: Dọn dẹp logs, cache và file tạm...${NC}"
    rm -rf logs/* bin/agy* /tmp/heo-agent* /tmp/.heo_agent* /tmp/zalo_qr.png 2>/dev/null || true
    mkdir -p logs
    touch logs/.gitkeep
    echo -e "${GREEN}✔ Đã dọn dẹp logs/ và bộ nhớ đệm tạm thời.${NC}"

    echo -e "\n${GREEN}==============================================================================${NC}"
    echo -e "${BOLD}${GREEN}✔ HOÀN TẤT DỌN DẸP & KHÔI PHỤC CÀI ĐẶT GỐC (FACTORY RESET 100%)!${NC}"
    echo -e "${GREEN}==============================================================================${NC}"
    echo -e "Toàn bộ phiên Zalo cũ, liên kết Sếp và mã PIN đã được xóa sạch hoàn toàn."
    echo -e "Bây giờ bạn có thể cài đặt mới tinh tươm bằng lệnh: ${BOLD}${CYAN}./install.sh${NC}\n"

else
    # Soft Clean
    echo -e "\n${CYAN}>>> Bước 1/3: Dừng container và tiến trình chạy nền...${NC}"
    ./stop.sh 2>/dev/null || true
    if command -v docker &> /dev/null; then
        if docker compose version &> /dev/null 2>&1; then
            docker compose down 2>/dev/null || true
        elif sudo docker compose version &> /dev/null 2>&1; then
            sudo docker compose down 2>/dev/null || true
        elif command -v docker-compose &> /dev/null; then
            docker-compose down 2>/dev/null || sudo docker-compose down 2>/dev/null || true
        fi
    fi
    if command -v podman &> /dev/null; then
        podman rm -f heo-agent-copilot zalo-agy-copilot 2>/dev/null || true
    fi
    echo -e "${GREEN}✔ Đã dừng dịch vụ container.${NC}"

    echo -e "\n${CYAN}>>> Bước 2/3: Gỡ bỏ phím tắt lệnh heo-agent & heo-zalo...${NC}"
    rm -f "$HOME/.local/bin/heo-agent" "$HOME/.local/bin/heo-zalo"
    if sudo -n true 2>/dev/null; then
        sudo rm -f /usr/local/bin/heo-agent /usr/local/bin/heo-zalo 2>/dev/null || true
    fi
    echo -e "${GREEN}✔ Đã gỡ bỏ symlink lệnh khỏi hệ thống.${NC}"

    echo -e "\n${CYAN}>>> Bước 3/3: Dọn dẹp logs và cache...${NC}"
    rm -rf logs/* bin/agy* /tmp/heo-agent* /tmp/.heo_agent* 2>/dev/null || true
    mkdir -p logs
    touch logs/.gitkeep
    echo -e "${CYAN}ℹ Giữ lại toàn bộ dữ liệu Zalo (data/), mã PIN & Sếp (config/config.json), và Google Auth (auth/).${NC}"

    echo -e "\n${GREEN}==============================================================================${NC}"
    echo -e "${BOLD}${GREEN}✔ HOÀN TẤT GỠ BỎ MỀM (DỮ LIỆU ĐƯỢC BẢO LƯU CHO LẦN SAU)!${NC}"
    echo -e "${GREEN}==============================================================================${NC}\n"
fi
