import sqlite3

conn = sqlite3.connect('mi_proyecto/db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

for t in tables:
    if t.startswith('catalogo_'):
        cur.execute(f"PRAGMA table_info({t})")
        cols = [c[1] for c in cur.fetchall()]
        print(f"\nTable {t}: {cols}")
        cur.execute(f"SELECT * FROM {t}")
        rows = cur.fetchall()
        for r in rows:
            row_str = str(r)
            if 'trapstar' in row_str.lower():
                print(f"  [CONTAINS TRAPSTAR in {t}]: {r}")

conn.close()
