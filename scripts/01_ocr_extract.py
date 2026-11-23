"""Step 1: Extract native page images from both PDFs, detect divider bars, and run Windows OCR."""

import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

WORKSPACE = Path(r"c:\Users\culfa\Desktop\ing")
SCRATCH_IMGS = Path(
    r"C:\Users\culfa\.gemini\antigravity\brain\ca747629-86e1-4787-89e8-56500f6a93ca\scratch\ocr_imgs"
)
RAW_OCR_JSON = Path(
    r"C:\Users\culfa\.gemini\antigravity\brain\ca747629-86e1-4787-89e8-56500f6a93ca\scratch\win_ocr_raw.json"
)
OUT_JSON = WORKSPACE / "data" / "ocr_pages.json"
PS_SCRIPT = WORKSPACE / "scripts" / "win_ocr_batch.ps1"

PDF_BOOK1 = WORKSPACE / "Reader at Work 1 - Flipbook by Nadro Iderk _ FlipHTML5.pdf"
PDF_BOOK2 = WORKSPACE / "reader at work 2 (Page 305) - Flipbook by Dilara Öz _ FlipHTML5.pdf"


def detect_divider_bars(img_bytes: bytes) -> list[int]:
    """Return center y-coordinates of thick full-width horizontal passage divider bars."""
    img = Image.open(io.BytesIO(img_bytes)).convert("L")
    arr = np.array(img)
    dark = arr < 140
    row_frac = dark.mean(axis=1)
    # Thick header divider bars span >= 68% of page width and >= 4 pixels high.
    mask = row_frac >= 0.68
    bars: list[int] = []
    in_run = False
    start_y = 0
    for y, val in enumerate(mask):
        if val and not in_run:
            in_run = True
            start_y = y
        elif not val and in_run:
            in_run = False
            if (y - start_y) >= 4:
                bars.append(int((start_y + y - 1) // 2))
    if in_run and (len(mask) - start_y) >= 4:
        bars.append(int((start_y + len(mask) - 1) // 2))
    return bars


def extract_book_pages(
    pdf_path: Path, book_num: int, start_page_1based: int, end_page_1based: int
) -> dict[str, dict]:
    """Extract native images to scratch and detect divider bars for each page."""
    doc = fitz.open(pdf_path)
    meta_by_file: dict[str, dict] = {}
    for p1 in range(start_page_1based, end_page_1based + 1):
        pg = doc[p1 - 1]
        imgs = pg.get_images(full=True)
        if len(imgs) == 1:
            xref = imgs[0][0]
            base = doc.extract_image(xref)
            ext = base["ext"]
            img_bytes = base["image"]
        else:
            pix = pg.get_pixmap(dpi=180)
            ext = "png"
            img_bytes = pix.tobytes("png")

        fname = f"b{book_num}_p{p1:03d}.{ext}"
        out_path = SCRATCH_IMGS / fname
        if not out_path.exists() or out_path.stat().st_size == 0:
            out_path.write_bytes(img_bytes)

        y_bars = detect_divider_bars(img_bytes)
        meta_by_file[fname] = {
            "book": book_num,
            "pdf_page": p1,
            "y_bars": y_bars,
        }
    doc.close()
    return meta_by_file


def main() -> None:
    t0 = time.time()
    SCRATCH_IMGS.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    print("Extracting native images from Reader at Work 1 (PDF p.18-167)...")
    meta1 = extract_book_pages(PDF_BOOK1, 1, 18, 167)
    print(f"  Book 1 pages extracted: {len(meta1)}")

    print("Extracting native images from Reader at Work 2 (PDF p.1-328)...")
    meta2 = extract_book_pages(PDF_BOOK2, 2, 1, 328)
    print(f"  Book 2 pages extracted: {len(meta2)}")

    all_meta = {**meta1, **meta2}
    print(f"Total images ready: {len(all_meta)} ({time.time() - t0:.1f}s)")

    print("Running Windows OCR batch script...")
    t_ocr = time.time()
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(PS_SCRIPT),
        "-ImageDir",
        str(SCRATCH_IMGS),
        "-OutJson",
        str(RAW_OCR_JSON),
    ]
    proc = subprocess.run(cmd, check=True, text=True)
    print(f"Windows OCR completed in {time.time() - t_ocr:.1f}s (exit {proc.returncode})")

    raw_pages = json.loads(RAW_OCR_JSON.read_text(encoding="utf-8"))
    merged = []
    for item in raw_pages:
        fname = item["file"]
        m = all_meta.get(fname)
        if not m:
            continue
        merged.append(
            {
                "file": fname,
                "book": m["book"],
                "pdf_page": m["pdf_page"],
                "img_w": item["img_w"],
                "img_h": item["img_h"],
                "y_bars": m["y_bars"],
                "lines": item["lines"],
            }
        )

    merged.sort(key=lambda r: (r["book"], r["pdf_page"]))
    OUT_JSON.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    b1_count = sum(1 for p in merged if p["book"] == 1)
    b2_count = sum(1 for p in merged if p["book"] == 2)
    print(f"Saved {len(merged)} pages (Book 1: {b1_count}, Book 2: {b2_count}) to {OUT_JSON}")
    print(f"Total elapsed: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
