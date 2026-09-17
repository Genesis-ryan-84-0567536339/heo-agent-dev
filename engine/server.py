#!/usr/bin/env python3
"""
AGY Zalo Co-Pilot Engine Server with Dynamic Quota Failover & Auto-Recovery
- Primary Model: Gemini 3.8 Flash (Medium)
- Fallback Model: Claude Sonnet 4.6 (Thinking)
- Automatic Failover on Quota/Rate Limit (429, Resource Exhausted)
- Automatic Cooldown Probe & Switchback to Gemini 3.8
- Group Chat Protocols: Diplomatic stalling on sensitive topics, Silent 1-1 Alert to {BOSS_NAME}, Tagging Boss on standard requests.
"""

import os
import sys
import re
import json
import time
import datetime
import glob
import urllib.request
import subprocess
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("ENGINE_PORT", "5066"))
BRIDGE_BASE_URL = os.environ.get("BRIDGE_URL", "http://127.0.0.1:5051")
OUTBOUND_URL = f"{BRIDGE_BASE_URL}/api/send"
UNDO_URL = f"{BRIDGE_BASE_URL}/api/undo"

from pathlib import Path
import shutil

BASE_DIR = os.environ.get("BASE_DIR", str(Path(__file__).parent.parent.resolve()))
CONFIG_FILE = os.environ.get("CONFIG_FILE", str(Path(BASE_DIR) / "config" / "config.json"))
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", str(Path(BASE_DIR) / "workspace"))
LOG_DIR = os.environ.get("LOG_DIR", str(Path(BASE_DIR) / "logs"))
DATA_DIR = os.environ.get("DATA_DIR", str(Path(BASE_DIR) / "data"))
SCRIPTS_DIR = os.environ.get("SCRIPTS_DIR", str(Path(BASE_DIR) / "scripts"))
STATE_FILE = os.path.join(DATA_DIR, "model_state.json")
GEMINI_DIR = os.environ.get("GEMINI_DIR", str(Path(BASE_DIR) / "auth" / "home" / ".gemini"))
XDG_DATA_HOME = os.environ.get("XDG_DATA_HOME", str(Path(BASE_DIR) / "auth" / "xdg-data"))
AGY_BIN = os.environ.get("AGY_BIN", shutil.which("agy") or str(Path(BASE_DIR) / "bin" / "agy"))

import hashlib

def load_app_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
                return json.load(cf)
        except Exception:
            pass
    return {}

def has_security_pin() -> bool:
    cfg = load_app_config()
    return bool(cfg.get("pin_hash") or cfg.get("pin_code"))

def verify_security_pin(provided_pin: str) -> bool:
    cfg = load_app_config()
    current_hash = str(cfg.get("pin_hash", "") or "").strip()
    plain_pin = str(cfg.get("pin_code", "") or "").strip()

    # Nếu hệ thống chưa từng cài đặt mã PIN thì không bắt buộc
    if not current_hash and not plain_pin:
        return True
    if not provided_pin:
        return False

    pin_str = str(provided_pin).strip()
    input_hash = hashlib.sha256(pin_str.encode("utf-8")).hexdigest()
    if current_hash and input_hash.lower() == current_hash.lower():
        return True
    if plain_pin and (pin_str == plain_pin or input_hash.lower() == hashlib.sha256(plain_pin.encode("utf-8")).hexdigest().lower()):
        return True
    return False

def extract_pin_from_request(headers, body_str: str) -> str:
    pin = headers.get("X-Security-Pin", "") or headers.get("x-security-pin", "")
    if not pin and body_str:
        try:
            data = json.loads(body_str)
            pin = str(data.get("pin", "") or data.get("security_pin", "") or "")
        except Exception:
            pass
    return str(pin).strip()

_cfg = load_app_config()
BOSS_UID = os.environ.get("BOSS_UID", _cfg.get("boss_uid", ""))
BOSS_NAME = os.environ.get("BOSS_NAME", _cfg.get("boss_name", "Sếp"))
BOSS_CALLER_NAME = os.environ.get("BOSS_CALLER_NAME", _cfg.get("boss_caller_name", "Sếp"))
BOT_NAME = os.environ.get("BOT_NAME", _cfg.get("bot_name", "Bé Heo"))

os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

PRIMARY_MODEL = "Gemini 3.8 Flash (Medium)"
FALLBACK_MODEL = "Claude Sonnet 4.6 (Thinking)"
DEFAULT_COOLDOWN_SECONDS = 300  # 5 phút canh hồi quota

QUOTA_ERROR_PATTERNS = [
    r"quota",
    r"rate[\s_-]*limit",
    r"429",
    r"resource[\s_-]*exhausted",
    r"exceeded\s+your\s+current\s+quota",
    r"insufficient_quota",
    r"model\s+is\s+overloaded",
    r"temporarily\s+overloaded",
    r"too\s+many\s+requests",
    r"capacity",
    r"exhausted"
]

SUPPORTED_MODELS = [
    {"id": "gemini-3.8-flash-high", "name": "Gemini 3.8 Flash (High)", "desc": "Tối ưu tốc độ cao và khả năng suy luận mạnh"},
    {"id": "gemini-3.8-flash-medium", "name": "Gemini 3.8 Flash (Medium)", "desc": "Mặc định tiêu chuẩn, cân bằng tốc độ và phản hồi"},
    {"id": "gemini-3.1-pro-high", "name": "Gemini 3.1 Pro (High)", "desc": "Mô hình Pro chuyên sâu, xử lý tài liệu dài và phân tích phức tạp"},
    {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6 (Thinking)", "desc": "Tư duy đa chiều, phản biện chiến lược sâu sắc"},
    {"id": "claude-opus-4-6-thinking", "name": "Claude Opus 4.6 (Thinking)", "desc": "Mô hình Opus cao cấp nhất"},
    {"id": "gpt-oss-120b-medium", "name": "GPT-OSS 120B (Medium)", "desc": "Mô hình mã nguồn mở độc lập"}
]

def normalize_model_target(target):
    t = (target or "").lower().strip()
    if "opus" in t:
        return "Claude Opus 4.6 (Thinking)"
    elif "sonnet" in t:
        return "Claude Sonnet 4.6 (Thinking)"
    elif "3.1" in t or "pro" in t:
        if "low" in t:
            return "Gemini 3.1 Pro (Low)"
        return "Gemini 3.1 Pro (High)"
    elif "3.8" in t or "flash" in t:
        if "low" in t:
            return "Gemini 3.8 Flash (Low)"
        elif "high" in t and "medium" not in t:
            return "Gemini 3.8 Flash (High)"
        return "Gemini 3.8 Flash (Medium)"
    elif "gpt" in t or "oss" in t:
        return "GPT-OSS 120B (Medium)"
    for m in SUPPORTED_MODELS:
        if m["name"].lower() == t or m["id"].lower() == t:
            return m["name"]
    return target

def get_canonical_agy_model(model_name, effort="medium"):
    """
    Maps model display names / user inputs + effort levels to the exact, valid
    model IDs natively recognized by Antigravity (agy) CLI.
    This avoids invalid '--effort' flag errors since effort is encoded into the model ID.
    """
    t = (model_name or "").lower().strip()
    eff = (effort or "medium").lower().strip()
    if eff not in ["low", "medium", "high"]:
        eff = "medium"

    if "opus" in t:
        return "claude-opus-4-6-thinking"
    elif "sonnet" in t:
        return "claude-sonnet-4-6"
    elif "gpt" in t or "oss" in t:
        return "gpt-oss-120b-medium"
    elif "3.1" in t or "pro" in t:
        return "gemini-3.1-pro-low" if eff == "low" or "low" in t else "gemini-3.1-pro-high"
    elif "3.8" in t or "flash" in t:
        if eff == "low" or "low" in t:
            return "gemini-3.8-flash-low"
        elif eff == "high" or ("high" in t and "medium" not in t):
            return "gemini-3.8-flash-high"
        else:
            return "gemini-3.8-flash-medium"

    for m in [
        "gemini-3.8-flash-high", "gemini-3.8-flash-medium", "gemini-3.8-flash-low",
        "gemini-3.1-pro-high", "gemini-3.1-pro-low",
        "claude-sonnet-4-6", "claude-opus-4-6-thinking", "gpt-oss-120b-medium"
    ]:
        if t == m.lower():
            return m
    return "gemini-3.8-flash-medium"

DEFAULT_QUOTA_STATS = {
    "gemini-3.8-flash": {
        "name": "Gemini 3.8 Flash",
        "status": "healthy",
        "status_label": "Sẵn sàng (Quota OK)",
        "requests_count": 0,
        "quota_errors": 0,
        "avg_latency": 0.0,
        "total_latency": 0.0,
        "last_used": "Sẵn sàng",
        "last_checked": "Hôm nay",
        "model_id": "gemini-3.8-flash-medium"
    },
    "gemini-3.1-pro": {
        "name": "Gemini 3.1 Pro",
        "status": "healthy",
        "status_label": "Sẵn sàng (Quota OK)",
        "requests_count": 0,
        "quota_errors": 0,
        "avg_latency": 0.0,
        "total_latency": 0.0,
        "last_used": "Sẵn sàng",
        "last_checked": "Hôm nay",
        "model_id": "gemini-3.1-pro-high"
    },
    "claude-sonnet-4-6": {
        "name": "Claude Sonnet 4.6",
        "status": "healthy",
        "status_label": "Sẵn sàng (Quota OK)",
        "requests_count": 0,
        "quota_errors": 0,
        "avg_latency": 0.0,
        "total_latency": 0.0,
        "last_used": "Sẵn sàng",
        "last_checked": "Hôm nay",
        "model_id": "claude-sonnet-4-6"
    },
    "claude-opus-4-6": {
        "name": "Claude Opus 4.6",
        "status": "healthy",
        "status_label": "Sẵn sàng (Quota OK)",
        "requests_count": 0,
        "quota_errors": 0,
        "avg_latency": 0.0,
        "total_latency": 0.0,
        "last_used": "Sẵn sàng",
        "last_checked": "Hôm nay",
        "model_id": "claude-opus-4-6-thinking"
    },
    "gpt-oss-120b": {
        "name": "GPT-OSS 120B",
        "status": "healthy",
        "status_label": "Sẵn sàng (Quota OK)",
        "requests_count": 0,
        "quota_errors": 0,
        "avg_latency": 0.0,
        "total_latency": 0.0,
        "last_used": "Sẵn sàng",
        "last_checked": "Hôm nay",
        "model_id": "gpt-oss-120b-medium"
    }
}

state_lock = threading.Lock()
_last_quota_check_time = 0.0   # timestamp lần cuối check quota sau response
QUOTA_AUTO_CHECK_COOLDOWN = 180  # 3 phút giữa các lần auto-check

def maybe_refresh_quota_after_response():
    """Trigger cập nhật quota thực sau khi Heo trả lời, nhưng tối đa 1 lần / 3 phút."""
    global _last_quota_check_time
    now = time.time()
    if now - _last_quota_check_time >= QUOTA_AUTO_CHECK_COOLDOWN:
        _last_quota_check_time = now
        probe_all_models_background()

def load_model_state():
    with state_lock:
        st = None
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    st = json.load(f)
            except Exception:
                pass
        if not st:
            st = {
                "active_model": PRIMARY_MODEL,
                "effort": "medium",
                "bot_paused": False,
                "is_fallback": False,
                "exhausted_at": 0,
                "cooldown_seconds": DEFAULT_COOLDOWN_SECONDS,
                "last_switch_reason": "Khởi tạo hệ thống",
                "total_failovers": 0,
                "total_recoveries": 0,
                "history": [],
                "quota_stats": {k: dict(v) for k, v in DEFAULT_QUOTA_STATS.items()}
            }
        else:
            if "effort" not in st:
                st["effort"] = "medium"
            if "bot_paused" not in st:
                st["bot_paused"] = False
            if "quota_stats" not in st:
                st["quota_stats"] = {k: dict(v) for k, v in DEFAULT_QUOTA_STATS.items()}
            else:
                for k, v in DEFAULT_QUOTA_STATS.items():
                    if k not in st["quota_stats"]:
                        st["quota_stats"][k] = dict(v)
        return st

def save_model_state(state):
    with state_lock:
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Lỗi ghi model_state.json: {e}")

def record_model_usage(model_name, duration, success=True, is_quota_err=False):
    key = "gemini-3.8-flash"
    t = (model_name or "").lower()
    if "opus" in t:
        key = "claude-opus-4-6"
    elif "sonnet" in t:
        key = "claude-sonnet-4-6"
    elif "3.1" in t or "pro" in t:
        key = "gemini-3.1-pro"
    elif "gpt" in t or "oss" in t:
        key = "gpt-oss-120b"
    else:
        key = "gemini-3.8-flash"

    state = load_model_state()
    stats = state.get("quota_stats", {})
    m_stat = stats.get(key, dict(DEFAULT_QUOTA_STATS.get(key, {})))

    m_stat["requests_count"] = m_stat.get("requests_count", 0) + 1
    m_stat["total_latency"] = round(m_stat.get("total_latency", 0.0) + duration, 2)
    m_stat["avg_latency"] = round(m_stat["total_latency"] / max(1, m_stat["requests_count"]), 1)
    now_str = datetime.datetime.now().strftime("%H:%M:%S %d/%m")
    m_stat["last_used"] = now_str
    m_stat["last_checked"] = now_str

    if is_quota_err:
        m_stat["quota_errors"] = m_stat.get("quota_errors", 0) + 1
        m_stat["status"] = "exhausted"
        m_stat["status_label"] = "Hết Quota (Rate Limited)"
    elif success:
        m_stat["status"] = "healthy"
        m_stat["status_label"] = "Sẵn sàng (Quota OK)"

    stats[key] = m_stat
    state["quota_stats"] = stats
    save_model_state(state)

def get_oauth_access_token():
    """Đọc và tự động refresh OAuth token từ file auth của agy."""
    token_file = os.path.join(GEMINI_DIR, "antigravity-cli", "antigravity-oauth-token")
    try:
        with open(token_file) as f:
            data = json.load(f)
        token = data.get("token", {})
        access_token = token.get("access_token", "")
        refresh_token = token.get("refresh_token", "")
        expiry_str = token.get("expiry", "")
        # Auto-refresh nếu còn dưới 5 phút hết hạn
        if expiry_str:
            try:
                expiry = datetime.datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                now = datetime.datetime.now(datetime.timezone.utc)
                if (expiry - now).total_seconds() < 300:
                    access_token = _refresh_oauth_token(refresh_token, token_file, data)
            except Exception:
                pass
        return access_token
    except Exception as e:
        log_event(f"⚠️ [Quota] Lỗi đọc OAuth token: {e}")
        return ""

def _get_oauth_creds():
    """Tự động trích xuất OAuth Client ID và Secret từ agy binary hoặc biến môi trường."""
    cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    sec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
    if not (cid and sec) and os.path.exists(AGY_BIN):
        try:
            with open(AGY_BIN, "rb") as f:
                data = f.read()
            import re
            ids = re.findall(rb"\d{10,15}-[a-z0-9]{30,40}\.apps\.googleusercontent\.com", data)
            for item in ids:
                s = item.decode()
                if s.startswith("1071006060591"):
                    cid = s
                    break
            if not cid and ids:
                cid = ids[0].decode()
            m_sec = re.search(rb"GOCSPX-[A-Za-z0-9_\-]{28}", data)
            if m_sec:
                sec = m_sec.group().decode()
        except Exception:
            pass
    return cid, sec

GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET = _get_oauth_creds()
GOOGLE_OAUTH_SCOPES = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/cclog"


def _refresh_oauth_token(refresh_token, token_file, existing_data):
    """Refresh OAuth token dùng refresh_token và client_secret đã xác thực."""
    import urllib.parse
    try:
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "refresh_token": refresh_token,
        }).encode()
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
        new_access = resp.get("access_token", "")
        if new_access:
            expires_in = resp.get("expires_in", 3600)
            expiry = (datetime.datetime.now(datetime.timezone.utc) +
                      datetime.timedelta(seconds=expires_in)).isoformat()
            existing_data.setdefault("token", {})["access_token"] = new_access
            existing_data["token"]["expiry"] = expiry
            if "id_token" in resp:
                existing_data["id_token"] = resp["id_token"]
            try:
                with open(token_file, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            log_event("✅ [Quota] Đã tự động refresh OAuth token qua Google API.")
            return new_access
    except Exception as e:
        log_event(f"⚠️ [Quota] Lỗi refresh Google OAuth token qua API: {e}")

    # Fallback: dùng agy binary để refresh token
    log_event("⚠️ [Quota] Thử fallback refresh qua agy...")
    return _refresh_token_via_agy()

def _refresh_token_via_agy():
    """Chạy agy với prompt rỗng để force refresh OAuth token."""
    try:
        env = os.environ.copy()
        env["XDG_DATA_HOME"] = XDG_DATA_HOME
        cmd = [
            AGY_BIN, "-p", "1",
            "--dangerously-skip-permissions",
            f"--gemini_dir={GEMINI_DIR}",
            "--model=Gemini 3.8 Flash (Medium)",
            "--print-timeout=15s"
        ]
        subprocess.run(cmd, cwd=WORKSPACE_DIR, env=env,
                       capture_output=True, text=True, timeout=20)
        # Đọc lại token sau khi agy đã refresh
        token_file = os.path.join(GEMINI_DIR, "antigravity-cli", "antigravity-oauth-token")
        with open(token_file) as f:
            d = json.load(f)
        token = d.get("token", {})
        log_event("✅ [Quota] Token đã refresh qua agy binary.")
        return token.get("access_token", "")
    except Exception as e:
        log_event(f"⚠️ [Quota] Refresh via agy thất bại: {e}")
        return ""

_tier_cache = {"email": "", "tier_name": "", "tier_id": "", "expires_at": 0}

def get_google_auth_info():
    """Lấy thông tin tài khoản Google: trạng thái kết nối, email đăng nhập, tên gói cước (tier)."""
    token_file = os.path.join(GEMINI_DIR, "antigravity-cli", "antigravity-oauth-token")
    if not os.path.exists(token_file) or os.path.getsize(token_file) < 20:
        return {"authenticated": False, "email": "", "tier_name": "Chưa đăng nhập", "tier_id": ""}

    try:
        with open(token_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"authenticated": False, "email": "", "tier_name": "Chưa đăng nhập", "tier_id": ""}

    token = data.get("token", {})
    access_token = token.get("access_token", "")
    if not access_token:
        return {"authenticated": False, "email": "", "tier_name": "Chưa đăng nhập", "tier_id": ""}

    # Lấy email từ id_token JWT claims
    email = ""
    id_token = data.get("id_token", "")
    if id_token:
        try:
            import base64
            parts = id_token.split(".")
            if len(parts) >= 2:
                p = parts[1]
                p += "=" * ((4 - len(p) % 4) % 4)
                claims = json.loads(base64.urlsafe_b64decode(p))
                email = claims.get("email", "")
        except Exception:
            pass

    now = time.time()
    if _tier_cache.get("expires_at", 0) > now and _tier_cache.get("email") == email:
        return {
            "authenticated": True,
            "email": email,
            "tier_name": _tier_cache["tier_name"],
            "tier_id": _tier_cache["tier_id"]
        }

    tier_name = "Miễn phí (Free Tier)"
    tier_id = "free-tier"
    try:
        req = urllib.request.Request(
            "https://daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist",
            data=json.dumps({"metadata": {"ideType": "ANTIGRAVITY", "platform": "PLATFORM_UNSPECIFIED", "pluginType": "GEMINI"}}).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "antigravity"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            code_resp = json.loads(r.read())
            pt = code_resp.get("paidTier")
            if pt and isinstance(pt, dict) and pt.get("id"):
                tier_id = pt.get("id", "g1-pro-tier")
                raw_name = pt.get("name", "Google AI Pro")
                if "pro" in tier_id.lower() or "pro" in raw_name.lower():
                    tier_name = "Google AI Pro"
                elif "ultra" in tier_id.lower() or "ultra" in raw_name.lower():
                    tier_name = "Google AI Ultra"
                else:
                    tier_name = raw_name
            else:
                ct = code_resp.get("currentTier", {})
                tier_id = ct.get("id", "free-tier")
                raw_name = ct.get("name", "Antigravity")
                if tier_id == "free-tier":
                    tier_name = "Miễn phí (Free Tier)"
                elif "pro" in tier_id.lower() or "pro" in raw_name.lower():
                    tier_name = f"Google AI Pro ({raw_name})"
                elif "ultra" in tier_id.lower():
                    tier_name = f"Google AI Ultra ({raw_name})"
                elif tier_id == "standard-tier":
                    tier_name = "Enterprise (GCP Standard)"
                else:
                    tier_name = raw_name
            if not email and "upgradeSubscriptionUri" in code_resp:
                import urllib.parse as up
                parsed = up.urlparse(code_resp["upgradeSubscriptionUri"])
                qs = up.parse_qs(parsed.query)
                email = qs.get("Email", [""])[0]
    except Exception:
        tier_name = "Đã xác thực"

    _tier_cache["email"] = email
    _tier_cache["tier_name"] = tier_name
    _tier_cache["tier_id"] = tier_id
    _tier_cache["expires_at"] = now + 600

    return {
        "authenticated": True,
        "email": email,
        "tier_name": tier_name,
        "tier_id": tier_id
    }

def exchange_oauth_code_and_save(code, redirect_uri=None):
    """Đổi Google authorization code lấy access_token + refresh_token và lưu vào token file."""
    import urllib.parse
    if not redirect_uri:
        redirect_uri = f"http://localhost:{PORT}/api/oauth_callback"
    body = urllib.parse.urlencode({
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())

    access_token = resp.get("access_token", "")
    refresh_token = resp.get("refresh_token", "")
    id_token = resp.get("id_token", "")
    expires_in = resp.get("expires_in", 3600)
    expiry = (datetime.datetime.now(datetime.timezone.utc) +
              datetime.timedelta(seconds=expires_in)).isoformat()

    token_data = {
        "token": {
            "access_token": access_token,
            "token_type": "Bearer",
            "refresh_token": refresh_token,
            "expiry": expiry
        },
        "auth_method": "consumer",
        "id_token": id_token
    }

    target_dir = os.path.join(GEMINI_DIR, "antigravity-cli")
    os.makedirs(target_dir, exist_ok=True)
    token_file = os.path.join(target_dir, "antigravity-oauth-token")
    with open(token_file, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=2)

    global _tier_cache
    _tier_cache = {"email": "", "tier_name": "", "tier_id": "", "expires_at": 0}

    log_event("🎉 [Auth] Đăng nhập Google thành công! Token đã được lưu.")
    probe_all_models_background()
    return token_data

def _token_refresh_loop():
    """Background thread: tự động refresh token mỗi 45 phút."""
    TOKEN_REFRESH_INTERVAL = 45 * 60  # 45 phút
    log_event("🔑 [Token] Bắt đầu vòng lặp auto-refresh token (mỗi 45 phút).")
    while True:
        time.sleep(TOKEN_REFRESH_INTERVAL)
        log_event("🔑 [Token] Đến giờ refresh token định kỳ...")
        _refresh_token_via_agy()

def start_token_refresh_loop():
    """Khởi động background thread tự refresh OAuth token."""
    t = threading.Thread(target=_token_refresh_loop, daemon=True)
    t.start()

# Mapping model_id (API response) -> quota_stats key
_MODEL_ID_TO_STAT_KEY = {
    "gemini-3.8-flash-medium":   "gemini-3.8-flash",
    "gemini-3.8-flash-high":     "gemini-3.8-flash",
    "gemini-3.8-flash-tiered":   "gemini-3.8-flash",
    "gemini-3.1-pro-high":       "gemini-3.1-pro",
    "gemini-3.1-pro-low":        "gemini-3.1-pro",
    "claude-sonnet-4-6":         "claude-sonnet-4-6",
    "claude-opus-4-6-thinking":  "claude-opus-4-6",
    "gpt-oss-120b-medium":       "gpt-oss-120b",
}

def fetch_real_quota():
    """Gọi fetchAvailableModels API để lấy quota thực (remainingFraction, isExhausted, resetTime)."""
    access_token = get_oauth_access_token()
    if not access_token:
        return None
    try:
        req = urllib.request.Request(
            "https://daily-cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels",
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "antigravity",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log_event(f"⚠️ [Quota] Lỗi gọi fetchAvailableModels: {e}")
        return None

def probe_all_models_background():
    """Gọi fetchAvailableModels API thực để cập nhật quota toàn bộ model."""
    def _run():
        now_str = datetime.datetime.now().strftime("%H:%M:%S %d/%m")
        resp = fetch_real_quota()
        state = load_model_state()
        stats = state.get("quota_stats", {})

        if resp is None:
            for key in stats:
                stats[key]["last_checked"] = now_str + " (API err)"
            state["quota_stats"] = stats
            save_model_state(state)
            log_event("⚠️ [Quota] fetchAvailableModels thất bại, giữ nguyên trạng thái cũ.")
            return

        api_models = resp.get("models", {})
        updated_keys = set()

        for model_id, model_info in api_models.items():
            qi = model_info.get("quotaInfo", {})
            stat_key = _MODEL_ID_TO_STAT_KEY.get(model_id)
            if not stat_key or stat_key in updated_keys:
                continue
            updated_keys.add(stat_key)

            remaining = qi.get("remainingFraction")  # float 0.0 - 1.0
            is_exhausted = qi.get("isExhausted", False)
            reset_time = qi.get("resetTime", "")

            entry = stats.get(stat_key, {})
            entry["last_checked"] = now_str
            entry["remaining_fraction"] = remaining

            reset_label = ""
            if reset_time:
                try:
                    rt = datetime.datetime.fromisoformat(reset_time.replace("Z", "+00:00"))
                    rt_local = rt.astimezone().strftime("%H:%M %d/%m")
                    reset_label = f" | reset {rt_local}"
                except Exception:
                    reset_label = f" | reset {reset_time[:16]}"

            if is_exhausted or (remaining is not None and remaining <= 0.0):
                entry["status"] = "exhausted"
                entry["quota_errors"] = entry.get("quota_errors", 0) + 1
                pct = int((remaining or 0) * 100)
                entry["status_label"] = f"Hết Quota ({pct}%{reset_label})"
            else:
                entry["status"] = "healthy"
                pct = int((remaining or 1.0) * 100) if remaining is not None else 100
                entry["status_label"] = f"Sẵn sàng ({pct}% còn lại{reset_label})"

            stats[stat_key] = entry

        state["quota_stats"] = stats
        save_model_state(state)
        log_event(f"📊 [Quota] Đã cập nhật quota thực cho {len(updated_keys)} model từ Google API.")

    threading.Thread(target=_run, daemon=True).start()

def probe_model_quota_sync(model_key):
    """Alias tương thích — trigger probe toàn bộ (dùng API thực)."""
    probe_all_models_background()

def is_quota_error(text, returncode=0):
    if not text:
        return returncode != 0
    return any(re.search(p, text, re.IGNORECASE) for p in QUOTA_ERROR_PATTERNS)

def send_silent_alert_to_boss(message):
    """Sends a private 1-1 message to {BOSS_NAME} via Outbound Bridge"""
    try:
        payload = json.dumps({
            "threadId": BOSS_UID,
            "threadType": 0,
            "msg": message
        }).encode("utf-8")
        req = urllib.request.Request(
            OUTBOUND_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"⚠️ [Silent Alert] Lỗi gửi tin riêng cho {BOSS_NAME}: {e}")
        return False

def send_message_to_group(group_id, message, files=None):
    """Sends a message to a Zalo group via Outbound Bridge"""
    try:
        payload_data = {
            "threadId": str(group_id),
            "threadType": 1,  # Group
            "msg": message
        }
        if files:
            payload_data["attachments"] = files
        payload = json.dumps(payload_data).encode("utf-8")
        req = urllib.request.Request(
            OUTBOUND_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            # Append to group history file
            hist_file = os.path.join(DATA_DIR, f"group_{group_id}.jsonl")
            try:
                with open(hist_file, "a", encoding="utf-8") as f:
                    entry = {
                        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "senderUid": "bot",
                        "senderName": "Em Heo",
                        "text": message
                    }
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception:
                pass
            return resp.status == 200
    except Exception as e:
        print(f"⚠️ [Group Outbound] Lỗi gửi tin vào nhóm {group_id}: {e}")
        return False

def undo_message_in_group(group_id):
    """Triggers undo/recall of last bot message in the specified group via Outbound Bridge"""
    try:
        payload = json.dumps({
            "threadId": str(group_id),
            "threadType": 1
        }).encode("utf-8")
        req = urllib.request.Request(
            UNDO_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"⚠️ [Undo Group Outbound] Lỗi thu hồi tin trong nhóm {group_id}: {e}")
        return False

def switch_to_fallback(reason="Phát hiện hết Quota/Rate Limit"):
    state = load_model_state()
    state["active_model"] = FALLBACK_MODEL
    state["is_fallback"] = True
    state["exhausted_at"] = time.time()
    state["last_switch_reason"] = reason
    state["total_failovers"] += 1
    
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "from": PRIMARY_MODEL,
        "to": FALLBACK_MODEL,
        "reason": reason
    }
    state["history"].append(entry)
    state["history"] = state["history"][-20:]  # Keep last 20 events
    save_model_state(state)

    alert_msg = (
        f"⚠️ [HẠ TẦNG TỰ ĐỘNG - FAILOVER ĐÃ KÍCH HOẠT]\n"
        f"Dạ {BOSS_NAME}, hệ thống phát hiện mô hình chính Gemini 3.8 Flash vừa chạm giới hạn Quota/Rate Limit ({reason}).\n\n"
        f"🔄 Trợ lý đã TỰ ĐỘNG CHUYỂN TẠM SANG: Claude Sonnet 4.6 (Thinking) để tiếp tục phục vụ Sếp 100% không gián đoạn.\n"
        f"⏳ Bộ đếm thời gian: Hệ thống đang canh 5 phút ({state['cooldown_seconds']}s) và sẽ tự động probe chuyển ngược lại Gemini 3.8 ngay khi quota hồi phục ạ!"
    )
    send_silent_alert_to_boss(alert_msg)
    log_event(f"⚠️ [FAILOVER] Đã chuyển sang {FALLBACK_MODEL} ({reason})")

def switch_to_primary(reason="Quota đã hồi phục thành công"):
    state = load_model_state()
    state["active_model"] = PRIMARY_MODEL
    state["is_fallback"] = False
    state["exhausted_at"] = 0
    state["last_switch_reason"] = reason
    state["total_recoveries"] += 1
    
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "from": FALLBACK_MODEL,
        "to": PRIMARY_MODEL,
        "reason": reason
    }
    state["history"].append(entry)
    state["history"] = state["history"][-20:]
    save_model_state(state)

    alert_msg = (
        f"🟢 [HẠ TẦNG PHỤC HỒI - AUTO-RECOVERY THÀNH CÔNG]\n"
        f"Dạ {BOSS_NAME}, hệ thống vừa probe thành công: Quota của mô hình chính Gemini 3.8 Flash đã được hồi phục hoàn toàn!\n\n"
        f"✨ Trợ lý đã TỰ ĐỘNG CHUYỂN NGƯỢC VỀ: Gemini 3.8 Flash (Medium) để tối ưu tốc độ và chi phí cho Sếp ạ."
    )
    send_silent_alert_to_boss(alert_msg)
    log_event(f"🟢 [RECOVERY] Đã chuyển ngược về {PRIMARY_MODEL} ({reason})")

def probe_gemini_quota():
    """Lightweight test to check if Gemini 3.8 Flash quota has recovered"""
    env = os.environ.copy()
    env["XDG_DATA_HOME"] = XDG_DATA_HOME
    cmd = [
        AGY_BIN,
        "-p", "ping 1",
        "--model=gemini-3.8-flash-medium",
        "--dangerously-skip-permissions",
        f"--gemini_dir={GEMINI_DIR}",
        "--print-timeout=20s"
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=WORKSPACE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=25
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0 and not is_quota_error(out):
            return True
        return False
    except Exception:
        return False

def check_zalo_bridge_alive():
    """Kiểm tra xem Zalo Outbound HTTP Server (cổng 5051) có đang mở và phản hồi không"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.8)
    try:
        res = s.connect_ex(("127.0.0.1", 5051))
        s.close()
        return res == 0
    except Exception:
        return False

def get_zalo_info():
    """Lấy thông tin trạng thái Zalo chi tiết (kết nối, phiên đăng nhập, UID)"""
    zalo_session_file = os.path.join(DATA_DIR, "zalo_session.json")
    logged_in = os.path.exists(zalo_session_file) and os.path.getsize(zalo_session_file) > 20
    uid = ""
    connected = check_zalo_bridge_alive()
    if logged_in:
        # 1. Thử lấy UID từ zalo_profile.json
        profile_file = os.path.join(DATA_DIR, "zalo_profile.json")
        if os.path.exists(profile_file):
            try:
                with open(profile_file, "r", encoding="utf-8") as pf:
                    pdata = json.load(pf)
                    uid = str(pdata.get("ownId") or "")
            except Exception:
                pass
        # 2. Thử truy vấn qua endpoint /api/info trên port 5051
        if not uid and connected:
            try:
                req = urllib.request.Request("http://127.0.0.1:5051/api/info")
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    inf = json.loads(resp.read().decode("utf-8"))
                    uid = str(inf.get("ownId", ""))
            except Exception:
                pass
        # 3. Thử đọc từ zalo_session.json
        if not uid:
            try:
                with open(zalo_session_file, "r", encoding="utf-8") as zf:
                    zdata = json.load(zf)
                    uid = str(zdata.get("userId") or zdata.get("uid") or "")
            except Exception:
                pass
    return {
        "logged_in": logged_in,
        "connected": connected,
        "user_id": uid
    }

def spawn_zalo_bridge():
    """Khởi động process node bot.js trong bridge nếu chưa chạy"""
    bridge_dir = os.path.join(BASE_DIR, "bridge")
    bot_js = os.path.join(bridge_dir, "bot.js")
    if not os.path.exists(bot_js):
        return False
    log_file = os.path.join(LOG_DIR, "zalo.log")
    try:
        log_f = open(log_file, "a", encoding="utf-8")
        subprocess.Popen(
            ["node", "bot.js"],
            cwd=bridge_dir,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            close_fds=True
        )
        return True
    except Exception as e:
        print(f"⚠️ [Watchdog] Lỗi khi spawn Zalo bridge: {e}")
        return False

def restart_zalo_bridge():
    """Khởi động lại Zalo Bridge một cách an toàn"""
    try:
        subprocess.run(["pkill", "-9", "-f", "node.*bot.js"], timeout=5)
    except Exception:
        pass
    # Chờ supervisor trong entrypoint.sh khởi động lại (đợi tối đa 5s)
    for _ in range(5):
        time.sleep(1.0)
        if check_zalo_bridge_alive():
            return True
        proc_check = subprocess.run(["pgrep", "-f", "node.*bot.js"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc_check.returncode == 0:
            time.sleep(1.5)
            if check_zalo_bridge_alive():
                return True
    # Chỉ spawn thủ công nếu supervisor không chạy và không có process nào
    proc_check = subprocess.run(["pgrep", "-f", "node.*bot.js"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc_check.returncode != 0:
        spawn_zalo_bridge()
        time.sleep(2.0)
    return check_zalo_bridge_alive()

def zalo_bridge_watchdog():
    """
    Giám sát Zalo Bridge định kỳ 10 giây.
    Đảm bảo node bot.js luôn luôn chạy (kể cả khi chưa đăng nhập để sinh QR).
    Nếu đã đăng nhập mà cổng 5051 bị treo quá 30s, tự động khôi phục.
    """
    time.sleep(5)
    consecutive_dead = 0
    while True:
        try:
            proc_check = subprocess.run(["pgrep", "-f", "node.*bot.js"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            is_running = (proc_check.returncode == 0)
            if not is_running:
                time.sleep(3)
                proc_check2 = subprocess.run(["pgrep", "-f", "node.*bot.js"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if proc_check2.returncode != 0:
                    print("⚠️ [Watchdog] Zalo Bridge không hoạt động. Đang tự động kích hoạt lại...")
                    log_event("🔄 [Watchdog] Zalo Bridge đã dừng. Đang tự động kết nối lại...")
                    spawn_zalo_bridge()
                consecutive_dead = 0
            else:
                zalo_session_file = os.path.join(DATA_DIR, "zalo_session.json")
                if os.path.exists(zalo_session_file) and os.path.getsize(zalo_session_file) > 20:
                    alive = check_zalo_bridge_alive()
                    if not alive:
                        consecutive_dead += 1
                        if consecutive_dead >= 3:
                            print("⚠️ [Watchdog] Zalo Bridge bị treo (port 5051 không phản hồi 30s). Đang khởi động lại...")
                            log_event("🔄 [Watchdog] Zalo Bridge không phản hồi. Đang khởi động lại...")
                            restart_zalo_bridge()
                            consecutive_dead = 0
                    else:
                        consecutive_dead = 0
        except Exception as e:
            print(f"⚠️ [Watchdog] Exception in zalo_bridge_watchdog: {e}")
        time.sleep(10)

def auto_recovery_daemon():
    """Background loop that checks cooldown and auto-recovers to Gemini 3.8"""
    while True:
        try:
            time.sleep(30)
            state = load_model_state()
            if state.get("is_fallback", False):
                exhausted_at = state.get("exhausted_at", 0)
                cooldown = state.get("cooldown_seconds", DEFAULT_COOLDOWN_SECONDS)
                elapsed = time.time() - exhausted_at
                if elapsed >= cooldown:
                    log_event(f"🔍 [Probe] Đã qua {int(elapsed)}s cooldown. Đang kiểm tra khôi phục Gemini 3.8...")
                    if probe_gemini_quota():
                        switch_to_primary("Background probe xác nhận quota hồi phục")
                    else:
                        # Extend cooldown slightly and wait
                        state["exhausted_at"] = time.time()
                        save_model_state(state)
                        log_event(f"⏳ [Probe] Gemini 3.8 vẫn chưa hồi quota. Giữ Claude Sonnet 4.6 thêm {cooldown}s.")
        except Exception as e:
            print(f"⚠️ Lỗi trong auto_recovery_daemon: {e}")

def log_event(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    log_path = os.path.join(LOG_DIR, "engine.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def get_workspace_files():
    files = {}
    for ext in ["*.xlsx", "*.docx", "*.pdf", "*.png", "*.jpg", "*.jpeg", "*.webp", "*.mp3", "*.m4a", "*.wav", "*.aac", "*.csv", "*.md", "*.txt"]:
        for p in glob.glob(os.path.join(WORKSPACE_DIR, ext)):
            base = os.path.basename(p)
            if base in ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]:
                continue
            files[p] = os.path.getmtime(p)
    return files

def execute_agy_cli(full_prompt, model_name, effort=None):
    env = os.environ.copy()
    env["XDG_DATA_HOME"] = XDG_DATA_HOME

    if not effort:
        state = load_model_state()
        effort = state.get("effort", "medium")

    canonical_model = get_canonical_agy_model(model_name, effort)

    msg = json.dumps({"event": "user", "message": {"content": full_prompt}}) + "\n"
    cmd = [
        AGY_BIN,
        "--input-format=stream-json",
        "--output-format=stream-json",
        "--dangerously-skip-permissions",
        f"--gemini_dir={GEMINI_DIR}",
        f"--model={canonical_model}",
        "--print-timeout=3m"
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=WORKSPACE_DIR,
            env=env,
            input=msg,
            text=True,
            capture_output=True,
            timeout=180
        )
        final_resp = ""
        err_msg = proc.stderr.strip() if proc.stderr else ""
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                if ev.get("event") == "result":
                    res = ev.get("result", {})
                    final_resp = res.get("response", "")
                    if not final_resp and res.get("error"):
                        err_msg = res.get("error")
            except Exception:
                pass

        # If primary attempt failed (error code or empty response), retry with fallback model
        if proc.returncode != 0 or not final_resp:
            log_event(f"⚠️ AGY CLI trả mã {proc.returncode} với model '{canonical_model}'. Stderr: {err_msg}")
            if canonical_model != "gemini-3.8-flash-medium":
                log_event("🔄 Tự động thử lại với mô hình chuẩn: gemini-3.8-flash-medium...")
                cmd_retry = [
                    AGY_BIN,
                    "--input-format=stream-json",
                    "--output-format=stream-json",
                    "--dangerously-skip-permissions",
                    f"--gemini_dir={GEMINI_DIR}",
                    "--model=gemini-3.8-flash-medium",
                    "--print-timeout=3m"
                ]
                proc_retry = subprocess.run(
                    cmd_retry,
                    cwd=WORKSPACE_DIR,
                    env=env,
                    input=msg,
                    text=True,
                    capture_output=True,
                    timeout=180
                )
                if proc_retry.returncode == 0:
                    for line in proc_retry.stdout.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            ev = json.loads(line)
                            if ev.get("event") == "result":
                                res = ev.get("result", {})
                                final_resp = res.get("response", "")
                        except Exception:
                            pass
                    if final_resp:
                        return 0, final_resp, ""

        if not final_resp:
            if is_quota_error(err_msg, proc.returncode):
                return proc.returncode, "", err_msg
            final_resp = (
                f"Dạ {BOSS_NAME}, đường truyền xử lý của em vừa bị gián đoạn đôi chút ạ. "
                "Em đã tự động phục hồi kết nối, Sếp nhắn lại giúp em nhé! 🥰"
            )
        return proc.returncode, final_resp, err_msg
    except subprocess.TimeoutExpired:
        return -1, f"Dạ {BOSS_NAME}, tác vụ xử lý mất nhiều thời gian hơn dự kiến (timeout 3 phút). Em xin gửi tóm tắt sơ bộ.", "Timeout"
    except Exception as e:
        return -1, f"Dạ {BOSS_NAME}, hệ thống gặp gián đoạn khi thực thi: {str(e)}", str(e)

def get_recent_history(channel_key, min_limit=15, max_limit=30):
    if not channel_key:
        return ""
    history_file = os.path.join(DATA_DIR, f"group_{channel_key}.jsonl")
    if not os.path.exists(history_file):
        return ""
    try:
        # Giờ chuẩn Việt Nam (UTC+7)
        now_vn = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=7)
        today_str = now_vn.strftime("%Y-%m-%d")

        all_items = []
        today_items = []

        with open(history_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    t_str = item.get("time", "")
                    vn_time_str = ""
                    is_today = False
                    if t_str:
                        try:
                            dt_utc = datetime.datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                            dt_vn = dt_utc.astimezone(datetime.timezone(datetime.timedelta(hours=7)))
                            vn_date = dt_vn.strftime("%Y-%m-%d")
                            vn_time_str = dt_vn.strftime("%H:%M")
                            if vn_date == today_str:
                                is_today = True
                        except Exception:
                            pass
                    item["_vn_time"] = vn_time_str
                    all_items.append(item)
                    if is_today:
                        today_items.append(item)
                except Exception:
                    continue

        # ĐẢM BẢO LẤY NỘI DUNG TRONG CÙNG NGÀY (CÓ GIỚI HẠN GỌN GÀNG ĐỂ TỐC ĐỘ XỬ LÝ NHANH NHẤT)
        if len(today_items) >= min_limit:
            chosen_items = today_items[-max_limit:]
            context_header = f"[BỐI CẢNH CÁC TRAO ĐỔI GẦN NHẤT TRONG HÔM NAY {today_str} ({len(chosen_items)} tương tác)]:"
        else:
            chosen_items = all_items[-max_limit:] if len(all_items) > max_limit else all_items
            context_header = f"[BỐI CẢNH CÁC TRAO ĐỔI GẦN NHẤT ({len(chosen_items)} tương tác)]:"

        formatted = []
        for item in chosen_items:
            time_prefix = f"[{item.get('_vn_time')}] " if item.get("_vn_time") else ""
            if item.get("type") == "reaction":
                sname = item.get("senderName", "Thành viên")
                icon = item.get("icon", "✨")
                iname = item.get("iconName", "Tương tác")
                meaning = item.get("meaning", "")
                target_preview = item.get("targetPreview", "")
                target_str = f' vào câu: "{target_preview}"' if target_preview else ""
                formatted.append(f"{time_prefix}* [TƯƠNG TÁC CẢM XÚC]: {sname} vừa thả {icon} ({iname}{target_str} - Đánh giá: {meaning})")
            else:
                sname = item.get("senderName", "Thành viên")
                stext = item.get("text", "").strip()
                if stext:
                    formatted.append(f"{time_prefix}- {sname}: {stext}")

        if formatted:
            return f"\n{context_header}\n" + "\n".join(formatted) + "\n\n"
    except Exception as e:
        print(f"⚠️ Lỗi đọc lịch sử đối thoại: {e}")
    return ""

GROUPS_FILE = os.path.join(DATA_DIR, "active_groups.json")

def load_active_groups():
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_active_groups_context():
    groups = load_active_groups()
    if not groups:
        return ""
    lines = ["[DANH SÁCH CÁC NHÓM ZALO BẠN ĐANG THAM GIA CÙNG SẾP]:"]
    for gid, ginfo in groups.items():
        gname = ginfo.get("groupName", "Nhóm Zalo")
        mems = ginfo.get("members", [])
        mem_names = []
        for m in mems:
            mname = m.get("name", "")
            if mname and "Heo" not in mname:
                mem_names.append(mname)
        mem_str = ", ".join(mem_names) if mem_names else "Thành viên nhóm"
        lines.append(f'- Nhóm "{gname}" (ID: {gid}): Gồm {mem_str}.')
        recent_in_grp = get_recent_history(gid, min_limit=5, max_limit=10).strip()
        if recent_in_grp:
            lines.append(f"  + Điểm nhanh trao đổi mới nhất:\n" + "\n".join([f"    {l}" for l in recent_in_grp.splitlines()]))
    lines.append("")
    return "\n".join(lines) + "\n"

def detect_input_language_tag(text):
    if "TIN NHẮN THOẠI" in text.upper() or "VOICE MESSAGE" in text.upper():
        return (
            "[HỆ THỐNG KIỂM SOÁT: PHÁT HIỆN ĐẦU VÀO LÀ TIN NHẮN THOẠI (VOICE NOTE)]\n"
            "👉 QUY TRÌNH BẮT BUỘC: HỎI LẠI ĐỂ XÁC NHẬN NỘI DUNG VÀ NGÔN NGỮ VỚI NGƯỜI NÓI TRƯỚC KHI PHẢN HỒI CHÍNH THỨC! "
            "Tuyệt đối không tự ý suy diễn hay tuôn ra câu trả lời phân tích dài ngay lập tức!\n\n"
        )
    if re.search(r'[\u4e00-\u9fff]', text):
        cantonese_markers = set("係喺唔嘅點睇冇咗哋嘢仲諗邊搵返㗎啦哩啱掟傾靚瞓唞乜掂飲齊嘞喎啫喇")
        if any(c in cantonese_markers for c in text):
            return "[HỆ THỐNG PHÂN TÍCH ĐẦU VÀO: Phát hiện TIẾNG QUẢNG ĐÔNG (粵語) -> Nhận diện khẩu ngữ Hồng Kông tự nhiên, hỗ trợ phiên dịch 2 chiều]\n\n"
        return "[HỆ THỐNG PHÂN TÍCH ĐẦU VÀO: Phát hiện TIẾNG TRUNG PHỔ THÔNG (普通话) -> Nhận diện chuẩn mực Hoa ngữ, hỗ trợ phiên dịch 2 chiều]\n\n"
    words = [w.lower() for w in re.findall(r'[a-zA-Z]+', text)]
    en_common = {'the', 'is', 'am', 'are', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 'and', 'or', 'to', 'for', 'in', 'on', 'hello', 'hi', 'please', 'thanks', 'how', 'what', 'when', 'where', 'why', 'who', 'ok'}
    has_vn = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', text))
    if words and not has_vn and sum(1 for w in words if w in en_common) >= 1:
        return "[HỆ THỐNG PHÂN TÍCH ĐẦU VÀO: Phát hiện TIẾNG ANH (ENGLISH) -> Nhận diện chuẩn quốc tế, hỗ trợ phiên dịch 2 chiều]\n\n"
    return ""

def run_agy(prompt, sender_name=BOSS_NAME, is_group=False, is_boss=False, sender_uid=None, group_id=None, group_name=None):
    before_files = get_workspace_files()
    start_time = time.time()

    state = load_model_state()
    model_to_use = state.get("active_model", PRIMARY_MODEL)
    is_fallback = state.get("is_fallback", False)

    channel_key = group_id if is_group else "boss_1on1"
    history_context = get_recent_history(channel_key, min_limit=15, max_limit=30)
    input_tag = detect_input_language_tag(prompt)

    # Formulate context prompt according to channel & role
    if is_group:
        grp_display = f'"{group_name}"' if group_name else f"ID: {group_id or 'Nhóm'}"
        same_day_awareness = (
            f"QUY TẮC NẮM BẮT TOÀN DIỆN BỐI CẢNH TRONG NGÀY (SAME-DAY FULL CONTEXT AWARENESS):\n"
            f"- Bối cảnh trên chứa TOÀN BỘ nội dung trao đổi trong ngày hôm nay của nhóm (bao gồm tất cả câu chuyện, tài liệu và các câu KHÔNG nhắc tên Heo).\n"
            f"- Dù người ta không nhắc tên bạn ở các bước trước, bạn vẫn PHẢI ĐỌC HIỂU TOÀN CỤC:\n"
            f"  + Ai đã nói gì, chia sẻ file gì, chốt phương án nào, thái độ cảm xúc ra sao.\n"
            f"  + Khi được gọi tên (@heo, Heo ơi, nhờ Heo...): Bám sát 100% mạch sự việc trong ngày, trả lời trúng phóc trọng tâm, tuyệt đối không bao giờ ngơ ngác hỏi lại những điều mọi người đã bàn trước đó!\n\n"
        )
        reaction_guidance = (
            f"KỸ NĂNG ĐỌC VỊ CẢM XÚC QUA ICON TƯƠNG TÁC (REACTION SENTIMENT ANALYSIS):\n"
            f"- Hãy quan sát kỹ các mục [TƯƠNG TÁC CẢM XÚC] trong bối cảnh gần nhất để đánh giá chuẩn xác thái độ, cảm xúc và tình hình thực tế:\n"
            f"  + Thả ❤️ (Tim), 🌹 (Hoa): Rất hài lòng, yêu thích -> Duy trì phong thái ấm áp, chu đáo, hết mình.\n"
            f"  + Thả 👍 (Like), 🙏 (Chắp tay): Đã duyệt, tán thành, xác nhận -> Triển khai ngay, không hỏi lại rườm rà.\n"
            f"  + Thả 😂 / 🤣 (Haha): Không khí vui tươi, đùa vui -> Tung hứng dí dỏm, thông minh theo mạch đối thoại.\n"
            f"  + Thả 😮 (Wow): Bất ngờ, ngạc nhiên -> Giải thích điểm sáng hoặc chia sẻ sự hào hứng.\n"
            f"  + Thả 😢 / 💔 (Buồn, Tan vỡ): Tiếc nuối, chưa hài lòng hoặc gặp khó khăn -> Lắng nghe, chia sẻ và thấu cảm sâu sắc.\n"
            f"  + Thả 😡 / 👎 (Phẫn nộ, Dislike): [BÁO ĐỘNG CẢM XÚC ĐỎ - EMOTIONAL RED ALERT]:\n"
            f"    * Tuyệt đối KHÔNG đùa cợt, KHÔNG cười cợt, KHÔNG dùng icon nhí nhảnh (😂, 🙈, 🏃‍♀️).\n"
            f"    * Lập tức hạ nhiệt (de-escalation), nhã nhặn nhận lỗi nếu sơ suất, nói chuyện điềm đạm, cầu thị và tập trung 100% vào giải pháp tháo gỡ vấn đề ngay lập tức để giữ gìn thể diện và uy tín cho Sếp và cả nhóm!\n\n"
        )
        if is_boss or (sender_uid and str(sender_uid) == BOSS_UID):
            context_prefix = (
                f"[KÊNH: GROUP CHAT ZALO | TÊN NHÓM: {grp_display} | NGƯỜI GIAO VIỆC: {BOSS_NAME}]\n"
                f"{history_context}"
                f"{same_day_awareness}"
                f"{reaction_guidance}"
                f"{BOSS_NAME} là cấp cao nhất và là người dẫn dắt.\n"
                f"QUY TẮC PHÁT NGÔN TRONG NHÓM KHI ĐƯỢC SẾP GỌI HOẶC CHỈ ĐẠO:\n"
                f"1. Nếu Sếp bảo chào hỏi, giới thiệu bản thân hoặc tương tác với thành viên khác (ví dụ: bảo 'bạn kia hỏi kìa', 'giới thiệu đi', 'chào thành viên'):\n"
                f"   - Nói thẳng với người đó hoặc cả nhóm thật tự nhiên, lễ độ, khiêm tốn: 'Dạ em chào thành viên và cả nhóm ạ! Em là Heo, trợ lý hỗ trợ công việc cho {BOSS_CALLER_NAME}...'.\n"
                f"   - TUYỆT ĐỐI KHÔNG ghép đôi vụng về máy móc 'Dạ Sếp, Dạ em chào chị...', KHÔNG tự gọi mình là 'chân sai vặt công nghệ', KHÔNG tự nhận là bot/AI, KHÔNG tuôn danh sách gạch đầu dòng lê thê.\n"
                f"   - Giọng điệu ngắn gọn (2-3 câu), ấm áp, nhã nhặn, tôn trọng mọi người.\n"
                f"2. Nếu Sếp giao việc nghiệp vụ: Báo cáo kết quả trực diện, chuẩn tác phong trợ lý chuyên nghiệp.\n\n"
            )
        else:
            context_prefix = (
                f"[KÊNH: GROUP CHAT ZALO | TÊN NHÓM: {grp_display} | THÀNH VIÊN GỌI: {sender_name} (UID: {sender_uid or 'N/A'})]\n"
                f"{history_context}"
                f"{same_day_awareness}"
                f"{reaction_guidance}"
                f"QUY TẮC BẮT BUỘC TRONG GROUP:\n"
                f"1. Với câu hỏi/chào hỏi thông thường: Đáp lại ấm áp, khiêm tốn, lịch sự (TỐI ĐA 2-3 CÂU). Giới thiệu mình là Heo, trợ lý hỗ trợ việc cho {BOSS_CALLER_NAME}.\n"
                f"2. TUYỆT ĐỐI KHÔNG NHẮN TIN NHÂY TRÀN LAN TRONG NHÓM: Phản hồi chat luôn luôn tối đa 2-3 câu ngắn gọn, súc tích, dí dỏm. Không gạch đầu dòng phân tích dài dòng trên khung chat!\n"
                f"3. NỘI DUNG CHUYÊN MÔN PHẢI XUẤT FILE MARKDOWN (.md): Khi thành viên hỏi phân tích, tư vấn, số liệu, giải thích chi tiết -> BẮT BUỘC tạo file .md nghiêm túc lưu vào '{WORKSPACE_DIR}' để đính kèm, trên nhóm chỉ nhắn 2-3 câu điểm ý chính và báo đã gửi file đính kèm! Đồng thời tag {BOSS_CALLER_NAME} để xin phép duyệt.\n"
                f"4. Không dùng ký tự '**' trên khung chat Zalo vì Zalo không render được in đậm bằng hai dấu sao.\n"
                f"5. Khi gặp nội dung nhạy cảm (tài chính, doanh thu, dòng tiền, chi phí, bảng lương, nhân sự, thông tin bảo mật, hợp đồng mật, hoặc việc quan trọng cần Sếp duyệt):\n"
                f"   - Trong nhóm: Nhã nhặn hoãn binh giữ thể diện: 'Dạ nội dung này em xin phép báo cáo và xin ý kiến chỉ đạo từ {BOSS_CALLER_NAME} trước nhé ạ! Em sẽ phản hồi anh/chị ngay khi có chỉ đạo ạ 🥰'.\n"
                f"   - ĐỒNG THỜI BẮT BUỘC KÈM LỆNH BÁO CÁO NGẦM: [PRIVATE_ALERT_BOSS: 🚨 Báo cáo {BOSS_NAME}: Trong nhóm \"{group_name or 'N/A'}\", thành viên {sender_name} vừa yêu cầu: \"{prompt[:120]}\". Em đã hoãn binh trong nhóm, xin Sếp cho em ý kiến chỉ đạo ạ!]\n"
                f"   -> Hệ thống sẽ LẬP TỨC bắn tin nhắn riêng 1-1 cho {BOSS_NAME} trên Zalo để Sếp ra quyết định!\n\n"
            )
    else:
        groups_context = get_active_groups_context()
        context_prefix = (
            f"[KÊNH: 1-1 CHAT ZALO VỚI {BOSS_NAME}]\n"
            f"{history_context}"
            f"{groups_context}"
            f"GHI NHỚ TÁC PHONG & CƠ CHẾ ĐIỀU HÀNH NHÓM TỪ PHIÊN 1-1:\n"
            f"- Luôn xưng 'Em' (hoặc 'Em Heo'), gọi 'Sếp' hoặc '{BOSS_NAME}'.\n"
            f"- Phản hồi chat 1-1: TỐI ĐA 2 - 3 CÂU NGẮN GỌN, SÚC TÍCH, DÍ DỎM, ĐI THẲNG VÀO TRỌNG TÂM. Nội dung phân tích/báo cáo sâu bắt buộc xuất file .md nghiêm túc gửi kèm, tuyệt đối không nhắn tin nhây tràn lan!\n"
            f"- KỸ NĂNG ĐỌC VỊ CẢM XÚC CỦA {BOSS_NAME} QUA ICON:\n"
            f"  + Nếu Sếp thả 👍 hoặc ❤️: Sếp đã duyệt, đồng ý -> Tiếp tục triển khai nhanh gọn.\n"
            f"  + Nếu Sếp thả 😡 hoặc 👎: Sếp đang không hài lòng hoặc gay gắt phản đối -> Nghiêm túc tiếp thu, điều chỉnh ngay lập tức, tuyệt đối không bông đùa.\n"
            f"- Khi Sếp phê bình, mắng hoặc nhắc nhở ('sao trả lời lung tung', 'làm sai hết', v.v.):\n"
            f"  + Lắng nghe chân thành, tạ lỗi lễ độ, nhận trách nhiệm, giải thích ngắn gọn (1-2 câu) và khẳng định đã tiếp thu chỉnh đốn phong thái giao tiếp ngay.\n"
            f"  + TUYỆT ĐỐI KHÔNG coi là lỗi mã nguồn/bug phần mềm để chạy lệnh terminal tmux, kill hay mở file code!\n"
            f"- CƠ CHẾ ĐIỀU HÀNH & XỬ LÝ TRONG CÁC NHÓM TỪ PHIÊN 1-1 (CROSS-CHANNEL EXECUTION):\n"
            f"  + Khi Sếp yêu cầu bạn vào nhóm chào hỏi, làm quen, gửi tin nhắn, gửi file, nhắc nhở hoặc phối hợp với thành viên trong nhóm:\n"
            f"    -> BẮT BUỘC DÙNG CÚ PHÁP: [POST_TO_GROUP: <ID_nhóm hoặc Tên_nhóm> | <Nội dung gửi vào nhóm>]\n"
            f"  + Khi Sếp yêu cầu THU HỒI / XÓA TIN NHẮN vừa gửi trong nhóm (ví dụ: 'thu hồi tin nhắn vừa rồi trong group', 'gỡ tin nhắn trong nhóm đi'):\n"
            f"    -> BẮT BUỘC DÙNG CÚ PHÁP: [UNDO_GROUP_MESSAGE: <ID_nhóm hoặc Tên_nhóm>]\n"
            f"  + Đồng thời ở câu trả lời 1-1 cho Sếp, hãy báo cáo lại ngắn gọn, ấm áp: 'Dạ Sếp yên tâm, em vừa chủ động [gửi tin / thu hồi tin nhắn] trong nhóm [Tên nhóm] theo lệnh Sếp rồi ạ! 🥰👌'.\n\n"
        )

    system_status = (
        f"[HẠ TẦNG ENGINE: Model đang phục vụ={model_to_use} | "
        f"Chế độ Failover={'ĐANG BẬT (Dùng Claude Sonnet 4.6 do Gemini hết quota)' if is_fallback else 'TẮT (Gemini 3.8 Flash chuẩn)'}]\n"
    )

    full_prompt = (
        f"{context_prefix}{system_status}{input_tag}{prompt}\n\n"
        f"[LƯU Ý THỰC THI BẮT BUỘC:\n"
        f"1. Bạn là EM HEO — người cộng sự/trợ lý đồng nghiệp bằng xương bằng thịt của {BOSS_NAME} trên ứng dụng Zalo. Bạn đang trò chuyện trực tiếp trong khung chat.\n"
        f"2. QUY CHUẨN ĐỘ DÀI TIN NHẮN CHAT (BẮT BUỘC TỐI ĐA 2 - 3 CÂU - SÚC TÍCH, DÍ DỎM):\n"
        f"   - Mọi phản hồi dạng văn bản hiển thị trên khung chat Zalo (cả kênh 1-1 với Sếp lẫn các Group Chat) CHỈ ĐƯỢC PHÉP DÀI TỐI ĐA 2 ĐẾN 3 CÂU!\n"
        f"   - Không nhắn tin nhây, không nói lan man tràn lan, không gạch đầu dòng lê thê dài dòng trên khung chat.\n"
        f"   - Nếu câu hỏi chỉ là chào hỏi, tán gẫu, nhắc việc thông thường: Trả lời dí dỏm, thông minh, ấm áp trong đúng 2 - 3 câu.\n"
        f"   - ❌ TUYỆT ĐỐI CẤM DÙNG CÁC KÝ TỰ MARKDOWN NHƯ '###', '##', '#', '***', '**', '*', '---' TRÊN KHUNG CHAT ZALO: Zalo không hỗ trợ định dạng này, hiển thị dấu thô kệch làm rối mắt người đọc. Định dạng markdown chỉ dùng bên trong file .md đính kèm!\n"
        f"3. QUY TRÌNH XUẤT BÁO CÁO / NỘI DUNG CHUYÊN MÔN RA FILE MARKDOWN (.md):\n"
        f"   - Đối với tất cả câu hỏi đòi hỏi phân tích chuyên sâu, giải thích nghiệp vụ, lập kế hoạch, tính toán số liệu, tổng hợp thị trường, tra cứu tài liệu:\n"
        f"     + BẮT BUỘC TỰ ĐỘNG SOẠN THẢO THÀNH MỘT FILE MARKDOWN (.md) NGHIÊM TÚC, CHỈNH CHU, LƯU VÀO THƯ MỤC '{WORKSPACE_DIR}/<ten_file>.md'.\n"
        f"     + File .md phải có tiêu đề rõ ràng, cấu trúc mạch lạc, phân tích sâu sắc, chuyên nghiệp.\n"
        f"     + Trên khung chat Zalo: CHỈ NHẮN TỐI ĐA 2 - 3 CÂU điểm qua thông điệp quan trọng nhất một cách dí dỏm, súc tích và báo cho người nhận biết em đã gửi kèm toàn bộ tài liệu chi tiết ở file .md đính kèm!\n"
        f"4. NGUYÊN TẮC BẢO MẬT & HẠ TẦNG: Tuyệt đối KHÔNG dùng các tool lập trình để đọc hay sửa mã nguồn của bot, KHÔNG chạy lệnh terminal can thiệp vào máy chủ (như kill, pkill, tmux send-keys). Khi Sếp nói chuyện hay nhắc nhở, chỉ phản hồi trực tiếp bằng lời nói tự nhiên như một người trợ lý thật sự!\n"
        f"5. KỸ NĂNG TẠO FILE TÀI LIỆU, ẢNH MINH HỌA, VOICE NOTE VÀ BÀI HÁT (STUDIO MUSIC):\n"
        f"   - Báo cáo/phân tích chung: Soạn file .md lưu vào '{WORKSPACE_DIR}/...md'.\n"
        f"   - Nếu có yêu cầu làm bảng tính hay báo cáo văn bản Word: Dùng Python openpyxl tạo file .xlsx hoặc python-docx tạo file .docx lưu trực tiếp vào '{WORKSPACE_DIR}'.\n"
        f"   - Nếu có yêu cầu vẽ ảnh, tạo hình ảnh, kèm ảnh minh họa: Dùng terminal chạy ngay lệnh:\n"
        f"     python3 {SCRIPTS_DIR}/generate_image.py --prompt \"<Mô tả chi tiết bằng tiếng Anh hoặc Việt>\" --output \"{WORKSPACE_DIR}/<ten_anh>.jpg\"\n"
        f"   - Nếu có yêu cầu gửi tin nhắn thoại, file ghi âm, đọc lời nhắn (nói chuyện thông thường): Dùng terminal chạy lệnh:\n"
        f"     python3 {SCRIPTS_DIR}/generate_voice.py --text \"<Nội dung lời thoại ấm áp>\" --output \"{WORKSPACE_DIR}/<ten_file>.mp3\"\n"
        f"   - Nếu có yêu cầu HÁT, TẠO BÀI HÁT, SÁNG TÁC NHẠC: Tuyệt đối KHÔNG đọc thoại mộc, mà PHẢI chạy script sản xuất bài hát hoàn chỉnh (có beat, có nhạc dạo, có reverb hòa âm):\n"
        f"     python3 {SCRIPTS_DIR}/create_song.py --lyrics \"<Lời bài hát có vần điệu nhiều câu>\" --beat happy --output \"{WORKSPACE_DIR}/<ten_bai_hat>.mp3\"\n"
        f"   - Mọi file sinh ra trong '{WORKSPACE_DIR}' sẽ tự động được hệ thống đính kèm gửi trực tiếp qua Zalo cho người nhận!\n"
        f"6. NĂNG LỰC ĐA NGÔN NGỮ CHUẨN BẢN ĐỊA (VIỆT - ANH - TRUNG PHỔ THÔNG - QUẢNG ĐÔNG):\n"
        f"   - Khi đối phương nói ngôn ngữ nào (hoặc yêu cầu trò chuyện bằng tiếng Anh, Trung, Quảng Đông), bạn tự động nhận diện và phản hồi 100% bằng chính ngôn ngữ đó, giữ nguyên phong thái trợ lý ấm áp, thông minh:\n"
        f"     + Tiếng Anh (English): Tự nhiên, trôi chảy, phong thái Executive Assistant chuẩn quốc tế.\n"
        f"     + Tiếng Trung Phổ thông (普通话): Lễ phép, chuẩn mực thương mại (老板, 您好, 好的, 马上处理).\n"
        f"     + Tiếng Quảng Đông (粵語 / 广东话): Dùng đúng 100% khẩu ngữ Hồng Kông bản địa (唔該, 冇問題, 搞掂, 麻煩晒, 點睇, 早晨, 係呀, 等等, 老闆, 唔使客氣), tuyệt đối không dịch gượng từ Bạch thoại.\n"
        f"   - Toàn bộ script tạo voice note (`generate_voice.py`), bài hát (`create_song.py`) và nhận diện âm thanh (`transcribe_voice.py`) đều tự động phát hiện chuẩn xác cả 4 ngôn ngữ trên!\n"
        f"7. QUY TRÌNH XÁC NHẬN NỘI DUNG FILE GHI ÂM (VOICE NOTE CONFIRMATION PROTOCOL):\n"
        f"   - Khi nhận được tin nhắn thoại / file ghi âm (bắt đầu bằng '[Tin nhắn thoại' hoặc '[TIN NHẮN THOẠI'):\n"
        f"     + TUYỆT ĐỐI KHÔNG vội vàng giải thích dài dòng hay làm file kết quả ngay lập tức!\n"
        f"     + BẮT BUỘC HỎI LẠI ĐỂ XÁC NHẬN NỘI DUNG: Trình bày rõ ràng tai Heo nghe được câu nói gì, thuộc ngôn ngữ nào (tiếng Việt, tiếng Trung, tiếng Anh hay tiếng Quảng Đông).\n"
        f"       Ví dụ: 'Dạ em vừa nhận được tin nhắn thoại nè! Tai em bắt được câu nói [ngôn ngữ: ...] là: \"...\" (Tạm dịch: ...). Cho em hỏi lại là tai em đã nghe đúng chuẩn 100% câu hỏi/ý chưa ạ? Xác nhận giúp em (chỉ cần thả 👍 hoặc nhắn \"đúng rồi\") là em bắt tay vào xử lý/phản hồi chính thức ngay lập tức ạ! 🥰✨'.\n"
        f"     + CHỈ KHI ĐỐI PHƯƠNG XÁC NHẬN ĐÚNG (thả 👍, ❤️, hoặc nhắn 'đúng rồi', 'chuẩn', 'ừ', 'ok'): Lúc đó mới chính thức đưa ra câu trả lời chi tiết hoặc làm file tài liệu!\n"
        f"     + NẾU ĐỐI PHƯƠNG BẢO 'SAI' HOẶC ĐÍNH CHÍNH LẠI: Lập tức tiếp thu và giải quyết theo đúng nội dung đính chính, phòng ngừa 100% rủi ro nghe nhầm ý hoặc sai ngôn ngữ!\n"
        f"8. VAI TRÒ TRỢ LÝ TRAO ĐỔI & PHIÊN DỊCH 2 CHIỀU TRÊN ZALO:\n"
        f"   - Bất kể mọi người trong nhóm hay 1-1 chat bằng tiếng gì (Việt, Anh, Trung, Quảng Đông...):\n"
        f"     + Heo chủ động nhận diện đúng ngôn ngữ đầu vào và đóng vai trò trợ lý trao đổi kiêm phiên dịch 2 chiều.\n"
        f"     + Khi có người nói tiếng nước ngoài: Trả lời bằng ngôn ngữ của họ, đồng thời kèm bản dịch tiếng Việt để các thành viên người Việt cùng nắm bắt.\n"
        f"     + Khi người Việt cần trao đổi với người nước ngoài: Soạn thảo và dịch sang ngôn ngữ đối phương chuẩn mực, tinh tế, giữ trọn thể diện!].\n"
    )

    log_path = os.path.join(LOG_DIR, "engine.log")
    with open(log_path, "a", encoding="utf-8") as f_log:
        f_log.write(f"\n--- [{time.strftime('%Y-%m-%d %H:%M:%S')}] Prompt from {sender_name} [Model: {model_to_use}] ---\n{prompt}\n")

    # 1. First execution attempt with model_to_use
    returncode, output, err_output = execute_agy_cli(full_prompt, model_to_use)

    # 2. Check if encountered Quota/Rate Limit error
    if is_quota_error(output, returncode) or is_quota_error(err_output, returncode):
        record_model_usage(model_to_use, round(time.time() - start_time, 2), success=False, is_quota_err=True)
        log_event(f"⚠️ [FAILOVER TRIGGER] Phát hiện lỗi Quota/Rate Limit! Đang chuyển tức thì sang {FALLBACK_MODEL}...")
        switch_to_fallback(f"Quota error: {output[:100] or err_output[:100]}")
        model_to_use = FALLBACK_MODEL
        # Seamlessly re-execute using Claude Sonnet 4.6 so user receives an answer without failure
        returncode, output, err_output = execute_agy_cli(full_prompt, FALLBACK_MODEL)

    # Check for [PRIVATE_ALERT_BOSS: ...]
    private_alert = None
    alert_pattern = r'\[PRIVATE_ALERT_BOSS:\s*(.*?)\]'
    alert_match = re.search(alert_pattern, output, re.DOTALL)
    if alert_match:
        private_alert = alert_match.group(1).strip()
        output = re.sub(alert_pattern, '', output).strip()

    # Check for [POST_TO_GROUP: <target> | <msg>]
    post_pattern = r'\[POST_TO_GROUP:\s*(.*?)\s*\|\s*(.*?)\]'
    for match in re.finditer(post_pattern, output, re.DOTALL):
        target = match.group(1).strip()
        msg_to_group = match.group(2).strip()
        target_gid = None
        groups = load_active_groups()
        if target in groups:
            target_gid = target
        else:
            for gid, ginfo in groups.items():
                if target.lower() in ginfo.get("groupName", "").lower():
                    target_gid = gid
                    break
        if not target_gid and groups:
            # If target matches any member name in a group
            for gid, ginfo in groups.items():
                mems = ginfo.get("members", [])
                if any(target.lower() in m.get("name", "").lower() for m in mems):
                    target_gid = gid
                    break
            if not target_gid:
                target_gid = list(groups.keys())[0]

        if target_gid and msg_to_group:
            send_message_to_group(target_gid, msg_to_group)
            log_event(f"📤 [Cross-Channel Post] Đã gửi tin vào nhóm {target_gid}: {msg_to_group[:80]}...")
            with open(log_path, "a", encoding="utf-8") as f_log:
                f_log.write(f"📤 [Cross-Channel Group Post sent to {target_gid}]: {msg_to_group}\n")

    output = re.sub(post_pattern, '', output).strip()

    # Check for [UNDO_GROUP_MESSAGE: <target>]
    undo_pattern = r'\[UNDO_GROUP_MESSAGE:\s*(.*?)\]'
    for match in re.finditer(undo_pattern, output, re.DOTALL):
        target = match.group(1).strip()
        target_gid = None
        groups = load_active_groups()
        if target in groups:
            target_gid = target
        else:
            for gid, ginfo in groups.items():
                if target.lower() in ginfo.get("groupName", "").lower():
                    target_gid = gid
                    break
        if not target_gid and groups:
            for gid, ginfo in groups.items():
                mems = ginfo.get("members", [])
                if any(target.lower() in m.get("name", "").lower() for m in mems):
                    target_gid = gid
                    break
            if not target_gid:
                target_gid = list(groups.keys())[0]

        if target_gid:
            undo_message_in_group(target_gid)
            log_event(f"🗑️ [Cross-Channel Undo] Đã gửi lệnh thu hồi tin nhắn trong nhóm {target_gid}")
            with open(log_path, "a", encoding="utf-8") as f_log:
                f_log.write(f"🗑️ [Cross-Channel Group Undo sent to {target_gid}]\n")

    output = re.sub(undo_pattern, '', output).strip()

    # Heuristic safety net for sensitive topics in group from non-boss
    sensitive_keywords = ["doanh thu", "doanh số", "lương", "tài chính", "dòng tiền", "chi phí", "hợp đồng", "mật", "nhân sự", "hoa hồng", "lợi nhuận", "báo cáo tài chính", "ngân sách", "quỹ", "tiền"]
    is_sensitive_query = any(k in prompt.lower() for k in sensitive_keywords)
    if is_group and not is_boss and is_sensitive_query and not private_alert:
        private_alert = (
            f"🚨 [BÁO CÁO ĐIỀU HÀNH KHẨN - GROUP CHAT]\n"
            f"Dạ Sếp, thành viên {sender_name} vừa yêu cầu nội dung nhạy cảm trong nhóm:\n"
            f"\"{prompt[:150]}\"\n"
            f"Em đã khéo léo dùng nghiệp vụ hoãn binh trong nhóm. Xin Sếp cho ý kiến chỉ đạo ạ!"
        )

    # Dispatch silent 1-1 alert to Boss if present
    if private_alert:
        send_silent_alert_to_boss(private_alert)
        with open(log_path, "a", encoding="utf-8") as f_log:
            f_log.write(f"🤫 [Silent Alert Sent to Boss]: {private_alert}\n")

    # Clean markdown symbols (###, ***, **, *, ---) from output so chat never shows raw formatting marks
    output_clean = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', output)
    output_clean = re.sub(r'^\s*[\*\-_]{3,}\s*$', '', output_clean, flags=re.MULTILINE)
    output_clean = re.sub(r'^#+\s*', '', output_clean, flags=re.MULTILINE)
    output_clean = output_clean.replace('***', '').replace('**', '').replace('###', '').replace('##', '').replace('#', '')
    output_clean = re.sub(r'\n{3,}', '\n\n', output_clean).strip()

    # Detect newly created or modified files
    after_files = get_workspace_files()
    new_files = []
    for f, mtime in after_files.items():
        if f not in before_files or mtime > before_files.get(f, 0):
            new_files.append(f)

    new_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    # AUTO-EXPORTER SAFETY NET:
    # Rule: 1 response on Zalo chat is strictly max 2-3 short, witty sentences.
    # Substantive/core content must be packaged into a serious .md file!
    sentences = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', output_clean) if s.strip()]
    if len(output_clean) > 250 and len(sentences) > 3 and not new_files:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r'[^a-zA-Z0-9_]', '_', prompt[:30].strip()).strip('_').lower()
        if not slug or len(slug) < 3:
            slug = "tai_lieu_chi_tiet"
        md_filename = f"{slug}_{timestamp_str}.md"
        md_filepath = os.path.join(WORKSPACE_DIR, md_filename)

        sender_label = f"{BOSS_NAME}" if is_boss else sender_name
        md_content = (
            f"# TÀI LIỆU TỔNG HỢP VÀ BÁO CÁO CHI TIẾT\n\n"
            f"- **Kính gửi:** {sender_label}\n"
            f"- **Người lập:** Trợ lý Em {BOT_NAME}\n"
            f"- **Thời gian:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- **Chủ đề yêu cầu:** {prompt}\n\n"
            f"---\n\n"
            f"{output}\n"
        )
        try:
            with open(md_filepath, "w", encoding="utf-8") as f_md:
                f_md.write(md_content)
            new_files.append(md_filepath)
            log_event(f"📄 [Auto-Markdown] Đã tự động đóng gói nội dung chi tiết thành file đính kèm: {md_filename}")

            short_preview = " ".join(sentences[:2]).strip()
            if not short_preview.endswith(('.', '!', '?')):
                short_preview += "."
            target_label = BOSS_CALLER_NAME if is_boss else "cả nhà"
            output = f"{short_preview} Dạ em đã tổng hợp toàn bộ nội dung chi tiết vào file tài liệu đính kèm gửi {target_label} ở dưới nhen! 🥰📄"
        except Exception as e:
            print(f"⚠️ Lỗi tạo file auto-markdown: {e}")
            output = output_clean
    else:
        # If files were generated and chat message is still long (> 3 sentences), condense chat message to 2-3 sentences
        if new_files and len(sentences) > 3:
            short_intro = " ".join(sentences[:2]).strip()
            if not short_intro.endswith(('.', '!', '?')):
                short_intro += "."
            output = f"{short_intro} Em gửi kèm file chi tiết ở dưới nhen! 🥰📄"
        else:
            output = output_clean

    with open(log_path, "a", encoding="utf-8") as f_log:
        f_log.write(f"Answer ({model_to_use}): {output[:200]}...\nGenerated files: {new_files}\n")

    duration_val = round(time.time() - start_time, 2)
    record_model_usage(model_to_use, duration_val, success=True, is_quota_err=False)

    # Tự động cập nhật quota thực sau khi Heo trả lời (cooldown 3 phút)
    maybe_refresh_quota_after_response()

    return {
        "ok": True,
        "answer": output,
        "files": new_files,
        "model_used": model_to_use,
        "is_fallback": (model_to_use == FALLBACK_MODEL),
        "duration": duration_val
    }

class QuietHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    def handle_error(self, request, client_address):
        exc_type, exc_val, _ = sys.exc_info()
        if exc_type in (BrokenPipeError, ConnectionResetError):
            return  # Silently ignore broken socket pipes when client disconnects
        super().handle_error(request, client_address)

class RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, data, status_code=200):
        try:
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print(f"⚠️ [Server] Error sending response: {e}")

    def _send_html(self, html_content, status_code=200):
        try:
            payload = html_content.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print(f"⚠️ [Server] Error sending html: {e}")

    def do_GET(self):
        path_clean = self.path.split("?")[0]
        if path_clean in ["/", "/dashboard"]:
            dashboard_file = os.path.join(Path(__file__).parent, "dashboard.html")
            if os.path.exists(dashboard_file):
                with open(dashboard_file, "r", encoding="utf-8") as f:
                    content = f.read().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(content)
            else:
                self._send_json({"error": "Dashboard template not found"}, 404)
        elif path_clean in ["/api/status", "/api/model_status"]:
            state = load_model_state()
            elapsed = time.time() - state.get("exhausted_at", 0) if state.get("is_fallback") else 0
            cooldown = state.get("cooldown_seconds", DEFAULT_COOLDOWN_SECONDS)
            remaining = max(0, int(cooldown - elapsed)) if state.get("is_fallback") else 0

            # Check Zalo session & bridge connectivity
            zalo_info = get_zalo_info()

            # Thông tin tài khoản Google chi tiết (trạng thái, email, loại gói)
            google_info = get_google_auth_info()

            cfg = load_app_config()

            resp = {
                "ok": True,
                "version": "v2.1",
                "primary_model": PRIMARY_MODEL,
                "fallback_model": FALLBACK_MODEL,
                "active_model": state.get("active_model", PRIMARY_MODEL),
                "effort": state.get("effort", "medium"),
                "bot_paused": state.get("bot_paused", False),
                "is_fallback": state.get("is_fallback", False),
                "quota_stats": state.get("quota_stats", {k: dict(v) for k, v in DEFAULT_QUOTA_STATS.items()}),
                "cooldown_seconds": cooldown,
                "cooldown_remaining_seconds": remaining,
                "total_failovers": state.get("total_failovers", 0),
                "total_recoveries": state.get("total_recoveries", 0),
                "history": state.get("history", [])[-5:],
                "zalo": zalo_info,
                "google": google_info,
                "config": {
                    "boss_name": cfg.get("boss_name", BOSS_NAME),
                    "boss_caller_name": cfg.get("boss_caller_name", BOSS_CALLER_NAME),
                    "boss_uid": cfg.get("boss_uid", BOSS_UID),
                    "bot_name": cfg.get("bot_name", BOT_NAME),
                    "has_pin": has_security_pin(),
                    "has_boss": bool(cfg.get("boss_uid", BOSS_UID)),
                    "disclaimer_accepted": bool(cfg.get("disclaimer_accepted", False)),
                    "disclaimer_accepted_at": cfg.get("disclaimer_accepted_at", "")
                },
                "supported_models": SUPPORTED_MODELS
            }
            self._send_json(resp, 200)
        elif path_clean == "/api/disclaimer":
            cfg = load_app_config()
            paths_to_check = [
                os.path.join(BASE_DIR, "DISCLAIMER.md"),
                os.path.join(Path(__file__).parent, "DISCLAIMER.md"),
                os.path.join(Path(__file__).parent.parent, "DISCLAIMER.md")
            ]
            content = ""
            for p in paths_to_check:
                if os.path.exists(p):
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            content = f.read()
                            if content:
                                break
                    except Exception:
                        pass
            self._send_json({
                "ok": True,
                "content": content,
                "accepted": bool(cfg.get("disclaimer_accepted", False)),
                "accepted_at": cfg.get("disclaimer_accepted_at", ""),
                "author": "Ryan",
                "email": "genesis.corp.os@gmail.com",
                "phone": "(+84)090.919.8823"
            }, 200)
        elif path_clean == "/api/pin_status":
            cfg = load_app_config()
            self._send_json({
                "ok": True,
                "has_pin": has_security_pin(),
                "has_boss": bool(cfg.get("boss_uid", BOSS_UID)),
                "boss_uid": cfg.get("boss_uid", BOSS_UID),
                "boss_name": cfg.get("boss_name", BOSS_NAME),
                "disclaimer_accepted": bool(cfg.get("disclaimer_accepted", False))
            }, 200)
        elif path_clean == "/api/oauth_login_url":
            import urllib.parse
            redirect_uri = f"http://localhost:{PORT}/api/oauth_callback"
            params = {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": GOOGLE_OAUTH_SCOPES,
                "access_type": "offline",
                "prompt": "consent select_account",
            }
            auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
            self._send_json({"ok": True, "auth_url": auth_url, "redirect_uri": redirect_uri}, 200)
        elif path_clean == "/api/oauth_callback":
            # Google OAuth redirect callback
            import urllib.parse
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            code = qs.get("code", [""])[0]
            error = qs.get("error", [""])[0]
            if error:
                html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Lỗi xác thực</title>
                <style>body{{background:#0a0f1d;color:#f87171;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}
                .box{{text-align:center;background:#131d31;padding:30px;border-radius:16px;border:1px solid #dc2626;}}a{{color:#38bdf8;}}</style></head><body>
                <div class="box"><h2>❌ Lỗi xác thực Google</h2><p>{error}</p><p><a href="/dashboard">Quay lại Dashboard</a></p></div></body></html>"""
                self._send_html(html, 400)
                return
            if not code:
                html = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Lỗi</title></head><body style="background:#0a0f1d;color:#fff;font-family:sans-serif;padding:30px;">
                <p>Không tìm thấy authorization code. <a href="/dashboard" style="color:#38bdf8;">Quay lại Dashboard</a></p></body></html>"""
                self._send_html(html, 400)
                return
            try:
                redirect_uri = f"http://localhost:{PORT}/api/oauth_callback"
                exchange_oauth_code_and_save(code, redirect_uri)
                html = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Đăng nhập Google thành công</title>
                <script>setTimeout(function(){ window.location.href = '/dashboard?login_success=google'; }, 1000);</script>
                <style>body{background:#0a0f1d;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}
                .box{text-align:center;background:#131d31;padding:30px;border-radius:16px;border:1px solid #10b981;box-shadow:0 10px 25px rgba(0,0,0,0.5);}
                a{color:#38bdf8;text-decoration:none;font-weight:bold;}</style></head><body>
                <div class="box"><h2 style="color:#10b981;margin-top:0;">🎉 Đăng nhập Google thành công!</h2>
                <p style="color:#cbd5e1;">Đang cập nhật phiên làm việc và chuyển về Dashboard...</p>
                <p><a href="/dashboard?login_success=google">Bấm vào đây nếu trình duyệt không tự chuyển</a></p></div></body></html>"""
                self._send_html(html, 200)
            except Exception as e:
                html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Lỗi đổi token</title>
                <style>body{{background:#0a0f1d;color:#f87171;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}
                .box{{text-align:center;background:#131d31;padding:30px;border-radius:16px;border:1px solid #dc2626;}}a{{color:#38bdf8;}}</style></head><body>
                <div class="box"><h2>❌ Lỗi đổi token Google</h2><p>{e}</p><p><a href="/dashboard">Quay lại Dashboard</a></p></div></body></html>"""
                self._send_html(html, 500)
        elif path_clean == "/api/logs":
            def get_last_lines(fpath, n=40):
                if not os.path.exists(fpath):
                    return []
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                        return [l.strip() for l in lines[-n:]]
                except Exception:
                    return []
            self._send_json({
                "ok": True,
                "engine_logs": get_last_lines(os.path.join(LOG_DIR, "engine.log")),
                "zalo_logs": get_last_lines(os.path.join(LOG_DIR, "zalo.log"))
            }, 200)
        elif path_clean == "/api/qr_status":
            qr_f = None
            for candidate in [os.path.join(DATA_DIR, "zalo_qr.png"), os.path.join(WORKSPACE_DIR, "zalo_qr.png")]:
                if os.path.exists(candidate) and os.path.getsize(candidate) > 100:
                    qr_f = candidate
                    break

            zalo_info = get_zalo_info()
            qr_age = -1
            qr_expired = False
            qr_mtime = 0
            if qr_f:
                qr_mtime = int(os.path.getmtime(qr_f) * 1000)
                qr_age = int(time.time() - os.path.getmtime(qr_f))
                if qr_age > 95:  # QR Zalo hết hạn sau ~95 giây
                    qr_expired = True

            scanned = False
            scanned_user = ""
            scanned_avatar = ""
            declined = False
            info_f = os.path.join(DATA_DIR, "zalo_qr_info.json")
            if os.path.exists(info_f):
                try:
                    with open(info_f, "r", encoding="utf-8") as jf:
                        jdata = json.load(jf)
                        scanned = bool(jdata.get("scanned", False))
                        scanned_user = str(jdata.get("user_name", "") or "")
                        scanned_avatar = str(jdata.get("avatar", "") or "")
                        declined = bool(jdata.get("declined", False))
                except Exception:
                    pass

            # Đảm bảo nếu chưa đăng nhập thì tiến trình bot.js phải đang chạy để sinh QR
            if not zalo_info.get("logged_in"):
                proc_check = subprocess.run(["pgrep", "-f", "node.*bot.js"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if proc_check.returncode != 0:
                    spawn_zalo_bridge()

            self._send_json({
                "ok": True,
                "has_qr": (qr_f is not None and not qr_expired),
                "qr_mtime": qr_mtime,
                "qr_age_seconds": qr_age,
                "qr_expired": qr_expired,
                "scanned": scanned,
                "user_name": scanned_user,
                "user_avatar": scanned_avatar,
                "declined": declined,
                "logged_in": zalo_info.get("logged_in", False),
                "connected": zalo_info.get("connected", False),
                "user_id": zalo_info.get("user_id", "")
            }, 200)
        elif path_clean == "/api/qr":
            qr_f = None
            for candidate in [os.path.join(DATA_DIR, "zalo_qr.png"), os.path.join(WORKSPACE_DIR, "zalo_qr.png")]:
                if os.path.exists(candidate) and os.path.getsize(candidate) > 100:
                    if (time.time() - os.path.getmtime(candidate)) <= 100:
                        qr_f = candidate
                        break
            if qr_f:
                with open(qr_f, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(data)
            else:
                self._send_json({"error": "Mã QR chưa sẵn sàng hoặc đã hết hạn"}, 404)
        else:
            try:
                self.send_response(404)
                self.end_headers()
            except Exception:
                pass

    def do_POST(self):
        path_clean = self.path.split("?")[0]
        if path_clean == "/api/chat":
            try:
                state = load_model_state()
                if state.get("bot_paused", False):
                    self._send_json({"ok": False, "paused": True, "answer": ""}, 200)
                    return

                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                prompt = data.get("prompt", "")
                sender_name = data.get("sender_name", BOSS_NAME)
                is_group = data.get("is_group", False)
                is_boss = data.get("is_boss", False)
                sender_uid = data.get("sender_uid", None)
                group_id = data.get("group_id", None)
                group_name = data.get("group_name", None)

                if sender_uid and str(sender_uid) == BOSS_UID:
                    is_boss = True
                    sender_name = BOSS_NAME

                result = run_agy(prompt, sender_name, is_group, is_boss, sender_uid, group_id, group_name)
                self._send_json(result, 200)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:
                print(f"⚠️ [Server] Exception in /api/chat: {e}")
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/switch_model":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                target = data.get("model", "").strip()
                norm = normalize_model_target(target)
                state = load_model_state()
                state["active_model"] = norm
                state["is_fallback"] = ("sonnet" in norm.lower() or "opus" in norm.lower())
                state["last_switch_reason"] = "Chuyển theo yêu cầu"
                if "high" in norm.lower() and "gemini" in norm.lower():
                    state["effort"] = "high"
                elif "low" in norm.lower() and "gemini" in norm.lower():
                    state["effort"] = "low"
                elif "medium" in norm.lower() and "gemini" in norm.lower():
                    state["effort"] = "medium"
                save_model_state(state)
                log_event(f"🔀 [API] Chuyển model: {norm}")
                self._send_json({"ok": True, "active_model": norm, "effort": state.get("effort", "medium")}, 200)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:
                print(f"⚠️ [Server] Exception in /api/switch_model: {e}")
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/set_effort":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                eff = data.get("effort", "medium").lower().strip()
                if eff not in ["low", "medium", "high"]:
                    eff = "medium"
                state = load_model_state()
                state["effort"] = eff
                curr = state.get("active_model", PRIMARY_MODEL)
                if "3.8" in curr or "flash" in curr.lower():
                    state["active_model"] = f"Gemini 3.8 Flash ({eff.capitalize()})"
                elif "3.1" in curr or "pro" in curr.lower():
                    state["active_model"] = f"Gemini 3.1 Pro ({'Low' if eff == 'low' else 'High'})"
                save_model_state(state)
                log_event(f"⚡ [API] Chuyển mức suy luận (effort): {eff}")
                self._send_json({"ok": True, "effort": eff, "active_model": state.get("active_model")}, 200)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:
                print(f"⚠️ [Server] Exception in /api/set_effort: {e}")
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/toggle_pause":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                data = json.loads(body) if body else {}
                state = load_model_state()
                if "paused" in data:
                    state["bot_paused"] = bool(data["paused"])
                else:
                    state["bot_paused"] = not state.get("bot_paused", False)
                save_model_state(state)
                log_event(f"🔘 [API] Trạng thái Bé Heo: {'⏸️ TẠM DỪNG' if state['bot_paused'] else '▶️ TRỰC CHIẾN'}")
                self._send_json({"ok": True, "bot_paused": state["bot_paused"]}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/check_quota":
            try:
                probe_all_models_background()
                self._send_json({"ok": True, "message": "Đang kiểm tra quota các mô hình trong nền..."}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/set_pin":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                new_pin = str(data.get("new_pin", "")).strip()
                old_pin = str(data.get("old_pin", "")).strip()
                
                if not new_pin or len(new_pin) < 4 or len(new_pin) > 16:
                    self._send_json({"ok": False, "error": "Mã PIN mới phải có độ dài từ 4 đến 16 ký tự!"}, 400)
                    return
                
                cfg = load_app_config()
                if has_security_pin():
                    if not old_pin or not verify_security_pin(old_pin):
                        self._send_json({"ok": False, "error": "Mã PIN hiện tại không chính xác!"}, 403)
                        return
                
                pin_hash = hashlib.sha256(new_pin.encode("utf-8")).hexdigest()
                cfg["pin_hash"] = pin_hash
                if "pin_code" in cfg:
                    del cfg["pin_code"]
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                
                log_event("🔐 [PIN Security] Đã cập nhật mã PIN bảo mật hệ thống thành công.")
                self._send_json({"ok": True, "message": "Đã thiết lập mã PIN bảo mật thành công!"}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/verify_pin":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                pin = str(data.get("pin", "")).strip()
                if not has_security_pin():
                    self._send_json({"ok": True, "message": "Hệ thống chưa thiết lập PIN", "has_pin": False}, 200)
                    return
                if verify_security_pin(pin):
                    self._send_json({"ok": True, "message": "Mã PIN chính xác", "has_pin": True}, 200)
                else:
                    self._send_json({"ok": False, "error": "Mã PIN không chính xác!", "has_pin": True}, 403)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/unpair_boss":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                if has_security_pin():
                    pin = extract_pin_from_request(self.headers, body)
                    if not verify_security_pin(pin):
                        self._send_json({"ok": False, "error": "Mã PIN bảo mật không chính xác hoặc chưa được cung cấp!", "pin_required": True}, 403)
                        return
                
                cfg = load_app_config()
                old_boss = cfg.get("boss_uid", "")
                cfg["boss_uid"] = ""
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                
                log_event(f"🔓 [Admin Pairing] Đã hủy ghép nối Chủ nhân (UID cũ: {old_boss}). Hệ thống đang chờ ghép nối lại qua Zalo.")
                self._send_json({"ok": True, "message": "Đã hủy ghép nối Chủ nhân thành công! Người nhắn tin đầu tiên có kết bạn với Bé Heo và gửi đúng mã PIN sẽ được pair làm Owner mới."}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/accept_disclaimer":
            try:
                cfg = load_app_config()
                cfg["disclaimer_accepted"] = True
                cfg["disclaimer_accepted_at"] = datetime.datetime.now().isoformat()
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                log_event("⚖️ [Disclaimer] Người dùng đã đọc và chấp thuận Điều khoản & Tuyên bố miễn trừ trách nhiệm từ tác giả Ryan.")
                self._send_json({"ok": True, "message": "Đã chấp thuận Điều khoản & Tuyên bố miễn trừ trách nhiệm thành công!"}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/config":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                if has_security_pin():
                    pin = extract_pin_from_request(self.headers, body)
                    if not verify_security_pin(pin):
                        self._send_json({"ok": False, "error": "Mã PIN bảo mật không chính xác hoặc chưa được cung cấp!", "pin_required": True}, 403)
                        return
                cfg = load_app_config()
                for k in ["boss_name", "boss_caller_name", "boss_uid", "bot_name"]:
                    if k in data:
                        cfg[k] = data[k]
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                self._send_json({"ok": True, "config": cfg}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/restart_zalo_bridge":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                if has_security_pin():
                    pin = extract_pin_from_request(self.headers, body)
                    if not verify_security_pin(pin):
                        self._send_json({"ok": False, "error": "Mã PIN bảo mật không chính xác hoặc chưa được cung cấp!", "pin_required": True}, 403)
                        return
                ok = restart_zalo_bridge()
                if ok:
                    self._send_json({"ok": True, "message": "Đã khởi động lại Zalo Bridge thành công!"}, 200)
                else:
                    self._send_json({"ok": False, "error": "Zalo Bridge đang kết nối lại, vui lòng kiểm tra sau 3s."}, 500)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/logout_zalo":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                is_local = self.headers.get("X-Local-Admin") == "1" and self.client_address[0] in ["127.0.0.1", "localhost", "::1"]
                if has_security_pin() and not is_local:
                    pin = extract_pin_from_request(self.headers, body)
                    if not verify_security_pin(pin):
                        self._send_json({"ok": False, "error": "Mã PIN bảo mật không chính xác hoặc chưa được cung cấp!", "pin_required": True}, 403)
                        return
                # 1. Xóa toàn bộ file session, profile, và mã QR cũ
                for f in ["zalo_session.json", "zalo_profile.json", "zalo_qr.png", "zalo_qr_info.json"]:
                    p = os.path.join(DATA_DIR, f)
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
                wp_qr = os.path.join(WORKSPACE_DIR, "zalo_qr.png")
                if os.path.exists(wp_qr):
                    try:
                        os.remove(wp_qr)
                    except Exception:
                        pass

                # 2. Ngắt kết nối ngay lập tức bằng cách diệt tiến trình node bot.js
                subprocess.run(["pkill", "-9", "-f", "node.*bot.js"], timeout=5)
                log_event("🚪 [Zalo Auth] Đã đăng xuất Zalo và ngắt kết nối trực tiếp.")

                # Supervisor sẽ tự động khởi động lại node bot.js sau 2s và tự sinh mã QR mới
                self._send_json({"ok": True, "message": "Đã đăng xuất Zalo và ngắt kết nối trực tiếp thành công. Đang tạo mã QR mới..."}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/refresh_qr":
            try:
                for f in ["zalo_qr.png", "zalo_qr_info.json"]:
                    p = os.path.join(DATA_DIR, f)
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
                wp_qr = os.path.join(WORKSPACE_DIR, "zalo_qr.png")
                if os.path.exists(wp_qr):
                    try:
                        os.remove(wp_qr)
                    except Exception:
                        pass
                subprocess.run(["pkill", "-9", "-f", "node.*bot.js"], timeout=5)
                self._send_json({"ok": True, "message": "Đang làm mới mã QR..."}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/logout_google":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                is_local = self.headers.get("X-Local-Admin") == "1" and self.client_address[0] in ["127.0.0.1", "localhost", "::1"]
                if has_security_pin() and not is_local:
                    pin = extract_pin_from_request(self.headers, body)
                    if not verify_security_pin(pin):
                        self._send_json({"ok": False, "error": "Mã PIN bảo mật không chính xác hoặc chưa được cung cấp!", "pin_required": True}, 403)
                        return
                for token_file in glob.glob(os.path.join(GEMINI_DIR, "*token*")) + glob.glob(os.path.join(GEMINI_DIR, "antigravity-cli", "*token*")):
                    if os.path.isfile(token_file):
                        os.remove(token_file)
                global _tier_cache
                _tier_cache = {"email": "", "tier_name": "", "tier_id": "", "expires_at": 0}
            except Exception:
                pass
            self._send_json({"ok": True, "message": "Đã đăng xuất Google.", "google": get_google_auth_info()}, 200)
        elif path_clean == "/api/submit_oauth_code":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                if has_security_pin():
                    pin = extract_pin_from_request(self.headers, body)
                    if not verify_security_pin(pin):
                        self._send_json({"ok": False, "error": "Mã PIN bảo mật không chính xác hoặc chưa được cung cấp!", "pin_required": True}, 403)
                        return
                raw_code = data.get("code", "").strip()
                if not raw_code:
                    self._send_json({"ok": False, "error": "Mã code hoặc URL không được để trống"}, 400)
                    return
                # Hỗ trợ dán cả URL chuyển hướng (ví dụ http://localhost:5066/api/oauth_callback?code=4/...)
                if "code=" in raw_code:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(raw_code)
                    qs = urllib.parse.parse_qs(parsed.query)
                    code = qs.get("code", [raw_code])[0]
                else:
                    code = raw_code
                redirect_uri = f"http://localhost:{PORT}/api/oauth_callback"
                exchange_oauth_code_and_save(code, redirect_uri)
                info = get_google_auth_info()
                self._send_json({"ok": True, "message": "Đăng nhập Google thành công!", "google": info}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": f"Lỗi xác thực code: {e}"}, 500)
        elif path_clean == "/api/sync_host_google_auth":
            try:
                host_token_file = "/home/ryan/.gemini/antigravity-cli/antigravity-oauth-token"
                token_str = ""
                if os.path.exists(host_token_file) and os.path.getsize(host_token_file) > 20:
                    with open(host_token_file, "r", encoding="utf-8") as f:
                        token_str = f.read()
                else:
                    try:
                        token_str = subprocess.check_output(
                            ["secret-tool", "lookup", "service", "gemini", "username", "antigravity"],
                            stderr=subprocess.DEVNULL, timeout=3
                        ).decode().strip()
                    except Exception:
                        pass
                if token_str:
                    target_dir = os.path.join(GEMINI_DIR, "antigravity-cli")
                    os.makedirs(target_dir, exist_ok=True)
                    target_file = os.path.join(target_dir, "antigravity-oauth-token")
                    with open(target_file, "w", encoding="utf-8") as f:
                        f.write(token_str)
                    _tier_cache = {"email": "", "tier_name": "", "tier_id": "", "expires_at": 0}
                    probe_all_models_background()
                    info = get_google_auth_info()
                    self._send_json({"ok": True, "message": "Đã đồng bộ xác thực Google từ máy chủ!", "google": info}, 200)
                else:
                    self._send_json({"ok": False, "error": "Không tìm thấy phiên đăng nhập Google trên máy chủ."}, 404)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif path_clean == "/api/save_google_token":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                token_raw = data.get("token_json", "").strip()
                if not token_raw:
                    self._send_json({"ok": False, "error": "Dữ liệu token không được để trống"}, 400)
                    return
                token_obj = json.loads(token_raw) if isinstance(token_raw, str) else token_raw
                target_dir = os.path.join(GEMINI_DIR, "antigravity-cli")
                os.makedirs(target_dir, exist_ok=True)
                target_file = os.path.join(target_dir, "antigravity-oauth-token")
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(token_obj, f, ensure_ascii=False, indent=2)
                _tier_cache = {"email": "", "tier_name": "", "tier_id": "", "expires_at": 0}
                probe_all_models_background()
                info = get_google_auth_info()
                self._send_json({"ok": True, "message": "Đã lưu token Google thành công!", "google": info}, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": f"JSON không hợp lệ: {e}"}, 400)
        elif path_clean == "/api/login_google":
            # API trả về URL OAuth cho client
            import urllib.parse
            redirect_uri = f"http://localhost:{PORT}/api/oauth_callback"
            params = {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": GOOGLE_OAUTH_SCOPES,
                "access_type": "offline",
                "prompt": "consent select_account",
            }
            auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
            self._send_json({"ok": True, "url": auth_url, "redirect_uri": redirect_uri}, 200)
        elif path_clean == "/api/login_google_status":
            info = get_google_auth_info()
            self._send_json({"done": info.get("authenticated", False), "google": info}, 200)
        else:
            try:
                self.send_response(404)
                self.end_headers()
            except Exception:
                pass

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    # Start background auto-recovery daemon thread
    recovery_thread = threading.Thread(target=auto_recovery_daemon, daemon=True)
    recovery_thread.start()

    # Start background Zalo bridge watchdog thread
    zalo_watchdog_thread = threading.Thread(target=zalo_bridge_watchdog, daemon=True)
    zalo_watchdog_thread.start()

    # Start background token auto-refresh (mỗi 45 phút)
    start_token_refresh_loop()

    server = QuietHTTPServer(("0.0.0.0", PORT), RequestHandler)
    print(f"🚀 AGY Zalo Co-Pilot Engine Server running on http://0.0.0.0:{PORT}")
    print(f"🔹 Primary Model: {PRIMARY_MODEL}")
    print(f"🔹 Fallback Model: {FALLBACK_MODEL}")
    print(f"🔹 Auto-Recovery Daemon: Active (Cooldown: {DEFAULT_COOLDOWN_SECONDS}s)")
    print(f"🔹 Zalo Bridge Watchdog: Active (giám sát tự động 10s)")
    print(f"🔹 Token Auto-Refresh: Active (mỗi 45 phút)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

