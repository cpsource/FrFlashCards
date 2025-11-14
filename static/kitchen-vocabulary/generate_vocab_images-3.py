import os
import csv
import sys
import base64
from pathlib import Path
from slugify import slugify
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from openai import OpenAI

# --------- CONFIG ---------
CSV_PATH = "french_kitchen_vocabulary.csv"
OUTPUT_DIR = Path("generated_images")
IMAGE_SIZE = "1024x1024"
MODEL = "gpt-image-1"
STYLE = "photorealistic"
BACKGROUND = "plain white background"

# NEW FLAG → whether to display the French word in the picture
SHOW_LABEL_ON_IMAGE = True  # Set to False for unlabeled images
# --------------------------

# Load environment variables from ~/.env or local .env
home_env = Path.home() / ".env"
if home_env.exists():
    load_dotenv(home_env)
else:
    load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "❌ OPENAI_API_KEY not found. Please set it in ~/.env or your environment."
    )

client = OpenAI(api_key=api_key)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_prompt(french: str, english: str) -> str:
    """Craft a clear prompt for a flashcard-style image."""
    base = (
        f"{STYLE} product-style image of “{french}” ({english}). "
        f"Centered, {BACKGROUND}, evenly lit, high detail, no watermark."
    )

    if SHOW_LABEL_ON_IMAGE:
        base += (
            " Add a small, clean sans-serif label with the exact French word "
            "below the object. Keep text sharp and readable."
        )
    else:
        base += " No text or labels in the image."

    return base


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=12))
def generate_image_b64(prompt: str) -> bytes:
    """Call OpenAI Images API and return raw PNG bytes."""
    result = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=IMAGE_SIZE,
    )
    b64 = result.data[0].b64_json
    return base64.b64decode(b64)


def main():
    if not Path(CSV_PATH).exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    # Optional: limit generation to a single word via command-line arg
    single_target = sys.argv[1].strip().lower() if len(sys.argv) > 1 else None

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

            if single_target and single_target != french.lower():
                continue

            fname = slugify(french, lowercase=True, max_length=80) + ".png"
            outpath = OUTPUT_DIR / fname
            if outpath.exists():
                print(f"✓ Skipping (exists): {outpath.name}")
                if single_target:
                    break
                continue

            prompt = build_prompt(french, english)
            print(f"→ Generating: {french}  ({english}) | label={SHOW_LABEL_ON_IMAGE}")
            try:
                png_bytes = generate_image_b64(prompt)
                outpath.write_bytes(png_bytes)
                print(f"  Saved: {outpath}")
            except Exception as e:
                print(f"  Failed for {french}: {e}")

            if single_target:
                break


if __name__ == "__main__":
    main()

