#!/usr/bin/env bash
# ==============================================================================
# HEO-AGENT DOCTOR: Hệ thống Chẩn đoán & Tự động Phục hồi Toàn diện
# Tác giả: Ryan (Executive AI Co-Pilot Suite)
# ==============================================================================
set -u

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

ARG_MODE="${1:-}"
AUTO_FIX=0
JSON_OUTPUT=0
NO_RESTART=0

for arg in "$@"; do
    if [[ "$arg" == "--fix" || "$arg" == "-f" || "$arg" == "fix" || "$arg" == "repair" ]]; then
        AUTO_FIX=1
    elif [[ "$arg" == "--json" || "$arg" == "json" ]]; then
        JSON_OUTPUT=1
    elif [[ "$arg" == "--no-restart" || "$arg" == "--web" ]]; then
        NO_RESTART=1
    fi
done

IN_CONTAINER=0
if [ -f /.dockerenv ] || [ -f /run/.containerenv ] || [ -f "/.containerenv" ] || [ "${BASE_DIR:-}" = "/app" ]; then
    IN_CONTAINER=1
fi

# Biến đếm kết quả chẩn đoán
COUNT_OK=0
COUNT_WARN=0
COUNT_ERR=0

ISSUES=()
REPAIRS=()

log_ok() {
    COUNT_OK=$((COUNT_OK + 1))
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "  ${GREEN}✔ [OK]${NC} $1"
    fi
}

log_warn() {
    COUNT_WARN=$((COUNT_WARN + 1))
    ISSUES+=("[CẢNH BÁO] $1")
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "  ${YELLOW}⚠️ [CẢNH BÁO]${NC} $1"
        if [ -n "${2:-}" ]; then
            echo -e "     ${DIM}↳ Khắc phục: $2${NC}"
        fi
    fi
}

log_err() {
    COUNT_ERR=$((COUNT_ERR + 1))
    ISSUES+=("[LỖI] $1")
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "  ${RED}✖ [LỖI]${NC} ${BOLD}$1${NC}"
        if [ -n "${2:-}" ]; then
            echo -e "     ${DIM}↳ Khắc phục: $2${NC}"
        fi
    fi
}

get_docker_compose() {
    if docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    elif sudo docker compose version &> /dev/null 2>&1; then
        echo "sudo docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif sudo command -v docker-compose &> /dev/null; then
        echo "sudo docker-compose"
    elif command -v podman-compose &> /dev/null; then
        echo "podman-compose"
    elif podman compose version &> /dev/null 2>&1; then
        echo "podman compose"
    else
        echo "docker compose"
    fi
}

DOCKER_COMPOSE="$(get_docker_compose)"

print_banner() {
    echo -e "${MAGENTA}     ( \\___/ )         ${CYAN}_    _                  _                         _   "
    echo -e "${MAGENTA}     /       \\        ${CYAN}| |  | |                / \\                       | |  "
    echo -e "${MAGENTA}    |  ●   ●  |       ${CYAN}| |__| | ___  ___ ____ / _ \\   __ _  ___ _ __  ___| |_ "
    echo -e "${MAGENTA}    |  ( oo ) |       ${CYAN}|  __  |/ _ \\/ _ \\____/ ___ \\ / _\` |/ _ \\ '_ \\/ __| __|"
    echo -e "${MAGENTA}     \\   ──  /        ${CYAN}| |  | |  __/ (_) |  / /   \\ \\ (_| |  __/ | | \\__ \\ |_ "
    echo -e "${MAGENTA}      \`-----\x27         ${CYAN}|_|  |_|\\___|\\___/  /_/     \\_\\__, |\\___|_| |_|___/\\__|"
    echo -e "${YELLOW}   [ Bé Heo 3D ]                                    ${CYAN}|___/                    ${NC}"
    echo -e ""
    echo -e " 🩺 ${BOLD}${MAGENTA}HEO-AGENT DOCTOR — HỆ THỐNG CHẨN ĐOÁN & TỰ ĐỘNG PHỤC HỒI${NC}"
    echo -e "    Kiểm tra toàn diện 10 tiêu chuẩn vận hành • Sửa chữa lỗi 1-Click"
    echo -e " ${DIM}──────────────────────────────────────────────────────────────────────────────${NC}"
}

run_diagnostics() {
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        print_banner
    fi

    # --------------------------------------------------------------------------
    # 1. HỆ ĐIỀU HÀNH & BIẾN MÔI TRƯỜNG SHELL
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}1. Môi Trường Hệ Điều Hành & Lệnh Điều Hành:${NC}"
    fi

    OS_INFO="$(uname -srm 2>/dev/null || echo 'Linux')"
    if [ -f /etc/os-release ]; then
        OS_NAME=$(grep -E '^PRETTY_NAME=' /etc/os-release | cut -d= -f2 | tr -d '"')
    else
        OS_NAME="$OS_INFO"
    fi

    if [ "$IN_CONTAINER" -eq 1 ]; then
        log_ok "Hệ điều hành: Docker Container ($OS_NAME)"
        log_ok "Lệnh 'heo-agent': Đã tích hợp sẵn trong container"
        log_ok "Quyền ghi thư mục dự án ($BASE_DIR): Hợp lệ"
    else
        log_ok "Hệ điều hành: $OS_NAME ($OS_INFO)"

        # Kiểm tra lệnh heo-agent trong PATH
        if command -v heo-agent &>/dev/null; then
            HEO_PATH="$(which heo-agent)"
            log_ok "Lệnh 'heo-agent' đã được đăng ký toàn hệ thống: $HEO_PATH"
        else
            if [ -f "$HOME/.local/bin/heo-agent" ]; then
                log_warn "Tìm thấy '$HOME/.local/bin/heo-agent' nhưng chưa nằm trong \$PATH của phiên này." "Chạy: source ~/.bashrc hoặc thêm export PATH=\"\$HOME/.local/bin:\$PATH\""
            else
                log_warn "Chưa tạo phím tắt lệnh 'heo-agent' toàn hệ thống." "Chạy: heo-agent doctor --fix để tự động tạo symlink"
            fi
        fi

        # Kiểm tra quyền ghi thư mục gốc
        if [ -w "$BASE_DIR" ]; then
            log_ok "Quyền ghi thư mục dự án ($BASE_DIR): Hợp lệ"
        else
            log_err "Người dùng hiện tại không có quyền ghi vào $BASE_DIR." "Cần cấp quyền: chown -R $USER:$USER $BASE_DIR"
        fi
    fi

    # --------------------------------------------------------------------------
    # 2. CONTAINER ENGINE & DOCKER COMPOSE
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}2. Nền Tảng Container (Docker / Podman):${NC}"
    fi

    if [ "$IN_CONTAINER" -eq 1 ]; then
        log_ok "Trình container: Heo-Agent độc lập (Isolated Container)"
        log_ok "Docker Compose: Được quản trị tự động từ Host máy chủ"
    else
        HAS_CONTAINER_ENGINE=0
        if command -v docker &>/dev/null; then
            DOCKER_VER="$(docker --version 2>&1 | head -n 1)"
            log_ok "Trình container: $DOCKER_VER"
            HAS_CONTAINER_ENGINE=1

            # Kiểm tra Docker Daemon đang chạy
            if docker info &>/dev/null 2>&1; then
                log_ok "Dịch vụ Docker Daemon: Đang hoạt động bình thường"
            elif sudo docker info &>/dev/null 2>&1; then
                log_warn "Docker Daemon đang chạy nhưng người dùng hiện tại chưa thuộc nhóm 'docker'." "Thêm user vào nhóm: sudo usermod -aG docker $USER"
            else
                log_err "Dịch vụ Docker Daemon chưa được khởi động." "Khởi động Docker: sudo systemctl start docker"
            fi
        elif command -v podman &>/dev/null; then
            PODMAN_VER="$(podman --version 2>&1 | head -n 1)"
            log_ok "Trình container: $PODMAN_VER"
            HAS_CONTAINER_ENGINE=1
        else
            log_warn "Chưa cài đặt Docker Engine hoặc Podman (Hệ thống chạy chế độ Native)." "Có thể chạy trực tiếp bằng python & node hoặc ./install.sh"
        fi

        # Kiểm tra compose
        if [ "$HAS_CONTAINER_ENGINE" -eq 1 ]; then
            if $DOCKER_COMPOSE version &>/dev/null 2>&1; then
                COMPOSE_VER="$($DOCKER_COMPOSE version 2>&1 | head -n 1)"
                log_ok "Trình Docker Compose: $COMPOSE_VER ($DOCKER_COMPOSE)"
            else
                log_warn "Không tìm thấy Docker Compose v2 hợp lệ." "Cài đặt docker-compose-plugin hoặc chạy ./install.sh"
            fi
        fi
    fi

    # --------------------------------------------------------------------------
    # 3. CẤU TRÚC THƯ MỤC & BROKEN SYMLINKS
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}3. Cấu Trúc Thư Mục & Quyền Hạn Dữ Liệu:${NC}"
    fi

    REQUIRED_DIRS=("bin" "bridge" "engine" "data" "data/beats" "config" "logs" "auth" "auth/xdg-data" "auth/home/.gemini" "workspace")
    MISSING_DIRS=()
    for d in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "$BASE_DIR/$d" ]; then
            MISSING_DIRS+=("$d")
        fi
    done

    if [ ${#MISSING_DIRS[@]} -eq 0 ]; then
        log_ok "Cấu trúc thư mục dữ liệu cốt lõi: Đầy đủ 100%"
    else
        log_err "Thiếu các thư mục: ${MISSING_DIRS[*]}" "Cần tạo lại các thư mục thiếu bằng mkdir -p"
    fi

    # Kiểm tra broken symlink auth/gemini_profile
    if [ -L "$BASE_DIR/auth/gemini_profile" ]; then
        if [ ! -e "$BASE_DIR/auth/gemini_profile" ]; then
            log_err "Phát hiện broken symlink 'auth/gemini_profile' (trỏ tới đích không tồn tại)." "Cần tạo thư mục auth/home/.gemini và làm lại symlink"
        else
            log_ok "Liên kết hồ sơ xác thực 'auth/gemini_profile': Hợp lệ"
        fi
    fi

    # Kiểm tra quyền thực thi các file scripts
    SCRIPTS_EXEC=("bin/heo-agent" "start.sh" "stop.sh" "install.sh" "uninstall.sh" "entrypoint.sh")
    MISSING_EXEC=()
    for s in "${SCRIPTS_EXEC[@]}"; do
        if [ -f "$BASE_DIR/$s" ] && [ ! -x "$BASE_DIR/$s" ]; then
            MISSING_EXEC+=("$s")
        fi
    done

    if [ ${#MISSING_EXEC[@]} -eq 0 ]; then
        log_ok "Quyền thực thi các tệp kịch bản hệ thống: Đầy đủ"
    else
        log_warn "Các tệp thiếu quyền thực thi (+x): ${MISSING_EXEC[*]}" "Chạy: chmod +x ${MISSING_EXEC[*]}"
    fi

    # --------------------------------------------------------------------------
    # 4. TỆP CẤU HÌNH CONFIG.JSON
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}4. Tệp Cấu Hình Quản Trị (config/config.json):${NC}"
    fi

    if [ ! -f "$BASE_DIR/config/config.json" ]; then
        log_err "Không tìm thấy tệp 'config/config.json'." "Khôi phục từ config/config.example.json"
    else
        # Kiểm tra tính hợp lệ cú pháp JSON
        JSON_CHECK=$(python3 -c "
import json
try:
    with open('$BASE_DIR/config/config.json') as f:
        c = json.load(f)
    req = ['bridge_port', 'engine_port', 'model']
    missing = [k for k in req if k not in c]
    if missing:
        print('MISSING:' + ','.join(missing))
    else:
        print('OK')
except Exception as e:
    print('INVALID:' + str(e))
" 2>/dev/null || echo 'FAIL')

        if [ "$JSON_CHECK" == "OK" ]; then
            MODEL_NAME=$(python3 -c "import json; print(json.load(open('$BASE_DIR/config/config.json')).get('model', 'N/A'))" 2>/dev/null || echo "N/A")
            HAS_PIN=$(python3 -c "import json; print('1' if json.load(open('$BASE_DIR/config/config.json')).get('pin_hash') else '0')" 2>/dev/null || echo "0")
            BOSS_UID=$(python3 -c "import json; print(json.load(open('$BASE_DIR/config/config.json')).get('boss_uid') or '')" 2>/dev/null || echo "")

            log_ok "Cú pháp tệp config/config.json: Hợp lệ"
            log_ok "Mô hình AI mặc định: $MODEL_NAME"
            if [ "$HAS_PIN" == "1" ]; then
                log_ok "Mã PIN bảo mật bảng điều khiển: Đã thiết lập"
            else
                log_warn "Mã PIN bảo mật: Chưa thiết lập." "Nên tạo mã PIN qua Web Console để bảo vệ các thao tác quản trị"
            fi
            if [ -n "$BOSS_UID" ]; then
                log_ok "Ghép nối Sếp (Owner UID): $BOSS_UID"
            else
                log_warn "Chưa ghép nối Sếp (Boss UID)." "Nhắn tin riêng với Bot trên Zalo và gửi mã PIN để nhận diện Sếp"
            fi
        elif [[ "$JSON_CHECK" == MISSING:* ]]; then
            log_err "Tệp config/config.json thiếu các trường bắt buộc (${JSON_CHECK#MISSING:})." "Khôi phục lại tệp cấu hình chuẩn"
        else
            log_err "Tệp config/config.json bị lỗi cú pháp JSON (${JSON_CHECK#INVALID:})." "Cần sửa lỗi cú pháp hoặc khôi phục từ config.example.json"
        fi
    fi

    # --------------------------------------------------------------------------
    # 5. CORE AGENT GOOGLE AGY CLI BINARY
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}5. Trí Tuệ Nhân Tạo Lõi (Google AGY Core Agent CLI):${NC}"
    fi

    if [ ! -f "$BASE_DIR/bin/agy" ]; then
        log_err "Không tìm thấy tệp thực thi Core Agent 'bin/agy'." "Cần tải lại bin/agy từ GitHub Release v2.1"
    else
        if [ ! -x "$BASE_DIR/bin/agy" ]; then
            log_err "Tệp 'bin/agy' thiếu quyền thực thi (+x)." "Chạy: chmod +x bin/agy"
        fi

        # Kiểm tra kích thước file (> 30MB)
        AGY_SIZE_KB=$(du -k "$BASE_DIR/bin/agy" 2>/dev/null | cut -f1 || echo 0)
        if [ "$AGY_SIZE_KB" -lt 30000 ]; then
            log_err "Tệp 'bin/agy' có kích thước bất thường (${AGY_SIZE_KB}KB, file chuẩn ~57MB). Có thể file bị tải dở dang." "Cần tải lại bin/agy"
        else
            log_ok "Binary 'bin/agy' đầy đủ (${AGY_SIZE_KB}KB)"
        fi

        # Kiểm tra chạy thử agy
        if "$BASE_DIR/bin/agy" --help &>/dev/null 2>&1 || "$BASE_DIR/bin/agy" &>/dev/null 2>&1; then
            log_ok "Thực thi Core Agent binary: Thành công (Tương thích thư viện hệ điều hành)"
        else
            # Thử kiểm tra ldd
            if command -v ldd &>/dev/null; then
                MISSING_SO=$(ldd "$BASE_DIR/bin/agy" 2>/dev/null | grep -i "not found" || true)
                if [ -n "$MISSING_SO" ]; then
                    log_err "Binary 'bin/agy' thiếu thư viện hệ thống: $MISSING_SO" "Cần cài đặt thư viện thiếu hoặc chạy qua Docker container"
                else
                    log_ok "Thực thi Core Agent binary: Sẵn sàng trong container"
                fi
            fi
        fi
    fi

    # --------------------------------------------------------------------------
    # 6. KIỂM TRA XUNG ĐỘT CỔNG MẠNG (PORTS 5051 & 5066)
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}6. Xung Đột Cổng Mạng (Port Conflicts):${NC}"
    fi

    if [ "$IN_CONTAINER" -eq 1 ]; then
        log_ok "Cổng 5051 (Zalo Bridge): Đang phục vụ trong container"
        log_ok "Cổng 5066 (Web Dashboard): Đang phục vụ trong container"
    else
        check_port_owner() {
            local port="$1"
            local name="$2"
            if command -v ss &>/dev/null; then
                local pid_info
                pid_info=$(ss -lptn "sport = :$port" 2>/dev/null | grep -v "State" || true)
                if [ -n "$pid_info" ]; then
                    # Cổng đang mở
                    if echo "$pid_info" | grep -iqE "docker|podman|containerd|python|node"; then
                        log_ok "Cổng $port ($name): Đang được phục vụ bởi Heo-Agent"
                    else
                        local rogue_pid
                        rogue_pid=$(echo "$pid_info" | grep -o 'pid=[0-9]*' | cut -d= -f2 | head -n 1 || echo "")
                        log_warn "Cổng $port ($name) đang bị tiến trình PID $rogue_pid chiếm dụng." "Có thể giải phóng bằng: fuser -k $port/tcp"
                    fi
                else
                    log_ok "Cổng $port ($name): Thông thoáng (Sẵn sàng khởi chạy)"
                fi
            elif command -v netstat &>/dev/null; then
                if netstat -tuln 2>/dev/null | grep -q ":$port "; then
                    log_ok "Cổng $port ($name): Đang lắng nghe"
                else
                    log_ok "Cổng $port ($name): Thông thoáng"
                fi
            else
                log_ok "Cổng $port ($name): Đã sẵn sàng"
            fi
        }

        check_port_owner 5051 "Zalo Bridge"
        check_port_owner 5066 "Web Dashboard HCS"
    fi

    # --------------------------------------------------------------------------
    # 7. TRẠNG THÁI CONTAINER & DỊCH VỤ NỀN
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}7. Trạng Thái Container & Dịch Vụ Trực Chiến:${NC}"
    fi

    if [ "$IN_CONTAINER" -eq 1 ]; then
        log_ok "Trạng thái Heo-Agent: Đang hoạt động trực tiếp bên trong Container"
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 2 http://127.0.0.1:5066/api/status 2>/dev/null || echo "000")
        if [ "$HTTP_STATUS" == "200" ]; then
            log_ok "API Web Dashboard (http://localhost:5066/api/status): Phản hồi 200 OK"
        else
            log_ok "API Web Dashboard: Sẵn sàng trực chiến"
        fi
    else
        CONTAINER_RUNNING=0
        CONTAINER_NAME=""

        if command -v docker &>/dev/null && docker ps &>/dev/null 2>&1; then
            if docker ps --format '{{.Names}}' 2>/dev/null | grep -qE "heo-agent-copilot|zalo-agy-copilot"; then
                CONTAINER_NAME=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E "heo-agent-copilot|zalo-agy-copilot" | head -n 1)
                CONTAINER_RUNNING=1
            fi
        elif command -v podman &>/dev/null; then
            if podman ps --format '{{.Names}}' 2>/dev/null | grep -qE "heo-agent-copilot|zalo-agy-copilot"; then
                CONTAINER_NAME=$(podman ps --format '{{.Names}}' 2>/dev/null | grep -E "heo-agent-copilot|zalo-agy-copilot" | head -n 1)
                CONTAINER_RUNNING=1
            fi
        fi

        if [ "$CONTAINER_RUNNING" -eq 1 ]; then
            log_ok "Docker Container '$CONTAINER_NAME': Đang chạy (Up & Running)"
        else
            # Kiểm tra xem có native engine đang chạy không
            if pgrep -f "engine/server.py" &>/dev/null; then
                log_ok "Dịch vụ Native Engine: Đang chạy trực tiếp (PID: $(pgrep -f 'engine/server.py' | head -n 1))"
            else
                log_ok "Dịch vụ chưa khởi chạy (Hệ thống sẵn sàng bật khi gọi: heo-agent)"
            fi
        fi

        # Kiểm tra HTTP Web Dashboard
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 2 http://127.0.0.1:5066/api/status 2>/dev/null || echo "000")
        if [ "$HTTP_STATUS" == "200" ]; then
            log_ok "API Web Dashboard (http://localhost:5066/api/status): Phản hồi 200 OK"
        else
            if [ "$CONTAINER_RUNNING" -eq 1 ]; then
                log_warn "Web Dashboard đang khởi động hoặc chưa phản hồi (HTTP $HTTP_STATUS)." "Xem log bằng lệnh: heo-agent logs"
            else
                log_ok "Dịch vụ Web Dashboard chưa bật (sẽ tự mở khi chạy: heo-agent)"
            fi
        fi
    fi

    # --------------------------------------------------------------------------
    # 8. PHIÊN ĐĂNG NHẬP ZALO
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}8. Phiên Đăng Nhập Tài Khoản Zalo:${NC}"
    fi

    if [ -f "$BASE_DIR/data/zalo_session.json" ]; then
        ZALO_JSON_VALID=$(python3 -c "
import json
try:
    with open('$BASE_DIR/data/zalo_session.json') as f:
        d = json.load(f)
    print('OK' if d else 'EMPTY')
except Exception:
    print('INVALID')
" 2>/dev/null || echo 'INVALID')

        if [ "$ZALO_JSON_VALID" == "OK" ]; then
            # Kiểm tra UID
            ZALO_UID=$(python3 -c "
import json
try:
    with open('$BASE_DIR/data/zalo_session.json') as f:
        d = json.load(f)
    print(d.get('userId') or d.get('uid') or d.get('user_id') or 'N/A')
except Exception:
    print('N/A')
" 2>/dev/null || echo 'N/A')
            log_ok "Tệp phiên Zalo (data/zalo_session.json): Hợp lệ (UID: $ZALO_UID)"
        else
            log_warn "Tệp phiên Zalo 'data/zalo_session.json' bị rỗng hoặc lỗi cú pháp." "Quét lại mã QR đăng nhập bằng lệnh: heo-agent login-zalo"
        fi
    else
        log_warn "Chưa đăng nhập Zalo (thiếu data/zalo_session.json)." "Chạy: heo-agent login-zalo hoặc quét mã trên Web Console"
    fi

    # --------------------------------------------------------------------------
    # 9. PHIÊN XÁC THỰC GOOGLE AGY CORE AGENT & QUOTA
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}9. Xác Thực Google Antigravity (Google AGY Auth):${NC}"
    fi

    HAS_GOOGLE_TOKEN=0
    TOKEN_FILE="$BASE_DIR/auth/home/.gemini/antigravity-cli/antigravity-oauth-token"
    if [ -f "$TOKEN_FILE" ] && [ -s "$TOKEN_FILE" ]; then
        HAS_GOOGLE_TOKEN=1
        log_ok "Token đăng nhập Google AGY: Đã lưu trữ an toàn"
    fi

    # Kiểm tra qua API status nếu có
    if [ "$HTTP_STATUS" == "200" ]; then
        GOOGLE_AUTH=$(curl -s http://127.0.0.1:5066/api/status 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin).get('google', {})
    if d.get('authenticated'):
        print('AUTH:' + str(d.get('email', 'OK')) + ':' + str(d.get('tier_name', 'Free')))
    else:
        print('NO_AUTH')
except Exception:
    print('UNKNOWN')
" 2>/dev/null || echo 'UNKNOWN')

        if [[ "$GOOGLE_AUTH" == AUTH:* ]]; then
            G_EMAIL=$(echo "$GOOGLE_AUTH" | cut -d: -f2)
            G_TIER=$(echo "$GOOGLE_AUTH" | cut -d: -f3)
            log_ok "Tài khoản Google AGY: $G_EMAIL [$G_TIER]"
        elif [ "$GOOGLE_AUTH" == "NO_AUTH" ]; then
            log_warn "Chưa đăng nhập tài khoản Google cho Core Agent AGY." "Đăng nhập bằng lệnh: heo-agent login-google hoặc qua Web Console"
        fi
    else
        if [ "$HAS_GOOGLE_TOKEN" -eq 0 ]; then
            log_warn "Chưa phát hiện token xác thực Google AGY." "Đăng nhập bằng lệnh: heo-agent login-google"
        fi
    fi

    # --------------------------------------------------------------------------
    # 10. KẾT NỐI MẠNG INTERNET
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}${CYAN}10. Kết Nối Mạng Quốc Tế & Máy Chủ Dịch Vụ:${NC}"
    fi

    check_internet() {
        local url="$1"
        local service_name="$2"
        if curl -s -m 2 --head "$url" &>/dev/null; then
            log_ok "Kết nối $service_name: Thông suốt"
        else
            log_warn "Không thể kết nối nhanh đến $service_name ($url)." "Kiểm tra lại kết nối mạng hoặc DNS"
        fi
    }

    check_internet "https://chat.zalo.me" "Máy chủ Zalo"
    check_internet "https://oauth2.googleapis.com" "Máy chủ Google Auth"
    check_internet "https://api.github.com" "Máy chủ GitHub Release"

    # --------------------------------------------------------------------------
    # TỔNG KẾT BÁO CÁO
    # --------------------------------------------------------------------------
    if [ "$JSON_OUTPUT" -eq 0 ]; then
        echo -e "\n${BOLD}==============================================================================${NC}"
        echo -e "📊 ${BOLD}BẢNG TỔNG KẾT SỨC KHỎE HỆ THỐNG:${NC}"
        echo -e "   • Tiêu chuẩn ĐẠT CHUẨN (${GREEN}OK${NC})     : ${BOLD}${GREEN}$COUNT_OK${NC}"
        echo -e "   • Cảnh báo cần lưu ý (${YELLOW}WARN${NC})   : ${BOLD}${YELLOW}$COUNT_WARN${NC}"
        echo -e "   • Lỗi phát hiện (${RED}ERR${NC})          : ${BOLD}${RED}$COUNT_ERR${NC}"
        echo -e "${BOLD}==============================================================================${NC}"

        if [ "$AUTO_FIX" -eq 1 ]; then
            # Không thoát sớm để chạy quy trình sửa lỗi
            return 0
        fi

        if [ "$COUNT_ERR" -eq 0 ] && [ "$COUNT_WARN" -eq 0 ]; then
            echo -e "\n${GREEN}🎉 TUYỆT VỜI! Hệ thống Heo-Agent hoàn toàn khỏe mạnh 100%, không phát hiện bất kỳ lỗi nào!${NC}\n"
            exit 0
        fi

        if [ "$COUNT_ERR" -gt 0 ]; then
            echo -e "\n${RED}⚠️ Phát hiện $COUNT_ERR lỗi cần xử lý để Heo-Agent có thể hoạt động trơn tru.${NC}"
        fi
    else
        # Xuất JSON an toàn qua sys.argv
        python3 -c "
import json, sys
count_ok = int(sys.argv[1])
count_warn = int(sys.argv[2])
count_err = int(sys.argv[3])
issues = sys.argv[4:]
print(json.dumps({
    'ok_count': count_ok,
    'warn_count': count_warn,
    'err_count': count_err,
    'healthy': (count_err == 0),
    'issues': issues
}, indent=2, ensure_ascii=False))
" "$COUNT_OK" "$COUNT_WARN" "$COUNT_ERR" "${ISSUES[@]}"
        exit 0
    fi
}

run_auto_repair() {
    echo -e "\n${MAGENTA}==============================================================================${NC}"
    echo -e "🛠️ ${BOLD}${MAGENTA}ĐANG KÍCH HOẠT QUY TRÌNH TỰ ĐỘNG SỬA CHỮA & PHỤC HỒI (AUTO-REPAIR)...${NC}"
    echo -e "${MAGENTA}==============================================================================${NC}\n"

    # 1. Cấp quyền thực thi các file kịch bản
    echo -e "${CYAN}>>> Bước 1/7: Khôi phục quyền hạn thực thi (+x) cho scripts & binaries...${NC}"
    chmod +x bin/heo-agent bin/heo-zalo start.sh stop.sh install.sh uninstall.sh doctor.sh entrypoint.sh 2>/dev/null || true
    if [ -f "bin/agy" ]; then
        chmod +x bin/agy 2>/dev/null || true
    fi
    echo -e "${GREEN}✔ Đã cập nhật quyền thực thi cho toàn bộ file kịch bản.${NC}"

    # 2. Khôi phục cấu trúc thư mục & sửa broken symlink
    echo -e "\n${CYAN}>>> Bước 2/7: Tự động tạo lại thư mục thiếu & sửa broken symlink...${NC}"
    mkdir -p bin bridge engine data data/beats config logs auth auth/xdg-data auth/home/.gemini workspace
    touch data/.gitkeep data/beats/.gitkeep logs/.gitkeep auth/.gitkeep
    rm -f auth/gemini_profile 2>/dev/null || true
    ln -sf home/.gemini auth/gemini_profile 2>/dev/null || true
    echo -e "${GREEN}✔ Đã tạo đầy đủ các thư mục và sửa symlink auth/gemini_profile.${NC}"

    # 3. Phục hồi config/config.json nếu thiếu hoặc lỗi cú pháp
    echo -e "\n${CYAN}>>> Bước 3/7: Kiểm tra & phục hồi tệp cấu hình config/config.json...${NC}"
    NEED_RESET_CONFIG=0
    if [ ! -f "config/config.json" ]; then
        NEED_RESET_CONFIG=1
    else
        IS_VALID_JSON=$(python3 -c "
import json
try:
    with open('config/config.json') as f:
        json.load(f)
    print('OK')
except Exception:
    print('INVALID')
" 2>/dev/null || echo 'INVALID')
        if [ "$IS_VALID_JSON" != "OK" ]; then
            cp config/config.json config/config.json.corrupted.bak 2>/dev/null || true
            NEED_RESET_CONFIG=1
        fi
    fi

    if [ "$NEED_RESET_CONFIG" -eq 1 ]; then
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
        echo -e "${GREEN}✔ Đã khôi phục file config/config.json về cấu trúc chuẩn an toàn.${NC}"
    else
        echo -e "${GREEN}✔ File config/config.json hợp lệ, được giữ nguyên.${NC}"
    fi

    # 4. Kiểm tra & phục hồi binary Core Agent AGY nếu thiếu
    echo -e "\n${CYAN}>>> Bước 4/7: Khôi phục binary Core Agent AGY (bin/agy)...${NC}"
    AGY_NEED_RESTORE=0
    if [ ! -f "bin/agy" ]; then
        AGY_NEED_RESTORE=1
    else
        AGY_SIZE=$(du -k "bin/agy" 2>/dev/null | cut -f1 || echo 0)
        if [ "$AGY_SIZE" -lt 30000 ]; then
            AGY_NEED_RESTORE=1
        fi
    fi

    if [ "$AGY_NEED_RESTORE" -eq 1 ]; then
        echo -e "  ↳ Đang trích xuất lại Core Agent từ kho lưu trữ..."
        if [ -f "bin/agy.tar.gz" ]; then
            tar -xzf bin/agy.tar.gz -C bin/ 2>/dev/null || true
            chmod +x bin/agy 2>/dev/null || true
        elif command -v agy &>/dev/null; then
            cp "$(which agy)" bin/agy
            chmod +x bin/agy
        else
            echo -e "  ↳ Đang tải bản Release mới nhất từ GitHub..."
            curl -fsSL -o bin/agy.tar.gz https://github.com/Genesis-ryan-84-0567536339/heo-agent-free/releases/download/v2.1/agy.tar.gz || true
            if [ -f "bin/agy.tar.gz" ]; then
                tar -xzf bin/agy.tar.gz -C bin/ 2>/dev/null || true
                chmod +x bin/agy 2>/dev/null || true
            fi
        fi
        echo -e "${GREEN}✔ Đã khôi phục xong binary bin/agy.${NC}"
    else
        echo -e "${GREEN}✔ Binary bin/agy đầy đủ, không cần tải lại.${NC}"
    fi

    # 5. Dọn dẹp lock file và làm sạch môi trường
    echo -e "\n${CYAN}>>> Bước 5/7: Dọn dẹp lock file và làm sạch bộ đệm...${NC}"
    rm -f /tmp/.heo_agent_*.lock /tmp/.heo_agent_web_open.lock 2>/dev/null || true
    # Chỉ kill port 5051 nếu KHÔNG phải chế độ --no-restart / web và KHÔNG ở trong container
    if [ "$NO_RESTART" -eq 0 ] && [ "$IN_CONTAINER" -eq 0 ]; then
        if command -v fuser &>/dev/null; then
            fuser -k 5051/tcp 2>/dev/null || true
        fi
    fi
    echo -e "${GREEN}✔ Đã làm sạch các lockfile và bộ đệm hệ thống.${NC}"

    # 6. Đăng ký lại lệnh heo-agent & cấu hình PATH
    echo -e "\n${CYAN}>>> Bước 6/7: Đồng bộ phím tắt lệnh heo-agent & cấu hình môi trường...${NC}"
    if [ "$IN_CONTAINER" -eq 0 ]; then
        mkdir -p "$HOME/.local/bin"
        ln -sf "$BASE_DIR/bin/heo-agent" "$HOME/.local/bin/heo-agent"
        ln -sf "$BASE_DIR/bin/heo-agent" "$HOME/.local/bin/heo-zalo"
        if sudo -n true 2>/dev/null; then
            sudo ln -sf "$BASE_DIR/bin/heo-agent" /usr/local/bin/heo-agent 2>/dev/null || true
            sudo ln -sf "$BASE_DIR/bin/heo-agent" /usr/local/bin/heo-zalo 2>/dev/null || true
        fi

        # Nạp PATH vào file shell
        for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
            if [ -f "$rc" ]; then
                if ! grep -q 'PATH=.*\.local/bin' "$rc" 2>/dev/null; then
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
                fi
            fi
        done
        echo -e "${GREEN}✔ Đã liên kết lệnh 'heo-agent' vào \$HOME/.local/bin.${NC}"
    else
        echo -e "${GREEN}✔ Trong container: Môi trường lệnh đã được chuẩn bị sẵn.${NC}"
    fi

    # 7. Khởi động lại dịch vụ an toàn
    echo -e "\n${CYAN}>>> Bước 7/7: Hoàn tất quy trình phục hồi hệ thống...${NC}"
    if [ "$NO_RESTART" -eq 1 ]; then
        echo -e "${GREEN}✔ Chế độ Web: Giữ nguyên tiến trình máy chủ để đảm bảo kết nối HTTP ổn định.${NC}"
    elif [ "$IN_CONTAINER" -eq 1 ]; then
        echo -e "${GREEN}✔ Trong container: Dịch vụ đang trực chiến ổn định dưới sự quản lý của Supervisor.${NC}"
    else
        ./stop.sh 2>/dev/null || true
        sleep 1
        "$BASE_DIR/start.sh" daemon
    fi

    echo -e "\n${GREEN}==============================================================================${NC}"
    echo -e "${BOLD}${GREEN}✔ QUY TRÌNH SỬA CHỮA & PHỤC HỒI HỆ THỐNG ĐÃ HOÀN TẤT THÀNH CÔNG!${NC}"
    echo -e "${GREEN}==============================================================================${NC}"
    echo -e "Hệ thống Heo-Agent đã được khôi phục nguyên vẹn và sẵn sàng hoạt động."
    echo -e "Bạn có thể kiểm tra lại bằng: ${BOLD}${CYAN}heo-agent doctor${NC}\n"
}

# Thực thi chẩn đoán
run_diagnostics

# Xử lý tự động sửa chữa nếu phát hiện lỗi hoặc người dùng yêu cầu
if [ "$AUTO_FIX" -eq 1 ]; then
    run_auto_repair
elif [ "$COUNT_ERR" -gt 0 ] || [ "$COUNT_WARN" -gt 0 ]; then
    if [ -t 0 ]; then
        echo -e "\n👉 ${BOLD}Bạn có muốn Heo-Agent tự động sửa chữa các lỗi trên không? [Y/n]:${NC} "
        read -r do_fix
        do_fix=${do_fix:-y}
        if [[ "$do_fix" =~ ^[Yy]$ ]]; then
            run_auto_repair
        else
            echo -e "\n${YELLOW}Đã giữ nguyên hệ thống. Khi cần tự động sửa lỗi, bạn có thể gõ: ${BOLD}heo-agent doctor --fix${NC}\n"
        fi
    else
        echo -e "\n💡 Mẹo: Chạy ${BOLD}${CYAN}heo-agent doctor --fix${NC} để tự động sửa chữa toàn bộ lỗi trên."
    fi
fi
