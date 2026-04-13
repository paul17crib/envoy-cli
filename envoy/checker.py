"""Core logic for checking .env completeness against a reference file."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class CheckResult:
    missing: List[str] = field(default_factory=list)   # in reference, not in target
    extra: List[str] = field(default_factory=list)     # in target, not in reference

    @property
    def ok(self) -> bool:
        return not self.missing and not self.extra

    def summary(self, strict: bool = False) -> str:
        lines = []
        for key in sorted(self.missing):
            lines.append(f"  [MISSING] {key}")
        if strict:
            for key in sorted(self.extra):
                lines.append(f"  [EXTRA]   {key}")
        return "\n".join(lines)

    def counts(self, strict: bool = False) -> str:
        """Return a short human-readable summary of issue counts.

        Example output::

            "1 missing, 2 extra"   # strict=True
            "1 missing"            # strict=False
            "ok"                   # no issues
        """
        parts = []
        if self.missing:
            parts.append(f"{len(self.missing)} missing")
        if strict and self.extra:
            parts.append(f"{len(self.extra)} extra")
        return ", ".join(parts) if parts else "ok"


def check_env(
    reference: Dict[str, str],
    target: Dict[str, str],
) -> CheckResult:
    """Compare target against reference and return a CheckResult."""
    ref_keys = set(reference.keys())
    tgt_keys = set(target.keys())

    return CheckResult(
        missing=sorted(ref_keys - tgt_keys),
        extra=sorted(tgt_keys - ref_keys),
    )


def missing_keys(reference: Dict[str, str], target: Dict[str, str]) -> List[str]:
    """Return keys present in reference but absent from target."""
    return sorted(set(reference.keys()) - set(target.keys()))


def extra_keys(reference: Dict[str, str], target: Dict[str, str]) -> List[str]:
    """Return keys present in target but absent from reference."""
    return sorted(set(target.keys()) - set(reference.keys()))
