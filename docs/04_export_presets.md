# Export Presets

## Animatic (CLI)
- Output: `renders/.../animatic.mp4`
- H.264 + AAC, 1080x1920, 30fps default

## Kdenlive export (intermediate)
- Filename: `edit_export.mp4`
- H.264, high quality
- Final normalization is done by FFmpeg script

## Final delivery (FFmpeg)
- `final_clean.mp4` (normalized)
- optional `final_burned.mp4` (captions burned in)

## Caption guidelines
- Large and readable
- Break lines aggressively to match pace
