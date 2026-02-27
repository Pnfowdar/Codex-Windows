import sqlite3
import json
import os

def restore_sidebar():
    db_path = r"C:\Users\pnfow\.codex-work\state_5.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all threads ordered by latest activity
    cursor.execute("SELECT id, updated_at FROM threads ORDER BY updated_at DESC")
    threads = cursor.fetchall()
    conn.close()
    
    # Create the title mapping and order list
    order = []
    titles = {}
    for t_id, t_updated in threads:
        order.append(t_id)
        titles[t_id] = "Recovered Chat"
    
    # Pack into the expected Javascript layout
    payload = {
        "titles": titles,
        "order": order
    }
    dumped = json.dumps(payload, ensure_ascii=True)
    
    print("\n[!] Discovered", len(threads), "chats.")
    print("Run the following Javascript in the Codex Developer Tools Console (Ctrl+Shift+I):")
    print("\nlocalStorage.setItem('codex:persisted-atom:thread-titles', JSON.stringify(" + dumped + "));\n")
    print("And then press Ctrl+R to refresh the UI.")

restore_sidebar()
