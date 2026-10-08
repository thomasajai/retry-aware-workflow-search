# Cost-Efficient Search for Agentic Workflows with Retries

Course project for [COMS 6113: Topics in Agentic Systems, Fall 2026](https://daplab.cs.columbia.edu/agentic-systems/).

The [full project description](PROJECT.md) is the canonical statement of the topic, motivation, problem, proposed approach, and suggested reading. Check the [course schedule](https://daplab.cs.columbia.edu/agentic-systems/) for upcoming requirements. The five requested papers are stored in the [local paper collection](papers/README.md).

## Working agreement

Always follow these instructions when working in this repository:

- Explain proposed changes before editing.
- Keep the user informed as work progresses.
- Make small, reviewable changes.
- Ask the user if anything important is ambiguous.
- Before running anything that consumes OpenRouter credits, explain why it is
  needed, what will run, its estimated total cost, and a small cost breakdown.

This agreement applies to code, documentation, and experiments.

### OpenRouter spending rule

Apply this rule to every paid workflow or script, including live tests,
diagnostics, verifier trials, batches, reruns, and retries. Before execution:

- State the purpose and expected learning/result, and whether saved responses or
  an offline check can answer the question first.
- Identify the script/workflow, models/providers, question and repetition counts,
  expected calls, and maximum calls including solver and transport retries.
- Give an estimated total in USD and a small breakdown by model/role: call count,
  estimated input tokens, total billed output tokens including reasoning, current
  provider rates, and estimated subtotal. State assumptions and uncertainty.
- Distinguish the expected estimate from the configured spending limit and a
  conservative upper estimate where available. Do not call an estimate a
  guaranteed maximum. If pricing or reasoning usage is uncertain, disclose it
  before execution rather than assuming the calls are free or negligible.
- Execute only within the user-authorized scope and spending limit. Give a new
  notice before a new paid run or rerun; obtain authorization before increasing
  scope or spend beyond existing authorization.

Afterward, report actual known cost, any missing cost measurements, request
counts, and what the run established. Offline work does not need a paid-run
notice. A saved paid response reused offline does not consume credits again.

## Solver-verifier workflow plan

The [solver-verifier plan](notes/solver-verifier-plan.md) records the agreed retry
rules, verifier screening experiment, LangGraph workflow, SQLite storage design,
and staged completion criteria. [Milestone 1 is complete](notes/solver-verifier-milestone-1.md):
offline storage, screening previews, and reviewed diagnostic fixtures are available.
The [Milestone 2 preparation report](notes/solver-verifier-milestone-2-preparation.md)
documents the screening runner and reviewed natural answers. The approved
[36-call pilot completed](notes/solver-verifier-pilot-results.md) for $0.00163967,
with no technical errors, but every candidate accepted an incorrect natural
solution. The user has now chosen **Gemini 2.5 Flash-Lite with recomputation and
reasoning** as the provisional verifier. Additional verifier selection is
deferred. The [offline loop milestone](notes/solver-verifier-milestone-3-offline.md)
implements the three-attempt LangGraph workflow, durable calls, and independent
option grading. **123 offline tests pass**. The [live loop pilot proposal](notes/solver-verifier-loop-pilot-proposal.md)
freezes six executions, a $0.00442248 estimate, $0.04 cap, and 36-request maximum.
The user instructed us to commit and run this small pilot.
Paid stages require advance cost disclosure and explicit execution with a
defined budget.

Preview all 27 solver triples or save controlled loop traces without model calls:

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_workflow.py --preview
.\.venv\Scripts\python.exe scripts/mathqa_workflow_demo.py --output results/workflow_previews/new-loop-demo
```

The demo uses a separate database and simulated responses, with no credentials
or HTTP. It demonstrates early acceptance, third-attempt acceptance, rejection
exhaustion, and independent scoring of an accepted wrong option. These commands
have no paid execution mode. Solver temperature 0.2 and a 512-token output cap
are frozen for this pilot; legacy batch defaults are unchanged.

`scripts/mathqa_workflow_pilot.py` adds a separate explicit paid adapter with
source/data-bound plans, provider price ceilings, and independent scoring.
The proposal records its advance cost breakdown and scope; a larger evaluation
requires its own proposal and authorization.

Preview the first 20 questions of the saved 100-question batch against all three
proposed verifier candidates, with the independently reviewed synthetic diagnostics:

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_verifier_trials.py --include-reviewed --output results/workflow_previews/milestone-1.json
```

This command is offline and reads the source database without modifying it. The
preview includes exact proposed prompts/settings, unusable-answer diagnostics,
coverage, and request counts. It has no paid execution option. Candidate provider
controls and current prices are marked pending review, so estimated future costs
remain unknown rather than being presented as zero. Natural-answer labels and
synthetic diagnostic labels remain separate and never enter verifier requests.

Fetch free public metadata and prepare a frozen 36-call pilot proposal (both
commands make zero generation requests and do not load an API key):

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_verifier_preflight.py --fetch --output results/workflow_previews/provider-metadata.json
.\.venv\Scripts\python.exe scripts/mathqa_verifier_screen.py --metadata results/workflow_previews/provider-metadata.json --plan results/workflow_previews/verifier-pilot.json
```

The plan includes exact requests, provider pins, prices, estimated token costs,
conservative per-call reservations, and offline review labels. It defaults to
one saved question (three solver answers), plus nine usable synthetic diagnostics,
for twelve requests per candidate. There are no new solver requests or transport
retries. Preparation does not overwrite an existing plan. Provider metadata must
be at most 24 hours old at execution; refreshing it requires a new plan/cost notice.

**Paid execution is a separate step.** Only after advance notice and authorization
for the proposed scope and numeric limits, invoke the screening runner with
`--run --plan <approved-plan> --budget-usd <authorized-limit> --max-requests <authorized-count> --report <new-report>`.
No budget is implicit. Requests run serially with no fallbacks or client retries.
Routing price ceilings use dollars per million tokens; reservations account for
input and total billed output, including reasoning. These are conservative
estimates, not guarantees of provider billing. The runner checks known spending
plus the next reservation before scheduling a call, and stops for unknown cost,
unknown token usage, provider/model changes, or an exceeded reservation. It also
refuses a second execution of the same frozen plan in the same database.

Responses, usage, reasoning tokens, costs, timing, and errors are retained in
SQLite. Synthetic proposals are offline sources, not invented paid solver calls;
saved solver costs are not charged to the new screening run. Reports separate
natural and synthetic quality, valid Boolean verdicts, technical/format errors,
unknown labels, and key-correct answers with bad reasoning. A rejected one-attempt
screening execution uses terminal status `failed` with reason `screen_reject`;
three-attempt exhaustion and final workflow scores apply to the later loop.

The [follow-up comparison proposal](notes/solver-verifier-comparison-proposal.md)
tests the unchanged baseline, an independent recomputation prompt, and that
prompt with a larger reasoning allowance across eight reviewed questions.
It reuses nine exact pilot verdicts, planning 189 new calls with no synthetic
reruns. Prepare it offline with `scripts/mathqa_verifier_compare.py`; this CLI
has no paid execution option. After authorization, execute the frozen plan via
the guarded screening runner. Comparison reports separate inspected regression
cases from expansion, paired changes from raw acceptance, and new spending
from reused historical costs. The comparison also stops on the first technical
or format error, including truncation. This follow-up has 82 passing offline
tests. The user approved a $0.25 cap; the run stopped after five new calls costing
$0.00136376 because DeepSeek's reasoning profile returned a truncated response
with inconsistent token counts. The [partial results and billing audit](notes/solver-verifier-comparison-results.md)
record incomplete coverage and the proposed next checkpoint. No verifier was
selected at that checkpoint. The [amended comparison proposal](notes/solver-verifier-comparison-amended-proposal.md)
excludes DeepSeek's reasoning profile and reuses thirteen judgments, leaving
163 new verifier calls. It is prepared with 89 passing offline tests, estimated
cost $0.03962351. The user approved the $0.22 cap, and the
[amended run stopped](notes/solver-verifier-comparison-amended-results.md) after
forty new calls costing $0.00483675 when DeepSeek recompute produced prose and
truncated before a verdict. Total known verifier-selection spend is $0.00784018.
All profiles have observed false acceptances. The subsequent user decision to
proceed provisionally with Gemini 2.5 is recorded above. Repeated `--reuse-run`
and `--exclude-candidate` options support explicit sources and profile subsets;
finished stopped runs contribute only eligible completed calls. Duplicate
matching judgments are rejected, and incorrect verdicts remain observations.

Apply workflow storage upgrades explicitly, without model calls:

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_workflow_store.py --migrate
```

An existing database is backed up under `results/backups/` before a pending
upgrade. Numbered migrations are applied transactionally with checksum checks;
an already up-to-date database is unchanged. Existing batch records are retained.
Backups and generated previews are local Git-ignored artifacts. To test the
offline implementation and existing behavior, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Python setup and MathQA solver

This repository uses uv with Python 3.12. From the repository root:

```powershell
uv sync
uv run python scripts/mathqa_solver.py
```

`uv sync` installs the dependency versions recorded in `uv.lock` into `.venv`.
`uv run` uses that environment without requiring manual activation. Set
`OPENROUTER_API_KEY` in the repository's `.env` before running the solver.
Each run makes one paid OpenRouter request using `deepseek/deepseek-v3.2`
for the fixed question `mathqa_test_0002`. Change `SELECTED_MODEL` in the script
to select another model from `MODELS`.

The LangGraph workflow is `START -> solver -> END`. It prints the answer with
one short calculation and the selected option, input and output token counts, and the total cost
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

Requests use temperature 0, a 1,024-token output limit, a 60-second HTTP timeout,
and no automatic client retries. The correct answer and dataset rationale are
excluded from the solver's prompt. With one call per workflow, the call cost
is also the total run cost; totals are not accumulated across previous runs.

`MAX_OUTPUT_TOKENS` sets the output limit, which includes reasoning tokens
as well as the visible answer on most providers. A `length` finish reason
is reported as a token-limit error even when no answer text is returned.
Requests set `reasoning.enabled` to `false` to disable internal reasoning where
supported. The prompt asks for one line containing only the calculation and
selected option. A shorter answer does not by itself limit internal reasoning.

The direct dependencies in `pyproject.toml` are `langgraph` for the workflow,
`httpx` for OpenRouter HTTP requests, and `python-dotenv` for loading `.env`.
`.python-version` selects Python 3.12. uv's cache is configured as `.uvcache`
inside this repository; both that cache and `.venv` are ignored by Git.

## MathQA batch experiment

`scripts/mathqa_batch.py` selects the first 50 records in the downloaded
200-question subset. Both batch runs and formatting trials use the model
profiles in `scripts/mathqa_models.py`:

| Model | Selected variant | Fixed provider |
| --- | --- | --- |
| Qwen2.5 7B | `json-prompt` | `phala` |
| Qwen3 32B | `json-schema-no-think` | `siliconflow/fp8` |
| DeepSeek V3.2 | `json-prompt` | `deepinfra/fp4` |

Each profile groups the model ID, API controls, selected variant, and control
notes. The variant determines the concrete prompt and local response contract;
Qwen3 also requests a strict JSON schema and appends `/no_think`. All three use
a 256-token output limit, fixed providers, and disabled provider fallbacks.
These are the selected trial settings; they do not guarantee valid output.

To add a model, add a `ModelProfile` entry to `MODEL_PROFILES` in that module,
after verifying its provider's applicable controls. Its position in the registry
sets its execution order. The batch includes it automatically; the trial CLI
also accepts its alias. Preview its prompt and controls with the trial script
before authorizing a paid test. Returned configurations are independent copies.

New runs save each model's prompt, settings, variant, and contract in SQLite.
Execution reads this saved snapshot rather than current profile definitions.
Existing runs retain their original settings and remain readable.
Save a prepared run without making API calls:

```powershell
uv run python scripts/mathqa_batch.py
```

To create and execute a new paid batch of 150 requests:

```powershell
uv run python scripts/mathqa_batch.py --run
```

For a small paid test with one question per model (three requests total):

```powershell
uv run python scripts/mathqa_batch.py --run --questions 1
```

For the new formatting trials, preview one model's candidate settings and prompt
against the first five questions without API calls or database changes:

```powershell
uv run python scripts/mathqa_experiments.py --list
uv run python scripts/mathqa_experiments.py --model qwen25
```

Add `--run` only when ready for that paid five-call trial. Available model aliases
are `qwen25`, `qwen3`, and `deepseek`; experiments compare a concrete line example,
prompt-only JSON, and API JSON schema, with additional Qwen3 `/no_think` variants.
Qwen2.5 and DeepSeek default to the selected `json-prompt` variant; Qwen3 defaults
to the selected `json-schema-no-think` variant. Use `--experiment` to select
another variant explicitly.
Generation status and local format validity are saved separately, preserving
original answers and complete responses. A diagnostic JSON report includes
validation, provider, reasoning usage, cost, and timing; HTML shows original
answers. Mathematical accuracy grading is deferred until after formatting trials.
See [the experiment notes](notes/mathqa-batch-experiment.md#stage-1-implemented-formatting-trials-before-accuracy-grading)
for the response contract, candidate settings, and trial sequence.

`--questions` defaults to 50 and must be between 1 and the dataset's record count.
It also works without `--run` to prepare a smaller run without API requests.
Set `OPENROUTER_API_KEY` in `.env` first. The script finishes all selected attempts
for each model before starting the next model. `MAX_CONCURRENT_REQUESTS` in
the script defaults to 5; it limits overlapping requests within that model.
The model order is Qwen 2.5 7B, Qwen3 32B, then DeepSeek V3.2.

Run settings and individual call outcomes are stored in the Git-ignored
`results/mathqa_runs.sqlite3`. Calls retain answer text, full response JSON,
raw response text, reported usage and cost, elapsed seconds, and errors.
Missing measurements stay `NULL`. Expected API failures are recorded and
the remaining attempts continue; there are no automatic retries. Unexpected
errors stop the batch, cancel pending tasks, and mark the run interrupted.
Ctrl+C also records interruption when the process can finish its cleanup.

Every invocation creates a new run; resume is not implemented. A completed
call means a nonempty answer was returned without a detected generation error.
New batch runs validate the JSON response locally and store parsed fields and
validation errors separately, preserving the original answer and full response.
The batch prints format-valid, invalid, and unvalidated counts among completed
generations separately from generation failures. A nonempty answer can be invalid;
valid JSON can still come from a truncated generation. Mathematical correctness
is not yet graded, and format validation never uses the dataset answer key.
See [the batch experiment note](notes/mathqa-batch-experiment.md) for the live-run
results, reasoning/format issues, and proposed next steps.
Batch run status and exit codes continue to describe generation outcomes.
Exit codes are 0 for setup or a batch without generation failures (even if some
responses are format-invalid), 1 for a batch with failed generations,
2 for invalid arguments or a missing key,
and 130 for Ctrl+C.

The separate `scripts/mathqa_table.py` script reads SQLite without changing it
and writes a standalone HTML answer table. The batch command also calls this
exporter after execution finishes or Ctrl+C cleanup completes. Export the most
recently created run independently:

```powershell
uv run python scripts/mathqa_table.py
```

Or select a specific run using the ID printed by the batch script:

```powershell
uv run python scripts/mathqa_table.py --run-id YOUR_RUN_ID
```

Open the printed HTML file path in a browser. Output defaults to
`results/mathqa_tables/mathqa_<run-id>.html` and is ignored by Git. Use `--output`
to choose another HTML path or `--database` to read another SQLite database.
The table follows the run's saved question and model order. Missing answers are
blank, failed and unfinished attempts are tinted, and partial answers remain
visible. If multiple attempts exist, the highest attempt number is shown.
Exporting makes no API requests. Setup-only runs therefore produce blank tables.

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
