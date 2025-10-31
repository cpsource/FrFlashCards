import os
import csv
import sys
import base64
from pathlib import Path
from slugify import slugify
from dotenv import load_dotenv
from openai import OpenAI
from openai import BadRequestError, APIError, APIConnectionError, RateLimitError

# --------- CONFIG ---------
CSV_PATH = "french_kitchen_vocabulary.csv"
OUTPUT_DIR = Path("generated_images")

IMAGE_SIZE = "1024x1024"
MODEL = "gpt-image-1"
STYLE = "photorealistic"
BACKGROUND = "plain white background"

# Show the French word in the image?
SHOW_LABEL_ON_IMAGE = True  # default True
# --------------------------

# Load env from ~/.env then local .env
home_env = Path.home() / ".env"
if home_env.exists():
    load_dotenv(home_env)
else:
    load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found in ~/.env or environment.")

client = OpenAI(api_key=api_key)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_prompt(french: str, english: str, with_label: bool) -> str:
    # Keep this version Unicode-friendly (primary)
    base = (
        f"{STYLE} product-style image of “{french}” ({english}). "
        f"Centered, {BACKGROUND}, evenly lit, high detail, no watermark."
    )
    if with_label:
        base += (
            " Add a small, clean sans-serif label with the exact French word "
            "below the object. Keep text sharp and readable."
        )
    else:
        base += " No text or labels in the image."
    return base


def build_ascii_fallback_prompt(french: str, english: str) -> str:
    # ASCII-only variant (no accents or fancy quotes), no label request
    # This helps diagnose if Unicode or label-text is causing the block.
    return (
        f"{STYLE} product-style image of '{english}' representing the French noun '{french}'. "
        "Centered, plain white background, evenly lit, high detail, no watermark. "
        "No text or labels in the image."
    )


def explain_openai_error(e: Exception, context: str = ""):
    print("\n====== OPENAI ERROR ======")
    if context:
        print(f"Context: {context}")
    print(f"Type: {type(e).__name__}")
    # Try to show as much as possible without assuming fields exist
    msg = getattr(e, "message", None) or str(e)
    print(f"Message: {msg}")
    # SDK v1 errors often carry .status_code/.code/.response
    code = getattr(e, "code", None)
    if code:
        print(f"Code: {code}")
    status = getattr(e, "status_code", None)
    if status:
        print(f"HTTP Status: {status}")
    resp = getattr(e, "response", None)
    if resp is not None:
        # response may have .text or .json
        try:
            print("Response JSON:", resp.json())
        except Exception:
            try:
                print("Response Text:", resp.text)
            except Exception:
                pass
    print("====== END ERROR ======\n")


def generate_once(model: str, prompt: str, size: str) -> bytes:
    result = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
    )
    b64 = result.data[0].b64_json
    return base64.b64decode(b64)


def generate_image_b64(french: str, english: str) -> bytes:
    # 1) Primary attempt (your config)
    primary_prompt = build_prompt(french, english, with_label=SHOW_LABEL_ON_IMAGE)
    try:
        return generate_once(MODEL, primary_prompt, IMAGE_SIZE)
    except BadRequestError as e:
        explain_openai_error(e, "Primary attempt")
        # 2) Fallback: ASCII-only, no label, smaller size
        fb_prompt = build_ascii_fallback_prompt(french, english)
        try:
            print("↪︎ Fallback: ASCII-only prompt, size=512x512, no label.")
            return generate_once(MODEL, fb_prompt, "512x512")
        except Exception as e2:
            explain_openai_error(e2, "Fallback attempt")
            raise
    except (APIError, APIConnectionError, RateLimitError) as e:
        explain_openai_error(e, "Transport/Limit issue")
        raise


def sanity_test():
    """Generate a tiny test image to verify model access & parameters."""
    test_prompt = "Photorealistic red apple on a plain white background, centered, no text."
    try:
        png = generate_once(MODEL, test_prompt, "256x256")
        (OUTPUT_DIR / "test_apple.png").write_bytes(png)
        print("✓ Sanity test succeeded: generated_images/test_apple.png")
    except Exception as e:
        explain_openai_error(e, "Sanity test")
        print("Sanity test failed. Common causes:")
        print(" - Model access: your org/account may not have image generation enabled.")
        print(" - Old SDK: upgrade with `pip install --upgrade openai`.")
        print(" - Org/project mismatch: ensure the correct API key/org is active in ~/.env.")


def main():
    # Optional flags:
    #   --test           : run the sanity test and exit
    #   "la cuillère"    : single-target French noun
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sanity_test()
        sys.exit(0)

    single_target = None
    if len(sys.argv) > 1:
        single_target = sys.argv[1].strip().lower()

    if not Path(CSV_PATH).exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"English", "French"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV must have columns: {sorted(required)}. Found: {reader.fieldnames}")

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

            print(f"→ Generating: {french}  ({english}) | label={SHOW_LABEL_ON_IMAGE}")
            try:
                png_bytes = generate_image_b64(french, english)
                outpath.write_bytes(png_bytes)
                print(f"  Saved: {outpath}")
            except Exception:
                print("  Failed for", french, "— see error details above.")
                if single_target:
                    sys.exit(1)

            if single_target:
                break


if __name__ == "__main__":
    main()

