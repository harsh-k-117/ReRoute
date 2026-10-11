"""Run acceptance tests and print passing/xfail counts."""

from __future__ import annotations

import pytest


class Scoreboard:
    passed = 0
    xfailed = 0
    failed = 0
    skipped = 0

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when != "call":
            return
        if report.skipped and hasattr(report, "wasxfail"):
            self.xfailed += 1
        elif report.passed:
            self.passed += 1
        elif report.skipped:
            self.skipped += 1
        else:
            self.failed += 1


def main() -> int:
    scoreboard = Scoreboard()
    exit_code = pytest.main(["-q", "-m", "acceptance"], plugins=[scoreboard])
    total = (
        scoreboard.passed + scoreboard.xfailed + scoreboard.failed + scoreboard.skipped
    )
    print(
        f"{scoreboard.passed} / {total} passing, "
        f"{scoreboard.xfailed} xfail, {scoreboard.failed} failed"
    )
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
