"""Step 2: Spatially clean OCR output and segment all passages from Reader at Work 1 & 2."""

import json
import re
import statistics
from pathlib import Path

WORKSPACE = Path(r"c:\Users\culfa\Desktop\ing")
OCR_JSON = WORKSPACE / "data" / "ocr_pages.json"
OUT_RAW = WORKSPACE / "data" / "raw_passages.json"
OUT_REPORT = WORKSPACE / "data" / "segmentation_report.json"

TR_MAP = str.maketrans("üÜşŞğĞıİöÖçÇ", "uUsSgGiIoOcC")

BOOK1_TOC_TITLES = {
    1: "MARY",
    2: "HANAKO",
    3: "LONGLEAT HOUSE",
    4: "NEW YORK UNIVERSITY",
    5: "UNIVERSITY OF LONDON",
    6: "JIM",
    7: "KATE",
    8: "THE OLD ENGLAND RESTAURANT & THE STATUE OF LIBERTY",
    9: "TOMIKO",
    10: "TOMIKO, KING AND TED",
    11: "THE GARSTON FAMILY",
    12: "CINEMAS",
    13: "PLAZA SHOPPING CENTRE",
    14: "THE INTERNATIONAL HOTEL",
    15: "JOB ADVERTISEMENTS",
    16: "YOUNG LOVE",
    17: "VARIOUS ADVERTISEMENTS",
    18: "SAN FRANCISCO",
    19: "LETTER FROM HALIMA AND AHMED",
    20: "DEREK",
    21: "ROLAND-EVI-DELLA",
    22: "LETTER FROM PAM",
    23: "JOAN",
    24: "MAHATMA GANDHI",
    25: "WILLIAM SHAKESPEARE",
    26: "ALFRED HITCHCOCK",
    27: "CHARLIE CHAPLIN",
    28: "SUPER TANKER DISASTER",
    29: "SELTON'S SECOND SHOPPING CENTRE",
    30: "LEBRAT'S VISIT",
    31: "THE BUZZ SURVEY",
    32: "D.H. LAWRENCE",
    33: "THE FUNNIEST FILM",
    34: "TOM'S DIARY",
    35: "ELVIS PRESLEY",
    36: "GOING TO BRITAIN",
    37: "TRANSPORTATION IN TURKEY",
    38: "AMY'S RESTAURANT",
    39: "SMALL CARS",
    40: "HOME SWEET HOME",
    41: "A MEETING",
    42: "LAURA",
    43: "LETTER FROM WENDY",
    44: "EDUCATION AT HOME (1)",
    45: "EDUCATION AT HOME (2)",
    46: "JOHN LENNON",
    47: "GUIDE TO GOOD EATING",
    48: "RADIO TIMES READER HOLIDAYS",
    49: "SEAFORD SCHOOL & BEDGEBURY SCHOOL",
    50: "LETTER FROM GEORGE",
    51: "NOTTINGHAM & BANGOR",
    52: "A LANGUAGE TEACHER'S PERSONAL OPINION",
    53: "THE WORLDS OF WALT DISNEY",
    54: "LETTER FROM FAMILY FRIENDS AGENCY",
    55: "LETTER FROM KATHY",
    56: "SINGLE FATHERS' CLUB",
    57: "PLANE CRASH IN PERU",
    58: "INVERNESS",
    59: "LACROSSE",
    60: "THE BARASANA",
    61: "THE MOTOR CAR INDUSTRY",
    62: "THE OSTRICH",
    63: "RUDYARD KIPLING",
    64: "VIDEO CLIPS",
    65: "DREAMS",
    66: "ORANGES",
    67: "THE POSTAGE STAMP",
    68: "VOLCANOES",
    69: "CONTAINERS",
    70: "LUMINOUS AND NON-LUMINOUS BODIES",
    71: "COAL",
    72: "CARS OF THE FUTURE",
    73: "USING ELECTRICITY",
    74: "POLYMER BATTERIES FOR ELECTRIC VEHICLES",
    75: "EFFECTS OF CIGARETTE SMOKING",
    76: "MICROSCOPIC ORGANISMS",
    77: "ROLLER-SKATING TAKES OFF",
    78: "LEARNING ABOUT MARS",
    79: "PIRATES",
    80: "GEOTHERMAL ENERGY",
    81: "BALI",
    82: "LIFE IN SPACE",
    83: "NICE NOT EASY",
    84: "THE OLYMPIC MARATHON",
    85: "THE TECHNOLOGICAL REVOLUTION",
    86: "MANCHESTER",
    87: "'SEN' OR 'SIZ'?",
    88: "VIVE LA DIFFERENCE!",
    89: "TORNADOES",
    90: "INDUSTRIAL MEDICINE AND SAFETY",
    91: "LEARNING ABOUT COMPUTERS",
    92: "SEAT BELTS",
    93: "JAMES DEAN",
    94: "SKYSCRAPERS",
    95: "TEMPERATE CLIMATES",
    96: "THE PEN",
    97: "POPULAR vs. QUALITY NEWSPAPERS",
    98: "ACID RAIN (1)",
    99: "ACID RAIN (2)",
    100: "THE KON-TIKI VOYAGE, 1947",
    101: "U.S. CITIES: PAST AND PRESENT",
    102: "SPAS: GOOD OR BAD?",
}

EXERCISE_HEADER_RE = re.compile(
    r"^(MARK THE|TRUE|FALSE|EXERCISES?|QUESTIONS?|VOCABULARY|REFERENCE|"
    r"COMPREHENSION|ANSWER THE|COMPLETE THE|FILL IN|CHOOSE THE|MATCH THE|"
    r"CIRCLE THE|READ THE|WRITE |PART [A-Z0-9]|SECTION [A-Z0-9]|"
    r"WHAT DO|WHICH OF|ACCORDING TO|FIND WORDS?|IN THE TEXT|A\.|B\.|C\.|D\.|E\.)",
    re.IGNORECASE,
)

QUESTION_START_RE = re.compile(
    r"^(?:[A-F]\.\s+|"
    r"Mark the statements|"
    r"Mark the best choice|"
    r"What do(?:es)? the following|"
    r"Complete the following|"
    r"Answer the following|"
    r"Fill in (?:each|the) blank|"
    r"Find words in|"
    r"Circle the|"
    r"Match the|"
    r"Choose the|"
    r"\d{1,2}\.\s+)",
    re.IGNORECASE,
)


def preclean_line(text: str) -> str:
    t = text.translate(TR_MAP)
    t = t.replace("•", "'").replace("’", "'").replace("‘", "'")
    t = t.replace("“", '"').replace("”", '"')
    t = re.sub(r"\bT\s+wo\b", "Two", t)
    t = re.sub(r"\bW\s+hat\b", "What", t)
    t = re.sub(r"\bT\s+he\b", "The", t)
    t = re.sub(r"\bI\s+n\b", "In", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_all_caps_title(text: str) -> bool:
    s = text.strip()
    if len(s) < 3 or len(s) > 95:
        return False
    if EXERCISE_HEADER_RE.match(s):
        return False
    if re.match(r"^[a-d]\)", s) or re.match(r"^\d+[\.\)]\s", s):
        return False
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 3:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if upper_ratio < 0.82:
        return False
    if re.search(r"[MW]{4,}", s):
        return False
    return True


def is_garbled_noise(text: str) -> bool:
    s = text.strip()
    if not s:
        return True
    if re.search(r"[MW]{4,}", s):
        return True
    alpha_num = sum(1 for c in s if c.isalnum())
    if len(s) >= 8 and alpha_num / len(s) < 0.45:
        return True
    return False


def compute_median_body_height(lines: list[dict]) -> float:
    heights = [
        l["h"]
        for l in lines
        if l["w"] > 120 and 15 <= l["h"] <= 42 and len(l["text"]) >= 12
    ]
    if not heights:
        heights = [l["h"] for l in lines if 15 <= l["h"] <= 42]
    return statistics.median(heights) if heights else 28.0


def clean_page_lines(page: dict) -> tuple[list[dict], int | None]:
    iw, ih = page["img_w"], page["img_h"]
    raw_lines = page["lines"]
    med_h = compute_median_body_height(raw_lines)

    book_page: int | None = None
    kept: list[dict] = []

    for l in raw_lines:
        txt = preclean_line(l["text"])
        if not txt or is_garbled_noise(txt):
            continue

        x, y, w, h = l["x"], l["y"], l["w"], l["h"]
        cx = (x + w / 2.0) / iw
        cy = y / ih

        # Drop tiny OCR noise (bar speckles, smudges, garbled bottom artifacts)
        if h <= 14.5 and len(txt) < 40:
            continue
        if any(abs(y - yb) <= 16 for yb in page["y_bars"]) and len(txt) < 35 and not re.fullmatch(r"\d{1,3}", txt):
            continue

        # 1. Bottom centered page number (remove from content)
        if cy > 0.875 and 0.28 <= cx <= 0.72 and len(txt) <= 7:
            m_num = re.fullmatch(r"(\d{1,3})", txt)
            if m_num:
                book_page = int(m_num.group(1))
                continue
            if re.fullmatch(r"[/|lI\d\[\]]{1,5}", txt):
                continue

        # 2. Top-right tiny stray artifact
        if cy < 0.06 and x > 0.85 * iw and len(txt) <= 3:
            continue

        # 3. Left-margin line numbers (multiples of 5, small width, normal body height)
        if (
            x < 0.14 * iw
            and w < 0.08 * iw
            and h < max(33.0, med_h * 1.18)
            and re.fullmatch(r"(?:5|10|15|20|25|30|35|40|45|50|55|60|65|70|75|80|85|90|95|100)", txt)
        ):
            has_bar_below = any(10 <= (yb - y) <= 95 for yb in page["y_bars"])
            if not has_bar_below:
                continue

        kept.append(
            {
                "text": txt,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "cx": cx,
                "cy": cy,
                "med_h": med_h,
            }
        )

    kept.sort(key=lambda item: (item["y"], item["x"]))
    merged: list[dict] = []
    for item in kept:
        if merged:
            prev = merged[-1]
            same_row = abs(item["y"] - prev["y"]) <= max(8.0, 0.38 * med_h)
            horiz_gap = item["x"] - (prev["x"] + prev["w"])
            if same_row and horiz_gap >= -12:
                prev["text"] = f"{prev['text']} {item['text']}".strip()
                prev["w"] = (item["x"] + item["w"]) - prev["x"]
                prev["cx"] = (prev["x"] + prev["w"] / 2.0) / iw
                prev["h"] = max(prev["h"], item["h"])
                continue
        merged.append(dict(item))

    return merged, book_page


def parse_tall_passage_num(txt: str) -> int | None:
    s = txt.strip()
    m = re.fullmatch(r"(\d{1,3})", s)
    if m:
        val = int(m.group(1))
        return val if 1 <= val <= 250 else None
    # Recover OCR-split leading '1' misread as '!', '|', 'l', 'I', ']' (e.g. '! 63' -> 163)
    m2 = re.fullmatch(r"[!|Il\]]\s*(\d{1,2})", s)
    if m2:
        val = int("1" + m2.group(1))
        return val if 1 <= val <= 250 else None
    return None


def find_passage_starts(page: dict, lines: list[dict]) -> list[dict]:
    iw, ih = page["img_w"], page["img_h"]
    y_bars = page["y_bars"]
    book = page["book"]
    starts: list[dict] = []

    if not lines:
        return starts

    med_h = lines[0]["med_h"]

    def is_passage_num_line(idx: int) -> int | None:
        l = lines[idx]
        if l["x"] > 0.25 * iw:
            return None
        num = parse_tall_passage_num(l["text"])
        if num is None:
            return None
        tall = l["h"] >= max(33.0, med_h * 1.26)
        bar_below = any(8 <= (yb - l["y"]) <= 115 for yb in y_bars)
        title_after = False
        for j in range(idx + 1, min(idx + 4, len(lines))):
            nxt = lines[j]
            if (nxt["y"] - l["y"]) < 240 and 0.22 <= nxt["cx"] <= 0.78 and is_all_caps_title(nxt["text"]):
                title_after = True
                break
        if bar_below or (tall and (l["cy"] < 0.25 or title_after)):
            return num
        return None

    used_indices: set[int] = set()

    for i, l in enumerate(lines):
        if i in used_indices:
            continue
        pnum = is_passage_num_line(i)
        if pnum is not None:
            title_parts = []
            body_start = i + 1
            for j in range(i + 1, min(i + 4, len(lines))):
                cand = lines[j]
                if cand["y"] - l["y"] > 300:
                    break
                if 0.22 <= cand["cx"] <= 0.78 and is_all_caps_title(cand["text"]):
                    title_parts.append(cand["text"])
                    used_indices.add(j)
                    body_start = j + 1
                elif title_parts:
                    break
                else:
                    break

            title = " ".join(title_parts).strip() if title_parts else ""
            starts.append(
                {
                    "line_idx": i,
                    "body_idx": body_start,
                    "passage_number": pnum,
                    "title": title,
                    "y": l["y"],
                    "reason": "number",
                }
            )
            used_indices.add(i)

    def near_existing_start(y_val: float) -> bool:
        return any(abs(s["y"] - y_val) < 230 for s in starts)

    # Top-of-page centered ALL-CAPS title without recognized number
    if lines and not near_existing_start(lines[0]["y"]):
        first = lines[0]
        if first["cy"] < 0.24 and 0.24 <= first["cx"] <= 0.76 and is_all_caps_title(first["text"]):
            has_prose_after = any(len(lines[k]["text"]) > 40 for k in range(1, min(4, len(lines))))
            bar_above = any(0 <= (first["y"] - yb) <= 130 for yb in y_bars)
            if has_prose_after and (first["cy"] < 0.19 or bar_above):
                title_parts = [first["text"]]
                body_start = 1
                if (
                    len(lines) > 1
                    and (lines[1]["y"] - first["y"]) < 70
                    and 0.24 <= lines[1]["cx"] <= 0.76
                    and is_all_caps_title(lines[1]["text"])
                ):
                    title_parts.append(lines[1]["text"])
                    body_start = 2
                starts.append(
                    {
                        "line_idx": 0,
                        "body_idx": body_start,
                        "passage_number": None,
                        "title": " ".join(title_parts),
                        "y": first["y"],
                        "reason": "top_title_no_num",
                    }
                )

    if book == 1:
        for yb in y_bars:
            if near_existing_start(yb):
                continue
            below_idxs = [idx for idx, l in enumerate(lines) if 5 <= (l["y"] - yb) <= 130]
            if below_idxs:
                idx0 = below_idxs[0]
                cand = lines[idx0]
                if 0.24 <= cand["cx"] <= 0.76 and is_all_caps_title(cand["text"]):
                    if cand["text"] not in {"A SHOPPING EXPERIENCE WITHOUT EQUAL", "SELTON TIMES"}:
                        title_parts = [cand["text"]]
                        body_start = idx0 + 1
                        if (
                            body_start < len(lines)
                            and (lines[body_start]["y"] - cand["y"]) < 70
                            and is_all_caps_title(lines[body_start]["text"])
                        ):
                            title_parts.append(lines[body_start]["text"])
                            body_start += 1
                        starts.append(
                            {
                                "line_idx": idx0,
                                "body_idx": body_start,
                                "passage_number": None,
                                "title": " ".join(title_parts),
                                "y": yb,
                                "reason": "bar_title_no_num",
                            }
                        )

    starts.sort(key=lambda s: s["line_idx"])
    return starts


def count_prose_words(text: str) -> int:
    lines = text.splitlines()
    prose = []
    for ln in lines:
        s = ln.strip()
        if QUESTION_START_RE.match(s):
            break
        prose.append(s)
    return len(" ".join(prose).split())


def is_cloze_exercise_only(text: str) -> bool:
    blanks = len(re.findall(r"\(\d{1,2}\)\s*[_]{2,}|\(\d{1,2}\)\s*,", text))
    has_fill_instr = bool(re.search(r"Fill in each blank with a suitable connector", text, re.IGNORECASE))
    return has_fill_instr or blanks >= 4


def is_appendix_page(book_num: int, lines: list[dict]) -> bool:
    if book_num != 2 or not lines:
        return False
    head = " ".join(l["text"] for l in lines[:3])
    return bool(re.search(r"\bAPPENDIX\s+A\b", head, re.IGNORECASE))


def segment_book(book_pages: list[dict], book_num: int, report: dict) -> list[dict]:
    passages: list[dict] = []
    current: dict | None = None
    prev_book_page: int | None = None
    in_appendix = False

    def flush_current(gap_after: bool = False):
        nonlocal current
        if not current:
            return
        full_text = "\n".join(current["chunks"]).strip()
        prose_wc = count_prose_words(full_text)
        total_wc = len(full_text.split())

        if is_cloze_exercise_only(full_text):
            report["skipped"].append(
                {
                    "book": book_num,
                    "title": current["title"],
                    "passage_number": current["passage_number"],
                    "pdf_pages": current["pdf_pages"],
                    "book_pages": current["book_pages"],
                    "reason": "standalone_cloze_drill",
                    "words": total_wc,
                }
            )
            current = None
            return

        if prose_wc < 28 and not current["title"]:
            report["skipped"].append(
                {
                    "book": book_num,
                    "title": current["title"],
                    "passage_number": current["passage_number"],
                    "pdf_pages": current["pdf_pages"],
                    "book_pages": current["book_pages"],
                    "reason": "short_orphan_fragment",
                    "words": total_wc,
                    "preview": full_text[:180],
                }
            )
            current = None
            return

        if prose_wc < 22:
            report["skipped"].append(
                {
                    "book": book_num,
                    "title": current["title"],
                    "passage_number": current["passage_number"],
                    "pdf_pages": current["pdf_pages"],
                    "book_pages": current["book_pages"],
                    "reason": "too_few_prose_words",
                    "words": total_wc,
                    "preview": full_text[:180],
                }
            )
            current = None
            return

        if gap_after:
            current["page_gap_after"] = True

        current["raw_text"] = full_text
        current["prose_word_count"] = prose_wc
        current["total_word_count"] = total_wc
        passages.append(current)
        current = None

    for page in book_pages:
        lines, book_page = clean_page_lines(page)
        pdf_page = page["pdf_page"]

        if in_appendix or is_appendix_page(book_num, lines):
            in_appendix = True
            flush_current(gap_after=False)
            report["skipped"].append(
                {
                    "book": book_num,
                    "pdf_pages": [pdf_page],
                    "book_pages": [book_page] if book_page else [],
                    "reason": "appendix_connectors",
                }
            )
            continue

        # Known silent page gap in Book 2 where both PDF p.113 (#71) and p.114 (orphan #72) lack bottom page numbers
        if book_num == 2 and pdf_page == 114:
            flush_current(gap_after=True)
            report["skipped"].append(
                {
                    "book": book_num,
                    "pdf_pages": [pdf_page],
                    "book_pages": [book_page] if book_page else [],
                    "reason": "orphan_continuation_after_silent_gap",
                    "preview": " ".join(l["text"] for l in lines[:4])[:180],
                }
            )
            continue

        if not lines:
            report["skipped"].append(
                {
                    "book": book_num,
                    "pdf_pages": [pdf_page],
                    "book_pages": [book_page] if book_page else [],
                    "reason": "blank_page",
                }
            )
            continue

        page_gap = False
        if book_page is not None and prev_book_page is not None:
            if book_page > prev_book_page + 1:
                page_gap = True
                report["page_gaps"].append(
                    {
                        "book": book_num,
                        "from_book_page": prev_book_page,
                        "to_book_page": book_page,
                        "at_pdf_page": pdf_page,
                    }
                )
        if book_page is not None:
            prev_book_page = book_page

        starts = find_passage_starts(page, lines)

        if page_gap and current is not None:
            flush_current(gap_after=True)

        if not starts:
            page_txt = "\n".join(l["text"] for l in lines)
            if current is not None:
                current["chunks"].append(page_txt)
                current["pdf_pages"].append(pdf_page)
                if book_page is not None and book_page not in current["book_pages"]:
                    current["book_pages"].append(book_page)
            else:
                report["skipped"].append(
                    {
                        "book": book_num,
                        "pdf_pages": [pdf_page],
                        "book_pages": [book_page] if book_page else [],
                        "reason": "orphan_continuation_after_gap",
                        "words": len(page_txt.split()),
                        "preview": page_txt[:180],
                    }
                )
        else:
            first_start_idx = starts[0]["line_idx"]
            if first_start_idx > 0:
                pre_txt = "\n".join(l["text"] for l in lines[:first_start_idx])
                if current is not None:
                    current["chunks"].append(pre_txt)
                    current["pdf_pages"].append(pdf_page)
                    if book_page is not None and book_page not in current["book_pages"]:
                        current["book_pages"].append(book_page)
                else:
                    report["skipped"].append(
                        {
                            "book": book_num,
                            "pdf_pages": [pdf_page],
                            "book_pages": [book_page] if book_page else [],
                            "reason": "orphan_pre_header_after_gap",
                            "words": len(pre_txt.split()),
                            "preview": pre_txt[:180],
                        }
                    )

            flush_current(gap_after=False)

            for s_idx, st in enumerate(starts):
                end_idx = starts[s_idx + 1]["line_idx"] if (s_idx + 1) < len(starts) else len(lines)
                body_lines = lines[st["body_idx"] : end_idx]
                body_txt = "\n".join(l["text"] for l in body_lines)

                current = {
                    "book": book_num,
                    "passage_number": st["passage_number"],
                    "title": st["title"],
                    "pdf_pages": [pdf_page],
                    "book_pages": [book_page] if book_page is not None else [],
                    "page_gap_after": False,
                    "start_reason": st["reason"],
                    "chunks": [body_txt] if body_txt else [],
                }
                if s_idx < len(starts) - 1:
                    flush_current(gap_after=False)

    flush_current(gap_after=False)

    prev_num = 0
    for idx, p in enumerate(passages, 1):
        if p["passage_number"] is None:
            prev_num += 1
            p["inferred_number"] = prev_num
        else:
            prev_num = p["passage_number"]
        num_for_id = p["passage_number"] if p["passage_number"] is not None else p["inferred_number"]
        p["id"] = f"raw{book_num}_{idx:03d}"
        p["seq_index"] = idx
        p["display_number"] = num_for_id

        # Fill official Book 1 TOC title if printed page omitted a centered ALL-CAPS title
        if book_num == 1 and num_for_id in BOOK1_TOC_TITLES:
            if not p["title"]:
                p["title"] = BOOK1_TOC_TITLES[num_for_id]
        elif book_num == 2 and not p["title"]:
            if num_for_id == 197:
                p["title"] = "LETTERS ON TELEVISION COVERAGE"

        p.pop("chunks", None)

    return passages


def main() -> None:
    pages = json.loads(OCR_JSON.read_text(encoding="utf-8"))
    b1_pages = [p for p in pages if p["book"] == 1]
    b2_pages = [p for p in pages if p["book"] == 2]

    report = {"page_gaps": [], "skipped": [], "anomalies": []}

    p1 = segment_book(b1_pages, 1, report)
    p2 = segment_book(b2_pages, 2, report)

    all_passages = p1 + p2
    OUT_RAW.write_text(json.dumps(all_passages, ensure_ascii=False, indent=2), encoding="utf-8")

    for p in all_passages:
        if p["prose_word_count"] < 40 or p["total_word_count"] > 1500 or not p["title"]:
            report["anomalies"].append(
                {
                    "id": p["id"],
                    "book": p["book"],
                    "passage_number": p["passage_number"],
                    "display_number": p["display_number"],
                    "title": p["title"],
                    "pdf_pages": p["pdf_pages"],
                    "prose_words": p["prose_word_count"],
                    "total_words": p["total_word_count"],
                    "preview": p["raw_text"][:140],
                }
            )

    OUT_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Segmented Book 1: {len(p1)} passages | Book 2: {len(p2)} passages | Total: {len(all_passages)}")
    print(f"Page gaps detected: {len(report['page_gaps'])} | Skipped items: {len(report['skipped'])} | Anomalies: {len(report['anomalies'])}")

    b2_nums = [p["display_number"] for p in p2]
    dups = [n for n in set(b2_nums) if b2_nums.count(n) > 1]
    missing_225 = [i for i in range(1, 226) if i not in set(b2_nums)]
    print(f"Book 2 duplicate display_numbers: {dups} | Missing from 1..225: {missing_225}")

    for label, plist in [("Book 1", p1), ("Book 2", p2)]:
        print(f"\n=== {label} First 5 / Middle 5 / Last 5 ===")
        sample = plist[:5] + plist[len(plist)//2 - 2 : len(plist)//2 + 3] + plist[-5:]
        for item in sample:
            print(
                f"  {item['id']} | #{item['passage_number']} (disp {item['display_number']}) | "
                f"pp.{item['pdf_pages']} (bk {item['book_pages']}) | "
                f"words={item['prose_word_count']}/{item['total_word_count']} | {item['title']!r}"
            )


if __name__ == "__main__":
    main()
