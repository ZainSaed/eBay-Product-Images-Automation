# eBay Product Images Automation

Automates product image creation for eBay listings. For each SKU + product
link in a CSV, this script fetches the main product photo from the brand's
website, removes the background, generates 8 rotated versions, composites
each onto a frame template, and exports eBay-ready PNGs named by SKU.

## Background

This started as a manual, repetitive task: copy a product image from a
brand's website, paste it into a branded frame, remove the background,
resize/position it by hand, download it, then repeat that 8 times per
product (one per rotation angle) — across hundreds of SKUs. This script
replaces that entire manual workflow with a single automated pipeline.

## What it does

For each row in `skus.csv`:
1. Fetches the product page and finds the main product image
2. Downloads it (cached locally so re-runs don't re-download)
3. Removes the background using `rembg` (free, runs locally, no paid API)
4. Creates 8 rotated versions of the product (0°, 45°, 90°...315°)
5. Places each onto `frame.png`, centered below the header/branding bar
6. Exports each as a 1600×1600 PNG named `SKU_1.png` ... `SKU_8.png`
7. Saves them in `output/<SKU>/`

## Setup (one-time)

1. Install Python 3.10+ from [python.org](https://python.org) if you don't have it.
2. Open a terminal in this folder and run:
   ```
   pip install rembg pillow requests
   ```
3. The first run will auto-download rembg's background-removal model (~180MB) — this happens once.

## Files you provide (not included in this repo)

- **`frame.png`** — the frame/template for the brand and region you're running. Swap this per workflow.
- **`skus.csv`** — two columns, `sku` and `link`, one row per product. Export from Google Sheets as CSV.

Example `skus.csv`:
```
sku,link
SKU12345,https://example-brand.com/product/SKU12345
SKU67890,https://example-brand.com/product/SKU67890
```

> If your Google Sheet has SKUs as hyperlinked text (link hidden behind the SKU), a plain CSV export will drop the URLs. Use a small Apps Script to extract the real links into their own column first, then export.

## Usage

```
python generate_product_images.py
```

Finished images appear in `output/<SKU>/SKU_1.png` through `SKU_8.png`.

## Tuning the look

Edit the CONFIG section at the top of `generate_product_images.py`:

| Setting | What it controls |
|---|---|
| `EXPORT_SIZE` | Final image size in pixels (square). Currently `1600`. |
| `PRODUCT_FILL_RATIO` | How much of the frame the product fills (`0.80` = 80%). |
| `SAFE_ZONE_TOP` / `SAFE_ZONE_BOTTOM` | Vertical area the product is centered within, as a fraction of frame height — keeps it clear of the header/branding bar. |
| `ROTATIONS` | The 8 angles used for the rotated versions. |

## Adding a new brand/region

Each brand/site is its own workflow since the site structure and frame differ:

1. Duplicate this project folder.
2. Swap in that brand's `frame.png`.
3. Swap in that region's `skus.csv`.
4. Check `find_product_image_url()` — it currently looks for an `<img class="hero-variant" ...>` tag first, then falls back to the `og:image` meta tag. If the new site's HTML doesn't match either pattern, add a new extraction strategy for it.

## Notes

- Raw downloaded source images are cached in `raw_downloads/` so re-running the script skips re-downloading images you already have. Delete this folder to force a fresh fetch.
- `frame.png`, `skus.csv`, `output/`, and `raw_downloads/` are all git-ignored — they contain business/product data and shouldn't be pushed to version control.
- Output is PNG (not JPG) to avoid compression artifacts.
