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
must remain outside binary quality denominators.

`natural_reviews.json` adds assistant reviews of 22 usable saved responses from
the first eight development questions: ten valid solutions, eleven invalid
solutions, and one unknown acceptance label. Each review is bound to the saved
run, dataset checksum, question/model, call ID, and exact answer hash. These are
independent hand calculations by the assistant, not human annotations. Cases
with ambiguous rounding or a question whose calculated answer is absent from
the options carry uncertainty notes. A demonstrably invalid calculation can
still receive a rejection label despite ambiguity in the question itself.

The preview stores labels separately from the exact proposed API requests.
Only the problem, choices, and solver proposal enter a verifier request. Results
from these controlled diagnostics must be reported separately from natural
saved-answer screening. Unreviewed natural responses retain answer-key labels
and unknown reasoning validity; they cannot measure reasoning false acceptance
or false rejection. The first pilot uses only the first three natural reviews
plus the nine usable synthetic cases. More independent review and larger
screening are needed before choosing a verifier in Milestone 2.
