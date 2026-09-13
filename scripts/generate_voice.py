#!/usr/bin/env python3
"""
generate_voice.py: Tạo file ghi âm / tin nhắn thoại AI đa ngôn ngữ (Text-to-Speech)
Hỗ trợ tự động nhận diện ngôn ngữ và phát âm chuẩn bản xứ:
- Tiếng Việt (vi): vi-VN-HoaiMyNeural (Nữ ấm áp, tự nhiên)
- Tiếng Anh (en): en-US-JennyNeural (Nữ thân thiện, chuẩn quốc tế)
- Tiếng Trung Quốc Phổ thông (zh): zh-CN-XiaoxiaoNeural (Nữ chuẩn phổ thông ấm áp)
- Tiếng Quảng Đông (yue): zh-HK-HiuMaanNeural (Nữ Hồng Kông khẩu ngữ chuẩn xác)
"""

import os
import sys
import re
import argparse
import asyncio
import time
import subprocess
import shutil
from pathlib import Path

BASE_DIR = os.environ.get("BASE_DIR", str(Path(__file__).parent.parent.resolve()))
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", str(Path(BASE_DIR) / "workspace"))

LANGUAGE_VOICE_MAP = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "yue": "zh-HK-HiuMaanNeural",
}

CANTONESE_CHARS = set("係喺唔嘅點睇冇咗哋嘢仲諗邊搵返㗎啦哩啱掟傾靚瞓唞乜掂飲齊嘞喎啫喇")
VIETNAMESE_ACCENTS = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.I)
CHINESE_CHARS = re.compile(r'[\u4e00-\u9fff]')

def detect_language(text):
    text = text.strip()
    if not text:
        return "vi"

    # 1. Kiểm tra ký tự tiếng Trung / Quảng Đông
    c_chars = CHINESE_CHARS.findall(text)
    if len(c_chars) >= 2 or (len(text) < 10 and len(c_chars) >= 1):
        if any(ch in CANTONESE_CHARS for ch in text):
            return "yue"
        return "zh"

    # 2. Đếm số lượng đặc trưng tiếng Anh vs tiếng Việt
    words = [w.lower() for w in re.findall(r'[a-zA-Z]+', text)]
    en_common = {
        'the', 'is', 'am', 'are', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 
        'and', 'or', 'to', 'for', 'in', 'on', 'at', 'with', 'hello', 'hi', 
        'please', 'thanks', 'thank', 'can', 'will', 'good', 'morning', 'afternoon', 
        'yes', 'no', 'of', 'how', 'what', 'when', 'where', 'why', 'who', 'ok',
        'ready', 'support', 'meeting', 'report', 'today', 'tomorrow', 'sure'
    }
    en_matches = sum(1 for w in words if w in en_common)
    vn_accents = len(VIETNAMESE_ACCENTS.findall(text))

    if en_matches >= 2 and en_matches > vn_accents:
        return "en"
    if vn_accents >= 2:
        return "vi"
    if en_matches >= 1 and len(words) >= 3:
        return "en"

    return "vi"

async def tts_async(text, output_file, voice="vi-VN-HoaiMyNeural", rate="+0%"):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)

def generate_voice(text, output_path, lang="auto", voice=None, rate="+0%"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    detected_lang = detect_language(text) if (not lang or lang == "auto") else lang
    selected_voice = voice or LANGUAGE_VOICE_MAP.get(detected_lang, LANGUAGE_VOICE_MAP["vi"])
    lang_label = {"vi": "Tiếng Việt", "en": "Tiếng Anh", "zh": "Tiếng Trung (Mandarin)", "yue": "Tiếng Quảng Đông (Cantonese)"}.get(detected_lang, detected_lang)

    print(f"🎙️ [AI Voice Note] Đang tạo file ghi âm [{lang_label} - {selected_voice}]: '{text[:60]}...'")
    try:
        asyncio.run(tts_async(text, output_path, voice=selected_voice, rate=rate))
        size_kb = os.path.getsize(output_path) // 1024
        print(f"✅ Đã tạo file ghi âm thành công: {output_path} ({size_kb} KB)")
        return True
    except Exception as e:
        print(f"⚠️ Lỗi tạo giọng đọc qua python module ({e}), thử dùng edge-tts CLI...")
        try:
            edge_bin = shutil.which("edge-tts") or "edge-tts"
            cmd = [
                edge_bin,
                "--voice", selected_voice,
                "--text", text,
                "--write-media", output_path
            ]
            subprocess.run(cmd, check=True, timeout=30)
            print(f"✅ Đã tạo file ghi âm qua CLI: {output_path}")
            return True
        except Exception as cli_err:
            print(f"❌ Lỗi hoàn toàn khi tạo voice: {cli_err}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Tạo file âm thanh / ghi âm lời nói AI đa ngôn ngữ")
    parser.add_argument("--text", "-t", required=True, help="Nội dung cần đọc thành tiếng")
    parser.add_argument("--output", "-o", default=None, help="Đường dẫn file âm thanh đầu ra (.mp3 hoặc .m4a)")
    parser.add_argument("--lang", "-l", choices=["auto", "vi", "en", "zh", "yue"], default="auto", help="Ngôn ngữ (mặc định: auto)")
    parser.add_argument("--voice", "-v", default=None, help="Tên giọng đọc cụ thể (nếu muốn chỉ định)")
    parser.add_argument("--rate", "-r", default="+0%", help="Tốc độ đọc (ví dụ: +10%, -5%)")
    args = parser.parse_args()

    output = args.output
    if not output:
        clean_name = "".join(c if c.isalnum() else "_" for c in args.text[:25]).strip("_")
        output = os.path.join(WORKSPACE_DIR, f"voice_{clean_name}_{int(time.time())}.mp3")

    success = generate_voice(args.text, output, lang=args.lang, voice=args.voice, rate=args.rate)
    if success:
        print(f"[OUTPUT_VOICE] {output}")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
