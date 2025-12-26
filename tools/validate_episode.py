from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_yaml(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Episode YAML must be a mapping (top-level object).")
    return data


def _find_beats(data: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    # Tolerant: support a few likely top-level keys.
    for key in ("beats", "timeline", "steps", "scenes"):
        v = data.get(key)
        if isinstance(v, list) and all(isinstance(x, dict) for x in v):
            return key, v  # type: ignore[return-value]
    raise ValueError("Could not find beats list (expected one of: beats/timeline/steps/scenes).")


def _duration_of(beat: Dict[str, Any]) -> float:
    # Tolerant: accept any of these.
    for k in ("duration_s", "duration", "seconds", "len_s"):
        v = beat.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    # If no duration is present, allow it (tho.py may infer), but warn.
    return 0.0


def _collect_ui_component_names(root: Path) -> List[str]:
    names: List[str] = []
    svg_dir = root / "assets" / "ui" / "svg"
    png_dir = root / "assets" / "ui" / "png"
    for d in (svg_dir, png_dir):
        if d.exists():
            for p in d.glob("*.svg" if d == svg_dir else "*.png"):
                names.append(p.stem)
    # Unique
    return sorted(set(names))


def _is_safe_token(s: str) -> bool:
    # no spaces, no path traversal
    return bool(re.fullmatch(r"[A-Za-z0-9_\-\.]+", s))


def validate_episode(path: Path, strict: bool) -> int:
    root = _root()
    data = _load_yaml(path)
    beats_key, beats = _find_beats(data)
    ui_known = set(_collect_ui_component_names(root))

    errors: List[str] = []
    warnings: List[str] = []

    if not beats:
        errors.append(f"{beats_key} list is empty.")

    total_s = 0.0
    for i, beat in enumerate(beats, start=1):
        dur = _duration_of(beat)
        if dur <= 0:
            warnings.append(f"Beat {i}: missing/invalid duration (duration_s/duration/seconds).")
        else:
            total_s += dur

        ui = beat.get("ui_component")
        if ui is not None:
            if not isinstance(ui, str) or not ui.strip():
                errors.append(f"Beat {i}: ui_component must be a non-empty string if provided.")
            else:
                ui_s = ui.strip()
                if not _is_safe_token(ui_s):
                    errors.append(f"Beat {i}: ui_component contains unsafe characters: {ui_s!r}")
                # Soft-check known asset names (don’t fail unless strict)
                if ui_s not in ui_known:
                    msg = f"Beat {i}: ui_component '{ui_s}' has no matching asset in assets/ui/(svg|png)."
                    if strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

        # Text fields sanity
        for k in ("on_screen", "overlay_text_snippet", "system_log"):
            if k in beat and beat[k] is not None and not isinstance(beat[k], str):
                errors.append(f"Beat {i}: {k} must be a string if provided.")

    if total_s > 0 and total_s < 10:
        warnings.append(f"Episode seems very short (~{total_s:.1f}s).")

    # Print results
    if warnings:
        print("VALIDATION WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return 2
    print(f"Episode YAML OK: beats={len(beats)} total_duration≈{total_s:.1f}s (duration may be inferred).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate an episode YAML before rendering.")
    ap.add_argument("--episode-yaml", required=True, help="Path to episode YAML.")
    ap.add_argument("--strict", action="store_true", help="Fail if ui_component assets are missing.")
    args = ap.parse_args()
    return validate_episode(Path(args.episode_yaml), strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
