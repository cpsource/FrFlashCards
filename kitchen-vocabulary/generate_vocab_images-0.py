import os
import csv
import base64
from pathlib import Path
from slugify import slugify
from tenacity import retry, stop_after_attempt, wait_exponential

from openai import OpenAI

# --------- CONFIG ---------
CSV_PATH = "french_kitchen_vocabulary.csv"   # path to your CSV
OUTPUT_DIR = Path("generated_images")         # where images will be saved
IMAGE_SIZE = "1024x1024"                      # 256x256, 512x512, 1024x1024, etc.
MODEL = "gpt-image-1"                         # OpenAI image model
ADD_LABEL_IN_PROMPT = True                    # ask model to include the French word as clean caption
STYLE = "photorealistic"                      # or "flat illustration", "cartoon", etc.
BACKGROUND = "plain white background"         # prompt hint; not an API param
# --------------------------

client = OpenAI()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def build_prompt(french: str, english: str) -> str:
    """Craft a clear, consistent prompt for flashcard-style images."""
    base = (
        f"{STYLE} product-style image of “{french}” ({english}). "
        f"Centered, {BACKGROUND}, evenly lit, high detail, no watermark."
    )
    if ADD_LABEL_IN_PROMPT:
        # Ask the model to place a clean, unobtrusive label
        base += (
            " Add a small, clean sans-serif label with the exact French word "
            "below the object. Keep text sharp and readable."
        )
    return base

@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=12))
def generate_image_b64(prompt: str) -> bytes:
    """
    Call OpenAI Images API and return raw PNG bytes (decoded from base64).
    Retries automatically on transient errors.
    """
    result = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=IMAGE_SIZE,
        # You can add: quality="high" or background="transparent" if desired/available
    )
    b64 = result.data[0].b64_json
    return base64.b64decode(b64)

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set in your environment.")
    if not Path(CSV_PATH).exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"English", "French"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                f"CSV must have columns: {sorted(required)}. Found: {reader.fieldnames}"
            )

        for row in reader:
            english = row["English"].strip()
            french = row["French"].strip()

            # File name like: la-casserole.png
            fname = slugify(french, lowercase=True, max_length=80) + ".png"
            outpath = OUTPUT_DIR / fname
            if outpath.exists():
                print(f"✓ Skipping (exists): {outpath.name}")
                continue

            prompt = build_prompt(french, english)
            print(f"→ Generating: {french}  ({english})")
            try:
                png_bytes = generate_image_b64(prompt)
                outpath.write_bytes(png_bytes)
                print(f"  Saved: {outpath}")
            except Exception as e:
                print(f"  Failed for {french}: {e}")

if __name__ == "__main__":
    main()

