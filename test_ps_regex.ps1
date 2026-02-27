$raw = Get-Content -Raw d:\Projects\Codex-Windows\work\app\webview\assets\index-BUvz-C55.js
$pattern = '([a-zA-Z_$]+)="2929582856",([a-zA-Z_$]+)\[(\d+)\]=\1\):\1=\2\[\3\];const ([a-zA-Z_$]+)=Xs\(\1\);?'

if ($raw -match $pattern) {
    Write-Host "Found match!"
    $replacement = '${1}="2929582856",${2}[${3}]=${1}):${1}=${2}[${3}];const ${4}=!1;'
    $patched = [regex]::Replace($raw, $pattern, $replacement)

    if ($patched -match 'const s=!1;') {
        Write-Host "Replaced properly!"
    }
    else {
        Write-Host "Failed to replace"
    }
}
else {
    Write-Host "No match"
}
