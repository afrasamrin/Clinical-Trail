"""Load the CSVs into an in-memory SQLite DB and run every query in sql/checks.sql."""
import re, sqlite3
import pandas as pd

con = sqlite3.connect(":memory:")
for t in ["dm", "ae", "lb"]:
    pd.read_csv(f"data/{t}.csv").to_sql(t, con, index=False)

blocks = re.split(r"-- name:\s*", open("sql/checks.sql").read())[1:]
for b in blocks:
    name, sql = b.split("\n", 1)
    df = pd.read_sql_query(sql.strip(), con)
    print(f"\n=== {name.strip()} ({len(df)} rows) ===")
    if len(df): print(df.head(10).to_string(index=False))
