#!/usr/bin/env bash
# ==============================================================================
# Heo-Agent (Bé Heo) — One-Line Installer & Setup Wizard
# Tiêu chuẩn hóa 100% trên Docker Engine & Docker Compose v2
# Giao diện TUI gọn gàng, thanh tiến độ % trực quan, chống tràn màn hình
# ==============================================================================
set -euo pipefail

INSTALL_LOG="/tmp/heo-agent-install.log"
echo "=== BẮT ĐẦU CÀI ĐẶT HEO-AGENT: $(date) ===" > "$INSTALL_LOG"

# Bảng mã màu ANSI
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Khôi phục con trỏ terminal an toàn khi thoát
restore_cursor() {
    printf "\033[?25h" 2>/dev/null || true
}
trap 'restore_cursor' EXIT INT TERM

# Tự động phát hiện độ rộng cột terminal an toàn, chống tràn dòng
get_term_cols() {
    local c=""
    if [ -t 1 ]; then
        c=$(stty size 2>/dev/null | awk '{print $2}')
        [ -z "$c" ] && c=$(tput cols 2>/dev/null || true)
    fi
    [ -z "$c" ] && c="${COLUMNS:-80}"
    if ! [[ "$c" =~ ^[0-9]+$ ]] || [ "$c" -le 0 ]; then
        c=80
    fi
    echo "$c"
}

# Vẽ thanh tiến độ % dạng thanh ngang gọn gàng [██████░░░░] (12 ký tự)
render_progress_bar() {
    local pct=$1
    local width=12
    local filled=$((pct * width / 100))
    local empty=$((width - filled))
    local bar=""
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done
    echo -n "$bar"
}

# Tự động đọc dòng log gần nhất để hiển thị gợi ý trạng thái theo thời gian thực
get_step_hint() {
    local recent_lines
    recent_lines=$(tail -n 6 "$INSTALL_LOG" 2>/dev/null || true)
    if echo "$recent_lines" | grep -qi "exporting\|naming to\|writing image"; then
        echo "Đóng gói image..."
    elif echo "$recent_lines" | grep -qi "pip\|installing collected packages\|wheel\|whl"; then
        echo "Cài thư viện Python AI..."
    elif echo "$recent_lines" | grep -qi "npm install\|npm ERR\|node_modules"; then
        echo "Cài thư viện Node.js Zalo..."
    elif echo "$recent_lines" | grep -qi "COPY"; then
        echo "Sao chép mã nguồn..."
    elif echo "$recent_lines" | grep -qi "apt-get\|unpacking\|setting up\|deb\|dpkg"; then
        echo "Cài gói hệ thống..."
    elif echo "$recent_lines" | grep -qi "curl\|downloading\|fetching"; then
        echo "Tải dữ liệu..."
    elif echo "$recent_lines" | grep -qi "git clone\|cloning"; then
        echo "Tải mã nguồn GitHub..."
    elif echo "$recent_lines" | grep -qi "tar -xzf\|extracting"; then
        echo "Giải nén Core Agent..."
    else
        echo "Đang xử lý tác vụ nền..."
    fi
}

# Thực thi một tác vụ trong nền với Spinner xoay động và thanh tiến độ % trên DUY NHẤT 1 DÒNG
run_step_with_progress() {
    local step_idx="$1"
    local step_title="$2"
    local start_pct="$3"
    local end_pct="$4"
    shift 4
    local cmd="$*"
    local total_steps=5

    local spin_chars=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local spin_idx=0
    local is_tty=0
    [ -t 1 ] && is_tty=1

    if [ "$is_tty" -eq 1 ]; then
        printf "\033[?25l" # Ẩn con trỏ terminal
    fi

    # Thực thi lệnh trong background và chuyển hướng toàn bộ output vào file log
    eval "$cmd" >> "$INSTALL_LOG" 2>&1 &
    local pid=$!

    local current_pct=$start_pct
    local tick=0

    while kill -0 "$pid" 2>/dev/null; do
        local now
        now=$(date +%s)
        local elapsed=$((now - TOTAL_INSTALL_START_TIME))
        local m=$((elapsed / 60))
        local s=$((elapsed % 60))
        local time_str
        printf -v time_str "%02d:%02d" "$m" "$s"

        tick=$((tick + 1))

        # Tăng dần % mượt mà theo thời gian thực
        if [ "$current_pct" -lt "$((end_pct - 1))" ]; then
            if [ "$step_idx" -eq 4 ]; then
                # Bước 4 build container kéo dài, tăng mỗi 3 nhịp (0.45s) để tiến độ đồng đều
                if [ $((tick % 3)) -eq 0 ]; then
                    current_pct=$((current_pct + 1))
                fi
            else
                if [ $((tick % 2)) -eq 0 ]; then
                    current_pct=$((current_pct + 1))
                fi
            fi
        fi

        local bar
        bar=$(render_progress_bar "$current_pct")
        local spin="${spin_chars[$spin_idx]}"
        spin_idx=$(((spin_idx + 1) % 10))

        if [ "$is_tty" -eq 1 ]; then
            local cols
            cols=$(get_term_cols)

            local title_padded="$step_title"
            while [ "${#title_padded}" -lt 18 ]; do title_padded="${title_padded} "; done
            title_padded="${title_padded:0:18}"

            # Độ dài dòng cơ bản = 52 cột (vừa vặn trên mọi kích thước terminal, kể cả màn hình nhỏ)
            local base_len=52
            local hint_str=""
            # Chỉ hiển thị gợi ý nếu màn hình rộng >= 80 cột để tuyệt đối không bị nhảy dòng
            if [ "$cols" -ge 80 ]; then
                local max_hint=$((cols - base_len - 8))
                if [ "$max_hint" -ge 10 ]; then
                    local hint
                    hint=$(get_step_hint)
                    hint_str=" \033[2m↳ ${hint:0:$max_hint}\033[0m"
                fi
            fi

            # Dùng \r\033[2K để xóa trọn vẹn dòng cũ và ghi đè trên đúng 1 dòng duy nhất
            printf "\r\033[2K${CYAN}%s${NC} ${DIM}[%d/%d]${NC} ${BOLD}%s${NC} [${GREEN}%s${NC}] ${BOLD}%3d%%${NC} ${DIM}(%s)${NC}%b" \
                "$spin" "$step_idx" "$total_steps" "$title_padded" "$bar" "$current_pct" "$time_str" "$hint_str"
        fi

        sleep 0.15
    done

    wait "$pid"
    local exit_code=$?
    local now
    now=$(date +%s)
    local total_elapsed=$((now - TOTAL_INSTALL_START_TIME))
    local tm=$((total_elapsed / 60))
    local ts=$((total_elapsed % 60))
    local time_str
    printf -v time_str "%02d:%02d" "$tm" "$ts"
    local bar_done
    bar_done=$(render_progress_bar "$end_pct")

    if [ "$exit_code" -eq 0 ]; then
        if [ "$step_idx" -eq "$total_steps" ]; then
            if [ "$is_tty" -eq 1 ]; then
                printf "\r\033[2K${GREEN}✔ ${BOLD}[%d/%d] Hoàn tất cài đặt   ${NC} [${GREEN}%s${NC}] ${BOLD}%3d%%${NC} ${DIM}(%s)${NC} ${BOLD}${GREEN}Thành công!${NC}\n" \
                    "$step_idx" "$total_steps" "$bar_done" "$end_pct" "$time_str"
                printf "\033[?25h" # Hiện lại con trỏ terminal
            else
                echo "✔ [${step_idx}/${total_steps}] Hoàn tất cài đặt (${end_pct}%) - Thành công!"
            fi
        else
            if [ "$is_tty" -eq 1 ]; then
                local title_padded="$step_title"
                while [ "${#title_padded}" -lt 18 ]; do title_padded="${title_padded} "; done
                title_padded="${title_padded:0:18}"
                printf "\r\033[2K${GREEN}✔${NC} ${DIM}[%d/%d]${NC} ${BOLD}%s${NC} [${GREEN}%s${NC}] ${BOLD}%3d%%${NC} ${DIM}(%s)${NC}" \
                    "$step_idx" "$total_steps" "$title_padded" "$bar_done" "$end_pct" "$time_str"
            else
                echo "✔ [${step_idx}/${total_steps}] ${step_title} (${end_pct}%) - Xong"
            fi
        fi
        return 0
    else
        restore_cursor
        if [ "$is_tty" -eq 1 ]; then
            printf "\n${RED}✖ [LỖI TẠI BƯỚC %d/%d] %s (Mã lỗi: %d)${NC}\n" "$step_idx" "$total_steps" "$step_title" "$exit_code"
        else
            echo "✖ [LỖI TẠI BƯỚC ${step_idx}/${total_steps}] ${step_title} (Mã lỗi: ${exit_code})"
        fi
        echo -e "\n${RED}========================== 25 DÒNG LOG LỖI GẦN NHẤT ==========================${NC}"
        tail -n 25 "$INSTALL_LOG" 2>/dev/null || true
        echo -e "${RED}==============================================================================${NC}"
        echo -e "${YELLOW}👉 Xem chi tiết toàn bộ nhật ký cài đặt tại: ${INSTALL_LOG}${NC}\n"
        exit "$exit_code"
    fi
}

# Banner khởi động hiện đại chuẩn thương hiệu Heo-Agent kèm Avatar Đầu Heo 3D
clear 2>/dev/null || true
echo -e "${MAGENTA}     ( \\___/ )         ${CYAN}_    _                  _                         _   "
echo -e "${MAGENTA}     /       \\        ${CYAN}| |  | |                / \\                       | |  "
echo -e "${MAGENTA}    |  ●   ●  |       ${CYAN}| |__| | ___  ___ ____ / _ \\   __ _  ___ _ __  ___| |_ "
echo -e "${MAGENTA}    |  ( oo ) |       ${CYAN}|  __  |/ _ \\/ _ \\____/ ___ \\ / _\` |/ _ \\ '_ \\/ __| __|"
echo -e "${MAGENTA}     \\   ──  /        ${CYAN}| |  | |  __/ (_) |  / /   \\ \\ (_| |  __/ | | \\__ \\ |_ "
echo -e "${MAGENTA}      \`-----\x27         ${CYAN}|_|  |_|\\___|\\___/  /_/     \\_\\__, |\\___|_| |_|___/\\__|"
echo -e "${YELLOW}   [ Bé Heo 3D ]                                    ${CYAN}|___/                    ${NC}"
echo -e ""
echo -e " 🐷 ${BOLD}${MAGENTA}HEO-AGENT (BÉ HEO) — TRỢ LÝ AI ĐIỀU HÀNH DOANH NGHIỆP${NC}"
echo -e "    Executive AI Co-Pilot Suite • Powered by Google Antigravity & Zalo"
echo -e "    Tác giả: ${BOLD}Ryan${NC} (${CYAN}genesis.corp.os@gmail.com${NC} • ${CYAN}(+84)090.919.8823${NC})"
echo -e " ${DIM}──────────────────────────────────────────────────────────────────────────────${NC}"
echo -e " 📄 Nhật ký cài đặt chi tiết: ${CYAN}${INSTALL_LOG}${NC}"
echo -e " 💡 Bạn có thể mở terminal khác và gõ: ${DIM}tail -f ${INSTALL_LOG}${NC} để theo dõi"
echo -e " ${DIM}──────────────────────────────────────────────────────────────────────────────${NC}\n"

# Giữ sudo token luôn sống trong quá trình cài đặt nếu người dùng đã có phiên sudo trước đó
if command -v sudo >/dev/null 2>&1; then
    if sudo -n true 2>/dev/null; then
        (while true; do sudo -n true; sleep 50; kill -0 "$$" || exit; done 2>/dev/null &)
    fi
fi

ensure_docker_running() {
    if docker info >/dev/null 2>&1; then
        return 0
    fi
    if command -v systemctl &> /dev/null; then
        if ! systemctl is-active --quiet docker 2>/dev/null; then
            if sudo -n true 2>/dev/null; then
                sudo systemctl enable --now docker 2>/dev/null || true
            fi
        fi
        if ! id -nG "$USER" 2>/dev/null | grep -qw "docker"; then
            if sudo -n true 2>/dev/null; then
                sudo usermod -aG docker "$USER" 2>/dev/null || true
            fi
        fi
    fi
}

install_docker_packages() {
    if command -v dnf &> /dev/null; then
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
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        local os_type="ubuntu"
        if grep -iq "debian" /etc/os-release 2>/dev/null; then
            os_type="debian"
        fi
        curl -fsSL "https://download.docker.com/linux/${os_type}/gpg" | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg || true
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        local codename
        codename=$(. /etc/os-release && echo "$VERSION_CODENAME")
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${os_type} ${codename} stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || sudo apt-get install -y docker.io docker-compose-v2
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm docker docker-compose
    else
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sudo sh /tmp/get-docker.sh
        rm -f /tmp/get-docker.sh
    fi
    ensure_docker_running
}

# ==============================================================================
# BƯỚC 1/5: KIỂM TRA VÀ CHUẨN BỊ DOCKER ENGINE
# ==============================================================================
needs_docker_install=false
is_podman_wrapper=false

if command -v docker &> /dev/null; then
    if docker --version 2>&1 | grep -iq "podman"; then
        is_podman_wrapper=true
        needs_docker_install=true
    elif ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        needs_docker_install=true
    fi
else
    needs_docker_install=true
fi

TOTAL_INSTALL_START_TIME=$(date +%s)

if [ "$needs_docker_install" = true ]; then
    echo -e "${YELLOW}⚠️ Hệ thống chưa có Docker CE hoặc đang dùng Podman giả lập.${NC}"
    if [ -t 0 ]; then
        read -r -p "👉 Bạn có muốn tự động cài đặt Docker CE & Docker Compose v2 chính thức không? [Y/n]: " do_install
    else
        do_install="y"
    fi
    do_install=${do_install:-y}
    if [[ ! "$do_install" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Lỗi: Đã hủy cài đặt. Heo-Agent yêu cầu Docker Engine tiêu chuẩn.${NC}"
        exit 1
    fi
    run_step_with_progress 1 "Cài Docker Engine" 0 20 "install_docker_packages"
else
    run_step_with_progress 1 "Môi trường Docker" 0 20 "ensure_docker_running"
fi

# Tự động chọn lệnh docker compose phù hợp
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif sudo docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="sudo docker compose"
elif command -v podman-compose &> /dev/null; then
    DOCKER_COMPOSE="podman-compose"
elif podman compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="podman compose"
elif command -v docker-compose &> /dev/null && docker-compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
elif sudo command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="sudo docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# ==============================================================================
# BƯỚC 2/5: CHUẨN BỊ MÃ NGUỒN & CẤU TRÚC DỮ LIỆU
# ==============================================================================
prepare_workspace_and_dirs() {
    INSTALL_DIR="heo-agent"
    if [[ -f "docker-compose.yml" ]] && [[ -d "bridge" ]] && [[ -d "engine" ]]; then
        WORKDIR="$(pwd)"
    else
        if [[ ! -d "$INSTALL_DIR" ]]; then
            git clone https://github.com/Genesis-ryan-84-0567536339/heo-agent-free.git "$INSTALL_DIR"
        else
            # Cập nhật code mới nhất nếu folder đã tồn tại
            (cd "$INSTALL_DIR" && git pull origin main 2>/dev/null || git pull 2>/dev/null || true)
        fi
        WORKDIR="$(pwd)/$INSTALL_DIR"
        cd "$WORKDIR"
    fi

    mkdir -p bin data workspace logs auth config auth/xdg-data auth/home/.gemini
    ln -sf home/.gemini auth/gemini_profile 2>/dev/null || true

    # Tự động đồng bộ phiên xác thực Google Core Agent từ máy chủ (secret-tool hoặc ~/.gemini)
    local host_token=""
    if command -v secret-tool >/dev/null 2>&1; then
        host_token=$(secret-tool lookup service gemini username antigravity 2>/dev/null || true)
    fi
    if [ -z "$host_token" ] && [ -f "$HOME/.gemini/antigravity-cli/antigravity-oauth-token" ]; then
        host_token=$(cat "$HOME/.gemini/antigravity-cli/antigravity-oauth-token" 2>/dev/null || true)
    fi
    if [ -n "$host_token" ]; then
        mkdir -p auth/home/.gemini/antigravity-cli
        echo "$host_token" > auth/home/.gemini/antigravity-cli/antigravity-oauth-token
    fi

    if [[ ! -f "config/config.json" ]] && [[ -f "config/config.example.json" ]]; then
        cp config/config.example.json config/config.json
    fi
}

run_step_with_progress 2 "Mã nguồn & Thư mục" 20 40 "prepare_workspace_and_dirs"

# Đảm bảo biến WORKDIR khả dụng
if [[ -f "docker-compose.yml" ]] && [[ -d "bridge" ]] && [[ -d "engine" ]]; then
    WORKDIR="$(pwd)"
else
    WORKDIR="$(pwd)/heo-agent"
    cd "$WORKDIR"
fi

# ==============================================================================
# BƯỚC 3/5: TẢI & THIẾT LẬP CORE AGENT GOOGLE AGY CLI
# ==============================================================================
setup_agy_cli() {
    if [[ -f "bin/agy" ]] && [[ -x "bin/agy" ]]; then
        return 0
    fi

    if [[ -f "bin/agy.tar.gz" ]]; then
        tar -xzf bin/agy.tar.gz -C bin/
        chmod +x bin/agy
        return 0
    fi

    if command -v agy &> /dev/null; then
        cp "$(which agy)" bin/agy
        chmod +x bin/agy
        return 0
    fi

    if [[ -f "$HOME/.local/bin/agy" ]]; then
        cp "$HOME/.local/bin/agy" bin/agy
        chmod +x bin/agy
        return 0
    fi

    # Tải bộ cài AGY 57.6MB từ GitHub Release
    curl -fsSL -o bin/agy.tar.gz https://github.com/Genesis-ryan-84-0567536339/heo-agent-free/releases/download/v2.1/agy.tar.gz || \
    curl -fsSL -o bin/agy.tar.gz https://github.com/Genesis-ryan-84-0567536339/heo-agent-free/releases/download/v1.0.0/agy.tar.gz

    if [[ -f "bin/agy.tar.gz" ]]; then
        tar -xzf bin/agy.tar.gz -C bin/
        chmod +x bin/agy
    fi

    if [[ ! -f "bin/agy" ]]; then
        return 1
    fi
}

run_step_with_progress 3 "Core Agent AGY" 40 60 "setup_agy_cli"

# ==============================================================================
# BƯỚC 4/5: ĐÓNG GÓI & BIÊN DỊCH DOCKER CONTAINER (BUILD IMAGE)
# ==============================================================================
build_docker_image() {
    $DOCKER_COMPOSE build
}

run_step_with_progress 4 "Đóng gói Container" 60 90 "build_docker_image"

# ==============================================================================
# BƯỚC 5/5: CẤU HÌNH MÔI TRƯỜNG & ĐĂNG KÝ LỆNH TOÀN HỆ THỐNG
# ==============================================================================
setup_system_commands() {
    chmod +x bin/heo-agent bin/heo-zalo doctor.sh start.sh stop.sh uninstall.sh 2>/dev/null || true
    mkdir -p "$HOME/.local/bin"
    ln -sf "$WORKDIR/bin/heo-agent" "$HOME/.local/bin/heo-agent"
    ln -sf "$WORKDIR/bin/heo-agent" "$HOME/.local/bin/heo-zalo"

    # Tự động ghi biến PATH vào cấu hình shell của người dùng
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        export PATH="$HOME/.local/bin:$PATH"
        for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
            if [ -f "$rc" ]; then
                if ! grep -q 'PATH=.*\.local/bin' "$rc" 2>/dev/null; then
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
                fi
            fi
        done
    fi

    # Đăng ký vào /usr/local/bin nếu có quyền sudo
    if sudo -n true 2>/dev/null; then
        sudo ln -sf "$WORKDIR/bin/heo-agent" /usr/local/bin/heo-agent 2>/dev/null || true
        sudo ln -sf "$WORKDIR/bin/heo-agent" /usr/local/bin/heo-zalo 2>/dev/null || true
    fi
}

run_step_with_progress 5 "Cấu hình Lệnh CLI" 90 100 "setup_system_commands"

# ==============================================================================
# BẢNG HƯỚNG DẪN LỆNH KHỞI ĐỘNG & LỆNH THÔNG DỤNG
# ==============================================================================
print_commands_guide() {
    echo -e "\n${GREEN}==============================================================================${NC}"
    echo -e "${BOLD}${GREEN}✔ QUÁ TRÌNH CÀI ĐẶT ĐÃ HOÀN TẤT 100%!${NC}"
    echo -e "${GREEN}==============================================================================${NC}"
    echo -e " Lệnh điều hành toàn hệ thống: ${BOLD}${CYAN}heo-agent${NC}  (hoặc ${CYAN}heo-zalo${NC})"
    echo -e " Bảng điều khiển Web Console:  ${BOLD}${CYAN}http://localhost:5066${NC}"
    echo -e " ${DIM}──────────────────────────────────────────────────────────────────────────────${NC}"
    echo -e "\n 🚀 ${BOLD}${YELLOW}1. CÁC LỆNH KHỞI ĐỘNG HỆ THỐNG:${NC}"
    echo -e "    👉 ${CYAN}heo-agent${NC}              : Khởi chạy hệ thống & tự động mở Web Dashboard"
    echo -e "    👉 ${CYAN}heo-agent --bg${NC}         : Chạy chế độ nền (Daemon 24/7 trực chiến ngầm)"
    echo -e "    👉 ${CYAN}heo-agent tui${NC}          : Mở lại Trình cấu hình Terminal & quét mã QR Zalo"
    echo -e "    👉 ${CYAN}heo-agent web${NC}          : Khởi chạy riêng và mở Web Console (cổng 5066)"
    echo -e ""
    echo -e " ⚙️ ${BOLD}${YELLOW}2. CÁC LỆNH THÔNG DỤNG HÀNG NGÀY:${NC}"
    echo -e "    👉 ${CYAN}heo-agent status${NC}       : Giám sát trạng thái hoạt động (Zalo, Quota AI, Bot)"
    echo -e "    👉 ${CYAN}heo-agent doctor${NC}       : Chẩn đoán toàn diện sức khỏe hệ thống (10 tiêu chuẩn)"
    echo -e "    👉 ${CYAN}heo-agent doctor --fix${NC} : Tự động sửa chữa & phục hồi khi gặp sự cố (1-Click)"
    echo -e "    👉 ${CYAN}heo-agent logs${NC}         : Xem luồng nhật ký hoạt động thời gian thực"
    echo -e "    👉 ${CYAN}heo-agent model${NC}        : Xem và đổi mô hình AI (flash, pro, sonnet, opus)"
    echo -e "    👉 ${CYAN}heo-agent effort${NC}       : Điều chỉnh mức suy luận logic (low, medium, high)"
    echo -e "    👉 ${CYAN}heo-agent login-zalo${NC}   : Quét lại mã QR đăng nhập tài khoản Zalo"
    echo -e "    👉 ${CYAN}heo-agent login-google${NC} : Xác thực / Đồng bộ Google AGY Core Agent"
    echo -e "    👉 ${CYAN}heo-agent restart${NC}      : Khởi động lại toàn bộ dịch vụ Heo-Agent"
    echo -e "    👉 ${CYAN}heo-agent stop${NC}         : Dừng toàn bộ hệ thống an toàn"
    echo -e "    👉 ${CYAN}heo-agent uninstall${NC}    : Dọn dẹp sạch sẽ & khôi phục cài đặt gốc (Factory Reset)"
    echo -e " ${DIM}──────────────────────────────────────────────────────────────────────────────${NC}"
    echo -e " 💡 ${DIM}Mẹo: Nếu vừa cài xong gõ 'heo-agent' chưa nhận ngay, hãy gõ: ${CYAN}source ~/.bashrc${NC}\n"
}

# Hiển thị bảng lệnh ngay khi kết thúc cài đặt
print_commands_guide

# Chạy Trình hướng dẫn cấu hình tương tác Terminal (TUI) nếu đang ở phiên tương tác
if [ -t 0 ] && [ -t 1 ]; then
    echo -e "${YELLOW}>>> Đang mở Trình Cấu Hình Tương Tác (TUI Setup Wizard)...${NC}"
    echo -e "${DIM}(Nhấn Ctrl+C bất kỳ lúc nào để quay lại danh sách lệnh phía trên)${NC}\n"
    $DOCKER_COMPOSE run --rm app tui || true
    # Sau khi thoát khỏi TUI, in lại danh sách lệnh để người dùng luôn có sẵn tài liệu trước mắt
    print_commands_guide
fi
