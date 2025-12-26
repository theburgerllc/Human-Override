# Episode YAML Schema (Show Control File)

Each episode YAML contains:
- `meta`: identifiers, length, tone, disclaimer
- `packaging`: titles, hook, end prompt
- `characters`: list of voice profiles
- `beats`: timecoded events

Timecode format:
- `MM:SS.s` (example: `00:14.0`)

Beat types (recommended):
- HOOK_BENEFIT
- ASK_PERMISSION
- URGENCY
- CONSENT_CLICK
- TWIST_SIGNAL
- FLIP_OUTCOME
- ESCALATION
- TRAP_APPEAL
- IMMEDIATE_CONSEQUENCE
- CHOICE_END
- DISCLAIMER

Beat requirements:
- `t` and `type` required
- at least one of `on_screen`, `ui_component`, or `vo` must exist
- `sfx` is optional; if present it must be a list of strings
