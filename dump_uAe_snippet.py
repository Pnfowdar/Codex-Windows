
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
uAe_sig = 'function uAe('

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = False
for i, line in enumerate(lines):
    if uAe_sig in line:
        idx = line.find(uAe_sig)
        snippet = line[idx:idx+500]
        # Write snippet to file
        with open(r'd:\Projects\Codex-Windows\uAe_snippet_debug.txt', 'w', encoding='utf-8') as f_out:
            f_out.write(snippet)
        print("Snippet written to uAe_snippet_debug.txt")
        found = True
        break

if not found:
    print("uAe signature not found.")
