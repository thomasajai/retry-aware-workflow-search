# Provisional verifier choice and offline loop — October 7, 2026

The user chose to proceed with Gemini 2.5 rather than spend more time selecting
a verifier. Use **Gemini 2.5 Flash-Lite with recomputation and reasoning** as
the provisional fixed verifier. Further verifier-selection experiments are
deferred. The observed mistakes remain in the results; this decision allows
workflow development to proceed without claiming the verifier is error-free.

| Frozen verifier control | Value |
| --- | --- |
| Internal profile | `flashlite25__reasoning` |
| Model | `google/gemini-2.5-flash-lite` |
| Provider pin | `google-ai-studio`; exclude flex/priority, no fallback |
| Temperature | 0 |
| Reasoning budget | 512 tokens |
| Total output cap | 1,024 tokens, including reasoning |
| Prompt | Independently recompute, then audit reasoning and selected option |
| Output | Exactly one Boolean `accepted` field |

The selection uses the existing tested profile unchanged. Workflow
configurations snapshot its complete prompt, settings, and provider controls;
the original screening profiles and stored plans retain their identities.

## Implemented offline

`scripts/mathqa_workflow.py` now implements one LangGraph for all 27 ordered
solver triples. Its solver, usability, verifier, advance, and finish nodes use
the existing workflow storage. Repeated solver models are allowed. Each
execution has at most three solver slots and six requests, with fewer requests
when an answer is accepted early or unusable.

Solver requests are rebuilt from the original question/options at every slot.
They contain no prior answer, feedback, attempt indicator, key, rationale, or
review label. Usability checks allow extractable cosmetic differences; they do
not grade mathematics. Unusable solver answers skip the verifier. Acceptance
stops immediately, and no rejected answer is returned as a fallback.

Known-billing solver failures consume a slot. Invalid/truncated verifier output
is recorded separately from rejection and advances to the next solver. If all
three slots finish without acceptance, the execution scores zero. A terminal
execution containing technical errors is labeled failed rather than describing
those errors as three mathematical rejections.

Calls are recorded before invoking the supplied sender, then finished with
their original payload, usage, costs, finish reason, and timing. The sender
receives only the built request. The runner requires explicit numeric limits,
conservative per-call reservations, and expected returned providers. Its serial
run-wide gate counts previous calls and costs across configurations/executions.
Unknown billing/usage, provider/model drift, token inconsistencies, reservation
overruns, exhausted budget/request cap, and cancellation stop scheduling and
mark the run incomplete. An unexpected sender error leaves a finished error
record and marks the execution/run interrupted. There is no automatic resume,
transport retry, provider fallback, or graph checkpoint reuse.

`scripts/mathqa_workflow_grading.py` independently checks the saved dataset
checksum and runtime question, then atomically stores option grades for
attempts and the final execution. A wrong accepted answer scores zero; a
rejected answer with the correct option does not rescue an exhausted execution.
Option correctness does not imply valid reasoning: reasoning labels remain
unknown unless separately reviewed. Incomplete executions receive no final
score. Duplicate grading versions are rejected without partial writes.

`workflow_model_configs()` adds proposed solver settings without changing
legacy batch defaults: temperature **0.2**, total output cap **512**, existing
prompts/provider pins, and existing other sampling controls. The larger cap
addresses previous 256-token truncations provisionally. These solver settings
still need provider preflight and a live integration pilot before the sweep.

## Verification and controlled trace

**112 offline tests pass**, including 23 new workflow/demo tests. They cover
first/second/third acceptance, all rejections, different models in each slot,
repetition, request isolation, unusable/cosmetic answers, truncation, invalid
verdicts, accepted wrong answers, independent grading, budget stops before or
between requests, shared run spending, unknown billing, usage/provider drift,
cancellation, unexpected errors, and mocked HTTP request/response integration.

A saved controlled demo contains four executions with sixteen mock calls:

| Controlled scenario | Solver slots reached | Outcome | Independent score |
| --- | ---: | --- | ---: |
| Accept first answer | 1 | Accepted | 1 |
| Reject twice, accept third | 3 | Accepted | 1 |
| Reject all three, despite correct options | 3 | Exhausted | 0 |
| Accept a wrong option | 1 | Accepted | 0 |

These are routing demonstrations, not live accuracy measurements. The demo
writes a separate SQLite database under ignored workflow previews; it neither
loads credentials nor makes HTTP requests. The real experiment database still
contains the same 81 verifier calls across three runs, costing $0.00784018.
Its integrity and foreign-key checks pass. No OpenRouter credits were consumed
by this implementation, testing, preview, or demo.

Artifacts:

- Configuration preview: `results/workflow_previews/workflow-configs-2026-10-07.json`.
- Controlled trace/report: `results/workflow_previews/loop-demo-2026-10-07/report.json`.
- Controlled database: `results/workflow_previews/loop-demo-2026-10-07/controlled-loop.sqlite3`.
- Source: `scripts/mathqa_workflow.py`, `scripts/mathqa_workflow_grading.py`,
  `scripts/mathqa_workflow_demo.py`, and `tests/test_mathqa_workflow.py`.

Offline commands:

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_workflow.py --preview
.\.venv\Scripts\python.exe scripts/mathqa_workflow_demo.py --output results/workflow_previews/another-controlled-demo
```

The preview never writes experiment observations. The demo refuses to overwrite
an existing directory. Neither command has a paid execution option. The graph
uses the installed LangGraph runtime; [its documented graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
supports the state, nodes, conditional routing, and compilation used here.

## Next milestone step

The offline part of Milestone 3 is complete. A small **live** loop pilot remains,
so Milestone 3 as a whole is still open. Next prepare the explicit HTTP adapter,
frozen pilot plan, current solver/verifier endpoint controls and prices, numeric
spending/request limits, and advance cost breakdown. The runner deliberately
has no default sender or paid CLI yet. No new live run is authorized by this
provisional verifier decision. After an approved pilot demonstrates the actual
integration, proceed to sequence evaluation rather than reopening verifier
selection automatically.
