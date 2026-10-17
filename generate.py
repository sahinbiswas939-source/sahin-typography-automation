

import os
import json
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
FPS = 30
SLIDE_SECONDS = 3
OUT = Path("output")
OUT.mkdir(exist_ok=True)

DATE = datetime.now().strftime("%Y-%m-%d")
VIDEO = OUT / f"typography_{DATE}.mp4"

FONTS = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def get_font(size):
    for path in FONTS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_daily_text():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Configure it in GitHub Secrets."
        )

    prompt = """
Create 5 short, powerful Hindi-English motivational typography lines
for a YouTube Short. The theme is discipline, self-respect and success.
Use original wording. Keep each line short enough for a phone screen.
Return ONLY a valid JSON array containing exactly 5 strings.
No markdown, no numbering, no hashtags.
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.9,
            "responseMimeType": "application/json"
        }
    }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash:generateContent"
        "?key=" + api_key
    )

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    raw = result["candidates"][0]["content"]["parts"][0]["text"]
    lines = json.loads(raw)

    if not isinstance(lines, list) or len(lines) != 5:
        raise ValueError("Gemini must return exactly 5 text lines.")

    return [str(line).strip() for line in lines]

def wrap_text(draw, text, font, max_width):
    words = text.split()
    rows = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                rows.append(current)
            current = word

    if current:
        rows.append(current)

    return rows

def create_slide(text, index):
    img = Image.new("RGB", (W, H))
    pixels = img.load()

    # Dark red-to-black gradient
    for y in range(H):
        for x in range(W):
            glow = max(0, 1 - abs(x - W // 2) / (W * 0.8))
            fade = y / H
            r = int(30 * (1 - fade) + 65 * glow)
            g = int(5 * (1 - fade))
            b = int(12 * (1 - fade))
            pixels[x, y] = (r, g, b)

    draw = ImageDraw.Draw(img)

    gold = (255, 202, 95)
    white = (255, 255, 255)

    # Decorative frame
    draw.rounded_rectangle(
        (30, 35, W - 30, H - 35),
        radius=24,
        outline=gold,
        width=3
    )

    draw.text(
        (W // 2, 105),
        "DAILY MOTIVATION",
        font=get_font(28),
        fill=gold,
        anchor="mm"
    )

    draw.line((150, 155, W - 150, 155), fill=gold, width=2)

    font_size = 58
    while font_size >= 30:
        font = get_font(font_size)
        rows = wrap_text(draw, text.upper(), font, W - 120)
        if len(rows) <= 5:
            break
        font_size -= 4

    line_height = font_size + 22
    start_y = (H - len(rows) * line_height) // 2

    for i, row in enumerate(rows):
        draw.text(
            (W // 2, start_y + i * line_height),
            row,
            font=font,
            fill=gold if i % 2 == 0 else white,
            anchor="mm",
            stroke_width=1,
            stroke_fill=(30, 10, 10)
        )

    draw.text(
        (W // 2, H - 115),
        "SAHIN TYPOGRAPHY",
        font=get_font(26),
        fill=gold,
        anchor="mm"
    )

    draw.text(
        (W // 2, H - 75),
        f"DAY {index + 1}  |  NEVER GIVE UP",
        font=get_font(18),
        fill=white,
        anchor="mm"
    )

    path = OUT / f"slide_{index:02d}.png"
    img.save(path)
    return path

def main():
    lines = get_daily_text()
    slides = [create_slide(line, i) for i, line in enumerate(lines)]

    concat_file = OUT / "slides.txt"
    with concat_file.open("w", encoding="utf-8") as f:
        for slide in slides:
            f.write(f"file '{slide.resolve()}'\n")
            f.write(f"duration {SLIDE_SECONDS}\n")
        # Repeat final image so its duration is respected
        f.write(f"file '{slides[-1].resolve()}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-vf", f"fps={FPS},format=yuv420p",
        "-t", str(len(slides) * SLIDE_SECONDS),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        str(VIDEO)
    ], check=True)

    print(f"Video created: {VIDEO}")

if __name__ == "__main__":
    main()
