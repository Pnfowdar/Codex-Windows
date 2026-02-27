import sqlite3
import os

db_dir = r"C:\Users\pnfow\.codex-work"
for file in os.listdir(db_dir):
    if file.endswith('.sqlite') or file.endswith('.db'):
        db_path = os.path.join(db_dir, file)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"--- {file} ---")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  Table: {table_name} (Rows: {count})")
            conn.close()
        except sqlite3.Error as e:
            print(f"Error reading {file}: {e}")
