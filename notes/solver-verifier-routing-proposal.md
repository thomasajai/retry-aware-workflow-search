# DeepSeek automatic routing check — October 8, 2026

Status: implementation and offline preparation authorized by the user. This
single paid check awaits approval of its **$0.07 / 36-request limits** under the
[OpenRouter spending rule](../README.md#openrouter-spending-rule). No generation
requests were made during preparation. Completing this check does not authorize
the broad evaluation, a rerun, or another provider/model change.

## Purpose and routing policy

Keep DeepSeek V3.2 and test whether OpenRouter routing across providers avoids
the capacity bottlenecks seen with pinned DeepInfra and Venice. Use the same two
previously exposed pilot questions, `mathqa_test_0002` and `mathqa_test_0047`,
three repetitions each: **six executions** of `deepseek-deepseek-deepseek` with
the fixed Gemini 2.5 Flash-Lite recomputation/reasoning verifier. This provides
availability and integration evidence, not a new verifier evaluation or a
reliable accuracy estimate. Sustained availability remains uncertain.

The new opt-in `auto` DeepSeek profile removes `provider.only` and sets no
provider order or sort. It uses OpenRouter's default routing with
`allow_fallbacks=true`, `require_parameters=true`, and `max_price` ceilings of
**$0.60 input / $1.70 output per million tokens**, with zero per-request fee.
The broader ceilings permit more provider choices than the old Venice prices
while keeping a finite, reviewed budget. See
[OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection).

Keep temperature 0.2, reasoning disabled, solver output cap 512, and original
question/options-only prompts for all three mathematical attempts. Gemini stays
pinned to `google-ai-studio`, temperature zero, reasoning budget 512, total
output cap 1,024. Calls are serial with 60-second inactivity timeouts. Local
usability checks and independent option-key grading are unchanged. Three
mathematical rejections score zero; technical stops remain incomplete.

**No client transport retries or unknown-billing holds apply to this check.**
OpenRouter may try providers internally within one HTTP request. Our maximum
counts client HTTP requests to OpenRouter; it does not claim to count or bound
individual upstream tries. Successful reported charges are recorded in full.
Missing cost/usage, unexpected model/provider, inconsistent usage, a charge
above the token-price ceiling, a reservation overrun, or a gateway failure stops
scheduling. Failed requests can have unresolved charges; no zero-cost inference.

## Provider capabilities and reproducibility

Free public metadata refreshed at **2026-10-08 18:34:54 UTC (2:34:54 p.m. EDT)**:
[DeepSeek endpoints](https://openrouter.ai/api/v1/models/deepseek/deepseek-v3.2/endpoints),
[Gemini endpoints](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints).

Eight active DeepSeek endpoints advertise our controls and fit the ceilings:

| Provider | Endpoint tag | USD per million input/output | Advertised quantization |
| --- | --- | --- | --- |
| GMICloud | `gmicloud/fp8` | $0.2088 / $0.3096 | fp8 |
| AtlasCloud | `atlas-cloud/fp8` | $0.26 / $0.38 | fp8 |
| DeepInfra | `deepinfra/fp4` | $0.26 / $0.38 | fp4 |
| Venice | `venice` | $0.26829 / $0.39024 | unknown |
| Baidu | `baidu/fp8` | $0.28 / $0.42 | fp8 |
| DigitalOcean | `digitalocean` | $0.30 / $0.96 | unknown |
| Friendli | `friendli` | $0.50 / $1.50 | unknown |
| Google | `google-vertex` | $0.56 / $1.68 | unknown |

These are advertised candidates, not guarantees of capacity or routing given
account settings. Preflight also excludes inactive providers, unsupported
controls/output limits, invalid prices, nonzero request fees, and separately
priced reasoning above the output ceiling. Provider names and full eligible
endpoint metadata are frozen in the plan. A response naming a provider outside
that frozen set stops further requests; this is a response audit, not an
outgoing single-provider pin. The gateway's price/parameter filters still apply.

Store each returned provider and full response/usage in the existing call rows;
reports add counts, known spend and unresolved charges by actual provider.
Endpoint quantization metadata is saved, but we cannot infer the exact endpoint
or quantization used from a provider name alone. Results describe DeepSeek under
this fixed routing policy. The model search remains 27 triples; changing
routing creates a new configuration snapshot, not additional solver aliases.

## Advance cost disclosure

Use the **routing ceiling rates**, rather than the cheapest candidate, to
estimate DeepSeek cost and reserve each call. Actual reported cost may be lower.

| Role/model | Routing and USD per million input/output | Expected / max calls | Estimated input/output tokens | Input subtotal | Output subtotal | Estimated role total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek V3.2 solver | automatic; ceiling $0.60 / $1.70 | 12 / 18 | 4,752 / 1,152 | $0.0028512 | $0.0019584 | $0.0048096 |
| Gemini 2.5 Flash-Lite verifier | Google AI Studio; $0.10 / $0.40 | 12 / 18 | 7,296 / 6,144 | $0.0007296 | $0.0024576 | $0.0031872 |

Expected **24 gateway requests / $0.0079968**, approximately **$0.008**. Maximum
**36 gateway requests**, eighteen per role. Assumptions: two mathematical
attempts per execution, 96 solver output tokens, 512 verifier output tokens
including reasoning once, message characters/3 plus 96 framing tokens for
inputs, no cache discount. Early acceptance reduces actual calls; rejection
and longer output can increase them within the approved limits.

Full-cap conservative reservations: solver **$0.0316080**, verifier
**$0.0263250**, total **$0.0579330**. Proposed scheduling cap **$0.07**. No
additional network-retry or unknown-charge allowance. Reservations use full
UTF-8 request size plus 256 framing tokens, full output caps and an 8,192-character
calculation when stressing verifier input. These are conservative estimates,
not guarantees of tokenization or billing. Before every request, known new spend
plus that request's reservation must fit the cap. An unreported charge stops
the run and remains unresolved; the cap is not described as a settled bill.

Prior development and availability checks remain separate: **$0.00990433555
known spend plus five unresolved charges** across those three runs. This figure
does not represent all project/account spending. The new plan neither reconciles
those charges nor authorizes spending to investigate them.

## Implementation and validation

Changes are confined to workflow profiles, provider preflight, runner guards,
the availability/evaluation adapters, and provider reporting. Existing default
pins and old retry snapshots remain available. No new database migration,
dependency, Alembic setup, or live database mutation is required for preparation.
The existing paid adapter still binds source/migration hashes, dataset,
exposure, schedule, model controls, prices, and metadata. A used plan cannot be
rerun/resumed automatically, and paid CLI options cannot change frozen routing.

All **165 offline tests pass**, including twelve new routing tests. They simulate provider changes, all three
mathematical rejections, original-only retry inputs, accepted wrong options,
unknown billing, unexpected model/provider, known gateway failures, price
overruns, budget stops before HTTP, ineligible endpoints, frozen routing drift,
and unchanged 27-sequence question selection. The full suite completed in
280.693 seconds. A separate comparison against commit `44e5b01` confirms exact
equality of legacy model profiles and all pinned workflow builders, both with
and without the old transport-retry policy. The frozen routed plan validates;
read-only checks of the live database pass integrity and foreign-key checks,
and all three historical stopped runs remain separate. No new migration or
paid call occurred during these checks.

Frozen local plan:
`results/workflow_previews/routed-availability-plan-2026-10-08.json`, SHA-256
`7b57f9602545463503be34e0b6066690c4ad1f385b6a3cccfbba20400233ff59`.
Metadata must be less than twenty-four hours old; refresh and re-disclose a new
plan if delayed. Report known spend, unresolved charges, coverage, actual
providers, retry positions, and what this check establishes at the next
checkpoint. No automatic broad evaluation follows.
