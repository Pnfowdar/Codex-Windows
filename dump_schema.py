import sqlite3

def dump_schema():
    conn = sqlite3.connect(r"C:\Users\pnfow\.codex-work\state_5.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        print(f"\n--- TABLE: {table} ---")
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
            
    conn.close()

dump_schema()
