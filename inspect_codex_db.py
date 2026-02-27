import sqlite3, json

db_path = r"C:\Users\pnfow\.codex-work\sqlite\codex.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)

for t in tables:
    cursor.execute(f"PRAGMA table_info({t})")
    cols = [(col[1], col[2]) for col in cursor.fetchall()]
    print(f"\n  {t}: {cols}")
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    count = cursor.fetchone()[0]
    print(f"  Rows: {count}")
    if count > 0 and count < 20:
        cursor.execute(f"SELECT * FROM {t} LIMIT 5")
        for row in cursor.fetchall():
            print(f"    {row}")

conn.close()
