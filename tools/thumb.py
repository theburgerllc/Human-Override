from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Reuse helpers from tho.py when available.
from tools.tho import load_config, ffmpeg_escape_drawtext, wrap_text


def root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_episode(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Episode YAML must be a mapping.")
    return data


def get_beats(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("beats", "timeline", "steps", "scenes"):
        v = data.get(key)
        if isinstance(v, list) and all(isinstance(x, dict) for x in v):
            return v  # type: ignore[return-value]
    raise ValueError("Could not find beats list.")


def pick_thumbnail_beat(beats: List[Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
    # Priority 1: explicit
    for i, b in enumerate(beats):
        if b.get("thumbnail") is True:
            return i, b
    # Priority 2: hook tag
    for i, b in enumerate(beats):
        if b.get("hook") is True or (isinstance(b.get("tags"), list) and "hook" in b.get("tags")):
            return i, b
    # Priority 3: first beat with strong on_screen
    for i, b in enumerate(beats):
        t = b.get("on_screen")
        if isinstance(t, str) and t.strip():
            return i, b
    return 0, beats[0]


def resolve_ffmpeg() -> str:
    r = root()
    if load_config is not None:
        cfg = load_config(r)  # type: ignore[misc]
        if getattr(cfg, "ffmpeg", None):
            return str(cfg.ffmpeg)
    return "ffmpeg"


def ui_png(name: str) -> Optional[Path]:
    p = root() / "assets" / "ui" / "png" / f"{name}.png"
    return p if p.exists() else None


def choose_ui_for_thumbnail(beat: Dict[str, Any]) -> Optional[Path]:
    # Prefer popup/card if available, else any ui_component
    ui = beat.get("ui_component")
    if isinstance(ui, str) and ui.strip():
        p = ui_png(ui.strip())
        if p:
            return p
    # fallback to a canonical popup if present
    for cand in ("popup_verify_identity", "popup_confirm_savings", "card_risk_signal"):
        p = ui_png(cand)
        if p:
            return p
    return None


def font_opt() -> str:
    r = root()
    if load_config is not None:
        cfg = load_config(r)  # type: ignore[misc]
        ff = getattr(cfg, "fontfile", None)
        if ff:
            p = str(ff).replace("\\", "/")
            return f":fontfile='{ffmpeg_escape_drawtext(p)}'"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a 16:9 thumbnail from an episode YAML.")
    ap.add_argument("--episode-yaml", required=True)
    ap.add_argument("--episode-id", required=True)
    ap.add_argument("--out", default="", help="Output PNG path. Defaults to outputs/thumbs/<episode-id>.png")
    args = ap.parse_args()

    ep_path = Path(args.episode_yaml)
    data = load_episode(ep_path)
    beats = get_beats(data)
    idx, beat = pick_thumbnail_beat(beats)

    headline = beat.get("thumbnail_headline") or beat.get("on_screen") or "THE HUMAN OVERRIDE"
    subline = beat.get("thumbnail_subline") or beat.get("overlay_text_snippet") or "ONE CLICK • SEASON 1"
    if not isinstance(headline, str):
        headline = "THE HUMAN OVERRIDE"
    if not isinstance(subline, str):
        subline = "ONE CLICK • SEASON 1"

    # Wrap for thumb layout
    headline_wrapped = wrap_text(headline.strip().upper(), width=18, max_lines=2)
    subline_wrapped = wrap_text(subline.strip(), width=30, max_lines=2)

    ui = choose_ui_for_thumbnail(beat)
    if ui is None:
        raise RuntimeError("No UI PNG found for thumbnail. Export UI assets first (export_ui_assets.bat).")

    out = Path(args.out) if args.out else (root() / "outputs" / "thumbs" / f"{args.episode_id}.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = resolve_ffmpeg()
    ui_path = str(ui).replace("\\", "/")

    # Layout:
    # - Dark background (1280x720)
    # - “Phone UI” (your 9:16 overlay) centered-left with subtle shadow
    # - Big headline on right, subline below
    fopt = font_opt()
    headline_txt = ffmpeg_escape_drawtext(headline_wrapped)
    subline_txt = ffmpeg_escape_drawtext(subline_wrapped)

    # Phone scale: 9:16 at h=680 => w≈383
    # Place phone at x=90, y=20 (leaves room for right-side text)
    filter_complex = (
        "color=c=black:s=1280x720,format=rgba,"
        "vignette=PI/5:eval=frame,noise=alls=6:allf=t+u[bg];"
        f"movie='{ffmpeg_escape_drawtext(ui_path)}',format=rgba,scale=-1:680[ui];"
        "[ui]colorchannelmixer=aa=0.35,gblur=sigma=12[shadow];"
        "[bg][shadow]overlay=x=94:y=28:format=auto[tmp1];"
        "[tmp1][ui]overlay=x=90:y=20:format=auto[tmp2];"
        f"[tmp2]drawtext=text='{headline_txt}'{fopt}:"
        "x=520:y=150:fontsize=64:fontcolor=white@0.95:"
        "borderw=3:bordercolor=black@0.45:shadowx=2:shadowy=2:shadowcolor=black@0.50:"
        "line_spacing=10:box=1:boxcolor=black@0.22:boxborderw=18[tmp3];"
        f"[tmp3]drawtext=text='{subline_txt}'{fopt}:"
        "x=520:y=350:fontsize=30:fontcolor=white@0.75:"
        "borderw=2:bordercolor=black@0.30:shadowx=1:shadowy=1:shadowcolor=black@0.40:"
        "line_spacing=8:box=1:boxcolor=black@0.18:boxborderw=14[out]"
    )

    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=30",
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-frames:v", "1",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    print(f"Thumbnail written: {out} (beat #{idx+1})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
