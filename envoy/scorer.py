"""scorer.py — Score .env files by quality, completeness, and security.

Produces a numeric score (0–100) with a breakdown of contributing factors
such as key naming conventions, secret strength, empty values, and duplicates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from envoy.masker import is_sensitive_key
from envoy.auditor import audit_env, AuditResult
from envoy.validator import validate_env


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ScoreBreakdown:
    """Individual scoring component."""

    name: str
    score: int          # points awarded for this component
    max_score: int      # maximum possible points
    notes: List[str] = field(default_factory=list)

    @property
    def pct(self) -> float:
        """Return percentage contribution (0.0–1.0)."""
        if self.max_score == 0:
            return 1.0
        return self.score / self.max_score


@dataclass
class EnvScore:
    """Aggregate quality score for a .env file."""

    total: int
    max_total: int
    grade: str
    breakdowns: List[ScoreBreakdown] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        """Return overall score as a percentage (0.0–100.0)."""
        if self.max_total == 0:
            return 100.0
        return (self.total / self.max_total) * 100.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_PLACEHOLDER_RE = re.compile(r'^(CHANGE[_-]?ME|TODO|FIXME|REPLACE|<[^>]+>|\[.*?\])$', re.I)
_SHORT_SECRET_THRESHOLD = 8


def _grade(pct: float) -> str:
    """Convert a 0–100 percentage to a letter grade."""
    if pct >= 90:
        return 'A'
    if pct >= 75:
        return 'B'
    if pct >= 60:
        return 'C'
    if pct >= 40:
        return 'D'
    return 'F'


# ---------------------------------------------------------------------------
# Scoring components
# ---------------------------------------------------------------------------

def _score_key_naming(env: Dict[str, str]) -> ScoreBreakdown:
    """Reward keys that follow UPPER_SNAKE_CASE conventions."""
    if not env:
        return ScoreBreakdown('key_naming', 20, 20, ['No keys to evaluate'])

    good = sum(1 for k in env if _VALID_KEY_RE.match(k))
    ratio = good / len(env)
    score = round(ratio * 20)
    notes = []
    if ratio < 1.0:
        bad = [k for k in env if not _VALID_KEY_RE.match(k)]
        notes.append(f"{len(bad)} key(s) do not follow UPPER_SNAKE_CASE: {', '.join(bad[:5])}")
    return ScoreBreakdown('key_naming', score, 20, notes)


def _score_no_empty_values(env: Dict[str, str]) -> ScoreBreakdown:
    """Penalise empty values, especially for sensitive keys."""
    if not env:
        return ScoreBreakdown('no_empty_values', 20, 20, ['No keys to evaluate'])

    empty = [k for k, v in env.items() if v.strip() == '']
    ratio = 1.0 - (len(empty) / len(env))
    score = round(ratio * 20)
    notes = [f"{k} is empty" for k in empty[:5]]
    return ScoreBreakdown('no_empty_values', score, 20, notes)


def _score_secret_strength(env: Dict[str, str]) -> ScoreBreakdown:
    """Reward strong (non-placeholder, sufficiently long) secret values."""
    sensitive = {k: v for k, v in env.items() if is_sensitive_key(k)}
    if not sensitive:
        return ScoreBreakdown('secret_strength', 30, 30, ['No sensitive keys detected'])

    issues: List[str] = []
    for k, v in sensitive.items():
        if not v.strip():
            issues.append(f"{k}: empty")
        elif _PLACEHOLDER_RE.match(v.strip()):
            issues.append(f"{k}: looks like a placeholder")
        elif len(v) < _SHORT_SECRET_THRESHOLD:
            issues.append(f"{k}: value is very short (< {_SHORT_SECRET_THRESHOLD} chars)")

    ratio = 1.0 - (len(issues) / len(sensitive))
    score = round(ratio * 30)
    return ScoreBreakdown('secret_strength', score, 30, issues[:5])


def _score_no_duplicates(env: Dict[str, str], raw_lines: List[str] | None = None) -> ScoreBreakdown:
    """Award points when no duplicate keys exist in the raw file."""
    # Without raw lines we can only confirm the parsed dict has no dups.
    score = 20
    notes: List[str] = []
    if raw_lines is not None:
        seen: Dict[str, int] = {}
        for line in raw_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                seen[key] = seen.get(key, 0) + 1
        dups = [k for k, c in seen.items() if c > 1]
        if dups:
            score = 0
            notes = [f"Duplicate key: {k}" for k in dups[:5]]
    return ScoreBreakdown('no_duplicates', score, 20, notes)


def _score_validation(env: Dict[str, str]) -> ScoreBreakdown:
    """Award points when all keys pass structural validation."""
    issues = validate_env(env)
    errors = [i for i in issues if i.level == 'error']
    score = 10 if not errors else 0
    notes = [i.message for i in errors[:5]]
    return ScoreBreakdown('validation', score, 10, notes)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_env(
    env: Dict[str, str],
    raw_lines: List[str] | None = None,
) -> EnvScore:
    """Compute a quality score for *env*.

    Parameters
    ----------
    env:
        Parsed key/value mapping.
    raw_lines:
        Optional list of raw file lines used to detect duplicate keys.

    Returns
    -------
    EnvScore
        Aggregate score with per-component breakdowns.
    """
    components = [
        _score_key_naming(env),
        _score_no_empty_values(env),
        _score_secret_strength(env),
        _score_no_duplicates(env, raw_lines),
        _score_validation(env),
    ]

    total = sum(c.score for c in components)
    max_total = sum(c.max_score for c in components)
    pct = (total / max_total * 100) if max_total else 100.0

    return EnvScore(
        total=total,
        max_total=max_total,
        grade=_grade(pct),
        breakdowns=components,
    )


def format_score_report(score: EnvScore, path: str = '') -> str:
    """Return a human-readable score report string."""
    header = f"Env Quality Score{f': {path}' if path else ''}"
    lines = [
        header,
        '=' * len(header),
        f"  Overall : {score.total}/{score.max_total}  ({score.percentage:.1f}%)  Grade: {score.grade}",
        '',
        '  Breakdown:',
    ]
    for b in score.breakdowns:
        lines.append(f"    {b.name:<20} {b.score:>3}/{b.max_score}")
        for note in b.notes:
            lines.append(f"      - {note}")
    return '\n'.join(lines)
