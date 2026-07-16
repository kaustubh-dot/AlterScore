"""Small, transparent text-quality adjustment for the synthetic demo.

The assessment model never consumes free text.  This module only makes a
bounded completion-quality adjustment after the answer-based score is mapped,
so a blank, weak, or repetitive response remains submit-able and cannot create
an opaque semantic or language-proficiency proxy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

TextQualityStatus = Literal["substantive", "limited", "gibberish"]

MIN_SUBSTANTIVE_WORDS: Final[int] = 10
LIMITED_TEXT_PENALTY_POINTS: Final[int] = -6
GIBBERISH_TEXT_PENALTY_POINTS: Final[int] = -12
MAX_TEXT_PENALTY_POINTS: Final[int] = abs(GIBBERISH_TEXT_PENALTY_POINTS)


@dataclass(frozen=True)
class TextQualityAssessment:
    """UI-safe description of the only free-text effect on a demo score."""

    status: TextQualityStatus
    reason: str
    score_adjustment_points: int
    max_penalty_points: int = MAX_TEXT_PENALTY_POINTS

    def as_dict(self) -> dict[str, str | int]:
        return {
            "status": self.status,
            "reason": self.reason,
            "score_adjustment_points": self.score_adjustment_points,
            "max_penalty_points": self.max_penalty_points,
        }


def assess_text_response_quality(text: str) -> TextQualityAssessment:
    """Classify text format only and return a fixed, bounded score effect.

    A substantive response receives no bonus.  The two deductions are fixed
    and visible to the user, which prevents a weak response from becoming a
    rejection and prevents stylistic wording from yielding an unbounded gain.
    """

    normalized_text = str(text or "").strip()
    tokens = _format_only_tokens(normalized_text)
    if len(tokens) < MIN_SUBSTANTIVE_WORDS:
        return TextQualityAssessment(
            status="limited",
            reason=(
                "The response is shorter than the 10-word demo quality check; "
                "it remains accepted with a fixed 6-point adjustment."
            ),
            score_adjustment_points=LIMITED_TEXT_PENALTY_POINTS,
        )

    if _is_repetitive_or_keyboard_spam(normalized_text, tokens):
        return TextQualityAssessment(
            status="gibberish",
            reason=(
                "The response appears repetitive or non-substantive; it remains "
                "accepted with the fixed maximum 12-point adjustment."
            ),
            score_adjustment_points=GIBBERISH_TEXT_PENALTY_POINTS,
        )

    return TextQualityAssessment(
        status="substantive",
        reason=(
            "The response met the basic length and repetition check; it does not "
            "add bonus points."
        ),
        score_adjustment_points=0,
    )


def _format_only_tokens(text: str) -> list[str]:
    """Return Unicode-safe whitespace tokens without interpreting language."""

    tokens: list[str] = []
    for raw_token in text.casefold().split():
        normalized = "".join(char for char in raw_token if char.isalnum())
        if normalized:
            tokens.append(normalized)
    return tokens


def _is_repetitive_or_keyboard_spam(text: str, tokens: list[str]) -> bool:
    """Use only simple format checks, never semantic or language inference."""

    del text
    if len(set(tokens)) / len(tokens) < 0.40:
        return True

    most_common_token_count = max(tokens.count(token) for token in set(tokens))
    if most_common_token_count > 5 and len(tokens) < 15:
        return True

    return False


__all__ = [
    "GIBBERISH_TEXT_PENALTY_POINTS",
    "LIMITED_TEXT_PENALTY_POINTS",
    "MAX_TEXT_PENALTY_POINTS",
    "MIN_SUBSTANTIVE_WORDS",
    "TextQualityAssessment",
    "TextQualityStatus",
    "assess_text_response_quality",
]
