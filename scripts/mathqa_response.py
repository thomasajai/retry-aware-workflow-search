"""Local response contracts for formatting trials; no mathematical grading."""

import json
import re


CONTRACTS = ("line-v1", "json-v1")
MAX_CALCULATION_CHARACTERS = 160
MAX_VALUE_CHARACTERS = 120
MATH_FUNCTIONS = {"gcd", "lcm", "sqrt", "abs", "floor", "ceil", "log", "ln", "min", "max", "round"}
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "calculation": {"type": "string", "description": "Compact arithmetic expression, at most 160 characters; no prose."},
        "option": {"type": "string", "enum": list("abcde")},
        "value": {"type": "string", "description": "Copy the selected option's value from the options."},
    },
    "required": ["calculation", "option", "value"],
    "additionalProperties": False,
}


def unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}.")
        result[key] = value
    return result


def validate_answer(answer: str | None, contract: str, options: str) -> dict:
    """Parse without repairing output; keep parsed fields even if they are invalid.

    Outer whitespace is allowed. Calculation syntax is only a format check:
    single-letter variables and named math functions are allowed, never evaluated.
    Option/value agreement checks the supplied choices, not the answer key.
    """
    if contract not in CONTRACTS:
        raise ValueError(f"Unknown response contract: {contract}.")
    fields = None
    errors = []
    if not isinstance(answer, str) or not answer.strip():
        errors.append("Missing answer text.")
    elif contract == "json-v1":
        try:
            parsed = json.loads(answer, object_pairs_hook=unique_object)
            if not isinstance(parsed, dict):
                errors.append("Expected one JSON object.")
            else:
                fields = parsed
        except ValueError as error:
            errors.append(f"Invalid JSON: {error}")
    else:
        match = re.fullmatch(r"([^;\r\n]+); ([a-e])\) ([^\r\n]+)", answer.strip())
        if match is None:
            errors.append("Expected one line: calculation; a-e) value.")
        else:
            fields = dict(zip(("calculation", "option", "value"), match.groups()))

    if fields is not None:
        if set(fields) != {"calculation", "option", "value"}:
            errors.append("Require exactly calculation, option, and value fields.")
        for name, limit in (("calculation", MAX_CALCULATION_CHARACTERS), ("value", MAX_VALUE_CHARACTERS)):
            field = fields.get(name)
            if not isinstance(field, str) or not field.strip():
                errors.append(f"{name} must be a nonempty string.")
            elif len(field) > limit or any(char in field for char in "\r\n<>`\\"):
                errors.append(f"{name} must be a single line of at most {limit} characters without markup or placeholders.")
        calculation = fields.get("calculation")
        if isinstance(calculation, str):
            words = re.findall(r"[A-Za-z_]+", calculation)
            if (any(len(word) != 1 and word not in MATH_FUNCTIONS for word in words)
                    or not re.search(r"\d", calculation)
                    or not re.search(r"[=+*/^%×÷≈√-]|gcd\(|lcm\(", calculation)):
                errors.append("calculation must be a compact math expression, not prose.")
        option = fields.get("option")
        if not isinstance(option, str) or option not in list("abcde"):
            errors.append("option must be one lowercase letter a-e.")
        else:
            choices = dict(re.findall(
                r"(?:^|,\s*)([a-e])\s*\)\s*(.*?)(?=,\s*[a-e]\s*\)|$)", options
            ))
            value = fields.get("value")
            if (option not in choices or not isinstance(value, str)
                    or " ".join(value.split()) != " ".join(choices[option].split())):
                errors.append("value must match the selected option text (ignoring whitespace).")
    return {"valid": not errors, "parsed_fields": fields, "errors": errors}
