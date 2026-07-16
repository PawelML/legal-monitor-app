"""Phase -1 contract for the future evaluation harness."""

from __future__ import annotations


def main() -> int:
    """Confirm that the stable evaluation command is available.

    The golden dataset and LLM quality metrics are deliberately introduced in
    Phase 1. Keeping the command stable from Phase -1 lets CI and contributors
    rely on one interface as the harness evolves.
    """
    print(
        "Evaluation harness bootstrap complete; golden-set evaluation starts in "
        "Phase 1."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
