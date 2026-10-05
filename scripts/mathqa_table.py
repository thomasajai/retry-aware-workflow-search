"""Export a MathQA run's answer table to a standalone local HTML file."""

import argparse
import json
import sqlite3
from html import escape
from pathlib import Path
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "results" / "mathqa_runs.sqlite3"
OUTPUT_DIRECTORY = PROJECT_ROOT / "results" / "mathqa_tables"


def export_table(
    run_id: str | None = None,
    *,
    database_path: Path = DATABASE_PATH,
    output_path: Path | None = None,
) -> Path:
    """Read one run and export its ordered answer cells without changing SQLite."""
    # mode=ro prevents both writes and creation of a missing database file.
    database_uri = database_path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    try:
        connection.row_factory = sqlite3.Row
        if run_id is None:
            run = connection.execute(
                "SELECT * FROM runs ORDER BY created_at_utc DESC, run_id DESC LIMIT 1"
            ).fetchone()
        else:
            run = connection.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if run is None:
            raise ValueError("No matching run was found in the database.")
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        grading_columns = (
            "g.score, g.option_letter, g.returned_value, g.gradable, g.value_conflict, g.diagnostics_json"
            if "call_gradings" in tables else
            "NULL AS score, NULL AS option_letter, NULL AS returned_value, NULL AS gradable, "
            "NULL AS value_conflict, NULL AS diagnostics_json"
        )
        grading_join = " LEFT JOIN call_gradings g USING (call_id)" if "call_gradings" in tables else ""
        validation_column = "v.format_valid" if "call_validations" in tables else "NULL AS format_valid"
        validation_join = " LEFT JOIN call_validations v USING (call_id)" if "call_validations" in tables else ""
        calls = connection.execute(
            f"SELECT c.*, {grading_columns}, {validation_column} FROM calls c{grading_join}{validation_join} "
            "WHERE c.run_id = ? ORDER BY attempt_number", (run["run_id"],),
        ).fetchall()
        grading = connection.execute(
            "SELECT * FROM run_gradings WHERE run_id = ?", (run["run_id"],)
        ).fetchone() if "run_gradings" in tables else None
        summaries = connection.execute(
            """
            SELECT * FROM model_gradings WHERE run_id = ?
            """,
            (run["run_id"],),
        ).fetchall() if "model_gradings" in tables else []
    finally:
        connection.close()

    models = json.loads(run["models_json"])
    question_ids = json.loads(run["question_ids_json"])
    # Later attempts overwrite earlier attempts for the same question/model pair.
    latest_calls = {
        (call["question_id"], call["requested_model"]): call for call in calls
    }
    headers = "".join(f'<th scope="col">{escape(model)}</th>' for model in models)
    rows = []
    score_rows = []
    for row_number, question_id in enumerate(question_ids, start=1):
        cells = []
        score_cells = []
        for model in models:
            call = latest_calls.get((question_id, model))
            answer = call["answer_text"] if call is not None else None
            status = call["status"] if call is not None else "missing"
            # CSS classes come from these fixed choices, never from model output.
            cell_class = {
                "failed": "failed",
                "interrupted": "unfinished",
                "running": "unfinished",
            }.get(status, "")
            if call is None or call["score"] is None:
                final = "Ungraded"
                diagnostics = ""
                score = "Ungraded"
            else:
                option, value = call["option_letter"], call["returned_value"]
                final = escape(f"{option}) {value if value is not None else '[value missing]'}" if option else
                               f"No usable final option; returned value: {value if value is not None else '[missing]'}")
                score = str(call["score"])
                diagnostics = "<br><span class=\"note\">" + escape(" ".join(json.loads(call["diagnostics_json"])["errors"])) + "</span>"
            format_status = ("unvalidated" if call is None or call["format_valid"] is None else
                             "valid" if call["format_valid"] else "invalid")
            cells.append(
                f'<td class="{cell_class}" title="{escape(status)}">'
                f'{final}{diagnostics}<br><span class="note">Generation: {escape(status)}; '
                f'format: {format_status}.</span><details><summary>Original reply</summary>'
                f'<pre>{escape(answer if answer is not None else "[No answer text saved]")}</pre></details></td>'
            )
            score_cells.append(f'<td class="{cell_class}">{score}</td>')
        label = (f'<th scope="row"><span class="row-number">{row_number:02}</span>'
                 f'{escape(question_id)}</th>')
        rows.append(
            f'<tr>{label}{"".join(cells)}</tr>'
        )
        score_rows.append(f'<tr>{label}{"".join(score_cells)}</tr>')

    by_model = {s["model"]: s for s in summaries}
    accuracy_rows = []
    for model in models:
        summary = by_model.get(model)
        values = ([str(summary["correct_count"]), str(summary["denominator"]),
                   f'{summary["accuracy_percent"]:.2f}%', str(summary["generation_failures"]),
                   str(summary["ungradable_completed"]), str(summary["format_invalid_completed"]),
                   str(summary["format_unvalidated_completed"])] if summary is not None else
                  ["Ungraded", str(len(question_ids)), "Ungraded", "—", "—", "—", "—"])
        accuracy_rows.append(f'<tr><th scope="row">{escape(model)}</th>' +
                             "".join(f'<td>{value}</td>' for value in values) + '</tr>')
    grading_status = (f"Fully graded ({grading['grader_version']})" if grading is not None else
                      "Ungraded; no complete batch grading saved")

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MathQA answer table</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f3f6fb; color: #17243b;
           font: 15px/1.55 system-ui, sans-serif; }}
    main {{ max-width: 1500px; margin: 0 auto; padding: 32px 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.2; }}
    .metadata {{ margin: 0 0 16px; color: #526078; overflow-wrap: anywhere; }}
    .legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px;
               color: #526078; font-size: 13px; }}
    .swatch {{ display: inline-block; width: 12px; height: 12px; margin-right: 5px;
               border: 1px solid #cad3e0; border-radius: 3px; vertical-align: middle; }}
    .table-wrap {{ overflow: auto; max-height: 75vh; border: 1px solid #dbe2ed;
                   border-radius: 10px; background: white; margin-bottom: 24px; }}
    table {{ width: 100%; min-width: 960px; table-layout: fixed;
             border-collapse: separate; border-spacing: 0; }}
    caption {{ text-align: left; padding: 14px 16px; color: #526078; }}
    th, td {{ padding: 14px 16px; text-align: left; vertical-align: top;
              border-top: 1px solid #e5eaf2; border-right: 1px solid #e5eaf2;
              overflow-wrap: anywhere; }}
    tr > :last-child {{ border-right: 0; }}
    thead th {{ position: sticky; top: 0; z-index: 2; background: #eaf0f8;
                color: #243f64; font-size: 13px; }}
    thead th:first-child {{ width: 225px; left: 0; z-index: 3; }}
    tbody th {{ position: sticky; left: 0; z-index: 1; background: #f8fafd;
                font-size: 12px; font-weight: 500; }}
    td {{ white-space: pre-wrap; }}
    pre {{ white-space: pre-wrap; margin: 8px 0; font: 13px/1.5 monospace; }}
    details {{ margin-top: 8px; }}
    summary {{ cursor: pointer; color: #243f64; }}
    .row-number {{ display: inline-block; min-width: 28px; color: #7b879b; }}
    .failed {{ background: #fff0f0; }}
    .unfinished {{ background: #fff6df; }}
    .note {{ color: #526078; font-size: 13px; }}
    @media (max-width: 600px) {{ main {{ padding: 20px 12px; }} h1 {{ font-size: 25px; }} }}
  </style>
</head>
<body>
  <main>
    <h1>MathQA answer table</h1>
    <p class="metadata">Run: {escape(run["run_id"])}<br>
      Status: {escape(run["status"].replace("_", " "))}<br>
      Grading: {escape(grading_status)}</p>
    <div class="legend">
      <span><span class="swatch failed"></span>Failed attempt</span>
      <span><span class="swatch unfinished"></span>Running or interrupted</span>
      <span>Ungraded: no saved score; generation and format are separate from correctness</span>
    </div>
    <div class="table-wrap">
      <table id="final-answers">
        <caption>Final answers: {len(question_ids)} questions × {len(models)} models</caption>
        <thead><tr><th scope="col">Question ID</th>{headers}</tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>
    <div class="table-wrap">
      <table id="scores">
        <caption>Scores: option-letter correctness (1 or 0)</caption>
        <thead><tr><th scope="col">Question ID</th>{headers}</tr></thead>
        <tbody>{"".join(score_rows)}</tbody>
      </table>
    </div>
    <div class="table-wrap">
      <table id="accuracy">
        <caption>Accuracy: all selected questions are included in each denominator</caption>
        <thead><tr><th scope="col">Model</th><th scope="col">Correct</th>
          <th scope="col">Denominator</th><th scope="col">Accuracy</th>
          <th scope="col">Generation failures</th><th scope="col">Ungradable completed</th>
          <th scope="col">Format-invalid completed</th><th scope="col">Format-unvalidated completed</th></tr></thead>
        <tbody>{"".join(accuracy_rows)}</tbody>
      </table>
    </div>
    <p class="note">The latest attempt is shown. Failed/truncated generations score 0, including partial replies.
      Calculations are not evaluated. Value conflicts use option text with whitespace runs collapsed;
      they do not affect the option-letter score. Expand Original reply to see saved text unchanged.
      Response JSON, usage, cost, timing, and error details remain in SQLite.</p>
  </main>
</body>
</html>
"""
    if output_path is None:
        # UUID validation keeps the default filename within the output directory.
        output_path = OUTPUT_DIRECTORY / f"mathqa_{UUID(run['run_id'])}.html"
    if output_path.resolve() == database_path.resolve():
        raise ValueError("The HTML output cannot overwrite the database.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="Run to export; defaults to the most recently created run.")
    parser.add_argument("--database", type=Path, default=DATABASE_PATH, help="SQLite database path.")
    parser.add_argument("--output", type=Path, help="HTML output path; defaults to a file named for the run.")
    args = parser.parse_args()
    try:
        output_path = export_table(args.run_id, database_path=args.database, output_path=args.output)
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.error(str(error))
    print(f"HTML table: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
