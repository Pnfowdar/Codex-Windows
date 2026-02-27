import sys, re
with open(r'd:\Projects\Codex-Windows\work\app\webview\assets\index-BUvz-C55.js', 'r', encoding='utf-8') as f:
    text = f.read()

# search for DFn usage
occurrences = [m.start() for m in re.finditer(r'DFn', text)]
with open('d:\\Projects\\Codex-Windows\\extracted_update_usage.txt', 'w', encoding='utf-8') as out:
    for idx in occurrences:
        out.write(f"--- MATCH AT {idx} ---\n")
        out.write(text[max(0, idx - 300): min(len(text), idx + 300)])
        out.write("\n\n")
