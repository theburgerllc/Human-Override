from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from tools.tho import compute_timeline


def root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_episode(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Episode YAML must be a mapping.")
    return data


def beats_key_and_list(data: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    for key in ("beats", "timeline", "steps", "scenes"):
        v = data.get(key)
        if isinstance(v, list) and all(isinstance(x, dict) for x in v):
            return key, v  # type: ignore[return-value]
    raise ValueError("Could not find beats list.")


def duration_of(beat: Dict[str, Any]) -> float:
    for k in ("duration_s", "duration", "seconds", "len_s"):
        v = beat.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    # If the main renderer infers durations, default to a conservative short beat
    return 2.5


def select_hook_indices(beats: List[Dict[str, Any]]) -> List[int]:
    idxs: List[int] = []
    for i, b in enumerate(beats):
        if b.get("hook") is True or b.get("shorts") is True:
            idxs.append(i)
        elif isinstance(b.get("tags"), list) and any(t in ("hook", "shorts") for t in b.get("tags")):
            idxs.append(i)
    return idxs


def pack_window(beats: List[Dict[str, Any]], start_i: int, max_s: float) -> List[int]:
    out: List[int] = []
    total = 0.0
    for i in range(start_i, len(beats)):
        d = duration_of(beats[i])
        if total + d > max_s and out:
            break
        out.append(i)
        total += d
        if total >= max_s:
            break
    return out


def build_variants(beats: List[Dict[str, Any]], target_s: float) -> List[List[int]]:
    # Strategy:
    # A) Hook-tagged beats if present, packed to ~target
    # B) First window ~target
    # C) Middle window ~target
    # D) Last window ~target
    hook = select_hook_indices(beats)
    variants: List[List[int]] = []

    if hook:
        # Pack contiguous ranges around hook beats
        first = hook[0]
        variants.append(pack_window(beats, first, target_s))

    # Always include an early window
    variants.append(pack_window(beats, 0, target_s))

    # Middle window
    mid = max(0, len(beats) // 2 - 1)
    variants.append(pack_window(beats, mid, target_s))

    # Last window
    last = max(0, len(beats) - 4)
    variants.append(pack_window(beats, last, target_s))

    # De-dup identical sequences
    uniq: List[List[int]] = []
    seen = set()
    for v in variants:
        key = tuple(v)
        if key not in seen and v:
            seen.add(key)
            uniq.append(v)

    return uniq[:3]  # keep it tight: 3 deliverables


def write_temp_yaml(data: Dict[str, Any], beats_key: str, beats: List[Dict[str, Any]], indices: List[int], out_path: Path) -> None:
    out = dict(data)
    out_beats = [beats[i] for i in indices]
    out[beats_key] = out_beats
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")


def run_tho_animatic(episode_id: str, episode_yaml: Path) -> None:
    import sys
    py_cmd = [sys.executable]

    cmd = py_cmd + ["tools/tho.py", "animatic", episode_id, "--episode-yaml", str(episode_yaml), "--run"]
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Shorts variants from an episode YAML.")
    ap.add_argument("--episode-yaml", required=True)
    ap.add_argument("--episode-id", required=True)
    ap.add_argument("--target-seconds", type=float, default=35.0)
    ap.add_argument("--out-dir", default="", help="Directory for temp YAMLs; renders go to renderer default outputs.")
    args = ap.parse_args()

    ep_path = Path(args.episode_yaml)
    data = load_episode(ep_path)
    beats_key, beats = beats_key_and_list(data)

    variants = build_variants(beats, target_s=float(args.target_seconds))
    if not variants:
        raise RuntimeError("No beats available to build shorts.")

    tmp_dir = Path(args.out_dir) if args.out_dir else (root() / "outputs" / "_tmp_shorts")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for n, idxs in enumerate(variants, start=1):
        short_id = f"{args.episode_id}_SHORT{n}"
        tmp_yaml = tmp_dir / f"{short_id}.yaml"
        write_temp_yaml(data, beats_key, beats, idxs, tmp_yaml)
        print(f"SHORT{n}: beats={len(idxs)} yaml={tmp_yaml}")
        run_tho_animatic(short_id, tmp_yaml)

    print("Shorts generation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
