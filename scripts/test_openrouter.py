"""Check OpenRouter authentication without a model call or printing secrets."""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the Authorization header to a redirected destination.
        return None


def read_key(path: Path) -> str:
    """Read a simple KEY=value file; allow comments and quoted values."""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        name, separator, value = line.strip().partition("=")
        if separator and name.strip() == "OPENROUTER_API_KEY":
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if not value or any(char.isspace() for char in value):
                raise ValueError
            return value
    raise ValueError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credits", action="store_true", help="Also check account credits and this key's spending limit.")
    args = parser.parse_args()
    env_path = Path(__file__).resolve().parents[1] / ".env"
    try:
        key = read_key(env_path)
    except (OSError, ValueError):
        print("Set OPENROUTER_API_KEY in the repository's .env file, then retry.", file=sys.stderr)
        return 1

    request = Request(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            payload = json.load(response)
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            print("OpenRouter returned an unexpected response.", file=sys.stderr)
            return 1
    except HTTPError as error:
        hints = {
            401: "Authentication failed. Check your key.",
            403: "Access denied. Check your key's permissions.",
            429: "Rate limited. Try again later.",
        }
        print(f"HTTP {error.code}: {hints.get(error.code, 'OpenRouter request failed.')}", file=sys.stderr)
        return 1
    except (URLError, OSError):
        print("Could not reach OpenRouter. Check your connection and retry.", file=sys.stderr)
        return 1
    except (ValueError, UnicodeError):
        print("OpenRouter returned an unreadable response.", file=sys.stderr)
        return 1

    print("Success: OpenRouter accepted your API key. No model request was made.")
    if args.credits:
        remaining = payload["data"].get("limit_remaining")
        if isinstance(remaining, (int, float)):
            print(f"Remaining under this key's spending limit: ${remaining:.4f} (not the account balance).")
        else:
            print("No spending limit reported for this key.")
        credits_request = Request(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        )
        try:
            with build_opener(NoRedirect()).open(credits_request, timeout=20) as response:
                data = json.load(response)["data"]
            from decimal import Decimal
            balance = Decimal(str(data["total_credits"])) - Decimal(str(data["total_usage"]))
            print(f"Available account credits: ${balance:.4f}")
        except HTTPError as error:
            print(f"Credit lookup failed (HTTP {error.code}). Account balance access may require a management key.", file=sys.stderr)
            return 1
        except (URLError, OSError, ValueError, KeyError, TypeError, ArithmeticError):
            print("Could not retrieve the account credit balance.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
