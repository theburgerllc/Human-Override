# Tooling CLI (tools/tho.py)

## Setup
1) Copy:
- `config.local.example.json` → `config.local.json`
2) Set `ffmpeg` path in `config.local.json`.
3) Run:
- `tools\\setup_venv_windows.bat`

## Validate
- `.venv\\Scripts\\python tools\\tho.py validate episodes\\season01_housing_mode\\ep01.yaml`

## Initialize render folder + generate outputs
- `.venv\\Scripts\\python tools\\tho.py init-episode S01E01 --episode-yaml episodes\\season01_housing_mode\\ep01.yaml`

Creates:
- `renders\\season01_housing_mode\\S01E01\\shotlist.md`
- `renders\\season01_housing_mode\\S01E01\\asset_manifest.json`

## Generate animatic
- `.venv\\Scripts\\python tools\\tho.py animatic S01E01 --episode-yaml episodes\\season01_housing_mode\\ep01.yaml --run`

Optional VO:
- `.venv\\Scripts\\python tools\\tho.py animatic S01E01 --episode-yaml episodes\\season01_housing_mode\\ep01.yaml --vo renders\\season01_housing_mode\\S01E01\\vo_mix.wav --run`

## UI overlays
If a beat references `ui_component`, the animatic will overlay:
- `assets\\ui\\png\\<ui_component>.png` (if it exists)

Export SVG → PNG overlays:
- Configure `scripts\\_config.bat` from example
- Run `scripts\\export_ui_assets.bat`
