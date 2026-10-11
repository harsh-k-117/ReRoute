from __future__ import annotations

from contract.models import InvariantResult, ValidationReport


def summarize_invariant(check: InvariantResult) -> str:
    status = "OK" if check.passed else "FAIL"
    return f"{check.id}: {status} - {check.details}"


def render_report(report: ValidationReport) -> list[str]:
    return [summarize_invariant(check) for check in report.checks]


def format_validation_summary(report: ValidationReport) -> str:
    summary = "\n".join(render_report(report))
    return summary + f"\nOverall: {'PASS' if report.passed else 'FAIL'}"


__all__ = ["summarize_invariant", "render_report", "format_validation_summary"]
