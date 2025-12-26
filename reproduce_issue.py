
import sys
import traceback
from pathlib import Path
from tools.tho import build_animatic_filter

try:
    print("Starting reproduction...")
    data = {
        "mode": "TEST",
        "beats": [
            {"t": "00:00.0", "type": "popup", "ui_component": "x", "on_screen": "y", "duration_s": 5.0}
        ]
    }
    build_animatic_filter(Path("."), data, 30, "minimal_glass", "S01E01")
    print("Success!")
except Exception:
    with open("repro_error.txt", "w") as f:
        traceback.print_exc(file=f)
    print("Failed. Traceback written to repro_error.txt")
