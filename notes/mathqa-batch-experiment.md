# MathQA batch baseline and open issues

Reviewed on 2026-10-04. This records the implemented baseline and observations
from the saved API responses. The proposed fixes below are not implemented.

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

## Proposed next steps, not yet implemented

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
