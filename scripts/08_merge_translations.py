"""Step 8: Merge Turkish transcript translations into data/passages.json and validate coverage."""

import json
import re
from pathlib import Path

WORKSPACE = Path(r"c:\Users\culfa\Desktop\ing")
DATA_JSON = WORKSPACE / "data" / "passages.json"
TR_BATCH_DIR = WORKSPACE / "data" / "tr_batches"


def split_paras(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"\n{2,}", text.strip()) if x.strip()]


def main() -> None:
    dataset = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    passages = dataset["passages"]

    tr_by_id: dict[str, str] = {}
    for bf in sorted(TR_BATCH_DIR.glob("tr_batch_*.json")):
        rows = json.loads(bf.read_text(encoding="utf-8"))
        for row in rows:
            tr_by_id[row["id"]] = row["tts_script_tr"].strip()

    missing = [p["id"] for p in passages if not tr_by_id.get(p["id"])]
    if missing:
        raise SystemExit(f"ERROR: Missing Turkish translations for {len(missing)} passage(s): {missing[:20]}")

    para_aligned = 0
    para_mismatches = []
    ratios = []

    for p in passages:
        tr = tr_by_id[p["id"]]
        en = p["tts_script"]
        p["tts_script_tr"] = tr
        ratios.append(len(tr) / max(1, len(en)))
        en_paras = split_paras(en)
        tr_paras = split_paras(tr)
        if len(en_paras) == len(tr_paras):
            para_aligned += 1
        else:
            para_mismatches.append((p["id"], len(en_paras), len(tr_paras)))

    DATA_JSON.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")

    avg_ratio = sum(ratios) / len(ratios)
    print(f"Merged Turkish transcripts for {len(passages)}/{len(passages)} passages.")
    print(f"Paragraph-aligned 1:1: {para_aligned}/{len(passages)} | Mismatches: {len(para_mismatches)} | Avg TR/EN length ratio: {avg_ratio:.2f}")
    if para_mismatches:
        print("Sample paragraph mismatches:", para_mismatches[:10])


if __name__ == "__main__":
    main()
