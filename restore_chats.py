"""
Codex Chat History Restorer - Injects thread titles from state_5.sqlite 
directly into the Electron Local Storage LevelDB so the sidebar repopulates
automatically without any manual DevTools intervention.
"""
import sqlite3
import json
import os
import struct

def get_threads_from_db():
    """Read all thread IDs and titles from the Codex state database."""
    db_path = os.path.join(os.environ.get("CODEX_HOME", os.path.expanduser("~\\.codex-work")), "state_5.sqlite")
    
    # Try numbered state files in descending order
    codex_home = os.environ.get("CODEX_HOME", os.path.expanduser("~\\.codex-work"))
    db_path = None
    for i in range(10, -1, -1):
        candidate = os.path.join(codex_home, f"state_{i}.sqlite")
        if os.path.exists(candidate):
            db_path = candidate
            break
    
    if not db_path:
        print("ERROR: No state_*.sqlite database found.")
        return None
    
    print(f"Reading threads from: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, updated_at FROM threads ORDER BY updated_at DESC")
    threads = cursor.fetchall()
    conn.close()
    return threads

def build_thread_titles_payload(threads):
    """Build the THREAD_TITLES payload matching the Codex frontend format."""
    order = []
    titles = {}
    for t_id, t_title, _ in threads:
        order.append(t_id)
        if t_title and t_title.strip():
            # Truncate to 80 chars like the frontend does
            title = t_title.strip().replace("\n", " ").replace("\r", " ")
            if len(title) > 80:
                title = title[:79].rstrip() + "…"
            titles[t_id] = title
        else:
            titles[t_id] = "Previous Chat"
    
    return {"titles": titles, "order": order}

def generate_js_injection(payload):
    """Generate the JavaScript code to inject into the preload or webview."""
    payload_json = json.dumps(payload, ensure_ascii=True)
    return f"""
// Auto-restore thread titles from state database
(function() {{
  try {{
    var key = 'codex:persisted-atom:thread-titles';
    var existing = localStorage.getItem(key);
    if (!existing || existing === 'null' || existing === '{{}}') {{
      var payload = {payload_json};
      localStorage.setItem(key, JSON.stringify(payload));
      console.log('[codex-restore] Restored ' + payload.order.length + ' thread titles to sidebar');
    }}
  }} catch(e) {{
    console.warn('[codex-restore] Failed to restore thread titles:', e);
  }}
}})();
"""

def main():
    threads = get_threads_from_db()
    if not threads:
        return
    
    print(f"Found {len(threads)} threads in database.")
    payload = build_thread_titles_payload(threads)
    js_code = generate_js_injection(payload)
    
    # Write the injection script to a file that run.ps1 can use
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "work", "restore_threads.js")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(js_code)
    
    print(f"Wrote restoration script to: {output_path}")
    print(f"Threads to restore: {len(threads)}")
    
    # Also output the raw JS for manual injection via DevTools
    print("\n" + "="*60)
    print("OPTION 1 (Automatic): The script above has been saved.")
    print("         It will be injected by run.ps1 on next launch.")
    print("="*60)
    print("\nOPTION 2 (Manual): Paste this into Codex DevTools Console:")
    print("-"*60)
    manual_js = f"localStorage.setItem('codex:persisted-atom:thread-titles', JSON.stringify({json.dumps(payload, ensure_ascii=True)})); location.reload();"
    print(manual_js)
    print("-"*60)

if __name__ == "__main__":
    main()
