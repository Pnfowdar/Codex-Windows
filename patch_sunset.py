path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-BUvz-C55.js'
target = 'i="2929582856",e[0]=i):i=e[0];const s=Xs(i);'
replacement = 'i="2929582856",e[0]=i):i=e[0];const s=!1;'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if target in content:
    new_content = content.replace(target, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Sunset screen check bypassed!")
else:
    print("ERROR: Target string not found. The minified hash or variable names might have changed.")
