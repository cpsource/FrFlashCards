import os
import csv
import sys
import base64
from pathlib import Path
from slugify import slugify
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from openai import OpenAI
from openai import BadRequestError, APIError, APIConnectionError, RateLimitError

# --------- CONFIG ---------
CSV_PATH = "french_kitchen_vocabulary.csv"
OUTPUT_DIR = Path("generated_images")

# Primary attempt
IMAGE_SIZE = "256x256"
MODEL = "gpt-image-1"
STYLE = "photorealistic"
BACKGROUND = "plain white background"

# Whether to display the French word in the image
SHOW_LABEL_ON_IMAGE = False  # default True

# Diagnostics
DEBUG_VERBOSE = True
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


def ensure_model_available(preferred: str) -> str:
    """Return a usable image model id or raise with guidance."""
    try:
        models = client.models.list()
        ids = {m.id for m in models.data}
        if preferred in ids:
            return preferred
        # Soft fallback: try known default
        if "gpt-image-1" in ids:
            if DEBUG_VERBOSE:
                print(f"⚠️  Model '{preferred}' not available; falling back to 'gpt-image-1'.")
            return "gpt-image-1"
        # Last resort: show what’s available
        available = sorted([m for m in ids if "image" in m or "vision" in m or "gpt" in m])
        raise RuntimeError(
            "❌ No accessible image model found for your account.\n"
            f"Tried '{preferred}'. Available models (subset): {available[:10]}"
        )
    except Exception as e:
        # If listing fails (some orgs restrict this), keep the preferred and hope it works
        if DEBUG_VERBOSE:
            print(f"ℹ️ Could not list models ({e}); proceeding with '{preferred}'.")
        return preferred


def build_prompt(french: str, english: str, with_label: bool) -> str:
    """Craft a clear prompt for a flashcard-style image."""
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


def explain_openai_error(e: Exception, context: str = ""):
    """Pretty-print error details to help diagnose BadRequestError causes."""
    header = f"❌ OpenAI error during {context}:" if context else "❌ OpenAI error:"
    print(header)
    if isinstance(e, BadRequestError):
        # BadRequestError typically includes a response body with details
        try:
            print(f"  type: BadRequestError")
            print(f"  message: {getattr(e, 'message', str(e))}")
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    body = e.response.json()
                    print(f"  details: {body}")
                except Exception:
                    pass
        except Exception:
            print(f"  {e}")
    elif isinstance(e, RateLimitError):
        print("  type: RateLimitError — you may be out of quota or hitting rate limits.")
    elif isinstance(e, APIConnectionError):
        print("  type: APIConnectionError — network/DNS issue.")
    elif isinstance(e, APIError):
        print(f"  type: APIError — server-side issue: {e}")
    else:
        print(f"  {type(e).__name__}: {e}")


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
def _generate_once(model: str, prompt: str, size: str) -> bytes:
    result = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
    )
    b64 = result.data[0].b64_json
    return base64.b64decode(b64)


def generate_image_b64(french: str, english: str) -> bytes:
    """
    Try a primary prompt; on BadRequestError, fall back to a simpler prompt (no label, smaller size).
    """
    model = ensure_model_available(MODEL)

    # Primary attempt (user-configured)
    prompt_primary = build_prompt(french, english, with_label=SHOW_LABEL_ON_IMAGE)
    try:
        return _generate_once(model, prompt_primary, IMAGE_SIZE)
    except BadRequestError as e:
        if DEBUG_VERBOSE:
            explain_openai_error(e, "primary image generation")
            print("↪︎ Fallback: removing label instruction and reducing size to 512x512.")
        # Fallback: simpler prompt, no label, smaller size
        prompt_fallback = build_prompt(french, english, with_label=False)
        try:
            return _generate_once(model, prompt_fallback, "512x512")
        except Exception as e2:
            # Show full details and re-raise
            if DEBUG_VERBOSE:
                explain_openai_error(e2, "fallback image generation")
            raise


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

            print(f"→ Generating: {french}  ({english}) | label={SHOW_LABEL_ON_IMAGE}")
            try:
                png_bytes = generate_image_b64(french, english)
                outpath.write_bytes(png_bytes)
                print(f"  Saved: {outpath}")
            except Exception as e:
                print(f"  Failed for {french}: see details above.")
                # Already printed diagnostics in generate_image_b64()
                if single_target:
                    # If user requested a single item, exit immediately
                    sys.exit(1)

            if single_target:
                break


if __name__ == "__main__":
    main()

