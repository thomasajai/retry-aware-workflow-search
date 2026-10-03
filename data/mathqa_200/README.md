# MathQA 200-question subset

200 unique questions sampled without replacement from the official MathQA **test** split (2,985 records), using seed **42**. Records are ordered by their original zero-based source indices.

## Files

- `mathqa_200.json`: JSON array of all 200 complete records.
- `mathqa_200.jsonl`: The same records, one JSON object per line.
- `questions_and_answers.md`: Readable questions, choices, answers, rationales, categories, and both formula representations.
- `constant_list.txt` and `operation_list.txt`: Original supporting vocabulary files from the release.
- `manifest.json`: Source URL, archive and output checksums, selected indices, sampling method, field descriptions, and validation results.

## Fields

Every original field is preserved: `Problem`, `Rationale`, `options`, `correct`, `annotated_formula`, `linear_formula`, and `category`.

Added convenience fields: `id` (stable identifier based on split and source index), `source_split`, `source_index` (zero-based), `parsed_options` (a dictionary from letters a-e to option text), and `correct_option` (the answer text corresponding to the original `correct` letter).

Answers and rationales are the dataset's supplied annotations, not newly generated solutions. Original typos and encoding artifacts are preserved. The authors note that rationales can be noisy, incomplete, or incorrect. Validation checks record count, uniqueness, original-field preservation, and answer-to-option mapping; it does not independently verify mathematical correctness.

## Source and reproducibility

- Homepage: https://math-qa.github.io/
- Official release: https://raw.githubusercontent.com/math-QA/math-qa.github.io/master/data/MathQA.zip
- Paper: https://aclanthology.org/N19-1245/

Selection: `sorted(random.Random(42).sample(range(2985), 200))` using Python's standard library. The exact selected indices and archive checksum are in `manifest.json`.

```python
import json
from pathlib import Path

questions = json.loads(Path("data/mathqa_200/mathqa_200.json").read_text(encoding="utf-8"))
print(questions[0]["Problem"])
print(questions[0]["correct"], questions[0]["correct_option"])
```
