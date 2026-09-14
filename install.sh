#!/usr/bin/env bash
# ==============================================================================
# Zalo-AGY Copilot (Bé Heo) — One-Line Installer & Setup Wizard
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
cat << 'EOF'
  _____       _             _    ______   __ 
 |__  / __ _| | ___       / \  / ___\ \ / / 
   / / / _` | |/ _ \ ___ / _ \| |  _ \ V /  
  / /_| (_| | | (_) |___/ ___ \ |_| | | |   
 |____|\__,_|_|\___/   /_/   \_\____| |_|   
    Executive AI Assistant — Powered by Google Antigravity & Zalo
EOF
echo -e "${NC}"

echo -e "${YELLOW}>>> Bước 1/4: Kiểm tra môi trường hệ thống...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Lỗi: Máy chủ chưa cài đặt Docker. Vui lòng cài Docker trước khi tiếp tục: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Lỗi: Máy chủ chưa cài đặt Docker Compose (v2). Vui lòng cập nhật Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✔ Docker và Docker Compose sẵn sàng!${NC}"

# Kiểm tra thư mục hiện tại
INSTALL_DIR="zalo-agy"
if [[ -f "docker-compose.yml" ]] && [[ -d "bridge" ]] && [[ -d "engine" ]]; then
    WORKDIR="$(pwd)"
else
    if [[ ! -d "$INSTALL_DIR" ]]; then
        echo -e "${YELLOW}>>> Đang tải mã nguồn từ GitHub...${NC}"
        git clone https://github.com/Genesis-ryan-84-0567536339/zalo-agy.git "$INSTALL_DIR"
    fi
    WORKDIR="$(pwd)/$INSTALL_DIR"
    cd "$WORKDIR"
fi

echo -e "${YELLOW}>>> Bước 2/4: Chuẩn bị AGY Binary và Cấu hình...${NC}"
mkdir -p bin data workspace logs auth config auth/gemini_profile auth/xdg-data

# Tìm hoặc tải agy binary
if [[ ! -f "bin/agy" ]]; then
    if [[ -f "bin/agy.tar.gz" ]]; then
        echo -e "${CYAN}Đang giải nén bin/agy.tar.gz...${NC}"
        tar -xzf bin/agy.tar.gz -C bin/
        chmod +x bin/agy
    elif command -v agy &> /dev/null; then
        HOST_AGY="$(which agy)"
        echo -e "${CYAN}Sao chép AGY CLI từ máy chủ (${HOST_AGY})...${NC}"
        cp "$HOST_AGY" bin/agy
        chmod +x bin/agy
    elif [[ -f "$HOME/.local/bin/agy" ]]; then
        echo -e "${CYAN}Sao chép AGY CLI từ $HOME/.local/bin/agy...${NC}"
        cp "$HOME/.local/bin/agy" bin/agy
        chmod +x bin/agy
    else
        echo -e "${CYAN}Đang tải AGY CLI binary từ GitHub Release...${NC}"
        curl -fsSL -o bin/agy.tar.gz https://github.com/Genesis-ryan-84-0567536339/zalo-agy/releases/download/v1.0.0/agy.tar.gz || true
        if [[ -f "bin/agy.tar.gz" ]]; then
            tar -xzf bin/agy.tar.gz -C bin/
            chmod +x bin/agy
        fi
    fi
fi

if [[ ! -f "bin/agy" ]]; then
    echo -e "${RED}Lỗi: Không thể tìm thấy hoặc tải AGY binary. Vui lòng đặt file thực thi agy vào thư mục bin/agy.${NC}"
    exit 1
fi
echo -e "${GREEN}✔ AGY Binary đã sẵn sàng!${NC}"

# Tạo config mặc định nếu chưa có
if [[ ! -f "config/config.json" ]] && [[ -f "config/config.example.json" ]]; then
    cp config/config.example.json config/config.json
fi

echo -e "${YELLOW}>>> Bước 3/4: Đóng gói Docker Container (Build Image)...${NC}"
docker compose build

echo -e "${YELLOW}>>> Bước 4/4: Khởi chạy Trình Cấu hình Trực quan (TUI Setup Wizard)...${NC}"
echo -e "${CYAN}Hệ thống sẽ mở giao diện Terminal tương tác để:${NC}"
echo -e "  1. Xác thực tài khoản Google cho AGY CLI"
echo -e "  2. Hiển thị mã QR để quét đăng nhập Zalo trên điện thoại"
echo -e "  3. Thiết lập quyền Chủ sở hữu (Boss UID)"
echo -e "  4. Mở Bảng điều khiển Live Dashboard giám sát thời gian thực\n"

# Chạy TUI tương tác
docker compose run --rm -it app tui

# Đăng ký lối tắt lệnh heo-zalo toàn hệ thống
chmod +x bin/heo-zalo 2>/dev/null || true
mkdir -p "$HOME/.local/bin"
ln -sf "$WORKDIR/bin/heo-zalo" "$HOME/.local/bin/heo-zalo"
if sudo -n true 2>/dev/null; then
    sudo ln -sf "$WORKDIR/bin/heo-zalo" /usr/local/bin/heo-zalo 2>/dev/null || true
fi

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}✔ CÀI ĐẶT VÀ CẤU HÌNH THÀNH CÔNG!${NC}"
echo -e "Hệ thống đã đăng ký lệnh điều hành toàn hệ thống: ${CYAN}heo-zalo${NC}"
echo -e "\n📌 BỘ LỆNH ĐIỀU HÀNH:"
echo -e "   👉 ${CYAN}heo-zalo${NC}         : Khởi chạy và mở TUI tương tác trực tiếp"
echo -e "   👉 ${CYAN}heo-zalo --bg${NC}    : Chạy ngầm 24/7 trong Docker"
echo -e "   👉 ${CYAN}heo-zalo status${NC}  : Kiểm tra trạng thái máy chủ"
echo -e "   👉 ${CYAN}heo-zalo logs${NC}    : Xem nhật ký hoạt động thời gian thực"
echo -e "   👉 ${CYAN}heo-zalo stop${NC}    : Dừng toàn bộ hệ thống an toàn"
echo -e "${GREEN}==============================================================================${NC}"
