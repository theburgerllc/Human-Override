
import os
import sys
import shutil
from pathlib import Path
from typing import Optional

# Configuration precedence: ENV > Config > PATH
# We will reuse the logic from tho.py but print explicitly what is found.

def resolve_tool(name: str, env_var: str, config_val: Optional[str]) -> str:
    # 1. ENV
    if os.environ.get(env_var):
        return f"[ENV] {os.environ[env_var]}"
    
    # 2. Config (simulated)
    if config_val:
        return f"[CONFIG] {config_val}"
    
    # 3. PATH
    path_exe = shutil.which(name)
    if path_exe:
        return f"[PATH] {path_exe}"
    
    return "[MISSING]"

def main():
    print("=== Environment Diagnostics ===")
    print(f"Python: {sys.executable}")
    
    # Simulate loading config just to check keys (we won't duplicate all tho.py logic, just read json if exists)
    import json
    cfg_path = Path("config.local.json")
    cfg_data = {}
    if cfg_path.exists():
        try:
            cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
            print(f"Config: Found {cfg_path}")
        except Exception as e:
            print(f"Config: Error reading {cfg_path}: {e}")
    else:
        print("Config: Not found (config.local.json)")

    # Check FFMPEG
    ff_env = os.environ.get("FFMPEG")
    ff_cfg = cfg_data.get("ffmpeg")
    print(f"FFMPEG Precedence:")
    print(f"  ENV:    {ff_env or '(unset)'}")
    print(f"  CONFIG: {ff_cfg or '(unset)'}")
    print(f"  PATH:   {shutil.which('ffmpeg') or '(not in PATH)'}")
    
    # Check INKSCAPE
    ink_env = os.environ.get("INKSCAPE")
    # INKSCAPE is usually handled by export_ui_assets.bat, not tho.py config, but let's check basic availability
    print(f"INKSCAPE Precedence (used in export_ui_assets.bat):")
    print(f"  ENV:    {ink_env or '(unset)'}")
    print(f"  PATH:   {shutil.which('inkscape') or '(not in PATH)'}")

    # Check FONTFILE
    font_env = os.environ.get("FONTFILE")
    font_cfg = cfg_data.get("fontfile")
    print(f"FONTFILE Precedence:")
    print(f"  ENV:    {font_env or '(unset)'}")
    print(f"  CONFIG: {font_cfg or '(unset)'}")

    # Check Mocks
    use_mocks = os.environ.get("USE_MOCKS")
    print(f"USE_MOCKS: {use_mocks or '(unset)'}")
    
    print("===============================")
    
    # Fail-fast check logic simulation
    final_ffmpeg = ff_env or ff_cfg or shutil.which("ffmpeg") or "ffmpeg"
    final_inkscape = ink_env or shutil.which("inkscape") or "inkscape"
    
    print(f"RESOLVED FFMPEG:   {final_ffmpeg}")
    print(f"RESOLVED INKSCAPE: {final_inkscape}")
    
    if use_mocks == "1":
        print("RESULT: MOCK MODE ACTIVE. Missing real tools is acceptable.")
    else:
        missing = []
        if not shutil.which(final_ffmpeg) and not  Path(final_ffmpeg).exists():
             # Simple existence check for absolute paths or PATH resolution
             if not shutil.which(final_ffmpeg):
                 missing.append(f"FFmpeg ({final_ffmpeg})")
        
        # Inkscape typically tricky to check if it's just 'inkscape' and not in path vs absolute
        # But we can try
        if not shutil.which(final_inkscape) and not Path(final_inkscape).exists():
             if not shutil.which(final_inkscape):
                 missing.append(f"Inkscape ({final_inkscape})")
        
        if missing:
             print(f"RESULT: FAIL. Real tools missing: {', '.join(missing)}")
             sys.exit(1)
        else:
             print("RESULT: PASS. Real tools appear resolvable (or at least paths are set).")
             sys.exit(0)

if __name__ == "__main__":
    main()
