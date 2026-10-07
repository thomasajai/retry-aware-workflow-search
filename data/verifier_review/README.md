# Verifier review fixtures

`cases.json` contains 12 hand-authored synthetic diagnostics, reviewed by Codex
independently of any candidate verifier. They are assistant-reviewed examples,
not human annotations or a representative sample of natural solver errors.

They cover valid reasoning and shortcuts, readable legacy format violations,
wrong options, a correct option with incorrect arithmetic, true arithmetic with
a wrong word-problem interpretation, conflicting values, unusable answers, and
an uncertain rounding convention. Each case includes reviewer attribution and
an explanation. No candidate verifier was called to create these labels.

`expected_accept: null` means no binary verdict label is supplied. Unusable cases
skip the verifier. The uncertain usable case may be inspected diagnostically but
must remain outside binary quality denominators. Natural saved answers have
answer-key labels and unknown reasoning validity until independently reviewed.

The preview stores labels separately from the exact proposed API requests.
Only the problem, choices, and solver proposal enter a verifier request. Results
from these controlled diagnostics must be reported separately from natural
saved-answer screening. More independent review of natural outputs is needed
before choosing a verifier in Milestone 2.
