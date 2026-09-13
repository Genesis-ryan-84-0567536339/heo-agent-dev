#!/usr/bin/env python3
"""
generate_image.py: Tạo ảnh minh họa chất lượng cao theo prompt bằng AI
Sử dụng Pollinations AI (Flux / SDXL) miễn phí, tốc độ cao (2-4s), không cần API key.
Có cơ chế fallback sang PIL/Pillow tạo ảnh đồ họa chuyên nghiệp nếu không có mạng.
"""

import os
import sys
import argparse
import urllib.parse
import urllib.request
import time
import random
from pathlib import Path

BASE_DIR = os.environ.get("BASE_DIR", str(Path(__file__).parent.parent.resolve()))
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", str(Path(BASE_DIR) / "workspace"))

def generate_image_ai(prompt, output_path, width=1024, height=768):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    seed = random.randint(1000, 999999)
    encoded_prompt = urllib.parse.quote(prompt.strip())
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"
    
    print(f"🎨 [AI Image Generator] Đang tạo ảnh từ prompt: '{prompt}'...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                data = response.read()
                with open(output_path, "wb") as f:
                    f.write(data)
                print(f"✅ Đã tạo ảnh thành công: {output_path} ({len(data) // 1024} KB)")
                return True
    except Exception as e:
        print(f"⚠️ Pollinations AI gặp sự cố ({str(e)}), chuyển sang vẽ đồ họa bằng Pillow...")
        return generate_fallback_image(prompt, output_path, width, height)

def generate_fallback_image(prompt, output_path, width=800, height=600):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), color=(27, 54, 93)) # Corporate Navy
        draw = ImageDraw.Draw(img)
        
        # Draw border & accent
        draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(212, 175, 55), width=4)
        
        text = f"MINH HỌA:\n{prompt}"
        draw.text((50, height // 2 - 50), text, fill=(255, 255, 255))
        img.save(output_path)
        print(f"✅ Đã tạo ảnh fallback bằng Pillow: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Lỗi tạo fallback image: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Tạo ảnh AI minh họa tự động cho Zalo Copilot")
    parser.add_argument("--prompt", "-p", required=True, help="Mô tả hình ảnh bằng tiếng Anh hoặc tiếng Việt")
    parser.add_argument("--output", "-o", default=None, help="Đường dẫn file ảnh đầu ra (.jpg hoặc .png)")
    parser.add_argument("--width", "-W", type=int, default=1024, help="Chiều rộng ảnh (pixel)")
    parser.add_argument("--height", "-H", type=int, default=768, help="Chiều cao ảnh (pixel)")
    args = parser.parse_args()

    output = args.output
    if not output:
        clean_name = "".join(c if c.isalnum() else "_" for c in args.prompt[:25]).strip("_")
        output = os.path.join(WORKSPACE_DIR, f"img_{clean_name}_{int(time.time())}.jpg")

    success = generate_image_ai(args.prompt, output, args.width, args.height)
    if success:
        print(f"[OUTPUT_IMAGE] {output}")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
