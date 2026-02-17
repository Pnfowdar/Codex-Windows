
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
uAe_sig = 'function uAe('
target = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric"}).format(n)'
replacement = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric",hour:"numeric",minute:"numeric"}).format(n)'

print(f"Searching for signature: {uAe_sig}")
print(f"Target: {target}")

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found_sig = False
patched = False

with open(path, 'w', encoding='utf-8') as f:
    for i, line in enumerate(lines):
        if uAe_sig in line:
            found_sig = True
            print(f"Found signature on line {i+1}")
            # print(f"Line content: {line}") # Too long to print fully
            print(f"Line length: {len(line)}")
            
            if target in line:
                print("Target matches strictly.")
                line = line.replace(target, replacement)
                patched = True
                print("Replaced target.")
            else:
                print("Target NOT in line. checking for partial matches or whitespace issues.")
                # find where uAe starts
                idx = line.find(uAe_sig)
                snippet = line[idx:idx+400]
                print(f"Snippet around uAe: {snippet}")
                
        f.write(line)

if patched:
    print("File successfully patched.")
elif found_sig:
    print("Found 'uAe' but could not match target string for replacement.")
else:
    print("Could not find 'function uAe(' in file.")
