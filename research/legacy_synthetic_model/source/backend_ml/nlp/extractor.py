"""Local NLP feature extraction for AlterScore open-text responses."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from hashlib import blake2b
import re
from typing import Any, Final

import numpy as np

SENTENCE_TRANSFORMER_MODEL_NAME: Final[str] = "all-MiniLM-L6-v2"
SPACY_MODEL_NAME: Final[str] = "en_core_web_sm"
RAW_EMBEDDING_DIM: Final[int] = 384
MIN_TEXT_LENGTH: Final[int] = 10
RAW_TEXT_RESPONSE_COLUMN: Final[str] = "open_response_text"

_FIRST_PERSON_TOKENS: Final[set[str]] = {
    "i",
    "me",
    "my",
    "myself",
    "mine",
    "we",
    "our",
    "us",
}

# ---------------------------------------------------------------------------
# Agency verbs — expanded to ~130 words covering financial resilience actions
# ---------------------------------------------------------------------------
_AGENCY_VERBS: Final[set[str]] = {
    # Original core verbs
    "act",
    "acted",
    "adjust",
    "adjusted",
    "analyzed",
    "budget",
    "budgeted",
    "build",
    "built",
    "choose",
    "chose",
    "decide",
    "decided",
    "earn",
    "earned",
    "find",
    "found",
    "handle",
    "handled",
    "held",
    "implemented",
    "learn",
    "learned",
    "manage",
    "managed",
    "negotiate",
    "negotiated",
    "plan",
    "planned",
    "recover",
    "rebuild",
    "rebuilt",
    "reduce",
    "reduced",
    "renegotiated",
    "resolved",
    "save",
    "saved",
    "solve",
    "solved",
    "start",
    "started",
    "work",
    "worked",
    # Financial & economic actions
    "pay",
    "paid",
    "repay",
    "repaid",
    "invest",
    "invested",
    "spend",
    "spent",
    "calculate",
    "calculated",
    "deposit",
    "deposited",
    "withdraw",
    "borrow",
    "lend",
    "lent",
    "purchase",
    "sell",
    "sold",
    "trade",
    "traded",
    # Planning & organization
    "organize",
    "organized",
    "prioritize",
    "prioritized",
    "schedule",
    "scheduled",
    "arrange",
    "arranged",
    "prepare",
    "prepared",
    "research",
    "researched",
    "evaluate",
    "evaluated",
    "assess",
    "assessed",
    "review",
    "reviewed",
    "compare",
    "compared",
    "consider",
    "considered",
    # Problem-solving & improvement
    "fix",
    "fixed",
    "correct",
    "corrected",
    "repair",
    "repaired",
    "improve",
    "improved",
    "adapt",
    "adapted",
    "modify",
    "modified",
    "change",
    "changed",
    "switch",
    "switched",
    "create",
    "created",
    "develop",
    "developed",
    "establish",
    "established",
    "maintain",
    "maintained",
    "sustain",
    # Effort & persistence
    "try",
    "tried",
    "attempt",
    "attempted",
    "pursue",
    "pursued",
    "persist",
    "persisted",
    "continue",
    "continued",
    "endure",
    "endured",
    "strive",
    "overcome",
    "overcame",
    "achieve",
    "achieved",
    "accomplish",
    "accomplished",
    "complete",
    "completed",
    "finish",
    "finished",
    "succeed",
    "succeeded",
    # Communication & help-seeking
    "contact",
    "contacted",
    "apply",
    "applied",
    "ask",
    "asked",
    "request",
    "requested",
    "discuss",
    "discussed",
    "explain",
    "explained",
    "inform",
    "informed",
    "consult",
    "consulted",
    "seek",
    "sought",
    # Control & discipline
    "control",
    "controlled",
    "limit",
    "limited",
    "restrict",
    "restricted",
    "avoid",
    "avoided",
    "prevent",
    "prevented",
    "stop",
    "stopped",
    "quit",
    "eliminate",
    "eliminated",
    "cut",
    "minimize",
    "minimized",
    # Support & contribution
    "help",
    "helped",
    "support",
    "supported",
    "assist",
    "assisted",
    "guide",
    "guided",
    "teach",
    "taught",
    "train",
    "trained",
    "educate",
    "contribute",
    "contributed",
    "volunteer",
    "volunteered",
    "donate",
    "donated",
    # Monitoring & tracking
    "track",
    "tracked",
    "monitor",
    "monitored",
    "check",
    "checked",
    "ensure",
    "ensured",
    "secure",
    "secured",
    "verify",
    "verified",
    "confirm",
    # Settlement & resolution
    "settle",
    "settled",
    "clear",
    "cleared",
    "resolve",
    "transfer",
    "transferred",
    "move",
    "moved",
    "shift",
    "shifted",
    # General positive actions
    "keep",
    "kept",
    "set",
    "take",
    "took",
    "taken",
    "make",
    "made",
    "use",
    "used",
    "give",
    "gave",
    "focus",
    "focused",
}

# ---------------------------------------------------------------------------
# Victim / negative-outcome phrases and tokens
# ---------------------------------------------------------------------------
_VICTIM_PHRASES: Final[tuple[str, ...]] = (
    "bad things kept happening",
    "fell apart",
    "give up",
    "gave up",
    "had no choice",
    "kept happening",
    "unable to do anything",
    "was unable",
    "could not do anything",
    "nothing worked",
    "no way out",
    "no option",
    "no options left",
)
_VICTIM_TOKENS: Final[set[str]] = {
    "failed",
    "forced",
    "happened",
    "lost",
    "stuck",
    "unable",
}

# ---------------------------------------------------------------------------
# Solution keywords — expanded to ~80 words
# ---------------------------------------------------------------------------
_SOLUTION_KEYWORDS: Final[set[str]] = {
    # Original
    "act",
    "analyzed",
    "budget",
    "contingency",
    "cut",
    "earn",
    "find",
    "freelance",
    "handle",
    "held",
    "help",
    "implemented",
    "learn",
    "manage",
    "negotiate",
    "plan",
    "recover",
    "rebuild",
    "rebuilt",
    "reduce",
    "renegotiated",
    "resolved",
    "save",
    "solve",
    "strictly",
    "work",
    # Financial actions
    "pay",
    "paid",
    "repay",
    "repaid",
    "invest",
    "invested",
    "deposit",
    "calculate",
    "calculated",
    # Planning & organization
    "organize",
    "organized",
    "prioritize",
    "prioritized",
    "prepare",
    "prepared",
    "research",
    "researched",
    "schedule",
    "scheduled",
    "arrange",
    "arranged",
    "evaluate",
    "evaluated",
    "assess",
    "assessed",
    "compare",
    "compared",
    "review",
    "reviewed",
    "consider",
    "considered",
    # Problem-solving
    "fix",
    "fixed",
    "correct",
    "corrected",
    "improve",
    "improved",
    "adapt",
    "adapted",
    "develop",
    "developed",
    "create",
    "created",
    "establish",
    "established",
    "maintain",
    "maintained",
    "adjust",
    "adjusted",
    "modify",
    "modified",
    "change",
    "changed",
    "switch",
    "switched",
    # Effort & persistence
    "try",
    "tried",
    "attempt",
    "attempted",
    "pursue",
    "pursued",
    "persist",
    "persisted",
    "continue",
    "continued",
    "overcome",
    "overcame",
    "achieve",
    "achieved",
    "accomplish",
    "accomplished",
    "succeed",
    "succeeded",
    # Control & discipline
    "control",
    "controlled",
    "limit",
    "limited",
    "restrict",
    "restricted",
    "avoid",
    "avoided",
    "prevent",
    "prevented",
    "stop",
    "stopped",
    "eliminate",
    "eliminated",
    "minimize",
    "minimized",
    # Communication
    "contact",
    "contacted",
    "apply",
    "applied",
    "ask",
    "asked",
    "consult",
    "consulted",
    "discuss",
    "discussed",
    "seek",
    "sought",
    # Support
    "support",
    "supported",
    "assist",
    "assisted",
    "guide",
    "guided",
    # Monitoring
    "track",
    "tracked",
    "monitor",
    "monitored",
    "check",
    "checked",
    "ensure",
    "ensured",
    "secure",
    "secured",
    # Settlement
    "settle",
    "settled",
    "clear",
    "cleared",
    "transfer",
    "transferred",
    # General action words
    "sacrifice",
    "discipline",
    "responsible",
    "carefully",
    "systematically",
    "proactively",
    "strategically",
    "focus",
    "focused",
}

# ---------------------------------------------------------------------------
# Sentiment keyword sets — expanded
# ---------------------------------------------------------------------------
_POSITIVE_WORDS: Final[set[str]] = {
    # Original
    "act",
    "better",
    "budget",
    "calm",
    "confident",
    "control",
    "earn",
    "found",
    "freelance",
    "good",
    "grateful",
    "handle",
    "help",
    "improve",
    "learned",
    "plan",
    "recover",
    "relief",
    "resolved",
    "save",
    "stable",
    "strictly",
    "work",
    # Expanded — character traits
    "responsible",
    "disciplined",
    "careful",
    "steady",
    "consistent",
    "reliable",
    "determined",
    "motivated",
    "hopeful",
    "optimistic",
    "strong",
    "resilient",
    "patient",
    "focused",
    "proactive",
    "strategic",
    "smart",
    "wise",
    "practical",
    "realistic",
    "balanced",
    "organized",
    "prepared",
    "committed",
    "dedicated",
    "hardworking",
    "diligent",
    "persistent",
    # Expanded — outcomes and progress
    "successful",
    "achieved",
    "progress",
    "growth",
    "improvement",
    "opportunity",
    "solution",
    "overcome",
    "managed",
    "handled",
    "accomplished",
    "settled",
    "cleared",
    "secured",
    "maintained",
    "developed",
    "established",
    "positive",
    "fortunate",
    "proud",
    "satisfied",
    "comfortable",
    "supported",
    "encouraged",
}

_NEGATIVE_WORDS: Final[set[str]] = {
    # Original (removed "up" — too generic, triggers on "set up", "came up")
    "apart",
    "bad",
    "crisis",
    "despair",
    "failed",
    "fell",
    "loss",
    "lost",
    "nothing",
    "stuck",
    "unable",
    "worse",
    # Expanded
    "hopeless",
    "helpless",
    "overwhelmed",
    "impossible",
    "terrible",
    "awful",
    "horrible",
    "ruined",
    "destroyed",
    "collapsed",
    "suffering",
    "painful",
    "devastated",
    "bankrupt",
    "defaulted",
    "foreclosure",
    "eviction",
    "homeless",
    "starving",
}

_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"[a-zA-Z']+")

# ---------------------------------------------------------------------------
# Agency detection window (tokens in either direction from verb)
# ---------------------------------------------------------------------------
_AGENCY_WINDOW: Final[int] = 8


def extract_nlp_features(text: str) -> dict[str, float | np.ndarray]:
    """Extract interpretable NLP features plus a raw embedding."""

    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        return _default_nlp_features()

    normalized_text = _normalize_text(text)
    tokens = _tokenize(normalized_text)

    if not _validate_text_quality(text, tokens):
        # Zero signal: gibberish/spam text demonstrates no agency or effort
        return {
            "text_sentiment_compound": 0.0,
            "text_agency_score": 0.0,
            "text_problem_solving_flag": 0.0,
            "_embedding_raw": np.zeros(RAW_EMBEDDING_DIM, dtype=float),
        }

    sentiment = _extract_sentiment(
        text=text, normalized_text=normalized_text, tokens=tokens
    )
    agency_score = _extract_agency_score(text=text, tokens=tokens)
    problem_solving_flag = _extract_problem_solving_flag(
        normalized_text=normalized_text, tokens=tokens
    )
    raw_embedding = extract_raw_text_embedding(text)

    # Effort bonus: reward longer, more detailed responses (up to +0.15)
    word_count = len(tokens)
    if word_count >= 20:
        effort_bonus = min(0.15, (word_count - 20) * 0.002)
        agency_score = min(1.0, agency_score + effort_bonus)

    return {
        "text_sentiment_compound": sentiment,
        "text_agency_score": agency_score,
        "text_problem_solving_flag": float(problem_solving_flag),
        "_embedding_raw": raw_embedding,
    }


def extract_raw_text_embedding(text: str) -> np.ndarray:
    """Return a 384-dim raw embedding from a local model or deterministic fallback."""

    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        return np.zeros(RAW_EMBEDDING_DIM, dtype=float)

    sentence_model = _load_sentence_transformer_model()
    if sentence_model is not None:
        try:
            embedding = sentence_model.encode(
                [text],
                show_progress_bar=False,
            )[0]
            return np.asarray(embedding, dtype=float)
        except Exception:
            pass

    return _hashed_embedding(text)


def extract_nlp_feature_batch(
    texts: Sequence[str],
) -> tuple[list[dict[str, float]], np.ndarray]:
    """Extract the interpretable NLP features and raw embeddings for many texts."""

    feature_rows: list[dict[str, float]] = []
    embeddings: list[np.ndarray] = []

    for text in texts:
        features = extract_nlp_features(text)
        embeddings.append(np.asarray(features.pop("_embedding_raw"), dtype=float))
        feature_rows.append({key: float(value) for key, value in features.items()})

    if not embeddings:
        return feature_rows, np.zeros((0, RAW_EMBEDDING_DIM), dtype=float)

    return feature_rows, np.vstack(embeddings)


def _default_nlp_features() -> dict[str, float | np.ndarray]:
    return {
        "text_sentiment_compound": 0.0,
        "text_agency_score": 0.0,
        "text_problem_solving_flag": 0.0,
        "_embedding_raw": np.zeros(RAW_EMBEDDING_DIM, dtype=float),
    }


def _extract_sentiment(text: str, normalized_text: str, tokens: Sequence[str]) -> float:
    analyzer = _load_vader_analyzer()
    if analyzer is not None:
        try:
            score = float(analyzer.polarity_scores(text)["compound"])
            return float(np.clip(score, -1.0, 1.0))
        except Exception:
            pass

    positive_hits = sum(token in _POSITIVE_WORDS for token in tokens)
    negative_hits = sum(token in _NEGATIVE_WORDS for token in tokens)
    negative_hits += sum(phrase in normalized_text for phrase in _VICTIM_PHRASES)

    if positive_hits == 0 and negative_hits == 0:
        return 0.0

    raw_score = (positive_hits - negative_hits) / max(len(tokens), 4)
    return float(np.clip(raw_score * 2.5, -1.0, 1.0))


def _extract_agency_score(text: str, tokens: Sequence[str]) -> float:
    spacy_model = _load_spacy_model()
    normalized_text = " ".join(text.strip().lower().split())
    victim_hits = sum(token in _VICTIM_TOKENS for token in tokens)
    victim_phrase_hits = sum(phrase in normalized_text for phrase in _VICTIM_PHRASES)

    if spacy_model is not None:
        try:
            doc = spacy_model(text)
            total_verbs = 0
            active_verbs = 0
            for token in doc:
                if token.pos_ != "VERB":
                    continue
                total_verbs += 1
                if token.lemma_.lower() not in _AGENCY_VERBS:
                    continue
                # Widened window: 8 tokens in EITHER direction
                window_start = max(0, token.i - _AGENCY_WINDOW)
                window_end = min(len(doc), token.i + _AGENCY_WINDOW + 1)
                if any(
                    doc[index].text.lower() in _FIRST_PERSON_TOKENS
                    for index in range(window_start, window_end)
                ):
                    active_verbs += 1

            score = active_verbs / (total_verbs + 1)
            adjusted_score = score - 0.08 * victim_hits - 0.10 * victim_phrase_hits
            return float(np.clip(adjusted_score, 0.0, 1.0))
        except Exception:
            pass

    # Fallback: token-based heuristic with widened window
    total_verbs = 0
    active_verbs = 0

    for index, token in enumerate(tokens):
        is_verb_like = (
            token in _AGENCY_VERBS
            or token in _VICTIM_TOKENS
            or token.endswith(("ed", "ing"))
        )
        if not is_verb_like:
            continue
        total_verbs += 1
        if token in _AGENCY_VERBS:
            # Widened window: 8 tokens in EITHER direction
            window_start = max(0, index - _AGENCY_WINDOW)
            window_end = min(len(tokens), index + _AGENCY_WINDOW + 1)
            if any(
                tokens[j] in _FIRST_PERSON_TOKENS
                for j in range(window_start, window_end)
            ):
                active_verbs += 1

    raw_score = active_verbs / (total_verbs + 1)
    adjusted_score = raw_score - 0.08 * victim_hits - 0.10 * victim_phrase_hits
    return float(np.clip(adjusted_score, 0.0, 1.0))


def _extract_problem_solving_flag(normalized_text: str, tokens: Sequence[str]) -> float:
    """Return a gradient score [0.0, 1.0] based on solution keyword density."""
    solution_hits = sum(token in _SOLUTION_KEYWORDS for token in tokens)
    victim_hits = sum(token in _VICTIM_TOKENS for token in tokens)
    victim_hits += sum(phrase in normalized_text for phrase in _VICTIM_PHRASES)

    if solution_hits == 0:
        return 0.0

    # Net solution signal after subtracting victim language
    net_solution = max(0, solution_hits - victim_hits)
    if net_solution == 0:
        return 0.0

    # Gradient: scale relative to text length, saturating around 3-6 solution words
    denominator = max(3, len(tokens) * 0.12)
    score = net_solution / denominator
    return float(np.clip(score, 0.0, 1.0))


def _hashed_embedding(text: str) -> np.ndarray:
    embedding = np.zeros(RAW_EMBEDDING_DIM, dtype=float)
    tokens = _tokenize(_normalize_text(text))

    if not tokens:
        return embedding

    for token in tokens:
        digest = blake2b(token.encode("utf-8"), digest_size=16).digest()
        index = int.from_bytes(digest[:2], byteorder="big") % RAW_EMBEDDING_DIM
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        magnitude = 1.0 + (digest[3] / 255.0)
        embedding[index] += sign * magnitude

    norm = float(np.linalg.norm(embedding))
    if norm > 0.0:
        embedding /= norm
    return embedding


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text)


def _validate_text_quality(text: str, tokens: list[str]) -> bool:
    """Return True if text passes basic quality, lexical diversity, and non-spam checks."""
    if len(tokens) < 3:
        return False

    # 1. Lexical Diversity check — softened from 0.60 to 0.40
    # Natural text has repeated articles, pronouns, and prepositions
    unique_ratio = len(set(tokens)) / len(tokens)
    if unique_ratio < 0.40:
        return False

    # 2. Maximum Single Word Repetition check — raised from 3 to 5
    word_counts: dict[str, int] = {}
    for word in tokens:
        word_counts[word] = word_counts.get(word, 0) + 1
    if any(count > 5 for count in word_counts.values()) and len(tokens) < 15:
        return False

    # 3. Character Repetition check (keyboard spam)
    cleaned_char_text = "".join(text.split()).lower()
    if len(cleaned_char_text) > 0:
        char_counts: dict[str, int] = {}
        for char in cleaned_char_text:
            char_counts[char] = char_counts.get(char, 0) + 1

        most_common_char = max(char_counts, key=char_counts.get)
        max_char_count = char_counts[most_common_char]
        max_char_ratio = max_char_count / len(cleaned_char_text)

        # Apply checks:
        # A high ratio is allowed for short strings if the character is a common English vowel (avoiding false positives like "I had a bad day").
        # If it's a consonant or is extremely long, apply standard spam limits.
        if len(cleaned_char_text) > 10:
            if most_common_char in "aeiou":
                if max_char_ratio > 0.45 and len(cleaned_char_text) > 20:
                    return False
            else:
                if max_char_ratio > 0.35:
                    return False

    return True


@lru_cache(maxsize=1)
def _load_vader_analyzer() -> Any | None:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        return SentimentIntensityAnalyzer()
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_spacy_model() -> Any | None:
    import os
    import sys

    if os.environ.get("ALTERSCORE_ENV") == "test" or "pytest" in sys.modules:
        return None
    try:
        import spacy

        return spacy.load(SPACY_MODEL_NAME, disable=["parser", "ner"])
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_sentence_transformer_model() -> Any | None:
    import os
    import sys

    if os.environ.get("ALTERSCORE_ENV") == "test" or "pytest" in sys.modules:
        return None

    try:
        from sentence_transformers import SentenceTransformer

        # Never block scoring on a runtime download. If the transformer model is
        # not already available locally, fall back to the deterministic hashed
        # embedding path below instead of attempting network access.
        return SentenceTransformer(
            SENTENCE_TRANSFORMER_MODEL_NAME,
            local_files_only=True,
        )
    except Exception:
        return None


__all__ = [
    "MIN_TEXT_LENGTH",
    "RAW_EMBEDDING_DIM",
    "RAW_TEXT_RESPONSE_COLUMN",
    "SENTENCE_TRANSFORMER_MODEL_NAME",
    "SPACY_MODEL_NAME",
    "extract_nlp_feature_batch",
    "extract_nlp_features",
    "extract_raw_text_embedding",
]
