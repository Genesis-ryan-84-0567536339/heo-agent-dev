#!/usr/bin/env python3
"""
tui.py: Giao diện Terminal TUI Độc lập và Toàn diện cho Zalo-AGY Copilot (Bé Heo)
- Xác thực tài khoản Google cho Antigravity CLI (agy) trực tiếp trên Terminal
- Hiển thị mã QR Code Zalo quét trên điện thoại (qua qrcode-terminal)
- Cấu hình quyền Chủ sở hữu (Boss UID)
- Bảng điều khiển giám sát thời gian thực (Live Monitoring Dashboard)
"""

import os
import sys
import time
import json
import signal
import shutil
import subprocess
import threading
import re
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("Vui lòng cài đặt rich: pip install rich")
    sys.exit(1)

console = Console()

def flush_stdin():
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass

BASE_DIR = os.environ.get("BASE_DIR", str(Path(__file__).parent.parent.resolve()))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
CONFIG_EXAMPLE = os.path.join(BASE_DIR, "config", "config.example.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
AUTH_DIR = os.path.join(BASE_DIR, "auth")
GEMINI_DIR = os.path.join(AUTH_DIR, "gemini_profile")
XDG_DATA_HOME = os.path.join(AUTH_DIR, "xdg-data")
BIN_DIR = os.path.join(BASE_DIR, "bin")
SESSION_FILE = os.path.join(DATA_DIR, "zalo_session.json")

# Ensure required directories exist
for d in [DATA_DIR, WORKSPACE_DIR, LOGS_DIR, AUTH_DIR, GEMINI_DIR, XDG_DATA_HOME, BIN_DIR]:
    os.makedirs(d, exist_ok=True)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        if os.path.exists(CONFIG_EXAMPLE):
            shutil.copy(CONFIG_EXAMPLE, CONFIG_FILE)
        else:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "boss_uid": "",
                    "boss_name": "Sếp",
                    "boss_caller_name": "Sếp",
                    "bot_name": "Bé Heo",
                    "model": "Gemini 3.8 Flash (High)",
                    "bridge_port": 5051,
                    "engine_port": 5066,
                    "auto_claim_boss": True
                }, f, indent=2)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        console.print(f"[bold red]Lỗi lưu config: {e}[/bold red]")
        return False

def check_or_extract_agy():
    agy_bin = shutil.which("agy") or os.path.join(BIN_DIR, "agy")
    if os.path.exists(agy_bin) and os.access(agy_bin, os.X_OK):
        return agy_bin
    
    # Check if agy.tar.gz exists in bin/
    tar_gz = os.path.join(BIN_DIR, "agy.tar.gz")
    if os.path.exists(tar_gz):
        console.print("[cyan]📦 Đang giải nén bộ cài AGY CLI từ bin/agy.tar.gz...[/cyan]")
        subprocess.run(["tar", "-xzf", tar_gz, "-C", BIN_DIR], check=True)
        if os.path.exists(agy_bin):
            os.chmod(agy_bin, 0o755)
            console.print("[green]✔ Đã chuẩn bị AGY binary thành công![/green]")
            return agy_bin

    # Check if host has agy in ~/.local/bin/agy
    host_agy = os.path.expanduser("~/.local/bin/agy")
    if os.path.exists(host_agy):
        console.print(f"[cyan]🔗 Phát hiện AGY CLI trên máy chủ ({host_agy}), tiến hành liên kết...[/cyan]")
        shutil.copy(host_agy, agy_bin)
        os.chmod(agy_bin, 0o755)
        return agy_bin

    return agy_bin

def render_banner():
    banner = r"""
[bold cyan]  _____       _             _    ______   __ [/bold cyan]
[bold cyan] |__  / __ _| | ___       / \  / ___\ \ / / [/bold cyan]
[bold cyan]   / / / _` | |/ _ \ ___ / _ \| |  _ \ V /  [/bold cyan]
[bold cyan]  / /_| (_| | | (_) |___/ ___ \ |_| | | |   [/bold cyan]
[bold cyan] |____|\__,_|_|\___/   /_/   \_\____| |_|   [/bold cyan]
[bold magenta]    Executive AI Assistant — Powered by Google Antigravity & Zalo[/bold magenta]
    """
    console.print(banner)

def step_agy_auth(agy_bin, config):
    # Đảm bảo đồng bộ cấu hình từ host nếu có
    host_cli_dir = os.path.expanduser("~/.gemini/antigravity-cli")
    target_cli_dir = os.path.join(GEMINI_DIR, "antigravity-cli")
    if os.path.exists(host_cli_dir) and not os.path.exists(target_cli_dir):
        os.makedirs(target_cli_dir, exist_ok=True)
        for fname in ["settings.json", "installation_id"]:
            src_f = os.path.join(host_cli_dir, fname)
            if os.path.exists(src_f):
                shutil.copy(src_f, os.path.join(target_cli_dir, fname))

    env = os.environ.copy()
    env["XDG_DATA_HOME"] = XDG_DATA_HOME
    test_cmd = [
        agy_bin,
        "--dangerously-skip-permissions",
        "-p", "ping"
    ]
    # 1. Kiểm tra nhanh xem đã xác thực từ trước chưa
    try:
        proc = subprocess.run(test_cmd, env=env, capture_output=True, text=True, timeout=3)
        if proc.returncode == 0:
            console.print(Panel("[bold green]✔ Google AGY Authentication: SẴN SÀNG HOẠT ĐỘNG[/bold green]\n"
                                "AGY CLI đã kết nối thành công với tài khoản Google!",
                                title="Bước 1: Google AGY Auth", border_style="green"))
            return True
    except Exception:
        pass

    # 2. Quy trình xác thực tương tác
    while True:
        console.print(Panel(
            "[bold yellow]⚡ Yêu cầu xác thực tài khoản Google cho AGY CLI[/bold yellow]\n\n"
            "Do hệ thống chạy trong Docker Container cô lập (không có giao diện Desktop),\n"
            "hệ thống sẽ tạo đường link đăng nhập để bạn mở trên trình duyệt Web của máy tính.",
            title="Bước 1: Google AGY Auth", border_style="yellow"
        ))

        flush_stdin()
        if not Confirm.ask("Bạn đã sẵn sàng lấy link đăng nhập Google AGY chưa?", default=True):
            console.print("[yellow]Đã tạm hoãn xác thực Google AGY.[/yellow]")
            return False

        console.print("[cyan]⏳ Đang khởi tạo phiên xác thực Google OAuth...[/cyan]")
        
        cmd = [
            agy_bin,
            "--dangerously-skip-permissions",
            "-p", "ping"
        ]

        try:
            p = subprocess.Popen(
                cmd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            auth_url = None
            url_pattern = re.compile(r"https://accounts\.google\.com/o/oauth2/[^\s]+")

            # Đọc stderr để bắt link OAuth
            for line in p.stderr:
                match = url_pattern.search(line)
                if match:
                    auth_url = match.group(0)
                    break
                if "already authenticated" in line.lower() or "pong" in line.lower():
                    break

            if auth_url:
                # Ghi link ra file để người dùng dễ mở nếu cần
                url_file = os.path.join(AUTH_DIR, "google_login_url.txt")
                try:
                    with open(url_file, "w", encoding="utf-8") as f:
                        f.write(auth_url.strip() + "\n")
                except Exception:
                    pass

                console.print("\n")
                console.print(Panel(
                    f"[bold green]🔗 LINK ĐĂNG NHẬP GOOGLE AGY (Bấm vào link hoặc copy mở bằng Chrome):[/bold green]\n\n"
                    f"[bold cyan underline]{auth_url}[/bold cyan underline]\n\n"
                    f"📌 [bold yellow]Hướng dẫn 3 bước tiếp theo:[/bold yellow]\n"
                    f"  1. Mở link trên bằng trình duyệt Web (Chrome, Edge, Firefox...).\n"
                    f"  2. Đăng nhập Google và bấm [bold green]Cho phép (Allow)[/bold green].\n"
                    f"  3. Trình duyệt sẽ hiển thị mã [bold cyan]Authorization Code[/bold cyan] (bắt đầu bằng [bold]4/0A...[/bold]).\n"
                    f"  4. Sao chép toàn bộ mã đó rồi dán vào ô bên dưới.\n"
                    f"[dim](Đường link này cũng đã được lưu vào file: {url_file})[/dim]",
                    title="👉 ĐĂNG NHẬP GOOGLE OAUTH", border_style="green", expand=True
                ))

                flush_stdin()
                code = Prompt.ask("\n👉 [bold yellow]Dán mã Authorization Code vào đây[/bold yellow]").strip()

                if not code:
                    console.print("[red]Mã xác thực không được để trống![/red]")
                    p.terminate()
                    continue

                console.print("[cyan]⏳ Đang gửi mã xác thực lên máy chủ Google...[/cyan]")
                p.stdin.write(code + "\n")
                p.stdin.flush()

                # Chờ agy hoàn tất xác thực (tối đa 25s)
                p.wait(timeout=25)

                if p.returncode == 0:
                    console.print(Panel("[bold green]✔ ĐĂNG NHẬP GOOGLE AGY THÀNH CÔNG![/bold green]\n"
                                        "Phiên làm việc đã được lưu trữ vĩnh viễn.",
                                        border_style="green"))
                    return True
                else:
                    stderr_out = p.stderr.read()
                    console.print(f"[bold red]❌ Xác thực chưa thành công (Mã lỗi: {p.returncode}).[/bold red]")
                    if stderr_out:
                        console.print(f"[dim]{stderr_out.strip()}[/dim]")
            else:
                # Nếu không tìm thấy URL, kiểm tra lại xem có phản hồi thành công không
                p.terminate()
                verify = subprocess.run(test_cmd, env=env, capture_output=True, text=True, timeout=5)
                if verify.returncode == 0:
                    console.print("[bold green]✔ Google AGY Authentication đã sẵn sàng![/bold green]")
                    return True

            flush_stdin()
            if not Confirm.ask("👉 Bạn có muốn thử lại không?", default=True):
                return False

        except Exception as e:
            console.print(f"[bold red]Lỗi khi xác thực: {e}[/bold red]")
            flush_stdin()
            if not Confirm.ask("👉 Bạn có muốn thử lại không?", default=True):
                return False



def step_zalo_login():
    if os.path.exists(SESSION_FILE) and os.path.getsize(SESSION_FILE) > 20:
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as sf:
                sdata = json.load(sf)
            console.print(Panel(
                f"[bold green]✔ Zalo Session: ĐÃ ĐĂNG NHẬP[/bold green]\n"
                f"Tài khoản ID: [bold]{sdata.get('userId', 'N/A')}[/bold]\n"
                f"File lưu trữ: [dim]{SESSION_FILE}[/dim]",
                title="Bước 2: Zalo QR Code Login", border_style="green"
            ))
            if not Confirm.ask("Bạn có muốn tiếp tục sử dụng phiên đăng nhập Zalo hiện tại không?", default=True):
                os.remove(SESSION_FILE)
            else:
                return True
        except Exception:
            pass

    console.print(Panel(
        "[bold cyan]📱 Quét mã QR để đăng nhập Zalo[/bold cyan]\n\n"
        "Hệ thống sẽ hiển thị mã QR Code ASCII ngay dưới đây.\n"
        "1. Mở ứng dụng [bold]Zalo[/bold] trên điện thoại di động.\n"
        "2. Chọn biểu tượng [bold]Quét mã QR[/bold] và hướng camera vào mã QR hiển thị bên dưới.\n"
        "3. Bấm [bold]Xác nhận đăng nhập[/bold] trên điện thoại.",
        title="Bước 2: Zalo QR Code Login", border_style="cyan"
    ))

    bridge_dir = os.path.join(BASE_DIR, "bridge")
    # Check node_modules
    if not os.path.exists(os.path.join(bridge_dir, "node_modules")):
        console.print("[yellow]📦 Đang cài đặt thư viện Node.js cho Zalo Bridge...[/yellow]")
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=bridge_dir, check=True)

    cmd = ["node", "bot.js", "--qr-only"]
    try:
        proc = subprocess.run(cmd, cwd=bridge_dir)
        if os.path.exists(SESSION_FILE) and os.path.getsize(SESSION_FILE) > 20:
            console.print("[bold green]✔ Đăng nhập Zalo thành công và đã lưu phiên làm việc![/bold green]")
            return True
        else:
            console.print("[bold red]❌ Chưa lưu được phiên đăng nhập Zalo. Vui lòng thử lại.[/bold red]")
            return False
    except Exception as e:
        console.print(f"[bold red]Lỗi khởi chạy Zalo bridge: {e}[/bold red]")
        return False

def step_boss_config(config):
    boss_uid = config.get("boss_uid", "").strip()
    if boss_uid:
        console.print(Panel(
            f"[bold green]✔ Chủ sở hữu (Boss UID): {boss_uid}[/bold green]\n"
            f"Tên hiển thị: [bold]{config.get('boss_name', 'Sếp')}[/bold]",
            title="Bước 3: Cấu hình Chủ sở hữu (Boss)", border_style="green"
        ))
        return config

    console.print(Panel(
        "[bold yellow]👑 Cấu hình quyền Chủ sở hữu (Boss Ownership)[/bold yellow]\n\n"
        "Khi được thiết lập quyền Boss, tài khoản Zalo cá nhân của bạn sẽ có toàn quyền:\n"
        "- Ra lệnh riêng 1-1 để điều hành mọi nhóm chat ([POST_TO_GROUP], [UNDO_GROUP_MESSAGE])\n"
        "- Nhận cảnh báo riêng tức thì khi trong nhóm có việc nhạy cảm ([PRIVATE_ALERT_BOSS])\n"
        "- Nhận diện và gọi 'Sếp' ấm áp chuẩn mực con người.\n\n"
        "[bold cyan]Tùy chọn:[/bold cyan]\n"
        "1. [bold]Auto-Claim (Khuyên dùng):[/bold] Sau khi khởi động, bạn chỉ cần mở Zalo nhắn 1 tin nhắn bất kỳ cho bot (ví dụ: 'Chào Heo'), hệ thống sẽ tự động gán tài khoản của bạn làm Sếp!\n"
        "2. Nhập Zalo UID thủ công ngay bây giờ.",
        title="Bước 3: Cấu hình Chủ sở hữu (Boss)", border_style="yellow"
    ))

    choice = Prompt.ask("Chọn phương thức (1: Auto-claim khi chat, 2: Nhập UID thủ công)", choices=["1", "2"], default="1")
    if choice == "2":
        uid = Prompt.ask("Nhập Zalo UID của bạn").strip()
        if uid:
            config["boss_uid"] = uid
            save_config(config)
            console.print(f"[green]✔ Đã cập nhật BOSS_UID: {uid}[/green]")
    else:
        config["auto_claim_boss"] = True
        save_config(config)
        console.print("[green]✔ Chế độ Auto-claim Boss đã được kích hoạt![/green]")

    return config

def run_services_dashboard(agy_bin, config):
    console.clear()
    render_banner()

    engine_port = config.get("engine_port", 5066)
    bridge_port = config.get("bridge_port", 5051)
    boss_name = config.get("boss_name", "Sếp")
    boss_uid = config.get("boss_uid", "") or "[Đang chờ Auto-Claim]"
    model_name = config.get("model", "Gemini 3.8 Flash (High)")

    console.print(Panel(
        f"[bold green]🚀 ĐANG KHỞI ĐỘNG HỆ THỐNG ZALO-AGY COPILOT...[/bold green]\n"
        f"• AI Engine: [bold cyan]Port {engine_port}[/bold cyan] (Model: {model_name})\n"
        f"• Zalo Bridge: [bold cyan]Port {bridge_port}[/bold cyan]\n"
        f"• Boss (Chủ sở hữu): [bold magenta]{boss_name}[/bold magenta] ({boss_uid})\n"
        f"• Nhấn [bold red]Ctrl + C[/bold red] để dừng toàn bộ hệ thống.",
        title="Trạng thái Khởi động", border_style="cyan"
    ))

    # Environment for subprocesses
    env = os.environ.copy()
    env["BASE_DIR"] = BASE_DIR
    env["WORKSPACE_DIR"] = WORKSPACE_DIR
    env["DATA_DIR"] = DATA_DIR
    env["LOGS_DIR"] = LOGS_DIR
    env["AUTH_DIR"] = AUTH_DIR
    env["GEMINI_DIR"] = GEMINI_DIR
    env["XDG_DATA_HOME"] = XDG_DATA_HOME
    env["AGY_BIN"] = agy_bin
    env["ENGINE_PORT"] = str(engine_port)
    env["BRIDGE_PORT"] = str(bridge_port)
    env["CONFIG_FILE"] = CONFIG_FILE

    # Spawn Engine
    engine_log = open(os.path.join(LOGS_DIR, "engine.log"), "a", encoding="utf-8")
    engine_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, "engine", "server.py")],
        env=env, stdout=engine_log, stderr=engine_log
    )

    time.sleep(1.5)

    # Spawn Bridge
    bridge_log = open(os.path.join(LOGS_DIR, "zalo.log"), "a", encoding="utf-8")
    bridge_proc = subprocess.Popen(
        ["node", "bot.js"],
        cwd=os.path.join(BASE_DIR, "bridge"),
        env=env, stdout=bridge_log, stderr=bridge_log
    )

    running = True

    def sig_handler(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    def tail_logs(file_path, num_lines=12):
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-num_lines:]]
        except Exception:
            return []

    start_time = time.time()

    with Live(console=console, screen=True, auto_refresh=False) as live:
        while running:
            uptime = int(time.time() - start_time)
            mins, secs = divmod(uptime, 60)
            hours, mins = divmod(mins, 60)
            uptime_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

            # Check process status
            e_status = "[green]RUNNING[/green]" if engine_proc.poll() is None else "[red]STOPPED[/red]"
            b_status = "[green]RUNNING[/green]" if bridge_proc.poll() is None else "[red]STOPPED[/red]"

            # Refresh config to check if Boss claimed
            curr_cfg = load_config()
            curr_boss = curr_cfg.get("boss_uid", "") or "[Đang chờ Auto-Claim]"

            layout = Layout()
            layout.split_column(
                Layout(name="header", size=4),
                Layout(name="main", ratio=1),
                Layout(name="footer", size=3)
            )

            # Header
            header_table = Table.grid(expand=True)
            header_table.add_column(justify="left")
            header_table.add_column(justify="right")
            header_table.add_row(
                "[bold cyan]ZALO-AGY COPILOT (BÉ HEO)[/bold cyan] | Executive Assistant Suite",
                f"Uptime: [bold yellow]{uptime_str}[/bold yellow] | Model: [bold green]{model_name}[/bold green]"
            )
            header_table.add_row(
                f"Engine: {e_status} (Port {engine_port}) | Bridge: {b_status} (Port {bridge_port})",
                f"Boss: [bold magenta]{curr_cfg.get('boss_name', 'Sếp')}[/bold magenta] ({curr_boss})"
            )
            layout["header"].update(Panel(header_table, border_style="cyan"))

            # Logs view
            zalo_lines = tail_logs(os.path.join(LOGS_DIR, "zalo.log"), 8)
            engine_lines = tail_logs(os.path.join(LOGS_DIR, "engine.log"), 8)

            log_table = Table(title="Dòng Sự Kiện Thời Gian Thực (Live Events)", expand=True, border_style="dim")
            log_table.add_column("Dịch vụ", style="bold cyan", width=12)
            log_table.add_column("Nhật ký gần nhất", style="dim")

            for l in engine_lines[-4:]:
                if l:
                    log_table.add_row("AGY-Engine", l)
            for l in zalo_lines[-6:]:
                if l:
                    log_table.add_row("Zalo-Bridge", l)

            layout["main"].update(Panel(log_table, border_style="blue"))

            # Footer
            layout["footer"].update(Panel(
                "[dim]Phím tắt: [bold red]Ctrl + C[/bold red] để dừng hệ thống an toàn. Dữ liệu tin nhắn được tự động lưu trong data/.[/dim]",
                border_style="dim"
            ))

            live.update(layout, refresh=True)
            time.sleep(1)

    console.print("\n[yellow]Đang dừng toàn bộ dịch vụ...[/yellow]")
    if engine_proc.poll() is None:
        engine_proc.terminate()
    if bridge_proc.poll() is None:
        bridge_proc.terminate()
    console.print("[bold green]✔ Đã dừng an toàn tất cả các tiến trình.[/bold green]")

def main():
    render_banner()
    agy_bin = check_or_extract_agy()
    config = load_config()

    console.print("[bold]1/4 Kiểm tra AGY Binary...[/bold]")
    if not os.path.exists(agy_bin):
        console.print(f"[bold red]❌ Không tìm thấy AGY CLI tại {agy_bin}[/bold red]")
        sys.exit(1)
    console.print(f"[green]✔ AGY Binary sẵn sàng: {agy_bin}[/green]\n")

    console.print("[bold]2/4 Xác thực Google AGY...[/bold]")
    if not step_agy_auth(agy_bin, config):
        sys.exit(1)
    console.print("")

    console.print("[bold]3/4 Đăng nhập Zalo QR...[/bold]")
    if not step_zalo_login():
        sys.exit(1)
    console.print("")

    console.print("[bold]4/4 Thiết lập Boss UID...[/bold]")
    config = step_boss_config(config)
    console.print("")

    console.print("[bold green]🎉 CẤU HÌNH HOÀN TẤT! KHỞI CHẠY HỆ THỐNG...[/bold green]")
    time.sleep(1)
    run_services_dashboard(agy_bin, config)

if __name__ == "__main__":
    main()
