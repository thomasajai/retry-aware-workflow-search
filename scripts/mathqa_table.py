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
        calls = connection.execute(
            """
            SELECT question_id, requested_model, attempt_number, answer_text, status
            FROM calls WHERE run_id = ? ORDER BY attempt_number
            """,
            (run["run_id"],),
        ).fetchall()
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
    for row_number, question_id in enumerate(question_ids, start=1):
        cells = []
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
            cells.append(
                f'<td class="{cell_class}" title="{escape(status)}">'
                f'{escape(answer if answer is not None else "")}</td>'
            )
        rows.append(
            f'<tr><th scope="row"><span class="row-number">{row_number:02}</span>'
            f'{escape(question_id)}</th>{"".join(cells)}</tr>'
        )

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
                   border-radius: 10px; background: white; }}
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
      Status: {escape(run["status"].replace("_", " "))}</p>
    <div class="legend">
      <span><span class="swatch failed"></span>Failed attempt</span>
      <span><span class="swatch unfinished"></span>Running or interrupted</span>
      <span>Blank cell: no answer text saved</span>
    </div>
    <div class="table-wrap">
      <table>
        <caption>{len(question_ids)} questions × {len(models)} model answer columns</caption>
        <thead><tr><th scope="col">Question ID</th>{headers}</tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>
    <p class="note">Cells contain saved answer text, including partial answers from failed attempts.
      The latest attempt is shown. Response JSON, usage, cost, timing, and error details remain in SQLite.</p>
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
