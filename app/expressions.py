"""Friendly expression name -> list of (morph_name, weight).

Morph names are the model's native (Japanese) morph names. Unknown names are
ignored by MorphController.set_weight, so a mapping entry that the current model
does not provide simply has no effect.
"""
from __future__ import annotations

EXPRESSIONS: dict[str, list[tuple[str, float]]] = {
    "idle": [],
    "neutral": [],

    "smile": [("口角上げ", 0.85)],
    "happy": [("口角上げ", 1.00), ("照れ", 0.20)],
    "grin": [("にやり", 0.90)],
    "cute": [("口角上げ", 0.60), ("照れ", 0.25)],

    "sad": [("困る", 0.90)],
    "cry": [("困る", 0.90), ("涙", 0.80)],
    "angry": [("怒り", 1.00)],
    "serious": [("真面目", 0.70)],
    "surprised": [("びっくり", 1.00)],
    "shocked": [("びっくり", 1.00), ("はちゅ目", 0.60)],
    "thinking": [("じと目", 0.80)],
    "sleepy": [("はぅ", 0.80), ("なごみ", 0.40)],
    "shy": [("照れ", 1.00)],
    "wink": [("ウィンク", 1.00)],
    "wink_r": [("ウィンク右", 1.00)],
    "star": [("星目", 1.00)],
    "heart": [("はぁと", 1.00)],
    "tongue": [("てへぺろ", 1.00)],
    "pout": [("む", 0.90)],
    "close_eye": [("まばたき", 1.00)],
    "smug": [("にやり２", 0.90)],
    "sparkle": [("目線", 0.0)],  # placeholder, ignored if missing
}

# vowel morphs used for lip sync
VOWELS: list[tuple[str, float]] = [
    ("あ", 1.0),
    ("い", 1.0),
    ("う", 1.0),
    ("え", 1.0),
    ("お", 1.0),
]

BLINK_MORPHS = ["まばたき", "ウィンク", "ウィンク右", "ウィンク２", "ウィンク２右"]


def apply_expression(morph, name: str) -> None:
    """Set one named expression, clearing the other expression morphs first."""
    entries = EXPRESSIONS.get(name)
    if entries is None:
        return
    for morph_name in _all_expression_morphs():
        morph.set_weight(morph_name, 0.0)
    for morph_name, weight in entries:
        morph.set_weight(morph_name, weight)


def _all_expression_morphs() -> set[str]:
    out: set[str] = set()
    for entries in EXPRESSIONS.values():
        for morph_name, _ in entries:
            out.add(morph_name)
    return out
