from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml


_TIME_RE = re.compile(r"^(?P<mm>\d{2}):(?P<ss>\d{2})\.(?P<ds>\d)$")


@dataclass(frozen=True)
class Config:
    ffmpeg: str = "ffmpeg"
    fontfile: str = ""
    default_fps: int = 30


def repo_root() -> Path:
    # tools/tho.py -> tools -> repo root
    return Path(__file__).resolve().parent.parent


def load_config(root: Path) -> Config:
    cfg_path = root / "config.local.json"
    if not cfg_path.exists():
        return Config()

    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to parse config.local.json: {e}") from e

    ffmpeg = os.environ.get("FFMPEG") or str(data.get("ffmpeg", "ffmpeg")).strip() or "ffmpeg"
    fontfile = os.environ.get("FONTFILE") or str(data.get("fontfile", "")).strip()
    default_fps = int(data.get("default_fps", 30))
    if default_fps <= 0:
        default_fps = 30
    return Config(ffmpeg=ffmpeg, fontfile=fontfile, default_fps=default_fps)


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def parse_timecode(tc: str) -> float:
    m = _TIME_RE.match(tc.strip())
    if not m:
        raise ValueError(f"Invalid timecode '{tc}'. Expected MM:SS.s (example 00:14.0)")
    mm = int(m.group("mm"))
    ss = int(m.group("ss"))
    ds = int(m.group("ds"))
    if ss >= 60:
        raise ValueError(f"Invalid seconds in timecode '{tc}'")
    return (mm * 60) + ss + (ds / 10.0)


def format_timecode(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    mm = int(seconds // 60)
    ss = int(seconds % 60)
    ds = int(round((seconds - int(seconds)) * 10)) % 10
    return f"{mm:02d}:{ss:02d}.{ds:d}"


def wrap_text(s: str, width: int = 34, max_lines: int = 2) -> str:
    # Simple whitespace wrap; keeps output deterministic for drawtext.
    words = s.strip().split()
    if not words:
        return ""
    lines: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for w in words:
        add = len(w) + (1 if cur else 0)
        if cur and (cur_len + add) > width:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
            if len(lines) >= max_lines:
                break
        else:
            cur.append(w)
            cur_len += add
    if len(lines) < max_lines and cur:
        lines.append(" ".join(cur))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    return "\\n".join(lines)


def ffmpeg_escape_drawtext(s: str) -> str:
    # Escapes for drawtext text='...'
    # Notes: ':' and '\' must be escaped; '%' prevents expansion; '\'' for single quote.
    s = s.replace("\\", "\\\\")
    s = s.replace(":", "\\:")
    s = s.replace("%", "\\\\%")
    s = s.replace("'", "\\'")
    s = s.replace("[", "\\[")
    s = s.replace("]", "\\]")
    s = s.replace("\n", "\\n")
    return s


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RuntimeError(f"Episode YAML not found: {path}")
    try:
        data = yaml.safe_load(raw)
    except Exception as e:
        raise RuntimeError(f"Invalid YAML in {path}: {e}") from e
    if not isinstance(data, dict):
        raise RuntimeError(f"Episode YAML must be a mapping at top level: {path}")
    return data


def validate_episode(data: Dict[str, Any], *, context: str = "") -> None:
    ctx = f" ({context})" if context else ""
    for key in ("meta", "packaging", "characters", "beats"):
        if key not in data:
            raise RuntimeError(f"Missing required key '{key}'{ctx}")

    if not isinstance(data["characters"], list):
        raise RuntimeError(f"'characters' must be a list{ctx}")
    if not isinstance(data["beats"], list) or not data["beats"]:
        raise RuntimeError(f"'beats' must be a non-empty list{ctx}")

    last_t: Optional[float] = None
    for i, beat in enumerate(data["beats"], start=1):
        if not isinstance(beat, dict):
            raise RuntimeError(f"Beat #{i} must be an object/map{ctx}")

        t = beat.get("t")
        btype = beat.get("type")
        if not isinstance(t, str):
            raise RuntimeError(f"Beat #{i} missing/invalid 't'{ctx}")
        if not isinstance(btype, str) or not btype.strip():
            raise RuntimeError(f"Beat #{i} missing/invalid 'type'{ctx}")

        try:
            t_s = parse_timecode(t)
        except ValueError as e:
            raise RuntimeError(f"Beat #{i} invalid timecode: {e}{ctx}") from e

        if last_t is not None and not (t_s > last_t):
            raise RuntimeError(
                f"Beats must have strictly increasing timecodes. Beat #{i} time {t} is not > previous."
                f"{ctx}"
            )
        last_t = t_s

        has_any = any(k in beat for k in ("on_screen", "ui_component", "vo"))
        if not has_any:
            raise RuntimeError(
                f"Beat #{i} must include at least one of: on_screen, ui_component, vo{ctx}"
            )

        if "sfx" in beat and not (
            isinstance(beat["sfx"], list) and all(isinstance(x, str) for x in beat["sfx"])
        ):
            raise RuntimeError(f"Beat #{i} has invalid 'sfx' (must be list[str]){ctx}")


def compute_timeline(data: Dict[str, Any]) -> List[Tuple[Dict[str, Any], float, float]]:
    beats: List[Dict[str, Any]] = data["beats"]
    times = [parse_timecode(b["t"]) for b in beats]
    dur = None
    meta = data.get("meta", {})
    if isinstance(meta, dict) and "target_length_seconds" in meta:
        try:
            dur = float(meta["target_length_seconds"])
        except Exception:
            dur = None

    result: List[Tuple[Dict[str, Any], float, float]] = []
    for idx, beat in enumerate(beats):
        start = times[idx]
        if idx < len(beats) - 1:
            end = times[idx + 1]
        else:
            end = dur if (dur is not None and dur > start) else (start + 3.0)
        result.append((beat, start, end))
    return result


def make_shotlist_markdown(data: Dict[str, Any]) -> str:
    rows = ["| Start | End | Type | On-screen | UI | SFX |", "|---:|---:|---|---|---|---|"]
    for beat, start, end in compute_timeline(data):
        on_screen = str(beat.get("on_screen", "") or "")
        if len(on_screen) > 56:
            on_screen = on_screen[:53] + "..."
        ui = str(beat.get("ui_component", "") or "")
        sfx = beat.get("sfx", [])
        sfx_s = ", ".join(sfx) if isinstance(sfx, list) else ""
        rows.append(
            f"| {format_timecode(start)} | {format_timecode(end)} | {beat.get('type','')} | {on_screen} | {ui} | {sfx_s} |"
        )
    return "\n".join(rows) + "\n"


def make_manifest(data: Dict[str, Any]) -> Dict[str, Any]:
    ui_components: List[str] = []
    sfx_items: List[str] = []
    on_screen_text: List[str] = []
    overlay_snippets: List[str] = []

    has_system_vo = False
    has_human_vo = False

    for beat in data["beats"]:
        ui = beat.get("ui_component")
        if isinstance(ui, str) and ui.strip():
            ui_components.append(ui.strip())

        sfx = beat.get("sfx")
        if isinstance(sfx, list):
            for x in sfx:
                if isinstance(x, str) and x.strip():
                    sfx_items.append(x.strip())

        txt = beat.get("on_screen")
        if isinstance(txt, str) and txt.strip():
            on_screen_text.append(txt.strip())

        snip = beat.get("overlay_text_snippet")
        if isinstance(snip, str) and snip.strip():
            overlay_snippets.append(snip.strip())

        vo = beat.get("vo")
        if isinstance(vo, dict):
            if "SYSTEM" in vo:
                has_system_vo = True
            if "HUMAN" in vo:
                has_human_vo = True

    def uniq(xs: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return {
        "ui_components": uniq(ui_components),
        "sfx": uniq(sfx_items),
        "on_screen_text": on_screen_text,
        "overlay_snippets": overlay_snippets,
        "has_system_vo": has_system_vo,
        "has_human_vo": has_human_vo,
    }


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def find_ui_png(root: Path, ui_component: str) -> Optional[Path]:
    p = root / "assets" / "ui" / "png" / f"{ui_component}.png"
    return p if p.exists() else None


def find_fx_png(root: Path, name: str) -> Optional[Path]:
    p = root / "assets" / "ui" / "png" / f"{name}.png"
    return p if p.exists() else None


def find_fx_png(root: Path, name: str) -> Optional[Path]:
    p = root / "assets" / "ui" / "png" / f"{name}.png"
    return p if p.exists() else None


def _safe_mode_token(raw: Optional[str]) -> str:
    """
    Convert a user-provided mode into a stable, log-safe token:
      - uppercase
      - spaces -> underscore
      - normalize common symbol substitutions (e.g., $ -> S)
      - strip unsafe chars
      - clamp length
    """
    if not raw or not isinstance(raw, str):
        return ""

    s = raw.strip().upper().replace(" ", "_")
    # Normalize symbol substitutions before stripping non-token chars.
    # Required by tests: "Crazy!@# Symbol$" -> "CRAZY_SYMBOLS"
    s = s.replace("$", "S")
    s = re.sub(r"[^A-Z0-9_\-]+", "", s)
    return s[:24].strip("_-")


def derive_episode_mode(data: Dict[str, Any]) -> str:
    """
    Derives episode mode from YAML with safe fallbacks.
    Preferred: data["mode"]
    Alternates: meta.mode, episode.mode, season.mode, series.mode, channel.mode
    Returns a safe token, or 'MODE_UNSET' if none found.
    """
    # Preferred key
    candidates: List[Optional[str]] = []
    v = data.get("mode")
    candidates.append(v if isinstance(v, str) else None)

    # Common alternates
    for k in ("meta", "episode", "season", "series", "channel"):
        obj = data.get(k)
        if isinstance(obj, dict):
            mv = obj.get("mode")
            candidates.append(mv if isinstance(mv, str) else None)

    # Last resort: a few legacy keys
    for k in ("season_mode", "series_mode", "episode_mode"):
        v2 = data.get(k)
        candidates.append(v2 if isinstance(v2, str) else None)

    for c in candidates:
        tok = _safe_mode_token(c)
        if tok:
            return tok
    return "MODE_UNSET"


def _fade_window_seconds(seg: float, base: float = 0.18) -> float:
    """
    Chooses a tasteful fade duration that adapts to short segments.
    Keeps fades subtle and premium, never “floaty.”
    """
    seg = max(0.0, float(seg))
    f = float(base)
    if seg <= 0.0:
        return 0.06
    if seg < (2.0 * f):
        f = max(0.06, seg / 4.0)
    return f


def build_animatic_filter(
    root: Path,
    data: Dict[str, Any],
    fps: int,
    style: str,
    episode_id: str,
) -> Tuple[str, List[str]]:
    if style != "minimal_glass":
        raise RuntimeError(f"Unsupported style: {style}")

    def alpha_expr(start: float, end: float, fade: float = 0.18) -> str:
        """
        Smooth fade in/out for drawtext alpha. Uses a short fade window at start/end.
        If the segment is very short, the fade is reduced automatically.
        """
        seg = max(0.0, end - start)
        f = float(fade)
        if seg <= 0.0:
            return "0"
        if seg < (2.0 * f):
            f = max(0.06, seg / 4.0)
        st = start
        en = end
        # alpha='if(lt(t,st+f),(t-st)/f, if(gt(t,en-f),(en-t)/f, 1))'
        return (
            f"if(gt(t,{en-f:.3f}),"
            f"({en:.3f}-t)/{f:.3f},1)"
        )

    def system_log_line(beat: Dict[str, Any], idx: int, total: int, mode_default: str) -> str:
        """
        Small, caption-safe ticker line. If beat.system_log exists, use it.
        Otherwise derive a deterministic line from UI + intent.
        """
        v = beat.get("system_log")
        if isinstance(v, str) and v.strip():
            return v.strip()
        # Per-beat override (optional) with fallback to episode mode
        beat_mode_raw = beat.get("mode") if isinstance(beat.get("mode"), str) else None
        mode_tok = _safe_mode_token(beat_mode_raw) or mode_default

        ui = beat.get("ui_component")
        ui_s = ui.strip() if isinstance(ui, str) else "none"
        on = beat.get("on_screen")
        on_s = on.strip() if isinstance(on, str) else ""
        # Keep it short and “product-y”
        evt = on_s.upper()
        evt = re.sub(r"[^A-Z0-9 ]+", "", evt)[:26].strip()
        if not evt:
            evt = "POLICY STEP"
        return f"LOG {idx+1:02d}/{total:02d} | MODE={mode_tok} | UI={ui_s} | EVT={evt}"

    def wants_specular_sweep(ui: Optional[str], overlay_exists: bool) -> bool:
        if not overlay_exists or not ui:
            return False
        u = ui.strip()
        return u.startswith("popup_")

    def should_render_main_text(ui: Optional[str], overlay_exists: bool, on_screen: str) -> bool:
        """
        When an overlay exists and already conveys the main text (e.g., ACCEPT button),
        suppress redundant drawtext for a cleaner, premium look.
        """
        if not on_screen.strip():
            return False
        if not overlay_exists or not ui:
            return True

        u = ui.strip()
        txt = on_screen.strip().upper()

        # Overlays that already contain the primary label
        if u.startswith("btn_"):
            return False
        if u.startswith("toggle_"):
            return False

        # End cards are fully designed overlays; avoid duplicating large on-screen blocks
        if u in ("end_card_choice", "end_card_disclaimer"):
            return False

        # Brand corner bug should not trigger redundant text (usually none, but safe)
        if u == "brand_corner_bug_override" and len(txt) <= 28:
            return True

        # If someone accidentally sets on_screen to the same single-word button label, suppress.
        if txt in ("ACCEPT", "LATER", "ENABLE", "SYNC NOW", "VERIFY", "CONTINUE") and (u.startswith("popup_") is False):
            return True

        return True

    def should_render_sub_text(ui: Optional[str], overlay_exists: bool, snippet: str) -> bool:
        if not snippet.strip():
            return False
        if not overlay_exists or not ui:
            return True
        u = ui.strip()
        # If end card overlay exists, keep it clean.
        if u in ("end_card_choice", "end_card_disclaimer"):
            return False
        # Button/toggle overlays are minimal; snippet usually creates clutter.
        if u.startswith("btn_") or u.startswith("toggle_"):
            return False
        return True

    def choose_text_layout(ui: Optional[str], overlay_exists: bool) -> Dict[str, int]:
        """
        Returns a layout dict:
          main_x, main_y, sub_x, sub_y, main_fs, sub_fs, wrap_main, wrap_sub, draw_panel
        If overlay_exists, we avoid drawing an extra "glass panel" behind text and instead
        place text inside the overlay's expected safe region.
        """
        # Defaults (used when no UI overlay is present)
        default = {
            "main_x": 130,
            "main_y": 790,
            "sub_x": 130,
            "sub_y": 930,
            "main_fs": 56,
            "sub_fs": 34,
            "wrap_main": 34,
            "wrap_sub": 44,
            "draw_panel": 1,
        }
        if not overlay_exists or not ui:
            return default

        # Overlay present: do not draw additional panel (prevents "double glass")
        base = {
            "draw_panel": 0,
            "main_x": 180,
            "sub_x": 180,
            "main_fs": 46,
            "sub_fs": 30,
            "wrap_main": 38,
            "wrap_sub": 52,
        }

        if ui.startswith("popup_"):
            # Center popup region (keeps clear of bottom caption zone)
            return {**default, **base, "main_y": 720, "sub_y": 865}
        if ui.startswith("card_"):
            # Lower-third card region
            return {**default, **base, "main_y": 1260, "sub_y": 1400, "main_fs": 40, "sub_fs": 28, "wrap_main": 44, "wrap_sub": 56}
        if ui.startswith("timer_"):
            # Top timer UI: keep text high and smaller
            return {**default, **base, "main_y": 150, "sub_y": 260, "main_fs": 34, "sub_fs": 26, "wrap_main": 52, "wrap_sub": 64}
        if ui.startswith("btn_") or ui.startswith("toggle_"):
            # Button/toggle overlays: keep any text modest and out of the way
            return {**default, **base, "main_y": 1180, "sub_y": 1320, "main_fs": 36, "sub_fs": 26, "wrap_main": 44, "wrap_sub": 56}
        if ui == "end_card_choice":
            return {**default, **base, "main_y": 740, "sub_y": 980, "main_fs": 48, "sub_fs": 30, "wrap_main": 40, "wrap_sub": 56}
        if ui == "end_card_disclaimer":
            return {**default, **base, "main_y": 1530, "sub_y": 1620, "main_fs": 32, "sub_fs": 24, "wrap_main": 56, "wrap_sub": 68}

        return {**default, **base, "main_y": 790, "sub_y": 930}

    # Base aesthetic
    # - subtle grain
    # - faint scanlines (horizontal only via w=1080)
    # - soft vignette
    chain = [
        "format=yuv420p",
        "noise=alls=6:allf=t+u",
        "drawgrid=w=1080:h=4:t=1:c=white@0.03",
        "vignette=PI/6",
    ]

    # Default panel (used only when no UI overlay exists for the beat)
    panel_x, panel_y, panel_w, panel_h = 90, 720, 900, 360

    # Font selection: prefer config fontfile if available, else Arial (system-resolved on Windows)
    cfg = load_config(root)
    font_opt = ""
    if cfg.fontfile:
        # ffmpeg drawtext expects escaped path in filtergraph; use forward slashes
        ff_font = cfg.fontfile.replace("\\", "/")
        font_opt = f":fontfile='{ffmpeg_escape_drawtext(ff_font)}'"

    # Font selection: prefer config fontfile if available, else Arial (system-resolved on Windows)
    cfg = load_config(root)
    font_opt = ""
    if cfg.fontfile:
        # ffmpeg drawtext expects escaped path in filtergraph; use forward slashes
        ff_font = cfg.fontfile.replace("\\", "/")
        font_opt = f":fontfile='{ffmpeg_escape_drawtext(ff_font)}'"

    overlay_jobs: List[Tuple[str, str, float, float]] = []  # (tag, png_path, start, end)
    sweep_jobs: List[Tuple[str, str, float, float, float, float]] = []  # (tag, png_path, st, en, x0, x1)
    filter_parts: List[str] = []

    # Start from background source labeled [v0]
    # We'll build a single stream by appending filters.
    stream = "[0:v]"
    filter_parts.append(f"{stream}{','.join([''] + chain)}[v_base]".replace("[0:v],", "[0:v]"))
    stream = "[v_base]"

    timeline = compute_timeline(data)

    # For each beat, optionally overlay UI PNG and draw glass + text.
    total_beats = len(timeline)
    episode_mode = derive_episode_mode(data)
    for idx, (beat, start, end) in enumerate(timeline):
        enable = f"between(t,{start:.3f},{end:.3f})"
        step_in = stream
        overlay_exists = False
        ui_name = None

        # Optional UI overlay (full-frame PNG)
        ui_comp = beat.get("ui_component")
        if isinstance(ui_comp, str) and ui_comp.strip():
            ui_name = ui_comp.strip()
            ui_png = find_ui_png(root, ui_name)
            if ui_png:
                overlay_exists = True
                tag = f"ui{idx}"
                p = str(ui_png).replace("\\", "/")
                overlay_jobs.append((tag, p, start, end))
                # Overlay at (0,0)
                out = f"[v_ui_{idx}]"
                filter_parts.append(
                    f"{step_in}[{tag}]overlay=x=0:y={0}:enable='{enable}'{out}"
                )
                step_in = out

                # Specular sweep (popup_* only): composited over the popup window area.
                if wants_specular_sweep(ui_name, overlay_exists):
                    fx = find_fx_png(root, "_specular_sweep_popup")
                    if fx:
                        # Sweep timing: short, premium
                        seg = max(0.0, end - start)
                        dur = min(0.70, max(0.28, seg * 0.55))
                        st = start + 0.04
                        en = min(end, st + dur)
                        # Travel across popup window: x from slightly off-left to slightly off-right
                        x0 = 120.0 - 460.0
                        x1 = 120.0 + 220.0
                        sweep_tag = f"sweep{idx}"
                        sweep_jobs.append((sweep_tag, str(fx).replace("\\", "/"), st, en, x0, x1))
                        out2 = f"[v_sweep_{idx}]"
                        # Move sweep layer during its own window only
                        xexpr = f"'if(lt(t,{en:.3f}),{x0:.3f}+((t-{st:.3f})/{max(0.001, (en-st)):.3f})*{(x1-x0):.3f},{x1:.3f})'"
                        filter_parts.append(
                            f"{step_in}[{sweep_tag}]overlay=x={xexpr}:y=560:enable='between(t,{st:.3f},{en:.3f})':format=auto{out2}"
                        )
                        step_in = out2

        layout = choose_text_layout(ui_name, overlay_exists)

        # Only draw the CLI "glass panel" when no UI overlay exists (prevents double-glass look)
        if int(layout["draw_panel"]) == 1:
            out_panel = f"[v_panel_{idx}]"
            filter_parts.append(
                f"{step_in}drawbox=x={panel_x}:y={panel_y}:w={panel_w}:h={panel_h}:color=white@0.06:t=fill:enable='{enable}'{out_panel}"
            )
            step_in = out_panel

        # Main on_screen text
        on_screen = beat.get("on_screen")
        if isinstance(on_screen, str):
            on_screen_s = on_screen.strip()
            if should_render_main_text(ui_name, overlay_exists, on_screen_s):
                wrapped = wrap_text(on_screen_s, width=int(layout["wrap_main"]), max_lines=2)
                txt = ffmpeg_escape_drawtext(wrapped)
                out_txt = f"[v_txt_{idx}]"
                aexpr = alpha_expr(start, end)
                filter_parts.append(
                    f"{step_in}drawtext=text='{txt}':expansion=none{font_opt}:x={int(layout['main_x'])}:y={int(layout['main_y'])}:fontsize={int(layout['main_fs'])}:fontcolor=white@0.92:borderw=2:bordercolor=black@0.35:shadowx=2:shadowy=2:shadowcolor=black@0.45:line_spacing=14:alpha='{aexpr}':enable='{enable}'{out_txt}"
                )
                step_in = out_txt

        # Secondary overlay snippet
        snip = beat.get("overlay_text_snippet")
        if isinstance(snip, str):
            snip_s = snip.strip()
            if should_render_sub_text(ui_name, overlay_exists, snip_s):
                wrapped2 = wrap_text(snip_s, width=int(layout["wrap_sub"]), max_lines=2)
                txt2 = ffmpeg_escape_drawtext(wrapped2)
                out_snip = f"[v_snip_{idx}]"
                aexpr2 = alpha_expr(start, end)
                filter_parts.append(
                    f"{step_in}drawtext=text='{txt2}':expansion=none{font_opt}:x={int(layout['sub_x'])}:y={int(layout['sub_y'])}:fontsize={int(layout['sub_fs'])}:fontcolor=white@0.72:borderw=1:bordercolor=black@0.25:shadowx=1:shadowy=1:shadowcolor=black@0.35:line_spacing=10:alpha='{aexpr2}':enable='{enable}'{out_snip}"
                )
                step_in = out_snip

        # System log ticker (caption-safe). Always last so it stays on top.
        log_line = system_log_line(beat, idx, total_beats, episode_mode)
        if isinstance(log_line, str) and log_line.strip():
            out_log = f"[v_log_{idx}]"
            log_txt = ffmpeg_escape_drawtext(log_line)
            aexpr = alpha_expr(start, end, fade=0.14)
            # y=1600 keeps it above bottom caption zone (1920-288=1632)
            filter_parts.append(
                f"{step_in}drawtext=text='{log_txt}':expansion=none{font_opt}:"
                f"x=60:y=1600:fontsize=22:fontcolor=white@0.65:"
                f"borderw=2:bordercolor=black@0.35:shadowx=1:shadowy=1:shadowcolor=black@0.35:"
                f"box=1:boxcolor=black@0.22:boxborderw=10:alpha='{aexpr}':enable='{enable}'{out_log}"
            )
            step_in = out_log

        # Watermark bug (optional): if first beat has brand corner bug overlay only
        stream = step_in

    # Ensure final stream is yuv420p for broad compatibility
    filter_parts.append(f"{stream}format=yuv420p[vout]")

    # Build overlay sources (as looping image streams) with per-beat fade-in/out on alpha.
    overlay_filters: List[str] = []
    for (tag, p, start, end) in overlay_jobs:
        seg = max(0.0, end - start)
        f = _fade_window_seconds(seg, base=0.18)
        fade_out_st = max(start, end - f)
        p_esc = ffmpeg_escape_drawtext(p)
        overlay_filters.append(
            f"movie='{p_esc}',"
            f"format=rgba,scale=1080:1920,"
            f"loop=loop=-1:size=1:start=0,"
            f"setpts=N/({int(fps)}*TB),"
            f"fade=t=in:st={start:.3f}:d={f:.3f}:alpha=1,"
            f"fade=t=out:st={fade_out_st:.3f}:d={f:.3f}:alpha=1"
            f"[{tag}]"
        )

    # Specular sweep streams (popup FX)
    for (tag, p, st, en, _x0, _x1) in sweep_jobs:
        seg = max(0.0, en - st)
        f = min(0.14, max(0.08, seg / 3.0))
        fade_out_st = max(st, en - f)
        p_esc = ffmpeg_escape_drawtext(p)
        overlay_filters.append(
            f"movie='{p_esc}',"
            f"format=rgba,"
            f"loop=loop=-1:size=1:start=0,"
            f"setpts=N/({int(fps)}*TB),"
            f"fade=t=in:st={st:.3f}:d={f:.3f}:alpha=1,"
            f"fade=t=out:st={fade_out_st:.3f}:d={f:.3f}:alpha=1"
            f"[{tag}]"
        )

    filter_complex = ";".join(overlay_filters + filter_parts)

    return filter_complex, ["-map", "[vout]"]


def run_ffmpeg(cmd: List[str]) -> int:
    try:
        # User requested robust Windows invocation via cmd /c for standard binaries
        # shell=True is risky and can be flaky with some escaping.
        if sys.platform == "win32" and (cmd[0].lower().endswith(".bat") or cmd[0].lower().endswith(".cmd")):
            # wrap: ['cmd', '/c', cmd[0], ...rest]
            new_cmd = ["cmd", "/c"] + cmd
            proc = subprocess.run(new_cmd, check=False)
        else:
            proc = subprocess.run(cmd, check=False)
        return int(proc.returncode)
    except FileNotFoundError:
        return 127


def cmd_validate(args: argparse.Namespace) -> int:
    root = repo_root()
    path = Path(args.episode_yaml).resolve()
    data = load_yaml(path)
    validate_episode(data, context=str(path))
    print(f"OK: {path}")
    return 0


def cmd_shotlist(args: argparse.Namespace) -> int:
    path = Path(args.episode_yaml).resolve()
    data = load_yaml(path)
    validate_episode(data, context=str(path))
    out = Path(args.out).resolve()
    ensure_dir(out.parent)
    out.write_text(make_shotlist_markdown(data), encoding="utf-8")
    print(f"Wrote: {out}")
    return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    path = Path(args.episode_yaml).resolve()
    data = load_yaml(path)
    validate_episode(data, context=str(path))
    out = Path(args.out).resolve()
    ensure_dir(out.parent)
    out.write_text(json.dumps(make_manifest(data), indent=2), encoding="utf-8")
    print(f"Wrote: {out}")
    return 0


def cmd_init_episode(args: argparse.Namespace) -> int:
    root = repo_root()
    ep = args.episode_id.strip()
    if not re.match(r"^[A-Z0-9_]+$", ep):
        die("episode_id must allow alphanumeric+underscore")
    ypath = Path(args.episode_yaml).resolve()
    data = load_yaml(ypath)
    validate_episode(data, context=str(ypath))

    render_dir = root / "renders" / "season01_housing_mode" / ep
    ensure_dir(render_dir)

    shot_out = render_dir / "shotlist.md"
    man_out = render_dir / "asset_manifest.json"
    shot_out.write_text(make_shotlist_markdown(data), encoding="utf-8")
    man_out.write_text(json.dumps(make_manifest(data), indent=2), encoding="utf-8")

    print(f"Initialized: {render_dir}")
    print(f"- {shot_out.name}")
    print(f"- {man_out.name}")
    return 0


def cmd_animatic(args: argparse.Namespace) -> int:
    root = repo_root()
    cfg = load_config(root)

    ep = args.episode_id.strip()
    if not re.match(r"^[A-Z0-9_]+$", ep):
        die("episode_id must allow alphanumeric+underscore (e.g. S01E01 or S01E01_SHORT1)")

    ypath = Path(args.episode_yaml).resolve()
    data = load_yaml(ypath)
    validate_episode(data, context=str(ypath))

    fps = int(args.fps or cfg.default_fps or 30)
    if fps <= 0:
        fps = 30

    # Determine duration
    meta = data.get("meta", {})
    dur = None
    if isinstance(meta, dict) and "target_length_seconds" in meta:
        try:
            dur = float(meta["target_length_seconds"])
        except Exception:
            dur = None
    if dur is None:
        timeline = compute_timeline(data)
        dur = max(end for _, _, end in timeline)

    render_dir = root / "renders" / "season01_housing_mode" / ep
    ensure_dir(render_dir)
    out_mp4 = render_dir / "animatic.mp4"

    # Video source
    ffmpeg = cfg.ffmpeg
    bg = f"color=c=#070A0D:s=1080x1920:r={fps}:d={dur:.3f}"

    # Audio: VO or silent
    inputs: List[str] = ["-f", "lavfi", "-i", bg]
    map_audio: List[str] = []
    if args.vo:
        vo = Path(args.vo).resolve()
        if not vo.exists():
            die(f"VO file not found: {vo}")
        inputs += ["-i", str(vo)]
        map_audio = ["-map", "1:a", "-c:a", "aac", "-b:a", "192k"]
    else:
        inputs += ["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={dur:.3f}"]
        map_audio = ["-map", "1:a", "-c:a", "aac", "-b:a", "192k"]

    filter_complex, map_video = build_animatic_filter(
        root=root,
        data=data,
        fps=fps,
        style=str(args.style or "minimal_glass"),
        episode_id=ep,
    )

    cmd: List[str] = [
        ffmpeg,
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        *map_video,
        *map_audio,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-movflags",
        "+faststart",
        "-shortest",
        str(out_mp4),
    ]

    print("FFmpeg command:")
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd))

    if args.run:
        rc = run_ffmpeg(cmd)
        if rc != 0:
            die(f"FFmpeg failed with exit code {rc}", code=rc)
        print(f"Wrote: {out_mp4}")
        return 0

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tho", description="The Human Override tooling CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate an episode YAML")
    p_val.add_argument("episode_yaml")
    p_val.set_defaults(fn=cmd_validate)

    p_init = sub.add_parser("init-episode", help="Create per-episode render folder + outputs")
    p_init.add_argument("episode_id", help="Example: S01E01")
    p_init.add_argument("--episode-yaml", required=True)
    p_init.set_defaults(fn=cmd_init_episode)

    p_shot = sub.add_parser("shotlist", help="Generate shotlist markdown")
    p_shot.add_argument("episode_yaml")
    p_shot.add_argument("--out", required=True)
    p_shot.set_defaults(fn=cmd_shotlist)

    p_man = sub.add_parser("manifest", help="Generate asset manifest json")
    p_man.add_argument("episode_yaml")
    p_man.add_argument("--out", required=True)
    p_man.set_defaults(fn=cmd_manifest)

    p_anim = sub.add_parser("animatic", help="Generate a styled animatic MP4 from YAML")
    p_anim.add_argument("episode_id", help="Example: S01E01")
    p_anim.add_argument("--episode-yaml", required=True)
    p_anim.add_argument("--vo", default="", help="Optional: path to vo_mix.wav")
    p_anim.add_argument("--fps", default="", help="Default 30")
    p_anim.add_argument("--style", default="minimal_glass", choices=["minimal_glass"])
    p_anim.add_argument("--run", action="store_true", help="Execute ffmpeg")
    p_anim.set_defaults(fn=cmd_animatic)

    return p


def main(argv: Sequence[str]) -> int:
    root = repo_root()
    # Provide a gentle hint if config.local.json missing
    if not (root / "config.local.json").exists():
        print("Note: config.local.json not found. Using defaults. Copy config.local.example.json to config.local.json and set ffmpeg path for --run.", file=sys.stderr)

    parser = build_parser()
    args = parser.parse_args(list(argv))
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
