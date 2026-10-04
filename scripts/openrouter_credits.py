"""Print OpenRouter key spending limits and account credits (USD)."""

import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from test_openrouter import NoRedirect, read_key


def main() -> int:
    try:
        key = os.environ.get("OPENROUTER_API_KEY") or read_key(
            Path(__file__).resolve().parents[1] / ".env"
        )
        if not key or any(char.isspace() for char in key):
            raise ValueError
    except (OSError, ValueError):
        print("Set OPENROUTER_API_KEY in your environment or the repository's .env file.", file=sys.stderr)
        return 1

    key_request = Request(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    key_status = 0
    try:
        with build_opener(NoRedirect()).open(key_request, timeout=20) as response:
            key_data = json.load(response)["data"]
        if not isinstance(key_data, dict) or "limit" not in key_data:
            raise ValueError
        lines = []
        for field, label in (
            ("limit", "Key spending limit"),
            ("limit_remaining", "Remaining under key limit"),
            ("usage", "Key total usage"),
        ):
            value = key_data.get(field)
            if value is None:
                display = "No limit set" if field == "limit" else "Not reported"
            else:
                amount = Decimal(str(value))
                if not amount.is_finite():
                    raise ValueError
                display = f"${amount:.4f}"
            lines.append(f"{label}: {display}")
        lines.append(f"Key limit reset: {key_data.get('limit_reset') or 'No scheduled reset'}")
        print("\n".join(lines))
    except HTTPError as error:
        print(f"Key limit lookup failed (HTTP {error.code}).", file=sys.stderr)
        key_status = 1
    except (URLError, OSError, ValueError, KeyError, TypeError, ArithmeticError):
        print("Could not retrieve the API key's spending limit.", file=sys.stderr)
        key_status = 1

    request = Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            data = json.load(response)["data"]
        purchased = Decimal(str(data["total_credits"]))
        used = Decimal(str(data["total_usage"]))
        if not purchased.is_finite() or not used.is_finite():
            raise ValueError
        remaining = purchased - used
    except HTTPError as error:
        hints = {
            401: "Authentication failed. Check OPENROUTER_API_KEY.",
            403: "Access denied. The credits endpoint may require a management key.",
            429: "Rate limited. Try again later.",
        }
        print(f"HTTP {error.code}: {hints.get(error.code, 'OpenRouter credit lookup failed.')}", file=sys.stderr)
        return 1
    except (URLError, OSError):
        print("Could not reach OpenRouter. Check your connection and retry.", file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError, ArithmeticError):
        print("OpenRouter returned an unexpected credit response.", file=sys.stderr)
        return 1

    print(f"Total credits:     ${purchased:.4f}")
    print(f"Total usage:       ${used:.4f}")
    print(f"Remaining credits: ${remaining:.4f}")
    return key_status


if __name__ == "__main__":
    sys.exit(main())
