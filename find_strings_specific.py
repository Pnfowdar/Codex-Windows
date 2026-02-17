
import re

files = [
    r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js',
    r'd:\Projects\Codex-Windows\work\app\webview\assets\index-CgwAo6pj.js'
]
queries = [r'Rate limit', r'Rate limit remaining']

for path in files:
    print(f"Checking {path}...")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for q in queries:
            print(f"Searching for '{q}' in {path}...")
            matches = [m.start() for m in re.finditer(re.escape(q), content)]
            if not matches:
                print("No matches.")
            for m in matches:
                print(f"Match for '{q}' at {m}:")
                start = max(0, m - 100)
                end = min(len(content), m + 200)
                print(content[start:end])
                print("-" * 50)
                break # Just show first match per query per file
    except Exception as e:
        print(f"Error: {e}")
