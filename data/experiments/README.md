# Saved experiment database

`mathqa_runs.sqlite3` is a frozen snapshot of the experiment database captured on
October 8, 2026. It includes legacy batch runs, solver/verifier runs, exact saved
requests and responses, configurations, costs, grades, and migration records.
`manifest.json` records its SHA-256 checksum, size, and table counts.

## Use saved data or continue experiments

From the repository root, create a working copy on a fresh checkout:

```powershell
New-Item -ItemType Directory -Force results | Out-Null
if (Test-Path results/mathqa_runs.sqlite3) {
    throw "A working database already exists; preserve it before restoring."
}
Copy-Item data/experiments/mathqa_runs.sqlite3 results/mathqa_runs.sqlite3
```

The scripts use `results/mathqa_runs.sqlite3` by default. That working database,
its journals, backups, and generated reports remain local. Commit an updated
snapshot deliberately when sharing additional results; binary database versions
cannot be merged meaningfully, so coordinate snapshot updates between collaborators.

Read the published snapshot directly without restoring it:

```powershell
uv run python scripts/mathqa_workflow_trie.py --database data/experiments/mathqa_runs.sqlite3
uv run python scripts/mathqa_table.py --database data/experiments/mathqa_runs.sqlite3
```

These exporters make no model calls. Installing dependencies may require network
access. New paid experiments need a local `.env` populated from `.env.example`,
a newly prepared plan, and the scope/budget authorization required in the root
README. Historical failed or interrupted runs are retained as evidence; restoring
the database does not authorize or automatically resume them.

Historical records retain their original dataset paths, source revisions, and
frozen settings. Those paths may refer to the original computer. Prepare new
plans in the new checkout instead of editing historical records or reusing an
old paid-run approval. The database is sufficient to inspect stored results and
preserve prior question exposure; generated HTML and standalone local plan files
can be regenerated where supported and are not included here.

## Snapshot validation

The snapshot was created with SQLite's backup API, rather than copying an open
database file. Its schema and every table row were compared with the source;
SQLite integrity and foreign-key checks passed. A scan found no matches for
secrets from the local `.env`, common API-token patterns, or private media paths
in the stored text. Historical machine paths and provider response identifiers
are retained for experiment provenance.

To verify the snapshot checksum:

```powershell
$snapshotManifest = Get-Content data/experiments/manifest.json | ConvertFrom-Json
if ((Get-FileHash data/experiments/mathqa_runs.sqlite3 -Algorithm SHA256).Hash.ToLower() -ne $snapshotManifest.sha256) {
    throw "Snapshot checksum mismatch."
}
```
