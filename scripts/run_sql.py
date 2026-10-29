"""
Run every SQL analysis query and save the results.

For each sql/NN_*.sql file (after running sql/00_setup.sql, which defines shared views):
  - saves the result to analysis/results/NN_*.csv
  - adds the question, the SQL and the result table to analysis/README.md

Uses DuckDB, which runs standard SQL directly on the CSV files: no database server to set up,
so anyone can re-run the analysis with one command.

Usage:
  pip install duckdb
  python scripts/run_sql.py
"""

import csv
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "analysis"


def question_and_why(sql_text):
    """Pull the 'Question:' and 'Why it matters:' lines out of a query's header comment."""
    header = []
    for line in sql_text.splitlines():
        if not line.startswith("--"):
            break
        header.append(line[2:].strip())
    joined = " ".join(header)
    q = re.search(r"Question:\s*(.*?)(Why it matters:|Method:|$)", joined)
    w = re.search(r"Why it matters:\s*(.*?)(Method:|$)", joined)
    m = re.search(r"Method:\s*(.*)$", joined)
    return (q.group(1).strip() if q else ""), (w.group(1).strip() if w else ""), (m.group(1).strip() if m else "")


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:,.2f}".rstrip("0").rstrip(".") if abs(v) < 100 else f"{v:,.0f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v).replace("|", "/")


def main():
    con = duckdb.connect()
    # Queries use paths relative to the repo root
    con.execute(f"SET file_search_path = '{ROOT}'")
    setup = (SQL_DIR / "00_setup.sql").read_text(encoding="utf-8")
    con.execute(setup)

    (OUT_DIR / "results").mkdir(parents=True, exist_ok=True)
    total_rows = con.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
    doc = [
        "# SQL analysis",
        "",
        f"Standard SQL run with DuckDB directly on `data/combined/prices_clean.csv` ({total_rows:,} published price rows). "
        "Shared views are defined in [`sql/00_setup.sql`](../sql/00_setup.sql). "
        "Re-run everything with `python scripts/run_sql.py`; full results are in [`analysis/results/`](results/).",
        "",
        "Prices are amounts paid to the hospital, not a patient's out-of-pocket cost. "
        "\"Typical commercial\" = median across a hospital's listed commercial plans.",
        "",
    ]

    for path in sorted(SQL_DIR.glob("[0-9][0-9]_*.sql")):
        if path.name.startswith("00_"):
            continue
        sql = path.read_text(encoding="utf-8")
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()

        with open(OUT_DIR / "results" / f"{path.stem}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)

        question, why, method = question_and_why(sql)
        title = path.stem[3:].replace("_", " ").capitalize()
        doc += [f"## {path.stem[:2]}. {title}", "", f"**Question:** {question}", ""]
        if why:
            doc += [f"**Why it matters:** {why}", ""]
        if method:
            doc += [f"**Method:** {method}", ""]
        doc += [f"Query: [`sql/{path.name}`](../sql/{path.name})", ""]
        doc.append("| " + " | ".join(cols) + " |")
        doc.append("|" + "|".join("---" for _ in cols) + "|")
        for r in rows[:20]:
            doc.append("| " + " | ".join(fmt(v) for v in r) + " |")
        if len(rows) > 20:
            doc.append(f"\n*Showing 20 of {len(rows)} rows; see the CSV for all.*")
        doc.append("")
        print(f"{path.name}: {len(rows)} rows")

    (OUT_DIR / "README.md").write_text("\n".join(doc), encoding="utf-8")
    print("Wrote analysis/README.md")


if __name__ == "__main__":
    main()
