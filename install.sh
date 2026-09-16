#!/usr/bin/env bash
# ==============================================================================
# Zalo-AGY Copilot (Bé Heo) — One-Line Installer & Setup Wizard
# Tiêu chuẩn hóa 100% trên Docker Engine & Docker Compose v2 (Cross-Platform)
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

ensure_docker_running() {
    if command -v systemctl &> /dev/null; then
        if ! systemctl is-active --quiet docker 2>/dev/null; then
            echo -e "${CYAN}>>> Đang kích hoạt dịch vụ Docker daemon...${NC}"
            sudo systemctl enable --now docker 2>/dev/null || true
        fi
        sudo usermod -aG docker "$USER" 2>/dev/null || true
    fi
}

check_and_install_engine() {
    local needs_docker=false
    local is_podman_wrapper=false

    # 1. Kiểm tra sự hiện diện của docker
    if command -v docker &> /dev/null; then
        # Kiểm tra xem có phải podman giả lập docker không
        if docker --version 2>&1 | grep -iq "podman"; then
            is_podman_wrapper=true
            needs_docker=true
        elif ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
            echo -e "${YELLOW}ℹ Phát hiện Docker CLI nhưng thiếu plugin Docker Compose v2.${NC}"
            needs_docker=true
        fi
    else
        needs_docker=true
    fi

    # Nếu đã có Docker CE và Docker Compose v2 thật
    if [ "$needs_docker" = false ]; then
        echo -e "${GREEN}✔ Đã phát hiện Docker Engine và Docker Compose v2 chính thức sẵn sàng!${NC}"
        ensure_docker_running
        return 0
    fi

    echo -e "${YELLOW}==============================================================================${NC}"
    if [ "$is_podman_wrapper" = true ]; then
        echo -e "${YELLOW}⚠️ Phát hiện hệ thống đang sử dụng Podman / podman-docker giả lập.${NC}"
        echo -e "${CYAN}Do podman-compose có nhiều lỗi cú pháp và không tương thích đầy đủ với Docker Compose v2,"
        echo -e "Zalo-AGY Copilot được thống nhất 100% trên Docker Engine chính thức (Docker CE & Compose v2)"
        echo -e "nhằm đảm bảo chạy mượt mà, đồng nhất trên mọi hệ điều hành (Ubuntu, Debian, Fedora, Arch, macOS, WSL2).${NC}"
        echo -e "${YELLOW}==============================================================================${NC}"
        if [ -t 0 ]; then
            read -r -p "👉 Bạn có muốn tự động gỡ podman-docker và cài đặt Docker CE chính thức không? [Y/n]: " do_install
        else
            read -r -p "👉 Bạn có muốn tự động gỡ podman-docker và cài đặt Docker CE chính thức không? [Y/n]: " do_install || do_install="y"
        fi
    else
        echo -e "${YELLOW}⚠️ Chưa tìm thấy Docker Engine & Docker Compose trên hệ thống.${NC}"
        echo -e "${CYAN}Zalo-AGY Copilot yêu cầu Docker Engine tiêu chuẩn để vận hành container.${NC}"
        echo -e "${YELLOW}==============================================================================${NC}"
        if [ -t 0 ]; then
            read -r -p "👉 Bạn có muốn tự động cài đặt Docker CE & Docker Compose ngay bây giờ không? [Y/n]: " do_install
        else
            read -r -p "👉 Bạn có muốn tự động cài đặt Docker CE & Docker Compose ngay bây giờ không? [Y/n]: " do_install || do_install="y"
        fi
    fi

    do_install=${do_install:-y}
    if [[ ! "$do_install" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Lỗi: Đã hủy cài đặt. Vui lòng cài đặt Docker Engine chính thức tại: https://docs.docker.com/engine/install/${NC}"
        exit 1
    fi

    echo -e "${CYAN}>>> Đang tiến hành cài đặt Docker Engine & Docker Compose chính thức...${NC}"

    if command -v dnf &> /dev/null; then
        # Fedora / RHEL / CentOS / Rocky Linux / AlmaLinux
        echo -e "${CYAN}Cấu hình Docker CE repository qua DNF...${NC}"
        # Gỡ xung đột podman-docker nếu có
        sudo dnf remove -y podman-docker podman-compose 2>/dev/null || true
        sudo dnf -y install dnf-plugins-core 2>/dev/null || sudo dnf -y install 'dnf5-command(config-manager)' 2>/dev/null || true
        if grep -iq "fedora" /etc/os-release 2>/dev/null; then
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo || true
        elif grep -iq "centos" /etc/os-release 2>/dev/null; then
            sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo || true
        else
            sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo || true
        fi
        sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    elif command -v apt-get &> /dev/null; then
        # Ubuntu / Debian / Linux Mint
        echo -e "${CYAN}Cấu hình Docker CE repository qua APT...${NC}"
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        local os_type="ubuntu"
        if grep -iq "debian" /etc/os-release 2>/dev/null; then
            os_type="debian"
        fi
        curl -fsSL "https://download.docker.com/linux/${os_type}/gpg" | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg || true
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        local codename
        codename=$(. /etc/os-release && echo "$VERSION_CODENAME")
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${os_type} ${codename} stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || sudo apt-get install -y docker.io docker-compose-v2
    elif command -v pacman &> /dev/null; then
        # Arch Linux / Manjaro
        echo -e "${CYAN}Cài đặt Docker qua Pacman...${NC}"
        sudo pacman -Sy --noconfirm docker docker-compose
    else
        # Kịch bản cài đặt tự động chính thức từ Docker Inc.
        echo -e "${CYAN}Chạy kịch bản cài đặt chính thức get.docker.com...${NC}"
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sudo sh /tmp/get-docker.sh
        rm -f /tmp/get-docker.sh
    fi

    ensure_docker_running

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Lỗi: Cài đặt Docker không thành công. Vui lòng kiểm tra quyền sudo hoặc cài đặt thủ công.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✔ Cài đặt Docker Engine & Docker Compose v2 thành công!${NC}"
}

check_and_install_engine

# Tự động chọn lệnh docker compose phù hợp (kể cả khi user chưa logout để nạp nhóm docker)
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif sudo docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="sudo docker compose"
elif command -v docker-compose &> /dev/null && docker-compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
elif sudo command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="sudo docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

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
$DOCKER_COMPOSE build

echo -e "${YELLOW}>>> Bước 4/4: Khởi chạy Trình Cấu hình Trực quan (TUI Setup Wizard)...${NC}"
echo -e "${CYAN}Hệ thống sẽ mở giao diện Terminal tương tác để:${NC}"
echo -e "  1. Xác thực tài khoản Google cho AGY CLI"
echo -e "  2. Hiển thị mã QR để quét đăng nhập Zalo trên điện thoại"
echo -e "  3. Thiết lập quyền Chủ sở hữu (Boss UID)"
echo -e "  4. Mở Bảng điều khiển Live Dashboard giám sát thời gian thực\n"

# Chạy TUI tương tác
$DOCKER_COMPOSE run --rm app tui

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
echo -e "   👉 ${CYAN}heo-zalo${NC}              : Mở TUI Dashboard tương tác trực tiếp"
echo -e "   👉 ${CYAN}heo-zalo --bg${NC}         : Khởi chạy chế độ nền (Daemon 24/7) trong Docker"
echo -e "   👉 ${CYAN}heo-zalo status${NC}       : Kiểm tra trạng thái máy chủ"
echo -e "   👉 ${CYAN}heo-zalo logs${NC}         : Xem nhật ký hoạt động thời gian thực"
echo -e "   👉 ${CYAN}heo-zalo restart${NC}      : Khởi động lại dịch vụ"
echo -e "   👉 ${CYAN}heo-zalo stop${NC}         : Dừng toàn bộ hệ thống an toàn"
echo -e "   👉 ${CYAN}heo-zalo uninstall${NC}    : Dọn dẹp & gỡ bỏ toàn bộ container, image"
echo -e "${GREEN}==============================================================================${NC}"
