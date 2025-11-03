#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
HINTS_DIR = BASE_DIR / "hints"
HINTS_JSON = HINTS_DIR / "hints.json"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def build_hints():
    if not HINTS_JSON.exists():
        print(f"⚠️  {HINTS_JSON} not found, skipping hints.")
        return

    try:
        raw = HINTS_JSON.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {HINTS_JSON}: {e}")
        print("Here is the file content for debugging:\n")
        print(raw)
        raise

    print(f"Building {len(data)} hint page(s) from {HINTS_JSON}.")

    ctx_base = {"current_year": datetime.now().year}

    for hint in data:
        fname = hint["file"]          # e.g. "L-heure-du-conte-hint.html"
        tpl_name = f"hints/{fname}"   # templates/hints/L-heure-du-conte-hint.html
        tpl_path = TEMPLATES_DIR / tpl_name
        out_path = HINTS_DIR / fname  # hints/L-heure-du-conte-hint.html

        if not tpl_path.exists():
            print(f"  ⚠️  Template not found for {fname} ({tpl_path}), skipping.")
            continue

        print(f"  Rendering {tpl_name} -> {out_path}")

        try:
            template = env.get_template(tpl_name)
        except TemplateNotFound:
            print(f"  ⚠️  Jinja could not find template {tpl_name}, skipping.")
            continue

        html = template.render(**ctx_base, hint=hint)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"    ✓ wrote {out_path}")


def main():
    print(f"Templates dir: {TEMPLATES_DIR}")
    print(f"Hints dir:     {HINTS_DIR}")
    build_hints()
    print("Done.")


if __name__ == "__main__":
    main()

