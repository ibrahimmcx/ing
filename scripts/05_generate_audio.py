"""Step 5: Synthesize Edge-TTS MP3 audio files for every passage with timeouts, retry & resume."""

import asyncio
import json
import os
import sys
from pathlib import Path

import edge_tts

WORKSPACE = Path(r"c:\Users\culfa\Desktop\ing")
DATA_JSON = WORKSPACE / "data" / "passages.json"
DATA_JS = WORKSPACE / "data" / "passages.js"


async def verify_and_fix_voices(dataset: dict) -> None:
    print("Fetching live Edge-TTS voice list...", flush=True)
    try:
        voices = await asyncio.wait_for(edge_tts.list_voices(), timeout=20)
    except Exception as exc:
        print(
            f"Warning: list_voices timed out or failed ({type(exc).__name__}: {exc}); "
            "proceeding with configured standard neural voices.",
            flush=True,
        )
        return

    available = {v["ShortName"] for v in voices}
    fallbacks = {}
    for locale in ("en-GB", "en-US", "en-AU"):
        cands = [v["ShortName"] for v in voices if v.get("Locale") == locale]
        if not cands:
            cands = [v["ShortName"] for v in voices if v.get("Locale", "").startswith("en-")]
        fallbacks[locale] = cands

    changed = False
    for p in dataset["passages"]:
        v = p["voice"]
        if v not in available:
            locale = "-".join(v.split("-")[:2])
            pool = fallbacks.get(locale) or fallbacks["en-US"]
            new_v = pool[0]
            print(f"Voice fallback for {p['id']}: {v} -> {new_v}", flush=True)
            p["voice"] = new_v
            changed = True

    if changed:
        DATA_JSON.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
        DATA_JS.write_text("window.PASSAGES_DATA = " + json.dumps(dataset, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("Voices verified.", flush=True)


async def synth_one(sem: asyncio.Semaphore, p: dict, stats: dict, total: int) -> None:
    out_path = WORKSPACE / p["audio_path"]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and out_path.stat().st_size > 2000:
        stats["skipped"] += 1
        stats["done"] += 1
        return

    tmp_path = out_path.with_suffix(".mp3.tmp")
    text = p["tts_script"].strip()
    voice = p["voice"]
    rate = p["rate"]

    async with sem:
        last_err = None
        for attempt in range(4):
            try:
                comm = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=rate,
                    connect_timeout=15,
                    receive_timeout=120,
                )
                await asyncio.wait_for(comm.save(str(tmp_path)), timeout=180)
                if tmp_path.exists() and tmp_path.stat().st_size > 2000:
                    os.replace(tmp_path, out_path)
                    stats["generated"] += 1
                    stats["done"] += 1
                    if stats["done"] % 10 == 0 or stats["done"] == total:
                        print(
                            f"Audio progress: {stats['done']}/{total} "
                            f"(generated={stats['generated']}, skipped={stats['skipped']}, failed={len(stats['failed'])})",
                            flush=True,
                        )
                    return
                last_err = f"Output file too small ({tmp_path.stat().st_size if tmp_path.exists() else 0} bytes)"
            except Exception as exc:
                last_err = f"{type(exc).__name__}: {exc}"
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            await asyncio.sleep(2 ** attempt)

        stats["failed"].append({"id": p["id"], "error": last_err})
        stats["done"] += 1
        print(f"FAILED {p['id']}: {last_err}", flush=True)


async def main_async() -> int:
    dataset = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    passages = dataset["passages"]
    total = len(passages)
    print(f"Starting Edge-TTS synthesis for {total} passages...", flush=True)
    await verify_and_fix_voices(dataset)

    stats = {"done": 0, "generated": 0, "skipped": 0, "failed": []}
    sem = asyncio.Semaphore(6)
    await asyncio.gather(*(synth_one(sem, p, stats, total) for p in passages))

    print(
        f"Audio synthesis complete: total={total}, generated={stats['generated']}, "
        f"skipped={stats['skipped']}, failed={len(stats['failed'])}",
        flush=True,
    )
    if stats["failed"]:
        print("Failed items:", json.dumps(stats["failed"], ensure_ascii=False), flush=True)
        return 1
    return 0


def main() -> None:
    rc = asyncio.run(main_async())
    sys.exit(rc)


if __name__ == "__main__":
    main()
