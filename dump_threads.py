import sqlite3

def dump_threads():
    conn = sqlite3.connect(r"C:\Users\pnfow\.codex-work\state_5.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, updated_at, title FROM threads ORDER BY updated_at DESC LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

dump_threads()
