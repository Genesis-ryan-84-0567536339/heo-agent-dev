#!/usr/bin/env python3
"""
create_song.py: Bộ công cụ sản xuất bài hát hoàn chỉnh cho Bé Heo
Quy trình chuyên nghiệp:
1. Tinh chỉnh lời bài hát theo nhịp điệu ca hát vui tươi (pitch cao hơn, ngân nga)
2. Thu âm vocal bằng giọng nữ truyền cảm Microsoft Edge TTS
3. Xử lý hiệu ứng phòng thu (Studio Reverb, Echo sân khấu, Stereo Widen) bằng ffmpeg
4. Hòa âm & Phối khí (Mixing & Mastering) với Beat nhạc nền ukulele/acoustic guitar vui nhộn
5. Tự động thêm nhạc dạo đầu (Intro) và nhạc kết thúc êm dịu (Fade-out Outro)
"""

import os
import sys
import re
import argparse
import asyncio
import subprocess
import tempfile
import time
from pathlib import Path

BASE_DIR = os.environ.get("BASE_DIR", str(Path(__file__).parent.parent.resolve()))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
BEATS_DIR = os.path.join(DATA_DIR, "beats")
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", os.path.join(BASE_DIR, "workspace"))

BEATS = {
    "happy": os.path.join(BEATS_DIR, "carefree_full.mp3"),
    "acoustic": os.path.join(BEATS_DIR, "life_of_riley_full.mp3"),
}

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
    c_chars = CHINESE_CHARS.findall(text)
    if len(c_chars) >= 2 or (len(text) < 10 and len(c_chars) >= 1):
        if any(ch in CANTONESE_CHARS for ch in text):
            return "yue"
        return "zh"
    words = [w.lower() for w in re.findall(r'[a-zA-Z]+', text)]
    en_common = {
        'the', 'is', 'am', 'are', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 
        'and', 'or', 'to', 'for', 'in', 'on', 'at', 'with', 'hello', 'hi', 
        'please', 'thanks', 'thank', 'can', 'will', 'good', 'morning', 'afternoon', 
        'yes', 'no', 'of', 'how', 'what', 'when', 'where', 'why', 'who', 'ok',
        'ready', 'support', 'meeting', 'report', 'today', 'tomorrow', 'sure', 'la'
    }
    en_matches = sum(1 for w in words if w in en_common)
    vn_accents = len(VIETNAMESE_ACCENTS.findall(text))
    if en_matches >= 2 and en_matches > vn_accents:
        return "en"
    if vn_accents >= 2:
        return "vi"
    return "vi"

async def tts_vocal(text, output_file, voice="vi-VN-HoaiMyNeural", pitch="+12Hz", rate="+3%"):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
    await communicate.save(output_file)

def get_audio_duration(file_path):
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        out = subprocess.check_output(cmd).decode().strip()
        return float(out)
    except Exception:
        return 30.0

def produce_song(lyrics, output_path, beat_style="happy", voice=None):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    lang = detect_language(lyrics)
    selected_voice = voice or LANGUAGE_VOICE_MAP.get(lang, LANGUAGE_VOICE_MAP["vi"])
    beat_file = BEATS.get(beat_style, BEATS["happy"])

    if not os.path.exists(beat_file):
        print(f"⚠️ Beat file not found: {beat_file}, looking in {BEATS_DIR}")
        for b in os.listdir(BEATS_DIR) if os.path.exists(BEATS_DIR) else []:
            if b.endswith(".mp3"):
                beat_file = os.path.join(BEATS_DIR, b)
                break

    print(f"🎵 [Studio Song Producer] Bắt đầu sản xuất ca khúc:")
    print(f"   - Lời bài hát: '{lyrics[:60]}...'")
    print(f"   - Giọng hát: {selected_voice} ({lang})")
    print(f"   - Beat: {beat_style} ({os.path.basename(beat_file)})")

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_vocal = os.path.join(tmpdir, "raw_vocal.mp3")
        reverb_vocal = os.path.join(tmpdir, "reverb_vocal.mp3")

        # 1. Thu âm vocal
        print("🎙️ Đang thu âm giọng hát vocal...")
        formatted_lyrics = lyrics.replace("\n", " ~ , ")
        asyncio.run(tts_vocal(formatted_lyrics, raw_vocal, voice=selected_voice, pitch="+14Hz", rate="+2%"))

        # 2. Xử lý hiệu ứng phòng thu: Reverb + Echo + Stereo Widen + Compressor
        print("🎛️ Đang xử lý Studio Reverb & Vocal Mastering...")
        filter_complex_vocal = (
            "aecho=0.8:0.88:60:0.3,"
            "stereotools=mlev=0.9:slev=1.2:sbal=0,"
            "acompressor=threshold=-18dB:ratio=3:attack=10:release=120"
        )
        cmd_vocal_fx = [
            "ffmpeg", "-y", "-i", raw_vocal,
            "-af", filter_complex_vocal,
            reverb_vocal
        ]
        subprocess.run(cmd_vocal_fx, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        vocal_dur = get_audio_duration(reverb_vocal)
        song_dur = vocal_dur + 4.5 # 1.5s intro + vocal + 3s outro fade

        # 3. Hòa âm vocal với Beat
        print(f"🎼 Đang hòa âm Vocal với Beat (Tổng thời lượng: {song_dur:.1f}s)...")
        filter_mix = (
            f"[0:a]volume=1.3,adelay=1500|1500[vocal];"
            f"[1:a]atrim=0:{song_dur},afade=t=out:st={song_dur-3}:d=3,volume=0.55[beat];"
            f"[vocal][beat]amix=inputs=2:duration=longest:dropout_transition=2,"
            f"alimiter=limit=0.95"
        )
        cmd_mix = [
            "ffmpeg", "-y",
            "-i", reverb_vocal,
            "-i", beat_file,
            "-filter_complex", filter_mix,
            "-c:a", "libmp3lame", "-b:a", "192k",
            output_path
        ]
        subprocess.run(cmd_mix, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    size_kb = os.path.getsize(output_path) // 1024
    print(f"🌟 [Hoàn tất ca khúc] Đã sản xuất thành công: {output_path} ({size_kb} KB, {song_dur:.1f}s)")
    return True

def main():
    parser = argparse.ArgumentParser(description="Tạo ca khúc studio hoàn chỉnh với Beat và Vocal cho Bé Heo")
    parser.add_argument("--lyrics", "-l", required=True, help="Lời bài hát (nhiều câu thơ vần điệu)")
    parser.add_argument("--output", "-o", default=None, help="File âm thanh hoàn chỉnh (.mp3)")
    parser.add_argument("--beat", "-b", choices=["happy", "acoustic"], default="happy", help="Phong cách điệu beat")
    parser.add_argument("--voice", "-v", default=None, help="Giọng hát chỉ định")
    args = parser.parse_args()

    output = args.output
    if not output:
        output = os.path.join(WORKSPACE_DIR, f"song_heo_{int(time.time())}.mp3")

    success = produce_song(args.lyrics, output, beat_style=args.beat, voice=args.voice)
    if success:
        print(f"[OUTPUT_SONG] {output}")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
