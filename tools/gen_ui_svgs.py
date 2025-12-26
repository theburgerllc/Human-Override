from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


UI_COMPONENTS: List[str] = [
    "brand_corner_bug_override",
    "popup_confirm_savings",
    "timer_15s",
    "btn_accept",
    "card_risk_signal",
    "card_rate_flip",
    "popup_appeal_available",
    "card_smart_lock_limited",
    "end_card_choice",
    "end_card_disclaimer",
    "popup_safety_sync_required",
    "timer_bar",
    "btn_later",
    "card_access_denied",
    "popup_verify_identity",
    "card_anomaly_detected",
    "card_review_eta",
    "popup_policy_update",
    "toggle_wellness",
    "card_tenant_score",
    "popup_stability_plan",
    "card_deposit_adjustment_pending",
    "popup_enable_context_access",
    "card_stability_index",
    "popup_processing_fee",
    "popup_deposit_hold",
    "card_correlation_threshold",
    "popup_opt_out_fee",
    "card_neighborhood_safety",
    "card_guest_recognition",
    "card_coverage_exclusion",
    "card_residence_not_confirmed",
]

FX_SWEEP_SVG_NAME = "_specular_sweep_popup"  # exported to assets/ui/png/_specular_sweep_popup.png


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def svg_header() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg width="1080" height="1920" viewBox="0 0 1080 1920" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="glassGrad" x1="0" y1="0" x2="1080" y2="1920" gradientUnits="userSpaceOnUse">
      <stop stop-color="white" stop-opacity="0.08"/>
      <stop offset="1" stop-color="white" stop-opacity="0.03"/>
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="black" flood-opacity="0.55"/>
    </filter>
    <filter id="microGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="0" stdDeviation="2.5" flood-color="white" flood-opacity="0.12"/>
    </filter>
    <style>
      .font { font-family: Inter, Segoe UI, Arial, sans-serif; }
      .h1 { font-size: 42px; font-weight: 700; letter-spacing: 0.5px; }
      .h2 { font-size: 28px; font-weight: 600; letter-spacing: 0.4px; }
      .body { font-size: 22px; font-weight: 400; letter-spacing: 0.2px; }
      .micro { font-size: 18px; font-weight: 500; letter-spacing: 0.25px; }
      .muted { fill: rgba(255,255,255,0.62); }
      .white { fill: rgba(255,255,255,0.92); }
      .stroke { stroke: rgba(255,255,255,0.16); }
    </style>
  </defs>
"""


def glass_card(x: int, y: int, w: int, h: int, radius: int = 28) -> str:
    return f"""
  <g filter="url(#softShadow)">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="url(#glassGrad)" />
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" class="stroke" fill="none"/>
  </g>
"""


def pill(x: int, y: int, w: int, h: int, label: str) -> str:
    return f"""
  <g filter="url(#microGlow)">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h//2}" fill="rgba(255,255,255,0.10)" class="stroke"/>
    <text x="{x + 18}" y="{y + int(h*0.70)}" class="font micro white">{esc(label)}</text>
  </g>
"""


def button(x: int, y: int, w: int, h: int, label: str) -> str:
    return f"""
  <g filter="url(#microGlow)">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h//2}" fill="rgba(255,255,255,0.14)" class="stroke"/>
    <text x="{x + w/2}" y="{y + int(h*0.68)}" text-anchor="middle" class="font h2 white">{esc(label)}</text>
  </g>
"""


def corner_bug() -> str:
    # Top-left bug: subtle, premium, not OS-like.
    return f"""
  <g>
    {pill(46, 54, 360, 58, "THE HUMAN OVERRIDE")}
    <circle cx="424" cy="83" r="10" fill="rgba(255,255,255,0.75)"/>
    <circle cx="452" cy="83" r="10" fill="rgba(255,255,255,0.35)"/>
  </g>
"""


def timer_top(style: str) -> str:
    # A thin top timer bar and label.
    bar_y = 112
    label = "OFFER EXPIRES" if style == "timer_15s" else "COMPLIANCE WINDOW"
    return f"""
  <g>
    {pill(318, 54, 444, 58, label)}
    <rect x="140" y="{bar_y}" width="800" height="14" rx="7" fill="rgba(255,255,255,0.10)"/>
    <rect x="140" y="{bar_y}" width="520" height="14" rx="7" fill="rgba(255,255,255,0.22)"/>
  </g>
"""


def popup_center(title: str, subtitle: str, primary: str, secondary: str) -> str:
    # Center popup, leaves plenty of negative space around.
    x, y, w, h = 120, 560, 840, 520
    return f"""
  {glass_card(x, y, w, h)}
  <text x="{x+44}" y="{y+86}" class="font h2 white">{esc(title)}</text>
  <text x="{x+44}" y="{y+138}" class="font body muted">{esc(subtitle)}</text>

  {button(x+44, y+356, 752, 86, primary)}
  <text x="{x+44}" y="{y+476}" class="font micro muted">{esc(secondary)}</text>
"""


def card_lower(title: str, subtitle: str, tag: str = "STATUS") -> str:
    # Lower-third card to avoid fighting the CLI drawtext block.
    x, y, w, h = 120, 1180, 840, 360
    return f"""
  {glass_card(x, y, w, h)}
  {pill(x+44, y+40, 180, 46, tag)}
  <text x="{x+44}" y="{y+140}" class="font h2 white">{esc(title)}</text>
  <text x="{x+44}" y="{y+196}" class="font body muted">{esc(subtitle)}</text>
  <rect x="{x+44}" y="{y+250}" width="752" height="2" fill="rgba(255,255,255,0.10)"/>
  <text x="{x+44}" y="{y+308}" class="font micro muted">SOURCE: LOCAL POLICY ENGINE</text>
"""


def end_choice() -> str:
    x, y, w, h = 120, 520, 840, 740
    return f"""
  {glass_card(x, y, w, h)}
  <text x="{x+44}" y="{y+92}" class="font h2 white">CHOOSE</text>
  <text x="{x+44}" y="{y+146}" class="font body muted">A or B decides tomorrow.</text>

  {pill(x+44, y+210, 140, 46, "OPTION A")}
  <text x="{x+44}" y="{y+280}" class="font body white">Instant relief.</text>
  <text x="{x+44}" y="{y+324}" class="font micro muted">Trade: deeper access.</text>

  {pill(x+44, y+392, 140, 46, "OPTION B")}
  <text x="{x+44}" y="{y+462}" class="font body white">Human review.</text>
  <text x="{x+44}" y="{y+506}" class="font micro muted">Trade: time + uncertainty.</text>

  {button(x+44, y+590, 752, 92, "COMMENT A OR B")}
"""


def end_disclaimer() -> str:
    # Place above caption zone, still near bottom.
    x, y, w, h = 120, 1470, 840, 260
    return f"""
  {glass_card(x, y, w, h)}
  <text x="{x+44}" y="{y+92}" class="font body white">Fictional scenario.</text>
  <text x="{x+44}" y="{y+144}" class="font micro muted">Inspired by real tech trends. No real persons.</text>
  <text x="{x+44}" y="{y+196}" class="font micro muted">For entertainment and commentary only.</text>
"""


def single_button_overlay(label: str) -> str:
    return f"""
  <g>
    {button(294, 1320, 492, 98, label)}
  </g>
"""


def toggle_overlay(label: str) -> str:
    # Minimal toggle at lower-third.
    x, y = 120, 1160
    return f"""
  {glass_card(x, y, 840, 320)}
  <text x="{x+44}" y="{y+110}" class="font h2 white">{esc(label)}</text>
  <rect x="{x+44}" y="{y+170}" width="160" height="54" rx="27" fill="rgba(255,255,255,0.10)" class="stroke"/>
  <circle cx="{x+44+124}" cy="{y+197}" r="20" fill="rgba(255,255,255,0.28)"/>
  <text x="{x+220}" y="{y+206}" class="font micro muted">ON</text>
"""


def specular_sweep_svg() -> str:
    """
    Transparent PNG exported from this SVG is used as an animated “specular sweep”
    over popup glass (composited in FFmpeg with motion + alpha fades).
    Canvas: 1200x520 (designed to cover the 840x520 popup window with room to travel).
    """
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg width="1200" height="520" viewBox="0 0 1200 520" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="sweep" x1="0" y1="0" x2="1200" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0.00" stop-color="white" stop-opacity="0.00"/>
      <stop offset="0.40" stop-color="white" stop-opacity="0.00"/>
      <stop offset="0.48" stop-color="white" stop-opacity="0.10"/>
      <stop offset="0.50" stop-color="white" stop-opacity="0.18"/>
      <stop offset="0.52" stop-color="white" stop-opacity="0.10"/>
      <stop offset="0.60" stop-color="white" stop-opacity="0.00"/>
      <stop offset="1.00" stop-color="white" stop-opacity="0.00"/>
    </linearGradient>
    <filter id="blur" x="-20%" y="-40%" width="140%" height="180%">
      <feGaussianBlur stdDeviation="10"/>
    </filter>
  </defs>
  <!-- Large rotated band so it reads as a premium diagonal specular highlight -->
  <g filter="url(#blur)">
    <rect x="-600" y="-420" width="2400" height="1360" fill="url(#sweep)" transform="rotate(-18 600 260)"/>
  </g>
</svg>
"""


def make_svg_for(name: str) -> str:
    # Map to sane defaults.
    if name == "brand_corner_bug_override":
        body = corner_bug()

    elif name in ("timer_15s", "timer_bar"):
        body = corner_bug() + timer_top(name)

    elif name.startswith("popup_"):
        title_map: Dict[str, str] = {
            "popup_confirm_savings": "CONTEXT ACCESS",
            "popup_appeal_available": "APPEAL OPTIONS",
            "popup_safety_sync_required": "SAFETY SYNC",
            "popup_verify_identity": "VERIFY IDENTITY",
            "popup_policy_update": "POLICY UPDATE",
            "popup_stability_plan": "STABILITY PLAN",
            "popup_enable_context_access": "CONTEXT ACCESS",
            "popup_processing_fee": "PROCESSING FEE",
            "popup_deposit_hold": "DEPOSIT HOLD",
            "popup_opt_out_fee": "OPT OUT",
        }
        subtitle_map: Dict[str, str] = {
            "popup_confirm_savings": "Enable access to prevent fraud.",
            "popup_appeal_available": "Choose speed or privacy.",
            "popup_safety_sync_required": "Sync to maintain access.",
            "popup_verify_identity": "Face, voice, or trusted contacts.",
            "popup_policy_update": "Terms updated for safety and fairness.",
            "popup_stability_plan": "Auto-pay and always-on verification.",
            "popup_enable_context_access": "Required to confirm eligibility.",
            "popup_processing_fee": "Manual review requires a fee.",
            "popup_deposit_hold": "Funds temporarily unavailable.",
            "popup_opt_out_fee": "Opting out requires inspection + fee.",
        }
        primary_map: Dict[str, str] = {
            "popup_confirm_savings": "ENABLE",
            "popup_appeal_available": "VIEW OPTIONS",
            "popup_safety_sync_required": "SYNC NOW",
            "popup_verify_identity": "VERIFY",
            "popup_policy_update": "ACKNOWLEDGE",
            "popup_stability_plan": "ACTIVATE",
            "popup_enable_context_access": "ENABLE",
            "popup_processing_fee": "CONTINUE",
            "popup_deposit_hold": "VERIFY SOURCE",
            "popup_opt_out_fee": "REQUEST OPT OUT",
        }
        title = title_map.get(name, "NOTICE")
        subtitle = subtitle_map.get(name, "Action required.")
        primary = primary_map.get(name, "CONTINUE")
        secondary = "Secondary action may delay resolution."
        body = corner_bug() + popup_center(title, subtitle, primary, secondary)

    elif name.startswith("card_"):
        title_map: Dict[str, str] = {
            "card_risk_signal": "RISK SIGNAL DETECTED",
            "card_rate_flip": "RATE UPDATED",
            "card_smart_lock_limited": "ACCESS: TEMP LIMITED",
            "card_access_denied": "ACCESS DENIED",
            "card_anomaly_detected": "ANOMALY DETECTED",
            "card_review_eta": "REVIEW ETA",
            "card_tenant_score": "TENANT SCORE",
            "card_deposit_adjustment_pending": "DEPOSIT ADJUSTMENT",
            "card_stability_index": "STABILITY INDEX",
            "card_correlation_threshold": "THRESHOLD EXCEEDED",
            "card_neighborhood_safety": "SAFETY MODE",
            "card_guest_recognition": "GUEST EVENT",
            "card_coverage_exclusion": "COVERAGE EXCLUSION",
            "card_residence_not_confirmed": "RESIDENCE STATUS",
        }
        subtitle_map: Dict[str, str] = {
            "card_risk_signal": "A predictive signal was triggered.",
            "card_rate_flip": "Terms changed after evaluation.",
            "card_smart_lock_limited": "Entry may require verification.",
            "card_access_denied": "Attempt blocked by policy engine.",
            "card_anomaly_detected": "Variance detected in recent activity.",
            "card_review_eta": "Queue time depends on cooperation.",
            "card_tenant_score": "Risk adjustment pending.",
            "card_deposit_adjustment_pending": "Additional conditions may apply.",
            "card_stability_index": "Stability can be restored via plan.",
            "card_correlation_threshold": "Multiple signals crossed threshold.",
            "card_neighborhood_safety": "Routing and access rules updated.",
            "card_guest_recognition": "Unregistered visitor detected.",
            "card_coverage_exclusion": "Coverage changed due to guest policy.",
            "card_residence_not_confirmed": "Final confirmation window active.",
        }
        title = title_map.get(name, "STATUS")
        subtitle = subtitle_map.get(name, "Policy evaluation complete.")
        body = corner_bug() + card_lower(title, subtitle)

    elif name.startswith("btn_"):
        label = "ACCEPT" if name == "btn_accept" else "LATER"
        body = corner_bug() + single_button_overlay(label)

    elif name.startswith("toggle_"):
        body = corner_bug() + toggle_overlay("WELLNESS INTEGRATION")

    elif name == "end_card_choice":
        body = corner_bug() + end_choice()

    elif name == "end_card_disclaimer":
        body = corner_bug() + end_disclaimer()

    else:
        body = corner_bug() + card_lower("NOTICE", "Placeholder overlay")

    return svg_header() + body + "\n</svg>\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Minimal Apple-black glass SVG overlays for ui_component keys.")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files.")
    ap.add_argument("--only", default="", help="Generate only one ui_component name.")
    args = ap.parse_args()

    root = repo_root()
    out_dir = root / "assets" / "ui" / "svg"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Always ensure the specular sweep asset exists.
    fx_svg = out_dir / f"{FX_SWEEP_SVG_NAME}.svg"
    if (not fx_svg.exists()) or args.force:
        fx_svg.write_text(specular_sweep_svg(), encoding="utf-8")

    names = UI_COMPONENTS
    if args.only.strip():
        names = [args.only.strip()]

    created = 0
    skipped = 0

    for name in names:
        out = out_dir / f"{name}.svg"
        if out.exists() and not args.force:
            skipped += 1
            continue
        out.write_text(make_svg_for(name), encoding="utf-8")
        created += 1

    print(f"SVG overlays: created={created}, skipped={skipped}, dir={out_dir}")
    print(f"FX asset ensured: {fx_svg.name}")
    if skipped:
        print("Tip: re-run with --force to overwrite existing overlays.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
