# Release Checklist

## 1. Environment Prep
- [ ] Clean git status: `git status` should be clean.
- [ ] Environment Variables: Ensure keys are set in `.env` (if applicable) or `config.local.json` matches prod settings.

## 2. Dependencies
- [ ] Run Diagnostics: `scripts\check_prereqs.bat` (Ensure result says PASS)
- [ ] Update dependencies: `pip install -r tools/requirements.txt`
- [ ] Check FFmpeg version: `ffmpeg -version`
- [ ] Check Inkscape (if using SVG pipeline): `inkscape --version`

## 3. Verification
- [ ] Run full pipeline on test episode:
  scripts\make_all.bat tests\golden.yaml S00E00
  ```
- [ ] Manual Check:
  - [ ] Watch `renders/season01_housing_mode/TEST_RELEASE_01/animatic.mp4`
  - [ ] Check `outputs/thumbs/TEST_RELEASE_01.png`
  - [ ] Check shorts in `outputs/_tmp_shorts/`
- [ ] Run Automated Tests:
  ```bat
  python -m pytest tests/test_p0_suite.py
  ```

## 4. Artifact Commit
- [ ] Commit any changed SVGs or PNGs (if policy allows checking in binaries).
- [ ] Tag version: `git tag vX.Y.Z`
- [ ] Push to main.

## 5. Deployment
- [ ] Sync `renders/` to target storage/shared drive.
- [ ] Ingest shotlists into editing software if needed.
