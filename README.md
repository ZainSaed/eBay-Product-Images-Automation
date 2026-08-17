# Product Image Automation

## What this does
For each SKU + product link in `skus.csv`, this script:
1. Fetches the product page and finds the main product image
2. Downloads it
3. Removes the background (using `rembg`, free & runs locally)
4. Creates 8 rotated versions (0°, 45°, 90°...315°) of the product
5. Places each onto `frame.png`, centered below the header bar
6. Exports each as a 1600×1600 JPEG named `SKU_1.jpg` ... `SKU_8.jpg`
7. Saves them in `output/<SKU>/`

## Setup (one-time)
1. Install Python 3.10+ from python.org if you don't have it
2. Open a terminal/command prompt in this folder
3. Run:
   ```
   pip install rembg pillow requests
   ```
   (First run of the script will also auto-download rembg's AI model, ~180MB — this happens once)

## Usage
1. Export your Google Sheet as CSV (File > Download > CSV), replacing `skus.csv`.
   Make sure the columns are named exactly `sku` and `link`.
2. Replace `frame.png` with the correct frame for the brand/region you're running.
3. Run:
   ```
   python generate_product_images.py
   ```
4. Finished images appear in `output/<SKU>/SKU_1.jpg` through `SKU_8.jpg`

## Tuning the look
Open `generate_product_images.py` and adjust these values near the top if the
product looks too big/small or too high/low in the frame:

- `PRODUCT_FILL_RATIO` — how much of the frame the product fills (0.6 = 60%)
- `SAFE_ZONE_TOP` / `SAFE_ZONE_BOTTOM` — vertical area the product is centered
  within, as a fraction of frame height (avoids the header bar)
- `ROTATIONS` — the 8 angles used; change if you want different angles

## Notes
- Raw downloaded images are cached in `raw_downloads/` so re-running the
  script won't re-download images you already have.
- For a different brand , duplicate this folder, swap in that
  brand's `frame.png`, and update the image-finding logic in
  `find_product_image_url()` if that site doesn't use an `og:image` meta tag
  the same way Breville does.
