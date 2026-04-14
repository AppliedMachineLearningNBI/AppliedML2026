# ------------------------------------------------------------------------- #
# Submission Checker
# ------------------------------------------------------------------------- #
#
# Code for checking that submissions of the initial project in Applied Machine Learning
# adheres to the naming scheme and file format required (in order for automatic evaluation).
#
# Date of latest version: 14th of April 2026
#
# ------------------------------------------------------------------------- #


#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run submission format checks for one student folder."
    )
    parser.add_argument(
        "submission_dir",
        help="Path to one student submission folder (contains CSV/TXT files).",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="Maximum errors printed per check phase (default: 20).",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    src_dir = base_dir / "SubmissionChecker/src"
    sys.path.insert(0, str(src_dir))

    from checker.solution_checker import SolutionChecker

    checker = SolutionChecker(max_errors=args.max_errors)
    checker.student_friendly_check(args.submission_dir)


if __name__ == "__main__":
    main()
