#!/usr/bin/env python3
"""
send_zalo.py: Công cụ dòng lệnh gửi tin nhắn / file / hình ảnh trực tiếp qua Zalo Bridge
Hỗ trợ cả gửi đến cá nhân (User) lẫn Nhóm (Group).
"""

import sys
import os
import argparse
import requests
from pathlib import Path

BRIDGE_URL = os.environ.get("BRIDGE_URL", "http://127.0.0.1:5051")

def send_message(thread_id, text, thread_type="user"):
    url = f"{BRIDGE_URL}/api/send"
    payload = {
        "thread_id": str(thread_id),
        "thread_type": thread_type.lower(),
        "message": text
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_file(thread_id, file_path, message="", thread_type="user"):
    url = f"{BRIDGE_URL}/api/send-file"
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"File does not exist: {file_path}"}
    
    payload = {
        "thread_id": str(thread_id),
        "thread_type": thread_type.lower(),
        "file_path": os.path.abspath(file_path),
        "message": message
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Gửi tin nhắn hoặc file qua Zalo Bridge")
    parser.add_argument("--thread", "-t", required=True, help="ID của người nhận hoặc nhóm")
    parser.add_argument("--type", choices=["user", "group"], default="user", help="Loại hội thoại: user hoặc group")
    parser.add_argument("--message", "-m", default="", help="Nội dung tin nhắn")
    parser.add_argument("--file", "-f", default=None, help="Đường dẫn file đính kèm (ảnh, văn bản, âm thanh)")

    args = parser.parse_args()

    if args.file:
        res = send_file(args.thread, args.file, message=args.message, thread_type=args.type)
    else:
        if not args.message:
            print("Lỗi: Cần cung cấp --message hoặc --file")
            sys.exit(1)
        res = send_message(args.thread, args.message, thread_type=args.type)

    print(res)

if __name__ == "__main__":
    main()
