import sys
import shutil
from pathlib import Path

def main():
    # minimalist mock: find the last argument that looks like a file path and touch it.
    # tho.py calls: -f lavfi -i ... [filters] -map ... out.mp4
    # thumb.py calls: ... out.png
    # mock_ui_assets calls: ... out.png
    
    args = sys.argv[1:]
    if "-version" in args:
        print("ffmpeg version MOCK-2025-12-23")
        return 0
        
    # Naive assumption: last arg is output.
    if not args:
        return 1
        
    out = Path(args[-1])
    # Ensure parent exists
    if not out.parent.exists():
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
            
    # Create empty file
    with open(out, 'wb') as f:
        f.write(b'\x00' * 1024) # 1KB dummy
        
    print(f"[available in environment] Mock FFmpeg created: {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
