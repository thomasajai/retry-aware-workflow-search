# MathQA batch baseline and open issues

Reviewed on 2026-10-04. This records baseline commit `c723cdf` and observations
from its saved API responses. The formatting trial harness is implemented;
authorized paid trials and their observations are recorded at the end.

Current state: the formatting experiment harness, per-model settings, local
response validation, additive storage and offline tests are implemented.
The shared profiles in `mathqa_models.py` select Qwen2.5 `json-prompt`,
Qwen3 `json-schema-no-think`, and DeepSeek `json-prompt`. Both the original batch
CLI and experiment CLI now use these definitions. Automatic answer-only grading
now follows all model batches; the implementation and offline check are recorded below.
Generated JSON diagnostics, HTML tables and SQLite runs are local
artifacts excluded from Git; this note records the reviewable trial evidence.
The sections below describe the baseline and the trials in chronological order.

## Automatic answer-only grading, 2026-10-05

`mathqa_grading.py` extracts final answer fields independently of the calculation
format validator. JSON profiles require one complete JSON object with unique
fields and an explicit lowercase `a`–`e` option. No JSON repair, Markdown removal,
case correction, value-to-option inference, or calculation evaluation is done.
Missing/non-string values receive diagnostics but a usable option still controls
the primary score. Line profiles require one unambiguous terminal `; letter) value`
segment; segment spacing and semicolons in the calculation are allowed. Multiple
option segments, trailing lines, malformed JSON and unusable options score 0.
Failed/truncated generations score 0 even if their partial text has final fields.

Returned values are preserved separately and compared with the selected option's
text after collapsing whitespace runs only. Mismatches (including punctuation or
internal spacing differences) are flagged independently of the option score.
The existing format validator and saved validation results are unchanged.

The scheduler retains sequential model batches, five concurrent requests within
each model, and zero retries. After the entire model loop finishes and the run's
generation status is saved, grading verifies the saved dataset path/checksum and
every selected question/model pair's final outcomes. Missing calls, running or
interrupted attempts, and interrupted runs are refused. All scores, diagnostics,
and model summaries are saved in one transaction in additive `run_gradings`,
`call_gradings`, and `model_gradings` tables. Original run/call/validation records
are untouched. Accuracy uses all selected questions; legacy runs remain ungraded
until explicitly graded. For legacy runs with multiple attempts, every attempt
must have a final outcome and the latest attempt supplies the accuracy score.

Future `mathqa_batch.py --run --questions N` and `mathqa_experiments.py --run`
commands automatically grade after all calls finish, print model accuracy,
generation failures, ungradable completed answers and separate format-invalid
completed counts, then export HTML. The batch exit code still describes generation
success; the experiment exit code also requires format success. Neither exit code
is an accuracy threshold. Setup/preview commands do not make API calls or grade.

The HTML exporter remains read-only and produces three tables: extracted final
answers with expandable original replies, per-question/model scores, and per-model
accuracy with diagnostic counts. Older ungraded and incomplete runs display
“Ungraded,” never an inferred zero. Generation status and format validity appear
separately in the final-answer cells.

The existing run `fbc7011d-0c77-49d7-9c0c-e0979ae2c6cd` was graded offline,
without API requests. Its dataset checksum matched; all 60 final attempts received
saved scores and three model summaries. Before/after fingerprints of every row in
`runs`, `calls`, and `call_validations` matched exactly.

| Model | Correct / selected | Accuracy | Generation failures | Ungradable completed | Format-invalid completed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5 | 6 / 20 | 30% | 0 | 1 | 6 |
| Qwen3 | 11 / 20 | 55% | 0 | 0 | 7 |
| DeepSeek V3.2 | 14 / 20 | 70% | 2 | 0 | 12 |

The ungradable Qwen2.5 option on question 0102 is `"none"`. Three value text
mismatches were flagged: Qwen2.5 question 0122 (`b`, `432` versus option b's
`428 .`), Qwen2.5 question 0292 (`6.7 kg.` versus `6.7 kg .`), and Qwen3
question 0229 (`58%` versus `58 %`). These do not alter primary scores.
The two DeepSeek output-limit failures remain zero-scoring selected questions.

The regenerated HTML has 20 question rows in each of the first two tables, 60
expandable original replies, 60 scores, and three accuracy rows. Its score-column
sums match the stored summaries. To repeat this offline operation:

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_grading.py --run-id fbc7011d-0c77-49d7-9c0c-e0979ae2c6cd
```

Offline tests cover extraction, calculation-format independence, wrong/missing/
ambiguous/malformed final answers, value conflicts, failed/truncated generations,
checksum/completion guards, post-all-model timing, the full denominator, a fourth
configured model, original preservation, repeat grading, legacy export, HTML
ordering/escaping and read-only export. No paid calls or commits were made.

### Authorized live batch: first 100 questions, 2026-10-05

Run `6e8ba4fd-3f6d-41f9-9522-23c84e0d332d` made exactly 300 requests using
the three selected profiles, sequential model batches, concurrency five within
each model, and zero retries. All requests returned HTTP 200 from the configured
providers (Phala, SiliconFlow, DeepInfra). Generation finished in 165.06 seconds
with status `completed_with_errors` and exit code 1.

| Model | Correct / selected | Accuracy | Generation failures | Ungradable completed | Format-invalid completed | Reported USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5 | 51 / 100 | 51% | 0 | 1 | 20 | 0.00364060 |
| Qwen3 | 65 / 100 | 65% | 0 | 0 | 31 | 0.00641422 |
| DeepSeek V3.2 | 81 / 100 | 81% | 6 | 0 | 58 | 0.00858156 |

All six DeepSeek failures reached the 256-token output limit: questions 0108,
0187, 0237, 0396, 0419, and 1085. They score 0 and remain in the denominator.
All 300 attempts reported costs, totaling USD 0.01863638 including failures.

Automatic grading occurred after the final generation finished. Verification
confirmed the dataset checksum, 300 saved scores, 300 expandable original replies,
100 question rows in each of the final-answer and score tables, three accuracy
rows, and agreement between HTML score totals and saved summaries. A read-only
check while Qwen3 was running found no grading records for this run.

HTML: `results/mathqa_tables/mathqa_6e8ba4fd-3f6d-41f9-9522-23c84e0d332d.html`.
Diagnostics, including saved grading metadata/summaries:
`results/mathqa_experiments/6e8ba4fd-3f6d-41f9-9522-23c84e0d332d.json`.
Original responses and grading records remain in SQLite; no changes were committed.

## Batch integration after the formatting trials

- `mathqa_models.py` contains a `ModelProfile` per model in an ordered registry.
  Each groups model ID, explicit API body settings, selected experiment, and
  control notes. One shared builder supplies the concrete prompt, response
  contract, and optional strict JSON schema to both scripts.
- New `mathqa_batch.py` runs use these selected profiles by default. Qwen2.5 uses
  Phala and omits the unsupported reasoning control; Qwen3 uses SiliconFlow FP8,
  reasoning-off, strict JSON schema, and `/no_think`; DeepSeek uses DeepInfra FP4
  and reasoning-off with prompt-only JSON. The exact prompts and settings from
  the trials are retained, including the 256-token limits and disabled provider
  fallbacks. No additional provider controls were assumed or introduced.
- Adding a registry entry includes that model in new batches and makes its alias
  available in the trial CLI. Its provider controls must be verified before a
  paid trial; available format variants share the existing line/JSON contracts.
- Every run saves all per-model settings and templates. Execution uses that
  snapshot, including when current profiles change. Legacy shared-settings runs
  remain readable and can still execute if prepared; no resume was added.
- Existing local validation now applies to normal new batches. Answers and full
  responses remain unchanged; parsed fields/errors stay in `call_validations`.
  Generation status, format validity, and mathematical correctness remain separate.
  The console reports generation failures and separate format counts among
  completed generations. Run status and batch exit code still describe generation
  success only; the trial CLI continues to fail for format errors too.
- Model order, concurrency of five within each model, no automatic retries,
  first-N question selection, and answer-key exclusion remain unchanged.
- Nineteen offline tests pass, including exact batch/trial request matching,
  adding a model, independent configuration copies, saved-setting execution,
  legacy execution/export, valid/invalid/truncated responses, raw preservation,
  concurrency and model order. Implementation verification used mocked responses;
  the subsequently authorized live check is recorded below.

### Integrated batch: first 20 questions

The authorized run `fbc7011d-0c77-49d7-9c0c-e0979ae2c6cd` used the selected
profiles for 20 questions per model (60 calls). It finished in approximately
43.32 seconds with status `completed_with_errors` and exit code 1.

| Model | Completed generations | Generation failures | Format-valid completed replies | Format-invalid completed replies | Reported cost (USD) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5 / Phala | 20 | 0 | 14 | 6 | 0.00073020 |
| Qwen3 / SiliconFlow | 20 | 0 | 13 | 7 | 0.00136616 |
| DeepSeek / DeepInfra | 18 | 2 | 6 | 12 | 0.00187360 |

Total reported cost was USD 0.00396996, including failed generations. All 60
responses reported zero reasoning tokens. This records reported usage rather
than proving anything about all internal computation. DeepSeek reached the
256-token output limit on `mathqa_test_0108` and `mathqa_test_0237`.
Among the 58 completed generations, 33 passed the existing format contract and
25 failed it. Mathematical accuracy has not been graded.

The first invocation, run `2aed44a8-1d7d-4a15-878b-c800cc4d9b0b`, recorded
60 connection failures with no HTTP responses in the restricted environment.
The live run above was a separate invocation with network access enabled;
automatic retries remain disabled. Both runs remain in the local database.

The batch generated `results/mathqa_tables/mathqa_fbc7011d-0c77-49d7-9c0c-e0979ae2c6cd.html`.
Diagnostics are in `results/mathqa_experiments/fbc7011d-0c77-49d7-9c0c-e0979ae2c6cd.json`.
These generated artifacts remain excluded from Git. The HTML table shows original
answers and highlights generation failures; it does not yet highlight format errors.

## What we built

- A batch runner for the first N records in the downloaded MathQA file, with
  50 questions by default and a `--questions` override.
- Up to five concurrent requests within one model, finishing that model's
  batch before starting the next model. There are no automatic retries.
- SQLite run IDs and call IDs. Runs preserve the model and question order,
  UTC timestamps, prompt, settings, dataset checksum, and concurrency limit.
  Calls preserve the request body, answer text, full response JSON, raw
  response text, token counts, reported USD cost, elapsed seconds, finish
  reason, and errors. Missing measurements remain NULL.
- A separate, read-only HTML exporter with one answer cell per question/model,
  saved row/column order, escaped text, and failure/interruption highlighting.
  Partial failed answers remain visible. The batch also exports after execution.
- Ten automated tests covering scheduling, model order, failure/cancellation
  handling, saved settings, question counts, and HTML export behavior.

The local database and generated HTML are excluded from Git. This note records
summaries, not a portable copy of the original call records.

## Live checks

The one-question run `be764fdd-f344-4805-9b90-a4b0fec13909` returned three
completed calls. Reported total cost was USD 0.0001780744.

The 20-question run `08c8d950-e7cb-446b-8160-720fb72f4f04` attempted 60 calls
and ended as `completed_with_errors`. All 60 responses had HTTP status 200;
ten generations reached the 1,024-output-token limit and were marked failed.
Total reported cost, including failed calls, was USD 0.0068154448. Run duration
was approximately 124.73 seconds. The exported table has 20 rows and 60 answer
cells.

| Model | Completed | Failed at token limit | Reported cost (USD) |
| --- | ---: | ---: | ---: |
| Qwen 2.5 7B Instruct | 20 | 0 | 0.0003578 |
| Qwen3 32B | 13 | 7 | 0.00407047 |
| DeepSeek V3.2 | 17 | 3 | 0.0023871748 |

"Completed" currently means a nonempty answer with no detected API/generation
error. It does not mean the response matches the requested template or that
the mathematics is correct.

## Issue 1: reasoning-off requests were not consistently honored

Every request saved `reasoning: {"enabled": false}`. The returned
`usage.completion_tokens_details.reasoning_tokens` gives this breakdown:

| Model / returned provider | Calls | Positive reported reasoning | Zero reported reasoning | Token-limit failures |
| --- | ---: | ---: | ---: | ---: |
| Qwen 2.5 / Phala | 20 | 0 | 20 | 0 |
| Qwen3 / DeepInfra | 14 | 14 | 0 | 6 |
| Qwen3 / SiliconFlow | 3 | 0 | 3 | 0 |
| Qwen3 / Tenstorrent | 3 | 0 | 3 | 1 |
| DeepSeek / GMICloud | 14 | 0 | 14 | 3 |
| DeepSeek / Phala | 1 | 0 | 1 | 0 |
| DeepSeek / Baidu | 4 | 0 | 4 | 0 |
| DeepSeek / SiliconFlow | 1 | 0 | 1 | 0 |

This associates the Qwen3 reasoning behavior with the returned provider; it
does not establish the exact cause inside the gateway or provider. Zero
reported reasoning is also an observation about the API's accounting, not
proof about all internal computation.

The DeepSeek failures contained long visible answers despite zero reported
reasoning. Disabling hidden reasoning alone will not solve those failures.

## Issue 2: the response template is only a prompt instruction

The prompt asks for `<calculation>; <option letter>) <option value>`, but some
answers copy the literal `<calculation>` placeholder or produce visible prose.
The runner has no format validator or constrained response schema. Such
answers can currently count as completed if they do not hit the token limit.

Increasing the output limit alone would allow more unwanted output and would
not enforce the requested format. Mathematical accuracy has not been graded.

## What the local AgentOpt checkout offers

Reviewed checkout: `08b2d2c7fe370c884d956afbe540a09abc163c27`, from
`https://github.com/AgentOptimizer/agentopt.git`.

- `agentopt/src/agentopt/proxy/usage.py`: usage accounting includes reasoning
  tokens where appropriate and rejects unrecognized usage instead of silently
  treating it as zero. This supports inspecting actual usage after each call.
- `agentopt/src/agentopt/proxy/interceptor.py`: request forwarding, routing,
  response recording, and latency measurement. It is not a template enforcer
  or a direct reasoning-off solution.
- `agentopt/examples/selection/local/langgraph.py`: separates output production
  from evaluation. Its substring scoring example is unsuitable for reliably
  checking MathQA option letters; we should write task-specific validation.
- `agentopt/docs/benchmark-results/index.md`: describes a MathQA solver/critic
  benchmark with up to three iterations. The actual MathQA workflow is not
  included in the reviewed checkout, so we cannot infer its prompt or parser.

Adding a critic or retries is unnecessary for the immediate formatting fix
and would change the current one-attempt baseline and its cost.

## Baseline proposed next steps, before formatting trials

1. Use settings per model and a fixed provider endpoint for reproducibility.
   Check endpoint support before requiring parameters, disable provider
   fallbacks for the controlled test, and verify the actual reasoning usage.
   Current public metadata lists no reasoning parameter for Qwen 2.5's Phala
   endpoint, so do not blindly send a shared reasoning parameter while also
   requiring support for every requested parameter.
2. For Qwen3, SiliconFlow is a candidate: all three observed calls reported
   zero reasoning and current metadata advertises structured-output support.
   This small observation is not a guarantee. Qwen's native hard switch is
   `enable_thinking=False` in the serving chat template; `/no_think` is a soft
   prompt switch. Do not assume arbitrary native server settings can simply
   be passed through OpenRouter.
3. Replace placeholder-only instructions with a concrete example, such as
   `30*29=870; c) 870`. For stronger enforcement, request a JSON schema with
   `calculation`, `option`, and `value`, and validate the parsed fields locally.
   Structured-output support varies by endpoint. Preserve raw answer text and
   the entire API response; store parsed fields separately. If desired, render
   those fields as the familiar calculation/output line in the table while
   clearly distinguishing that display from the original answer.
4. Track generation success, format validity, and mathematical correctness
   separately. A schema can constrain structure, but does not establish correct
   calculations. Unknown reasoning usage must remain unknown, not become zero.
5. Before another 20-question run, use a small controlled trial containing a
   simple question and a previously truncated question. Inspect routing,
   reasoning usage, format, finish reason, cost, and latency. No new paid model
   calls were made during this investigation.

## Primary documentation checked

- [OpenRouter reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens):
  hiding reasoning with `exclude` still computes and bills it; supported
  controls vary, and reasoning generally shares the output-token budget.
- [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection):
  provider selection, fallbacks, and `require_parameters`. Advertised parameter
  support does not itself prove that a specific nested setting was honored.
- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs):
  JSON schema requests and provider-specific support.
- [Qwen3 official model card](https://huggingface.co/Qwen/Qwen3-32B): hard and
  soft switches between thinking and non-thinking modes.
- Public endpoint metadata checked for
  [Qwen 2.5](https://openrouter.ai/api/v1/models/qwen/qwen-2.5-7b-instruct/endpoints),
  [Qwen3](https://openrouter.ai/api/v1/models/qwen/qwen3-32b/endpoints), and
  [DeepSeek V3.2](https://openrouter.ai/api/v1/models/deepseek/deepseek-v3.2/endpoints).

Endpoint availability and supported parameters can change; recheck before
choosing the settings for the next run.

## Stage 1 implemented: formatting trials, before accuracy grading

`scripts/mathqa_experiments.py` previews one model/experiment without HTTP calls
or database changes. `--run` creates and executes a new run, defaulting to the
first five questions. It reuses the existing scheduler: up to five concurrent
requests, one attempt per question, no automatic retries. The original batch
command remains the baseline until trials identify settings to adopt.

Each model has explicit candidate settings, checked against public endpoint
metadata on 2026-10-04 (Qwen2.5 metadata was cached four days earlier):

| Alias | Model | Fixed endpoint | Initial controls |
| --- | --- | --- | --- |
| `qwen25` | Qwen2.5 7B Instruct | `phala` | temperature 0; omit unsupported reasoning control |
| `qwen3` | Qwen3 32B | `siliconflow/fp8` | reasoning enabled=false; temperature 0.7, top_p 0.8, top_k 20 |
| `deepseek` | DeepSeek V3.2 | `deepinfra/fp4` | reasoning enabled=false; temperature 0 |

All candidates use max_tokens=256, stream=false, provider.only, disabled
fallbacks, and require_parameters=true. This is an initial bounded trial, not
a claim that 256 tokens or these sampling settings are optimal. Qwen3 sampling
follows its official non-thinking guidance for the advertised controls;
SiliconFlow does not advertise min_p. DeepInfra was selected for DeepSeek
because it advertises both reasoning and structured outputs and was healthy
in the checked metadata; SiliconFlow's DeepSeek endpoint reported status -2.
Provider restrictions can fail when the endpoint is unavailable; there is no
silent switch to another provider. Recheck metadata before paid trials.

The gateway reasoning-off request remains a hypothesis to test by inspecting
returned usage. No native enable_thinking or thinking parameter is assumed to
pass through OpenRouter. Qwen3-only `/no_think` variants test the documented
soft prompt switch separately. We do not use reasoning.exclude to hide evidence.

Available experiments:

- `line-example`: concrete unrelated example `6*7=42; b) 42`.
- `json-prompt`: the same fields as JSON, enforced only by prompt and local validation.
- `json-schema`: exactly the same JSON prompt, adding strict API JSON schema.
- Qwen3 only: `line-no-think` and `json-schema-no-think`, adding `/no_think`
  to the corresponding prompt while retaining the other settings.

The local contracts are `line-v1` and `json-v1`. Both require a nonempty compact
calculation (at most 160 characters), one lowercase option letter a-e, and a
nonempty value (at most 120 characters). Values must match the chosen option
text, ignoring whitespace. Calculations must contain a digit and a math
operation; multi-letter words are restricted to the named math functions in
the prompt. This is a lexical formatting check, not expression evaluation or
proof of mathematical correctness. Fields cannot contain newlines, markup,
placeholders, or LaTeX. Outer whitespace is accepted; JSON may be pretty-printed,
but field values must be single-line strings. Duplicate JSON fields, extra
fields, missing fields, Markdown fences, and surrounding commentary are invalid.
The API schema constrains fields/types/option enumeration; local validation
additionally enforces brevity and option/value agreement. No answer key,
rationale, or correct-option field is sent to the model. The example avoids
the earlier suggested 30*29=870, which would reveal the first question's answer.

New runs snapshot configurations in request_settings_json.model_configs;
each call continues to save its exact request and untouched answer, full API
JSON and raw response body. The additive call_validations table stores contract,
parsed fields, validity and errors separately. Legacy calls have no inferred
validation results. Existing generation statuses keep their original meaning.
No automatic backfill, recovery, retry, or mathematical grading is introduced.

The JSON diagnostic report records each call's answer, parsed fields, errors,
generation status, finish reason, returned provider, reported reasoning tokens,
cost and latency. Unknown reasoning counts remain null. Summaries separate
generation failures from invalid completed responses. Format success requires
both a completed generation and valid format, divided by all selected questions;
even syntactically valid truncated responses are unsuccessful. This is a format
score, not accuracy. The existing HTML exporter still shows original answers.
The CLI returns 1 if any selected question lacks a completed, valid response.
The read-only report command also handles databases that have not been migrated;
legacy validation stays unknown and the latest saved attempt is shown.

```powershell
# Read-only catalog and preview; neither makes API requests.
uv run python scripts/mathqa_experiments.py --list
uv run python scripts/mathqa_experiments.py --model qwen25 --experiment line-example

# Only after explicitly deciding to make this five-call paid trial:
uv run python scripts/mathqa_experiments.py --model qwen25 --experiment line-example --run

# Inspect a saved trial without making new API requests:
uv run python scripts/mathqa_experiments.py --report-run YOUR_RUN_ID
```

Start with Qwen2.5's line example, inspect all five original answers and
validation diagnostics, then try JSON prompt/schema on that same model if
needed. Continue to Qwen3 and DeepSeek in the existing model order, one trial
at a time. Five questions are a quick diagnostic, not a reliable accuracy
estimate. After reviewing formatting trials, choose settings before implementing
post-batch accuracy grading with all selected questions as its denominator.

Offline validation: 16 tests pass, including all ten baseline tests and six
focused tests for contract parsing, settings, safe previews, raw preservation,
separate outcomes, and additive migration/legacy export. No paid calls were
made to validate this implementation.

## First authorized formatting trial: Qwen2.5 line-example

Executed on 2026-10-04 after explicit user authorization, run
`9fae80a9-1d2e-40b5-978e-dda3691522c1`. Exactly five calls were made, with
concurrency five and no retries. The fixed Phala endpoint was rechecked before
execution and returned status 0 with the requested sampling controls advertised.
Settings: temperature=0, max_tokens=256, stream=false, Phala only, no fallbacks,
require_parameters=true, and no unsupported reasoning parameter.

All five calls returned HTTP 200 and finish_reason=stop. Generation completed
5/5; strict local formatting passed 3/5 (60%). There were two invalid completed
responses, no missing calls, and no truncations. All five returned provider Phala
and reported zero reasoning tokens. Reported cost totaled USD 0.0001702;
completion tokens totaled 178. Individual request latency ranged from 0.499
to 1.054 seconds; saved batch start-to-finish duration was about 1.175 seconds.

Original answers, without corrections:

| Question ID | Original answer | Format valid |
| --- | --- | --- |
| mathqa_test_0002 | `28*(28-1)/2=392; c) 870` | Yes |
| mathqa_test_0013 | `sum(floor(1000/pow(10, i)) - floor(999/pow(10, i-1))) for i in (1,2,3)=192;c) 192` | No |
| mathqa_test_0026 | `(0.3*60000+0.4*72000)/(60000+72000)=0.344;b) 34.4%` | No |
| mathqa_test_0047 | `gcd(1345,775)=85; b) 10` | Yes |
| mathqa_test_0079 | `1638 * (1/2) / (1/2 + 1/3 + 1/4) = 756; c) 756` | Yes |

Both rejected answers failed the line parser because the required space after
the semicolon was absent. The parser stops there and preserves no parsed fields
for these answers; the saved error is "Expected one line: calculation; a-e) value."
Inspection also shows the zero-count expression uses sum, pow, for and in,
outside the allowed function/word list, and the tax answer does not copy the
option's internal percent spacing. These are observations, not additional saved
validator errors. Format-valid answers for questions 0002 and 0047 contain
incorrect/inconsistent calculations. No mathematical accuracy score was computed
or persisted. The prompt, contract and settings were not altered after the trial.

Full diagnostic report:
`results/mathqa_experiments/9fae80a9-1d2e-40b5-978e-dda3691522c1.json`.
Original-answer HTML:
`results/mathqa_tables/mathqa_9fae80a9-1d2e-40b5-978e-dda3691522c1.html`.
Original responses and raw bodies remain in SQLite. The script returned exit
code 1 because two responses were format-invalid, despite the generation run
status being completed.

The proposed next trial was Qwen2.5 json-schema on the same five questions, retaining
provider and sampling settings. This tests whether API structure constraints
improve compliance; local expression/value validation is still required. That
trial was subsequently executed as recorded in the next section.

## Second authorized formatting trial: Qwen2.5 json-schema

Executed on 2026-10-04 after explicit user authorization, run
`b28a220b-e65e-490e-998d-9f4ba62e03d1`. The same first five questions, Phala
endpoint, temperature 0, max_tokens 256, concurrency five, disabled fallbacks
and zero retries were retained. Phala metadata was rechecked before execution
and advertised response_format and structured_outputs with status 0. This
trial changed the prompt to JSON and supplied response_format.type=json_schema,
strict=true, with the three required string fields and the a-e option enum.

All five calls returned HTTP 200, finish_reason=stop, provider Phala, and zero
reported reasoning tokens. Generation completed 5/5 without truncation. JSON
parsing succeeded 4/5; the full local response contract passed 3/5 (60%), the
same full-format score as the first line-example trial. Two completed responses
were invalid. Total reported cost was USD 0.000198, with 262 completion tokens.
Individual latency ranged from 0.852 to 1.401 seconds; saved batch duration
was 1.515946 seconds. Exit code 1 reflects format failures, while the saved
generation run status is completed.

Original answers, without corrections:

| Question ID | Original answer | Format valid |
| --- | --- | --- |
| mathqa_test_0002 | `{"calculation": "28*27/2=378", "option": "d", "value": "352"}` | Yes |
| mathqa_test_0013 | `{"calculation": "sum(floor(1000/pow(10,i))/10+floor(1000/10/(pow(10,i)))*9 for i in range(3))+sum(1 for j in range(1,1001) if '0' in str(j))", "option": "b", "value": "191"}` | No |
| mathqa_test_0026 | `{"calculation": "(0.3*60000+0.4*72000)/(60000+72000)*100=35.6%\",\"option\":\"d\",\"value\":\"35.6 %\"}<tool_call>\n` | No |
| mathqa_test_0047 | `{"calculation": "gcd(1345, 775)", "option": "b", "value": "10"}` | Yes |
| mathqa_test_0079 | `{"calculation": "1638 * (1/2) / (1/2 + 1/3 + 1/4)=756", "option": "c", "value": "756"}` | Yes |

The zero-count answer parsed and had the required fields but failed the local
calculation lexical rule (sum, pow, for, in, range, if and str are outside its
allowed function/word list). The tax answer was not valid JSON: broken escaping
left a string unterminated and included a literal tool-call marker. It was not
truncated, refused, or returned as an API error. This demonstrates that the
strict schema request did not reliably produce schema-conforming answers on
this endpoint in this trial. Saved responses do not establish why enforcement
failed, nor isolate the effect of schema from the changed JSON prompt.

Format-valid responses still contain mathematical errors or inconsistencies:
the tickets calculation ends at 378 but selects 352, and the distribution answer
selects 10 while gcd(1345,775) is 5. No accuracy score was computed or persisted.
No prompts, settings, schemas or validators were altered after observing results.

Full diagnostic report:
`results/mathqa_experiments/b28a220b-e65e-490e-998d-9f4ba62e03d1.json`.
Original-answer HTML:
`results/mathqa_tables/mathqa_b28a220b-e65e-490e-998d-9f4ba62e03d1.html`.
Untouched original answers, entire API responses and raw bodies remain in SQLite.
Exactly this five-call trial was executed; no further paid calls were made.

## Third authorized formatting trial: Qwen2.5 json-prompt

Executed on 2026-10-04 after explicit user authorization, run
`b2415bae-c4a4-4c33-9fd5-20a3ca986bee`. The same JSON prompt as the schema
trial was used, omitting response_format entirely. The same first five questions,
Phala endpoint, temperature 0, max_tokens 256, concurrency five, disabled
fallbacks and zero retries were retained. Phala metadata was rechecked before
execution and reported status 0 with the requested sampling controls advertised.

All five calls returned HTTP 200, finish_reason=stop, provider Phala, and zero
reported reasoning tokens. Generation completed 5/5 with no truncations or
missing calls. All five answers parsed as JSON; full format compliance was
4/5 (80%), with one invalid completed response. Total reported cost was
USD 0.0001878, with 211 completion tokens. Individual latency ranged from
2.898 to 4.787 seconds; saved batch duration was 4.889133 seconds. Exit code 1
reflects the format failure; the saved generation run status is completed.

Original answers, without corrections:

| Question ID | Original answer | Format valid |
| --- | --- | --- |
| mathqa_test_0002 | `{"calculation":"28*(28-1)/2=380","option":"e","value":"380"}` | Yes |
| mathqa_test_0013 | `{"calculation":"sum(floor(1000/pow(10,i))-floor(999/pow(10,i)) for i in range(3))+100+10=192","option":"c","value":"192"}` | No |
| mathqa_test_0026 | `{"calculation":"(0.3*60000+0.4*72000)/(60000+72000)*100","option":"b","value":"34.4 %"}` | Yes |
| mathqa_test_0047 | `{"calculation":"gcd(1345,775)=91","option":"a","value":"91"}` | Yes |
| mathqa_test_0079 | `{"calculation":"1638 * (1/2) / (1/2 + 1/3 + 1/4)","option":"c","value":"756"}` | Yes |

The zero-count answer parsed and had the required fields but failed the local
calculation lexical rule (sum, pow, for, in and range are outside the allowed
function/word list). The saved error is "calculation must be a compact math
expression, not prose." Format-valid responses still contain mathematical
errors: the tickets expression does not evaluate to 380; the tax expression
does not yield the selected 34.4%; and gcd(1345,775) is 5 rather than 91.
No accuracy score was computed or persisted. No prompt, settings, schema or
validator changes were made after observing results.

Full diagnostic report:
`results/mathqa_experiments/b2415bae-c4a4-4c33-9fd5-20a3ca986bee.json`.
Original-answer HTML:
`results/mathqa_tables/mathqa_b2415bae-c4a4-4c33-9fd5-20a3ca986bee.html`.
Original answers, entire responses and raw bodies remain in SQLite. Exactly
five paid calls were made for this trial; no further trials were executed.

All three configured Qwen2.5 experiments have now been executed once:

| Experiment | Generation completed | Valid JSON | Full format compliance | Reported cost (USD) | Batch seconds |
| --- | --- | --- | --- | --- | --- |
| line-example | 5/5 | Not applicable | 3/5 (60%) | 0.0001702 | 1.175215 |
| json-schema | 5/5 | 4/5 | 3/5 (60%) | 0.0001980 | 1.515946 |
| json-prompt | 5/5 | 5/5 | 4/5 (80%) | 0.0001878 | 4.889133 |

Prompt-only JSON had the highest observed format score in these three
five-question trials. One run per variant is insufficient to establish a
reliable advantage, and this comparison is not mathematical accuracy grading.

## Selected Qwen2.5 configuration

On 2026-10-04 the user selected prompt-only JSON (`json-prompt`) for Qwen2.5.
The experiment CLI now uses it when `--model qwen25` is supplied without an
explicit `--experiment`. The selected configuration retains the tested JSON
prompt, Phala endpoint, temperature 0, max_tokens 256, local `json-v1` validation,
concurrency five and zero retries. It omits API response_format and unsupported
reasoning controls. This choice does not relax the validator or assert
mathematical correctness. Explicit experiment overrides remain available;
Qwen3 and DeepSeek retain their initial `line-example` defaults pending trials.
The original batch command remains the baseline; saved runs are unchanged.
No paid calls were made when recording this selection.

```powershell
# Preview the selected Qwen2.5 configuration without making API requests.
uv run python scripts/mathqa_experiments.py --model qwen25
```

## Qwen3 formatting experiment suite, 2026-10-04

All five configured variants were executed after explicit user authorization, with exactly 25 paid calls. Trials ran sequentially, with five concurrent calls within each trial and no retries.

Settings retained: SiliconFlow `siliconflow/fp8`, temperature 0.7, top_p 0.8, top_k 20, max_tokens 256, stream=false, reasoning.enabled=false, provider.only, allow_fallbacks=false, require_parameters=true. The endpoint was rechecked before execution: status 0, with reasoning, sampling and structured-output controls advertised. All trials used the same first five questions, without answer keys or rationales in requests.

All 25 calls returned HTTP 200, finish_reason=stop, provider SiliconFlow and zero reported reasoning tokens. There were no generation failures, truncations, missing responses or missing reported costs. Reported zero reasoning is an accounting observation, not proof about every internal computation.

Full local format compliance totaled 19/25; reported suite cost was USD 0.00151790. These are formatting results, not mathematical accuracy. No accuracy score was computed or stored.

| Experiment | Generation | Valid JSON | Full format | Invalid completed | Reported USD | Batch seconds |
| --- | --- | --- | --- | --- | --- | --- |
| line-example | 5/5 | Not applicable | 4/5 (80%) | 1 | 0.00027002 | 6.004450 |
| json-prompt | 5/5 | 5/5 | 4/5 (80%) | 1 | 0.00032475 | 3.802731 |
| json-schema | 5/5 | 5/5 | 4/5 (80%) | 1 | 0.00030765 | 3.620711 |
| line-no-think | 5/5 | Not applicable | 3/5 (60%) | 2 | 0.00028636 | 3.175482 |
| json-schema-no-think | 5/5 | 5/5 | 4/5 (80%) | 1 | 0.00032912 | 3.067371 |

All three JSON variants produced five parseable JSON objects with the required fields. The zero-count answer failed the calculation lexical rule in each JSON trial because its calculation included prose. The schema constrains types, fields and option enumeration; its descriptions do not constrain calculation text to an arithmetic expression.

The line-example tax answer used `34.4%` where the supplied option text is `34.4 %`, so exact option-text validation rejected it. The validator collapses whitespace runs but does not remove spaces between tokens. In line-no-think, the tickets answer contained extra semicolons and the tax answer used `b )` instead of `b)`, both failing the line parser. These strict contract results were retained without repair or retroactive rule changes.

Adding /no_think did not increase format compliance in these single trials. All variants already reported zero reasoning tokens. Temperature 0.7 and only five questions per variant limit conclusions about relative performance or causality. Four variants tied at 80%; there is no established format winner.

Some format-valid answers have incorrect calculations or disagree with their selected value. For example, the json-schema-no-think tickets answer asserts `(28+2)*(28+1)/2=870`, although the expression evaluates to 435. Format compliance remains separate from mathematical correctness. No prompts, settings, validators or selected defaults were changed after observing results.

Original answers below are preserved verbatim. Full API JSON, raw bodies, requests, usage, timings and errors remain in SQLite; per-run JSON diagnostics and HTML exports are also saved. All runs have generation status completed; each CLI returned 1 because at least one answer was format-invalid.

### line-example

Run ID: `23ddc195-5220-4a3f-a9b4-1d6c0ccca4f5`. [Diagnostic JSON](../results/mathqa_experiments/23ddc195-5220-4a3f-a9b4-1d6c0ccca4f5.json); [original-answer HTML](../results/mathqa_tables/mathqa_23ddc195-5220-4a3f-a9b4-1d6c0ccca4f5.html). Individual request latency: 1.792-5.872 seconds. Completion tokens: 164.

| Question ID | Original answer | Format valid | Saved validation errors |
| --- | --- | --- | --- |
| mathqa_test_0002 | `(28+2)*(28+1)/2=380; e) 380` | Yes | None |
| mathqa_test_0013 | `1000//10*1 + 1000//100*2 + 1000//1000*3; a) 190` | Yes | None |
| mathqa_test_0026 | `(60000*0.3 + 72000*0.4) / (60000 + 72000) = 0.344; b) 34.4%` | No | value must match the selected option text (ignoring whitespace). |
| mathqa_test_0047 | `gcd(1345,775)=5; d) 5` | Yes | None |
| mathqa_test_0079 | `1638/( (1/2)+(1/3)+(1/4) )*(1/2); c) 756` | Yes | None |

### json-prompt

Run ID: `78aec3a1-d554-4e54-861a-71a52a457481`. [Diagnostic JSON](../results/mathqa_experiments/78aec3a1-d554-4e54-861a-71a52a457481.json); [original-answer HTML](../results/mathqa_tables/mathqa_78aec3a1-d554-4e54-861a-71a52a457481.html). Individual request latency: 1.800-3.669 seconds. Completion tokens: 233.

| Question ID | Original answer | Format valid | Saved validation errors |
| --- | --- | --- | --- |
| mathqa_test_0002 | `{"calculation":"(28+2)*(28+1)/2=380","option":"e","value":"380"}` | Yes | None |
| mathqa_test_0013 | `{"calculation":"count zeros in 1-999 and add for 1000: 9*10^2*1 + 9*10*1 + 9*1 = 192","option":"c","value":"192"}` | No | calculation must be a compact math expression, not prose. |
| mathqa_test_0026 | `{"calculation":"(0.3*60000 + 0.4*72000)/(60000 + 72000)=35.6","option":"d","value":"35.6 %"}` | Yes | None |
| mathqa_test_0047 | `{"calculation":"gcd(1345,775)=5","option":"d","value":"5"}` | Yes | None |
| mathqa_test_0079 | `{"calculation":"1/2 + 1/3 + 1/4 = 13/12; a = 1638 * (1/2 / 13/12) = 756","option":"c","value":"756"}` | Yes | None |

### json-schema

Run ID: `c12bdeff-56bf-44c7-94d8-32f367637a4a`. [Diagnostic JSON](../results/mathqa_experiments/c12bdeff-56bf-44c7-94d8-32f367637a4a.json); [original-answer HTML](../results/mathqa_tables/mathqa_c12bdeff-56bf-44c7-94d8-32f367637a4a.html). Individual request latency: 2.289-3.465 seconds. Completion tokens: 203.

| Question ID | Original answer | Format valid | Saved validation errors |
| --- | --- | --- | --- |
| mathqa_test_0002 | `{"calculation":"(28+2)*(28+1)/2=435","option":"e","value":"380"}` | Yes | None |
| mathqa_test_0013 | `{"calculation":"count zeros in 1-999 and add for 1000","option":"c","value":"192"}` | No | calculation must be a compact math expression, not prose. |
| mathqa_test_0026 | `{"calculation":"(0.3*60000 + 0.4*72000)/(60000 + 72000)=35.6","option":"d","value":"35.6 %"}` | Yes | None |
| mathqa_test_0047 | `{"calculation":"gcd(1345,775)=5","option":"d","value":"5"}` | Yes | None |
| mathqa_test_0079 | `{"calculation":"1/2 + 1/3 + 1/4 = 13/12; 1638 * (1/2 / 13/12) = 756","option":"c","value":"756"}` | Yes | None |

### line-no-think

Run ID: `6890c5da-1166-4879-b022-2ad653c36abf`. [Diagnostic JSON](../results/mathqa_experiments/6890c5da-1166-4879-b022-2ad653c36abf.json); [original-answer HTML](../results/mathqa_tables/mathqa_6890c5da-1166-4879-b022-2ad653c36abf.html). Individual request latency: 1.599-3.058 seconds. Completion tokens: 188.

| Question ID | Original answer | Format valid | Saved validation errors |
| --- | --- | --- | --- |
| mathqa_test_0002 | `n=28+2; t=n*(n-1); t=380; e) 380` | No | Expected one line: calculation; a-e) value. |
| mathqa_test_0013 | `(999 // 10 % 10) * 1 + (999 // 100 % 10) * 2 + (999 // 1000 % 10) * 3; c) 192` | Yes | None |
| mathqa_test_0026 | `(60000*0.3 + 72000*0.4) / (60000 + 72000) = 0.344; b ) 34.4 %` | No | Expected one line: calculation; a-e) value. |
| mathqa_test_0047 | `gcd(1345, 775) = 5; d) 5` | Yes | None |
| mathqa_test_0079 | `1638 / (6 + 4 + 3) * 6 = 756; c) 756` | Yes | None |

### json-schema-no-think

Run ID: `df394bc2-b92f-4b73-9e44-dfc71c6dd9ef`. [Diagnostic JSON](../results/mathqa_experiments/df394bc2-b92f-4b73-9e44-dfc71c6dd9ef.json); [original-answer HTML](../results/mathqa_tables/mathqa_df394bc2-b92f-4b73-9e44-dfc71c6dd9ef.html). Individual request latency: 2.165-2.957 seconds. Completion tokens: 236.

| Question ID | Original answer | Format valid | Saved validation errors |
| --- | --- | --- | --- |
| mathqa_test_0002 | `{"calculation":"(28+2)*(28+1)/2=870","option":"c","value":"870"}` | Yes | None |
| mathqa_test_0013 | `{"calculation":"count zeros in numbers 1 to 1000: 9 (1-99) + 100 (100-999) + 3 (1000) = 192","option":"c","value":"192"}` | No | calculation must be a compact math expression, not prose. |
| mathqa_test_0026 | `{"calculation":"(0.3*60000 + 0.4*72000)/(60000 + 72000)=35.6","option":"d","value":"35.6 %"}` | Yes | None |
| mathqa_test_0047 | `{"calculation":"gcd(1345,775)=5","option":"d","value":"5"}` | Yes | None |
| mathqa_test_0079 | `{"calculation":"1/2 : 1/3 : 1/4 = 6 : 4 : 3; a = 1638 * 6 / (6+4+3)= 756","option":"c","value":"756"}` | Yes | None |

All five Qwen3 experiments are complete. Qwen3 retains its prior line-example default pending the user's selection. No DeepSeek experiments or other paid trials were run as part of this suite.

## Selected Qwen3 configuration

On 2026-10-04 the user selected `json-schema-no-think` for Qwen3. The experiment
CLI now selects it when `--model qwen3` is supplied without `--experiment`.
This retains the tested JSON prompt with `/no_think`, strict JSON schema,
SiliconFlow `siliconflow/fp8`, temperature 0.7, top_p 0.8, top_k 20,
max_tokens 256, reasoning.enabled=false, local json-v1 validation, concurrency
five and zero retries. Explicit overrides remain available. The selection
does not relax the response contract or change previous saved runs. Qwen2.5's
selected prompt-only JSON configuration remains in place. No paid Qwen3 calls
were made while recording this choice.

## Selected DeepSeek configuration

The user selected `json-prompt` for DeepSeek on 2026-10-04 after reviewing its
three trials. The experiment CLI now chooses it when `--model deepseek` is
supplied without `--experiment`. This retains the tested JSON prompt, DeepInfra
`deepinfra/fp4`, temperature 0, max_tokens 256, reasoning.enabled=false, local
json-v1 validation, concurrency five and zero retries. API response_format is
omitted. The validator and saved runs are unchanged; explicit experiment
overrides remain available. No paid calls were made to record this selection.

All three model defaults have now been selected:

| Model | Selected experiment |
| --- | --- |
| Qwen2.5 | json-prompt |
| Qwen3 | json-schema-no-think |
| DeepSeek V3.2 | json-prompt |

These defaults apply to mathqa_experiments.py. The original mathqa_batch.py CLI
remains the baseline pending integration of the selected configurations.

## DeepSeek formatting experiment suite, 2026-10-04

All three configured DeepSeek variants were attempted after explicit user authorization, with exactly 15 requests. The preceding interruption happened after the Qwen3 default change and endpoint preflight, before any DeepSeek trial was created or sent. SQLite was checked before continuation to avoid duplicate calls. Trials ran sequentially with five concurrent requests each, one attempt per question and no retries.

Settings retained: DeepInfra `deepinfra/fp4`, temperature 0, max_tokens 256, stream=false, reasoning.enabled=false, provider.only, allow_fallbacks=false and require_parameters=true. Endpoint preflight reported status 0 with reasoning, sampling and structured-output controls advertised. All trials used the same first five questions, without answer keys or rationales in the model prompts.

Nine requests returned HTTP 200, provider DeepInfra, finish_reason=stop and zero reported reasoning tokens. Six were rejected with HTTP 429, provider_error_code=engine_overloaded, limit_source=upstream_provider_shared_pool. Those six have no answer, reasoning-token count or reported cost. Unknown usage remains unknown. There were no truncated generations or missing call records. No retries or provider changes were attempted.

Primary format success was 2/15, using all selected questions across the three trials. Seven completed responses were format-invalid, separately from the six API failures. Reported costs sum to USD 0.00066530, with cost unknown for six rejected requests; this is the sum of reported costs, not a complete measured total for every attempt. No mathematical accuracy score was computed or stored.

| Experiment | Generation completed | API failures | Invalid completed | Valid JSON (all selected) | Full format | Reported USD | Missing costs | Batch seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| line-example | 3/5 | 2 | 2 | Not applicable | 1/5 (20%) | 0.00018324 | 2 | 14.753746 |
| json-prompt | 5/5 | 0 | 4 | 5/5 | 1/5 (20%) | 0.00042212 | 0 | 5.913966 |
| json-schema | 1/5 | 4 | 1 | 1/5 | 0/5 (0%) | 0.00005994 | 4 | 7.779783 |

All five returned prompt-only JSON answers parsed successfully. The only returned schema answer also parsed successfully; four other schema calls were rate-limited and returned no answer. This prevents a clean comparison of schema versus prompt-only reliability.

Line-example: tickets and tax received HTTP 429. The zero-count calculation used count0, rejected by the rule allowing only single-letter variables and named math functions. The shares answer had additional semicolons, rejected by the line parser. The distribution answer passed format validation but selected e) none of these despite stating gcd=5.

Json-prompt: four calculation fields used multi-letter variable labels (stations_between, total_stations, tickets, zeros, john_tax, ingrid_tax, total_income, total_tax, combined_rate, total, ratio, sum or a_share), which the contract disallows. The tax calculation also exceeded 160 characters. Pretty-printed JSON was accepted; line breaks around fields were not the failure. The distribution calculation passed local validation.

Json-schema: the tickets answer parsed as JSON but used stations and tickets as variable labels, failing the local lexical rule. The other four requests received HTTP 429. The JSON schema constrains fields/types/option enumeration; its descriptions do not enforce the calculation vocabulary.

These observed low format scores partly reflect the deliberately narrow calculation vocabulary rather than JSON parsing failure. No prompts, schemas, settings or validators were altered after observing results. No DeepSeek variant was selected automatically. Qwen2.5 remains json-prompt and Qwen3 is now the user-selected json-schema-no-think; DeepSeek retains its initial line-example default pending selection.

Original answers and errors are preserved below. JSON blocks preserve the original formatting and field order. Full API JSON, raw bodies, requests and usage remain in SQLite; per-run diagnostic JSON and HTML exports are saved. No additional paid calls were made.

### DeepSeek line-example

Run ID: `23f31503-c642-4617-88c2-dfb1864fa1ef`. [Diagnostic JSON](../results/mathqa_experiments/23f31503-c642-4617-88c2-dfb1864fa1ef.json); [original-answer HTML](../results/mathqa_tables/mathqa_23f31503-c642-4617-88c2-dfb1864fa1ef.html). All-request latency: 0.323-14.632 seconds. Reported completion tokens: 71 (excluding unknown usage).

**mathqa_test_0002**: generation failed; format invalid.

No answer returned. OpenRouter returned HTTP 429.

Saved validation errors: Missing answer text.

**mathqa_test_0013**: generation completed; format invalid.

```text
count0=9*10+9*10+100+1; c) 192
```

Saved validation errors: calculation must be a compact math expression, not prose.

**mathqa_test_0026**: generation failed; format invalid.

No answer returned. OpenRouter returned HTTP 429.

Saved validation errors: Missing answer text.

**mathqa_test_0047**: generation completed; format valid.

```text
gcd(1345,775)=5; e) none of these
```

Saved validation errors: None

**mathqa_test_0079**: generation completed; format invalid.

```text
1/2:1/3:1/4=6:4:3;1638/(6+4+3)*6=756; c) 756
```

Saved validation errors: Expected one line: calculation; a-e) value.

### DeepSeek json-prompt

Run ID: `b7c8ec54-d98e-4f19-88b5-feb81334efac`. [Diagnostic JSON](../results/mathqa_experiments/b7c8ec54-d98e-4f19-88b5-feb81334efac.json); [original-answer HTML](../results/mathqa_tables/mathqa_b7c8ec54-d98e-4f19-88b5-feb81334efac.html). All-request latency: 5.557-5.797 seconds. Reported completion tokens: 363 (excluding unknown usage).

**mathqa_test_0002**: generation completed; format invalid.

```json
{
  "calculation": "stations_between=28, total_stations=28+2=30, tickets=30*29=870",
  "option": "c",
  "value": "870"
}
```

Saved validation errors: calculation must be a compact math expression, not prose.

**mathqa_test_0013**: generation completed; format invalid.

```json
{
  "calculation": "zeros=floor(1000/10)+floor(1000/100)*9+floor(1000/1000)*99+1=100+90+99+1=192",
  "option": "c",
  "value": "192"
}
```

Saved validation errors: calculation must be a compact math expression, not prose.

**mathqa_test_0026**: generation completed; format invalid.

```json
{"calculation":"john_tax=60000*0.3=18000; ingrid_tax=72000*0.4=28800; total_income=60000+72000=132000; total_tax=18000+28800=46800; combined_rate=46800/132000=0.354545...=35.4545%","option":"d","value":"35.6 %"}
```

Saved validation errors: calculation must be a single line of at most 160 characters without markup or placeholders. calculation must be a compact math expression, not prose.

**mathqa_test_0047**: generation completed; format valid.

```json
{
  "calculation": "gcd(1345,775)=gcd(775,570)=gcd(570,205)=gcd(205,160)=gcd(160,45)=gcd(45,25)=gcd(25,20)=gcd(20,5)=gcd(5,0)=5",
  "option": "d",
  "value": "5"
}
```

Saved validation errors: None

**mathqa_test_0079**: generation completed; format invalid.

```json
{
  "calculation": "total=1638; ratio=1/2:1/3:1/4; lcm(2,3,4)=12; a:b:c=6:4:3; sum=6+4+3=13; a_share=1638*6/13=756",
  "option": "c",
  "value": "756"
}
```

Saved validation errors: calculation must be a compact math expression, not prose.

### DeepSeek json-schema

Run ID: `ef6406e6-f5a2-4900-bdba-2be543494ee0`. [Diagnostic JSON](../results/mathqa_experiments/ef6406e6-f5a2-4900-bdba-2be543494ee0.json); [original-answer HTML](../results/mathqa_tables/mathqa_ef6406e6-f5a2-4900-bdba-2be543494ee0.html). All-request latency: 0.238-7.696 seconds. Reported completion tokens: 38 (excluding unknown usage).

**mathqa_test_0002**: generation completed; format invalid.

```json
{
  "calculation": "stations=28+2=30, tickets=30*29=870",
  "option": "c",
  "value": "870"
}
```

Saved validation errors: calculation must be a compact math expression, not prose.

**mathqa_test_0013**: generation failed; format invalid.

No answer returned. OpenRouter returned HTTP 429.

Saved validation errors: Missing answer text.

**mathqa_test_0026**: generation failed; format invalid.

No answer returned. OpenRouter returned HTTP 429.

Saved validation errors: Missing answer text.

**mathqa_test_0047**: generation failed; format invalid.

No answer returned. OpenRouter returned HTTP 429.

Saved validation errors: Missing answer text.

**mathqa_test_0079**: generation failed; format invalid.

No answer returned. OpenRouter returned HTTP 429.

Saved validation errors: Missing answer text.
