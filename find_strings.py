
import re
import os

path = r'd:\Projects\Codex-Windows\work\app\webview\assets'
queries = [r'Rate limit', r'Rate limit remaining']

for root, dirs, files in os.walk(path):
    for file in files:
        if not file.endswith('.js'): continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            for q in queries:
                if q in content:
                    print(f"Found '{q}' in {file}")
                    # Print context
                    matches = [m.start() for m in re.finditer(re.escape(q), content)]
                    for m in matches:
                        start = max(0, m - 100)
                        end = min(len(content), m + 200)
                        print(f"...{content[start:end]}...")
                        print("-" * 50)
        except Exception as e:
            print(f"Error reading {file}: {e}")
