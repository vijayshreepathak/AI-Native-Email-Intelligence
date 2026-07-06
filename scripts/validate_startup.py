#!/usr/bin/env python3
"""Pre-flight checks run by start.sh before uvicorn binds."""

from __future__ import annotations

import sys
import traceback


def main() -> int:
    print("--- Validating environment ---")
    try:
        from app.config import get_settings
        from app.startup_validation import env_summary, validate_production_env

        settings = get_settings()
        for key, value in env_summary(settings).items():
            print(f"  {key}: {value}")

        validate_production_env(settings)
        print("Environment validation: OK")
    except Exception:
        print("ERROR: Environment validation failed", file=sys.stderr)
        traceback.print_exc()
        return 1

    print("--- Validating application import ---")
    try:
        from app.main import app  # noqa: F401

        print(f"Application import: OK ({app.title})")
    except Exception:
        print("ERROR: Application import failed", file=sys.stderr)
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
