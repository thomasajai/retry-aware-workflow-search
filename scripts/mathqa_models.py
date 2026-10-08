"""Shared MathQA model profiles; selected settings from the formatting trials."""

from copy import deepcopy
from dataclasses import dataclass

from mathqa_response import ANSWER_SCHEMA


EXPERIMENTS = ("line-example", "json-prompt", "json-schema", "line-no-think", "json-schema-no-think")
LINE_PROMPT = (
    "Solve this multiple-choice math problem.\n"
    "Return only one line: a compact calculation; the lowercase option letter) the option value.\n"
    "Unrelated example: for 6 times 7 with options a) 40, b) 42, c) 44, d) 46, e) 48, return:\n"
    "6*7=42; b) 42\n"
    "Calculation: at most 160 characters; numbers, arithmetic, single-letter variables or math functions "
    "(gcd, lcm, sqrt, abs, floor, ceil, log, ln, min, max, round). No prose or units in calculation.\n"
    "Copy the selected option value exactly, at most 120 characters. No headings, Markdown, LaTeX, or extra lines.\n\n"
    "Problem: {problem}\nOptions: {options}"
)
JSON_PROMPT = (
    "Solve this multiple-choice math problem.\n"
    "Return only a JSON object with exactly three string fields: calculation, option, value.\n"
    'Unrelated example: for 6 times 7 with options a) 40, b) 42, c) 44, d) 46, e) 48, return:\n'
    '{{"calculation":"6*7=42","option":"b","value":"42"}}\n'
    "Calculation: at most 160 characters; numbers, arithmetic, single-letter variables or math functions "
    "(gcd, lcm, sqrt, abs, floor, ceil, log, ln, min, max, round). No prose or units in calculation.\n"
    "Option: one lowercase letter a-e. Value: copy the selected option text exactly, at most 120 characters.\n"
    "No Markdown, LaTeX, commentary, extra fields, or line breaks inside field values.\n\n"
    "Problem: {problem}\nOptions: {options}"
)


@dataclass(frozen=True)
class ModelProfile:
    """One model's tested controls and selected formatting variant.

    Request dictionaries returned by config() are independent snapshots; edit
    this registry for future runs, never a saved run's settings.
    """

    model: str
    body_settings: dict
    control_notes: str
    default_experiment: str

    def config(self, experiment: str | None = None) -> dict:
        experiment = self.default_experiment if experiment is None else experiment
        if experiment not in EXPERIMENTS:
            raise ValueError(f"Unknown experiment: {experiment}.")
        if experiment.endswith("no-think") and self.model != "qwen/qwen3-32b":
            raise ValueError("/no_think experiments apply only to Qwen3.")
        settings = {
            "body_settings": deepcopy(self.body_settings),
            "control_notes": self.control_notes,
            "experiment": experiment,
            "response_contract": "json-v1" if experiment.startswith("json") else "line-v1",
            "prompt_template": JSON_PROMPT if experiment.startswith("json") else LINE_PROMPT,
        }
        if experiment.endswith("no-think"):
            settings["prompt_template"] += "\n/no_think"
        if experiment.startswith("json-schema"):
            settings["body_settings"]["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "mathqa_answer", "strict": True, "schema": deepcopy(ANSWER_SCHEMA)},
            }
        return settings


MODEL_PROFILES = {
    "qwen25": ModelProfile(
        default_experiment="json-prompt",
        model="qwen/qwen-2.5-7b-instruct",
        body_settings={
            "temperature": 0, "max_tokens": 256, "stream": False,
            "provider": {"only": ["phala"], "allow_fallbacks": False, "require_parameters": True},
        },
        control_notes="No reasoning parameter: Phala does not advertise it for Qwen2.5.",
    ),
    "qwen3": ModelProfile(
        default_experiment="json-schema-no-think",
        model="qwen/qwen3-32b",
        body_settings={
            "temperature": 0.7, "top_p": 0.8, "top_k": 20,
            "max_tokens": 256, "stream": False, "reasoning": {"enabled": False},
            "provider": {"only": ["siliconflow/fp8"], "allow_fallbacks": False, "require_parameters": True},
        },
        control_notes="Gateway reasoning-off is a trial request, not a guarantee. /no_think is tested separately. Sampling follows Qwen's non-thinking recommendation.",
    ),
    "deepseek": ModelProfile(
        default_experiment="json-prompt",
        model="deepseek/deepseek-v3.2",
        body_settings={
            "temperature": 0, "max_tokens": 256, "stream": False,
            "reasoning": {"enabled": False},
            "provider": {"only": ["deepinfra/fp4"], "allow_fallbacks": False, "require_parameters": True},
        },
        control_notes="DeepInfra advertises reasoning and structured outputs. Inspect returned reasoning usage and visible verbosity separately.",
    ),
}


def default_model_configs() -> dict[str, dict]:
    """Fresh configurations in the registry's model execution order."""
    configs = {profile.model: profile.config() for profile in MODEL_PROFILES.values()}
    if len(configs) != len(MODEL_PROFILES):
        raise ValueError("Model profiles must have unique model IDs.")
    return configs


def experiment_config(model_alias: str, experiment: str) -> tuple[str, dict]:
    """Use the same model controls for batch defaults and formatting trials."""
    profile = MODEL_PROFILES[model_alias]
    return profile.model, profile.config(experiment)


WORKFLOW_DEEPSEEK_PROVIDERS = ("deepinfra/fp4", "venice", "auto")
WORKFLOW_DEEPSEEK_PRICE_LIMITS = {"prompt": 0.60, "completion": 1.70, "request": 0}


def workflow_model_configs(*, temperature=0.2, max_tokens=512, deepseek_provider="deepinfra/fp4"):
    """Proposed loop controls; preserve legacy batch defaults and prompts."""
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not 0 < temperature <= 1:
        raise ValueError("Workflow temperature must be small and nonzero (0 < value <= 1).")
    if type(max_tokens) is not int or max_tokens < 1:
        raise ValueError("Workflow output limit must be a positive integer.")
    if deepseek_provider not in WORKFLOW_DEEPSEEK_PROVIDERS:
        raise ValueError("Undeclared workflow DeepSeek provider.")
    configs = {}
    for alias, model_profile in MODEL_PROFILES.items():
        config = model_profile.config()
        config["body_settings"].update(temperature=temperature, max_tokens=max_tokens)
        if alias == "deepseek" and deepseek_provider == "auto":
            config["body_settings"]["provider"] = {
                "allow_fallbacks": True, "require_parameters": True,
                "max_price": deepcopy(WORKFLOW_DEEPSEEK_PRICE_LIMITS),
            }
            config["control_notes"] = "OpenRouter default routing within fixed price ceilings; provider/quantization may vary. Audit returned provider, usage and reasoning."
        elif alias == "deepseek" and deepseek_provider != "deepinfra/fp4":
            config["body_settings"]["provider"]["only"] = [deepseek_provider]
            config["control_notes"] = "Venice advertises reasoning controls. Inspect returned reasoning usage and visible verbosity separately."
        configs[alias] = {"model": model_profile.model, **config}
    return configs
