# Cost-Efficient Search for Agentic Workflows with Retries

Course project for [COMS 6113: Topics in Agentic Systems, Fall 2026](https://daplab.cs.columbia.edu/agentic-systems/).

The [full project description](PROJECT.md) is the canonical statement of the topic, motivation, problem, proposed approach, and suggested reading. Check the [course schedule](https://daplab.cs.columbia.edu/agentic-systems/) for upcoming requirements. The five requested papers are stored in the [local paper collection](papers/README.md).

## Python setup and MathQA solver

This repository uses uv with Python 3.12. From the repository root:

```powershell
uv sync
uv run python scripts/mathqa_solver.py
```

`uv sync` installs the dependency versions recorded in `uv.lock` into `.venv`.
`uv run` uses that environment without requiring manual activation. Set
`OPENROUTER_API_KEY` in the repository's `.env` before running the solver.
Each run makes one paid OpenRouter request using `qwen/qwen-2.5-7b-instruct`
for the fixed question `mathqa_test_0002`. Change `SELECTED_MODEL` in the script
to select another model from `MODELS`.

The LangGraph workflow is `START -> solver -> END`. It prints the answer with
reasoning and calculation, input and output token counts, and the total cost
for that run. OpenRouter's reported usage is appended to
`results/mathqa_calls.jsonl`, which is ignored by Git. Failed requests are also
logged; unavailable usage is recorded as `null`, not zero. The log preserves
additional usage fields, such as reasoning and cached token counts.

The script also prints and logs `elapsed_seconds`, measured with
`time.perf_counter()` around the HTTP request. It includes waiting for the
complete response (requests use `stream=False`) or a request error, including
connection setup and network time. It excludes response JSON parsing, answer
validation, and writing the call log. Failed requests retain their duration.
This is a local measurement, separate from OpenRouter's server timing fields.

Requests use temperature 0, a 512-token output limit, a 60-second HTTP timeout,
and no automatic client retries. The correct answer and dataset rationale are
excluded from the solver's prompt. With one call per workflow, the call cost
is also the total run cost; totals are not accumulated across previous runs.

The direct dependencies in `pyproject.toml` are `langgraph` for the workflow,
`httpx` for OpenRouter HTTP requests, and `python-dotenv` for loading `.env`.
`.python-version` selects Python 3.12. uv's cache is configured as `.uvcache`
inside this repository; both that cache and `.venv` are ignored by Git.

## OpenRouter key check

Fill in `OPENROUTER_API_KEY` in the local `.env` file (or copy `.env.example`
to `.env` if setting up a fresh checkout). Keep the real key out of
`.env.example`. Run from the repository root:

```powershell
python scripts/test_openrouter.py
```

To also check the account credit balance and the key's remaining spending limit:

```powershell
python scripts/test_openrouter.py --credits
```

The spending limit is a cap, not funded credit. If the credits endpoint denies
access, account balance lookup may require a management key.

This uses Python's standard library; no packages need to be installed. It checks
authentication using [OpenRouter's current-key endpoint](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key)
without generating tokens. It does not print the key or API response. Success
confirms authentication, not model access or available credit. Failures return
a nonzero exit code. `.env` and `.env.*` are ignored by Git, except for the
placeholder `.env.example`. The local file stores the key as plain text.

## Research question

How can we profile and search model assignments for multi-stage agent workflows with retries under a limited evaluation budget? The search should account for success, deployment cost, and latency, including failed attempts and execution paths that terminate early. It should also report the cost of *finding* a configuration, separate from the cost of *running* it.

AgentOpt and VineLM are starting points. Candidate ideas include reusing measurements for shared execution prefixes, allocating samples to uncertain or promising configurations, and eliminating candidates that cannot compete. Small search spaces can be evaluated exhaustively as a reference; other comparisons include random search and uniform sample allocation.

The three papers emphasized in the September 21 meeting were [AgentOpt](https://arxiv.org/abs/2604.06296), [VineLM](https://arxiv.org/abs/2605.23914), and [SCOPE](https://arxiv.org/abs/2606.00774). The current presentation names Matrix UCB-E and GittinsEval as its strongest baselines. See the [decision log](notes/decision-log.md) for the experiment plan, open choices, and deck review items.

## September 25 checkpoint

The [course schedule](https://daplab.cs.columbia.edu/agentic-systems/) asks each team to:

- Identify 4–5 related papers and explain the strongest 1–2 baselines.
- Show one initial experiment: the question, comparison, first result, and what was learned.
- Duplicate and complete slides 4–9 of the course's linked deck, append the team slides before class, and rehearse a 10-minute presentation (5 minutes related work and baselines; 5 minutes first result).

The full experiment plot is due October 9. This is a tracking list from the course website, not a record of completed work.

## Source material

- `references/2026-09-21/` — whiteboard and notebook photos supplied with the September 21 meeting.
- `notes/` — meeting summaries and action items.

Meeting summary: [September 21 discussion](notes/2026-09-21-meeting-notes.md).

The meeting notes summarize discussion and tentative ideas. They do not automatically turn every suggestion in the discussion or photos into an agreed team decision.
