"""
Product Image Frame Automation
================================
Reads SKUs + product links from a CSV, fetches the main product image from
each link, removes the background, generates 8 rotated versions, composites
each onto a frame template, and exports eBay-ready images named by SKU.

SETUP:
    pip install rembg pillow requests

USAGE:
    python generate_product_images.py
"""

import os
import re
import csv
import io
import requests
from PIL import Image
from rembg import remove, new_session

# ============================================================
# CONFIG — edit these for each brand/region workflow
# ============================================================

FRAME_PATH = "frame.png"
INPUT_CSV = "skus.csv"
OUTPUT_DIR = "output"
RAW_CACHE_DIR = "raw_downloads"

EXPORT_SIZE = 1600
FRAME_NATIVE_SIZE = 1254
PRODUCT_FILL_RATIO = 0.80

SAFE_ZONE_TOP = 0.18
SAFE_ZONE_BOTTOM = 0.98

ROTATIONS = [0, 45, 90, 135, 180, 225, 270, 315]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def find_product_image_url(page_url: str) -> str | None:
    resp = requests.get(page_url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    html = resp.text

    match = re.search(
        r'<img[^>]*class=["\'][^"\']*hero-variant[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
        html
    )
    if match:
        return match.group(1)

    match = re.search(
        r'<img[^>]*src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*hero-variant[^"\']*["\']',
        html
    )
    if match:
        return match.group(1)

    match = re.search(r'property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html)
    if not match:
        match = re.search(r'content=["\']([^"\']+)["\']\s+property=["\']og:image["\']', html)
    if match:
        return match.group(1)

    return None


def download_image(url: str, dest_path: str, retries: int = 3) -> str:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            return dest_path
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"    Download attempt {attempt}/{retries} failed: {e}")
    raise last_error


_session = new_session("u2net")

def remove_background(input_path: str) -> Image.Image:
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes, session=_session)
    return Image.open(io.BytesIO(output_bytes)).convert("RGBA")


def trim_transparent(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    if bbox:
        return img.crop(bbox)
    return img


def composite_on_frame(product_img: Image.Image, frame_img: Image.Image, angle: int) -> Image.Image:
    frame = frame_img.convert("RGBA").copy()
    fw, fh = frame.size

    rotated = product_img.rotate(angle, expand=True, resample=Image.BICUBIC)
    rotated = trim_transparent(rotated)

    zone_top = int(fh * SAFE_ZONE_TOP)
    zone_bottom = int(fh * SAFE_ZONE_BOTTOM)
    zone_h = zone_bottom - zone_top
    zone_w = fw

    target_w = zone_w * PRODUCT_FILL_RATIO
    target_h = zone_h * PRODUCT_FILL_RATIO
    scale = min(target_w / rotated.width, target_h / rotated.height)
    new_w = max(1, int(rotated.width * scale))
    new_h = max(1, int(rotated.height * scale))
    rotated = rotated.resize((new_w, new_h), Image.LANCZOS)

    paste_x = (fw - new_w) // 2
    paste_y = zone_top + (zone_h - new_h) // 2

    frame.alpha_composite(rotated, (paste_x, paste_y))
    return frame


def export_final(img: Image.Image, path: str):
    img = img.resize((EXPORT_SIZE, EXPORT_SIZE), Image.LANCZOS)
    img.save(path, "PNG")


def process_sku(sku: str, link: str, frame_img: Image.Image):
    print(f"\n--- Processing SKU {sku} ---")
    os.makedirs(RAW_CACHE_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_CACHE_DIR, f"{sku}.jpg")

    if not os.path.exists(raw_path):
        print(f"  Finding image on: {link}")
        img_url = find_product_image_url(link)
        if not img_url:
            print(f"  ⚠️  Could not find product image for {sku}, skipping.")
            return
        print(f"  Downloading: {img_url}")
        download_image(img_url, raw_path)
    else:
        print(f"  Using cached raw image: {raw_path}")

    print("  Removing background...")
    cutout = remove_background(raw_path)
    cutout = trim_transparent(cutout)

    sku_dir = os.path.join(OUTPUT_DIR, sku)
    os.makedirs(sku_dir, exist_ok=True)

    for i, angle in enumerate(ROTATIONS, start=1):
        composited = composite_on_frame(cutout, frame_img, angle)
        out_path = os.path.join(sku_dir, f"{sku}_{i}.png")
        export_final(composited, out_path)
        print(f"  Saved: {out_path}")


def main():
    frame_img = Image.open(FRAME_PATH).convert("RGBA")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} SKUs from {INPUT_CSV}")

    for row in rows:
        sku = row["sku"].strip()
        link = row["link"].strip()
        if not sku or not link:
            continue
        try:
            process_sku(sku, link, frame_img)
        except Exception as e:
            print(f"  ❌ Error processing {sku}: {e}")

    print("\nAll done. Check the 'output' folder.")


if __name__ == "__main__":
    main()