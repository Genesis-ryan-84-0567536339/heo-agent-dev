#!/usr/bin/env python3
"""
transcribe_voice.py: Tự động chuyển đổi tin nhắn thoại Zalo (.aac/.mp3) thành văn bản
Hỗ trợ nhận diện thông minh song song đa ngôn ngữ (Concurrent Multi-Language STT):
- Tiếng Việt (vi-VN)
- Tiếng Trung Quốc Phổ thông (zh-CN)
- Tiếng Quảng Đông (yue-Hant-HK)
- Tiếng Anh (en-US)

Phân tích toàn diện các khả năng ngôn ngữ để hệ thống chủ động hỏi lại
xác nhận nội dung với người nói trước khi phản hồi chính thức.
"""

import sys
import os
import re
import urllib.request
import tempfile
import subprocess
import concurrent.futures
import speech_recognition as sr

LANG_CONFIG = [
    ("zh", "Tiếng Trung Phổ thông", "zh-CN"),
    ("yue", "Tiếng Quảng Đông", "yue-Hant-HK"),
    ("vi", "Tiếng Việt", "vi-VN"),
    ("en", "Tiếng Anh", "en-US"),
]

EN_COMMON = {
    'the', 'is', 'am', 'are', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 
    'and', 'or', 'to', 'for', 'in', 'on', 'at', 'with', 'hello', 'hi', 
    'please', 'thanks', 'thank', 'can', 'will', 'good', 'morning', 'afternoon', 
    'yes', 'no', 'of', 'how', 'what', 'when', 'where', 'why', 'who', 'ok'
}

CANTONESE_MARKERS = set("係喺唔嘅點睇冇咗哋嘢仲諗邊搵返㗎啦哩啱掟傾靚瞓唞乜掂飲齊嘞喎啫喇")

def transcribe_single_lang(audio_data, lang_code):
    r = sr.Recognizer()
    try:
        res = r.recognize_google(audio_data, language=lang_code)
        return res.strip() if isinstance(res, str) else ""
    except Exception:
        return ""

def is_valid_chinese(text):
    if not text:
        return False
    hanzi_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    return hanzi_count >= 2

def is_valid_cantonese(text):
    if not is_valid_chinese(text):
        return False
    return any(ch in CANTONESE_MARKERS for ch in text)

def is_valid_english(text):
    if not text:
        return False
    words = [w.lower() for w in re.findall(r'[a-zA-Z]+', text)]
    if not words:
        return False
    matches = sum(1 for w in words if w in EN_COMMON)
    if matches >= 2 or (len(words) >= 3 and matches >= 1):
        return True
    viet_accents = len(re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text, re.I))
    return matches > viet_accents and len(words) >= 2

def transcribe_audio_multi(audio_path):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)
    except Exception as e:
        sys.stderr.write(f"Error reading audio file {audio_path}: {e}\n")
        return None

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_lang = {
            executor.submit(transcribe_single_lang, audio_data, code): (key, name)
            for key, name, code in LANG_CONFIG
        }
        for future in concurrent.futures.as_completed(future_to_lang):
            key, name = future_to_lang[future]
            try:
                text = future.result()
                if text:
                    results[key] = (name, text)
            except Exception:
                pass

    if not results:
        return None

    # Lọc các ứng viên hợp lệ
    candidates = []
    
    # 1. Tiếng Trung
    zh_cand = results.get("zh")
    if zh_cand and is_valid_chinese(zh_cand[1]):
        candidates.append(("zh", zh_cand[0], zh_cand[1]))

    # 2. Tiếng Quảng Đông
    yue_cand = results.get("yue")
    if yue_cand and is_valid_cantonese(yue_cand[1]):
        candidates.append(("yue", yue_cand[0], yue_cand[1]))
    elif yue_cand and is_valid_chinese(yue_cand[1]) and not zh_cand:
        candidates.append(("yue", yue_cand[0], yue_cand[1]))

    # 3. Tiếng Anh
    en_cand = results.get("en")
    if en_cand and is_valid_english(en_cand[1]):
        candidates.append(("en", en_cand[0], en_cand[1]))

    # 4. Tiếng Việt
    vi_cand = results.get("vi")
    if vi_cand and vi_cand[1]:
        # Nếu tiếng Anh hay Trung quá áp đảo thì cân nhắc
        candidates.append(("vi", vi_cand[0], vi_cand[1]))

    # Đưa ra ứng viên tốt nhất kèm tag nhận diện
    best_cand = None
    if any(c[0] in ("zh", "yue") for c in candidates):
        best_cand = next(c for c in candidates if c[0] in ("zh", "yue"))
    elif any(c[0] == "en" for c in candidates):
        best_cand = next(c for c in candidates if c[0] == "en")
    elif any(c[0] == "vi" for c in candidates):
        best_cand = next(c for c in candidates if c[0] == "vi")
    else:
        first_key = list(results.keys())[0]
        best_cand = (first_key, results[first_key][0], results[first_key][1])

    # Trả về chuỗi đặc biệt kèm metadata ngôn ngữ và các phương án dự phòng
    main_text = best_cand[2]
    main_lang = best_cand[0]
    main_lang_name = best_cand[1]

    alt_desc = []
    for c_key, c_name, c_txt in candidates:
        if c_key != main_lang:
            alt_desc.append(f"{c_name}: '{c_txt}'")

    alt_str = f" | Dự phòng: {'; '.join(alt_desc)}" if alt_desc else ""
    return f"[VOICE_TRANSCRIPTION | Lang: {main_lang} ({main_lang_name}) | Nội dung: '{main_text}'{alt_str}]"

def main():
    if len(sys.argv) < 2:
        print("Usage: transcribe_voice.py <audio_url_or_path>")
        sys.exit(1)

    input_src = sys.argv[1].strip()
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_audio = os.path.join(tmpdir, "input.aac")
        wav_audio = os.path.join(tmpdir, "converted.wav")

        if input_src.startswith("http://") or input_src.startswith("https://"):
            req = urllib.request.Request(
                input_src,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req) as response, open(raw_audio, 'wb') as out_file:
                out_file.write(response.read())
        else:
            raw_audio = input_src

        # Convert sang 16kHz mono WAV cho SpeechRecognition
        cmd = [
            "ffmpeg", "-y", "-i", raw_audio,
            "-ar", "16000", "-ac", "1", "-f", "wav",
            wav_audio
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            sys.stderr.write(f"FFmpeg error: {e}\n")
            sys.exit(1)

        result = transcribe_audio_multi(wav_audio)
        if result:
            print(result)
        else:
            print("[Không nhận diện được giọng nói]")

if __name__ == "__main__":
    main()
