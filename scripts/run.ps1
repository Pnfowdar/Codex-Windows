param(
  [string]$DmgPath,
  [string]$WorkDir = (Join-Path $PSScriptRoot "..\work"),
  [string]$CodexCliPath,
  [switch]$Reuse,
  [switch]$NoLaunch,
  [switch]$EnableLogging
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name not found."
  }
}

function Set-CoreShellEnvironment() {
  if (-not $env:SystemRoot) {
    $env:SystemRoot = $env:WINDIR
  }
  if (-not $env:WINDIR) {
    $env:WINDIR = $env:SystemRoot
  }

  if (-not $env:ComSpec -and $env:SystemRoot) {
    $env:ComSpec = Join-Path $env:SystemRoot "System32\cmd.exe"
  }

  if (-not $env:PATHEXT) {
    $env:PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC"
  }
}

function Resolve-7z([string]$BaseDir) {
  $cmd = Get-Command 7z -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Path }
  $p1 = Join-Path $env:ProgramFiles "7-Zip\7z.exe"
  $p2 = Join-Path ${env:ProgramFiles(x86)} "7-Zip\7z.exe"
  if (Test-Path $p1) { return $p1 }
  if (Test-Path $p2) { return $p2 }
  $wg = Get-Command winget -ErrorAction SilentlyContinue
  if ($wg) {
    & winget install --id 7zip.7zip -e --source winget --accept-package-agreements --accept-source-agreements --silent | Out-Null
    if (Test-Path $p1) { return $p1 }
    if (Test-Path $p2) { return $p2 }
  }
  if (-not $BaseDir) { return $null }
  $tools = Join-Path $BaseDir "tools"
  New-Item -ItemType Directory -Force -Path $tools | Out-Null
  $sevenZipDir = Join-Path $tools "7zip"
  New-Item -ItemType Directory -Force -Path $sevenZipDir | Out-Null
  $homeUrl = "https://www.7-zip.org/"
  try { $html = (Invoke-WebRequest -Uri $homeUrl -UseBasicParsing).Content } catch { return $null }
  $extra = [regex]::Match($html, 'href="a/(7z[0-9]+-extra\.7z)"').Groups[1].Value
  if (-not $extra) { return $null }
  $extraUrl = "https://www.7-zip.org/a/$extra"
  $sevenRUrl = "https://www.7-zip.org/a/7zr.exe"
  $sevenR = Join-Path $tools "7zr.exe"
  $extraPath = Join-Path $tools $extra
  if (-not (Test-Path $sevenR)) { Invoke-WebRequest -Uri $sevenRUrl -OutFile $sevenR }
  if (-not (Test-Path $extraPath)) { Invoke-WebRequest -Uri $extraUrl -OutFile $extraPath }
  & $sevenR x -y $extraPath -o"$sevenZipDir" | Out-Null
  $p3 = Join-Path $sevenZipDir "7z.exe"
  if (Test-Path $p3) { return $p3 }
  return $null
}

function Resolve-CodexCliPath([string]$Explicit) {
  if ($Explicit) {
    if (Test-Path $Explicit) { return (Resolve-Path $Explicit).Path }
    throw "Codex CLI not found: $Explicit"
  }

  $envOverride = $env:CODEX_CLI_PATH
  if ($envOverride -and (Test-Path $envOverride)) {
    return (Resolve-Path $envOverride).Path
  }

  $script:ResolvePreferred = @()
  $script:ResolveFallback = @()

  function Add-Candidate([string]$Candidate) {
    if (-not $Candidate) { return }
    $normalized = $Candidate.Trim()
    if (-not $normalized) { return }
    if ($normalized -match '\\.windsurf\\extensions\\' -or $normalized -match '\\fnm_multishells\\') {
      $script:ResolveFallback += $normalized
    }
    else {
      $script:ResolvePreferred += $normalized
    }
  }

  # Collect all npm global root directories to search
  $npmRoots = @()
  try {
    $npmRoot = (& npm root -g 2>$null).Trim()
    if ($npmRoot) { $npmRoots += $npmRoot }
  }
  catch {}

  # fnm stores real global packages in its persistent node-versions directory.
  # npm root -g under fnm returns a transient multishell symlink, so also check the real path.
  try {
    $fnmBase = Join-Path $env:APPDATA "fnm\node-versions"
    if (Test-Path $fnmBase) {
      $nodeVer = (& node --version 2>$null).Trim()
      if ($nodeVer) {
        $fnmRoot = Join-Path $fnmBase "$nodeVer\installation\node_modules"
        if ((Test-Path $fnmRoot) -and ($npmRoots -notcontains $fnmRoot)) {
          $npmRoots += $fnmRoot
        }
      }
    }
  }
  catch {}

  $arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "aarch64-pc-windows-msvc" } else { "x86_64-pc-windows-msvc" }
  foreach ($root in $npmRoots) {
    # Legacy path: @openai/codex/vendor/<arch>/codex/codex.exe
    Add-Candidate (Join-Path $root "@openai\codex\vendor\$arch\codex\codex.exe")
    Add-Candidate (Join-Path $root "@openai\codex\vendor\x86_64-pc-windows-msvc\codex\codex.exe")
    Add-Candidate (Join-Path $root "@openai\codex\vendor\aarch64-pc-windows-msvc\codex\codex.exe")
    # New structure: search recursively through entire @openai dir for platform-specific packages
    $openaiDir = Join-Path $root "@openai"
    if (Test-Path $openaiDir) {
      $found = Get-ChildItem -Path $openaiDir -Recurse -Filter "codex.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($found) { Add-Candidate $found.FullName }
    }
  }

  # PATH discovery as fallback (may include Windsurf-bundled codex.exe)
  try {
    $whereExe = & where.exe codex.exe 2>$null
    if ($whereExe) {
      foreach ($match in @($whereExe)) { Add-Candidate $match }
    }
    $whereCmd = & where.exe codex 2>$null
    if ($whereCmd) {
      foreach ($match in @($whereCmd)) { Add-Candidate $match }
    }
  }
  catch {}

  # Direct Windsurf extension fallback if PATH discovery is unavailable
  try {
    $windsurfBinRoot = Join-Path $env:USERPROFILE ".windsurf\extensions"
    if (Test-Path $windsurfBinRoot) {
      $windsurfCodex = Get-ChildItem -Path $windsurfBinRoot -Directory -Filter "openai.chatgpt-*" -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending |
      ForEach-Object {
        Get-ChildItem -Path (Join-Path $_.FullName "bin") -Recurse -Filter "codex.exe" -File -ErrorAction SilentlyContinue
      } |
      Select-Object -First 1
      if ($windsurfCodex) {
        Add-Candidate $windsurfCodex.FullName
      }
    }
  }
  catch {}

  $candidates = @($script:ResolvePreferred + $script:ResolveFallback)

  foreach ($c in $candidates) {
    if (-not $c) { continue }
    $candidatePath = $c

    # "where codex" can return extension-less shims; prefer a sibling codex.exe when available.
    if ([System.IO.Path]::GetExtension($candidatePath) -eq "") {
      $exeSibling = "$candidatePath.exe"
      if (Test-Path $exeSibling) {
        $candidatePath = $exeSibling
      }
    }

    if ([System.IO.Path]::GetExtension($candidatePath) -ne ".exe" -and [System.IO.Path]::GetExtension($candidatePath) -ne ".cmd") {
      continue
    }

    if ($candidatePath -match '\.cmd$' -and (Test-Path $candidatePath)) {
      try {
        $cmdDir = Split-Path $candidatePath -Parent
        # Search entire @openai dir to handle both legacy and new package structures
        $openaiDir = Join-Path $cmdDir "node_modules\@openai"
        if (Test-Path $openaiDir) {
          $found = Get-ChildItem -Recurse -Filter "codex.exe" $openaiDir -ErrorAction SilentlyContinue | Select-Object -First 1
          if ($found) { return (Resolve-Path $found.FullName).Path }
        }
      }
      catch {}
    }
    if ($candidatePath -match '\.exe$' -and (Test-Path $candidatePath)) {
      return (Resolve-Path $candidatePath).Path
    }
  }

  return $null
}

function Write-Header([string]$Text) {
  Write-Host "`n=== $Text ===" -ForegroundColor Cyan
}

function Get-ProfileSuffix([string]$CodexHome) {
  if (-not $CodexHome) { return $null }
  $leaf = Split-Path -Path $CodexHome -Leaf
  if (-not $leaf) { $leaf = $CodexHome }
  $suffix = $leaf.ToLowerInvariant()
  $suffix = $suffix -replace '[^a-z0-9_-]', '-'
  $suffix = $suffix.Trim('-')
  if (-not $suffix) { return $null }
  return $suffix
}

function Update-Preload([string]$AppDir) {
  $preload = Join-Path $AppDir ".vite\build\preload.js"
  if (-not (Test-Path $preload)) { return }
  $raw = Get-Content -Raw $preload
  $processExpose = 'const P={env:process.env,platform:process.platform,versions:process.versions,arch:process.arch,cwd:()=>process.env.PWD,argv:process.argv,pid:process.pid};n.contextBridge.exposeInMainWorld("process",P);'
  if ($raw -notlike "*$processExpose*") {
    $re = 'n\.contextBridge\.exposeInMainWorld\("codexWindowType",[A-Za-z0-9_$]+\);n\.contextBridge\.exposeInMainWorld\("electronBridge",[A-Za-z0-9_$]+\);'
    $m = [regex]::Match($raw, $re)
    if (-not $m.Success) { throw "preload patch point not found." }
    $raw = $raw.Replace($m.Value, "$processExpose$m")
    Set-Content -NoNewline -Path $preload -Value $raw
  }
}


function Add-GitToPath() {
  $candidates = @(
    (Join-Path $env:ProgramFiles "Git\cmd\git.exe"),
    (Join-Path $env:ProgramFiles "Git\bin\git.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Git\cmd\git.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Git\bin\git.exe")
  ) | Where-Object { $_ -and (Test-Path $_) }
  if (-not $candidates -or $candidates.Count -eq 0) { return }
  $gitDir = Split-Path $candidates[0] -Parent
  if ($env:PATH -notlike "*$gitDir*") {
    $env:PATH = "$gitDir;$env:PATH"
  }
}

function Add-DirToPath([string]$Dir) {
  if (-not $Dir) { return }
  if (-not (Test-Path $Dir)) { return }
  $parts = @($env:PATH -split ';' | Where-Object { $_ -and $_.Trim() })
  if ($parts -contains $Dir) { return }
  $env:PATH = "$Dir;$env:PATH"
}

function Repair-BasePath() {
  $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
  $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
  $merged = @()
  foreach ($segment in @($env:PATH, $machinePath, $userPath)) {
    if (-not $segment) { continue }
    $merged += ($segment -split ';' | Where-Object { $_ -and $_.Trim() })
  }
  $deduped = @()
  foreach ($entry in $merged) {
    if ($deduped -contains $entry) { continue }
    $deduped += $entry
  }
  $env:PATH = ($deduped -join ';')
}

function Add-CommonToolPaths() {
  Repair-BasePath

  Add-DirToPath (Join-Path $env:WINDIR "System32")
  Add-DirToPath (Join-Path $env:WINDIR "System32\Wbem")
  Add-DirToPath (Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0")
  Add-DirToPath $env:WINDIR

  Add-DirToPath (Join-Path $env:ProgramFiles "nodejs")
  Add-DirToPath (Join-Path ${env:ProgramFiles(x86)} "nodejs")
  Add-DirToPath (Join-Path $env:ProgramFiles "Git\cmd")
  Add-DirToPath (Join-Path ${env:ProgramFiles(x86)} "Git\cmd")

  Add-DirToPath (Join-Path $env:USERPROFILE ".cargo\bin")
  Add-DirToPath (Join-Path $env:USERPROFILE "go\bin")
  Add-DirToPath (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps")
  Add-DirToPath (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\Scripts")
  Add-DirToPath (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\Scripts")
  Add-DirToPath (Join-Path $env:USERPROFILE ".pyenv\pyenv-win\bin")
  Add-DirToPath (Join-Path $env:USERPROFILE ".pyenv\pyenv-win\shims")

  $fnmMultishell = Join-Path $env:LOCALAPPDATA "fnm_multishells"
  if (Test-Path $fnmMultishell) {
    $latestNodeDir = Get-ChildItem -Path $fnmMultishell -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
    if ($latestNodeDir) {
      Add-DirToPath $latestNodeDir.FullName
    }
  }
}

Set-CoreShellEnvironment
Add-CommonToolPaths
Add-GitToPath

Test-Command node
Test-Command npm
Test-Command npx

foreach ($k in @("npm_config_runtime", "npm_config_target", "npm_config_disturl", "npm_config_arch", "npm_config_build_from_source")) {
  if (Test-Path "Env:$k") { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
}

if (-not $DmgPath) {
  $default = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")) "Codex.dmg"
  if (Test-Path $default) {
    $DmgPath = $default
  }
  else {
    $cand = Get-ChildItem -Path (Resolve-Path (Join-Path $PSScriptRoot "..")) -Filter "*.dmg" -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cand) {
      $DmgPath = $cand.FullName
    }
    else {
      throw "No DMG found."
    }
  }
}

$DmgPath = (Resolve-Path $DmgPath).Path
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$WorkDir = (Resolve-Path $WorkDir).Path

$sevenZip = Resolve-7z $WorkDir
if (-not $sevenZip) { throw "7z not found." }

$extractedDir = Join-Path $WorkDir "extracted"
$electronDir = Join-Path $WorkDir "electron"
$appDir = Join-Path $WorkDir "app"
$nativeDir = Join-Path $WorkDir "native-builds"
$profileSuffix = Get-ProfileSuffix $env:CODEX_HOME
if ($profileSuffix) {
  $userDataDir = Join-Path $WorkDir "userdata-$profileSuffix"
  $cacheDir = Join-Path $WorkDir "cache-$profileSuffix"
}
else {
  $userDataDir = Join-Path $WorkDir "userdata"
  $cacheDir = Join-Path $WorkDir "cache"
}
Write-Host "Using profile data dir: $userDataDir" -ForegroundColor DarkGray
Write-Host "Using profile cache dir: $cacheDir" -ForegroundColor DarkGray

if (-not $Reuse) {
  Write-Header "Extracting DMG"
  New-Item -ItemType Directory -Force -Path $extractedDir | Out-Null
  & $sevenZip x -y $DmgPath -o"$extractedDir" | Out-Null

  Write-Header "Extracting app.asar"
  New-Item -ItemType Directory -Force -Path $electronDir | Out-Null
  $hfs = Join-Path $extractedDir "4.hfs"
  if (Test-Path $hfs) {
    & $sevenZip x -y $hfs "Codex Installer/Codex.app/Contents/Resources/app.asar" "Codex Installer/Codex.app/Contents/Resources/app.asar.unpacked" -o"$electronDir" | Out-Null
  }
  else {
    $directApp = Join-Path $extractedDir "Codex Installer\Codex.app\Contents\Resources\app.asar"
    if (-not (Test-Path $directApp)) {
      throw "app.asar not found."
    }
    $directUnpacked = Join-Path $extractedDir "Codex Installer\Codex.app\Contents\Resources\app.asar.unpacked"
    New-Item -ItemType Directory -Force -Path (Split-Path $directApp -Parent) | Out-Null
    $destBase = Join-Path $electronDir "Codex Installer\Codex.app\Contents\Resources"
    New-Item -ItemType Directory -Force -Path $destBase | Out-Null
    Copy-Item -Force $directApp (Join-Path $destBase "app.asar")
    if (Test-Path $directUnpacked) {
      & robocopy $directUnpacked (Join-Path $destBase "app.asar.unpacked") /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null
    }
  }

  Write-Header "Unpacking app.asar"
  New-Item -ItemType Directory -Force -Path $appDir | Out-Null
  $asar = Join-Path $electronDir "Codex Installer\Codex.app\Contents\Resources\app.asar"
  if (-not (Test-Path $asar)) { throw "app.asar not found." }
  & npx --yes @electron/asar extract $asar $appDir

  Write-Header "Syncing app.asar.unpacked"
  $unpacked = Join-Path $electronDir "Codex Installer\Codex.app\Contents\Resources\app.asar.unpacked"
  if (Test-Path $unpacked) {
    & robocopy $unpacked $appDir /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null
  }
}

Write-Header "Patching preload"
Update-Preload $appDir

Write-Header "Reading app metadata"
$pkgPath = Join-Path $appDir "package.json"
if (-not (Test-Path $pkgPath)) { throw "package.json not found." }
$pkg = Get-Content -Raw $pkgPath | ConvertFrom-Json
$electronVersion = $pkg.devDependencies.electron
$betterVersion = $pkg.dependencies."better-sqlite3"
$ptyVersion = $pkg.dependencies."node-pty"

if (-not $electronVersion) { throw "Electron version not found." }

Write-Header "Preparing native modules"
$arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "win32-arm64" } else { "win32-x64" }
$bsDst = Join-Path $appDir "node_modules\better-sqlite3\build\Release\better_sqlite3.node"
$ptyDstPre = Join-Path $appDir "node_modules\node-pty\prebuilds\$arch"
$appHasNative = (Test-Path $bsDst) -and (Test-Path (Join-Path $ptyDstPre "pty.node"))
$electronExe = Join-Path $nativeDir "node_modules\electron\dist\electron.exe"
$skipNative = $Reuse -and $appHasNative
if ($skipNative) {
  Write-Host "Native modules already present in app. Skipping rebuild." -ForegroundColor Cyan
}
else {
  New-Item -ItemType Directory -Force -Path $nativeDir | Out-Null
  Push-Location $nativeDir
  if (-not (Test-Path (Join-Path $nativeDir "package.json"))) {
    & npm init -y | Out-Null
  }

  $bsSrcProbe = Join-Path $nativeDir "node_modules\better-sqlite3\build\Release\better_sqlite3.node"
  $ptySrcProbe = Join-Path $nativeDir "node_modules\node-pty\prebuilds\$arch\pty.node"
  $electronExe = Join-Path $nativeDir "node_modules\electron\dist\electron.exe"
  $haveNative = (Test-Path $bsSrcProbe) -and (Test-Path $ptySrcProbe) -and (Test-Path $electronExe)

  if (-not $haveNative) {
    $deps = @(
      "better-sqlite3@$betterVersion",
      "node-pty@$ptyVersion",
      "@electron/rebuild",
      "prebuild-install",
      "electron@$electronVersion"
    )
    & npm install --no-save @deps
    if ($LASTEXITCODE -ne 0) { throw "npm install failed." }
    $electronExe = Join-Path $nativeDir "node_modules\electron\dist\electron.exe"
  }
  else {
    Write-Host "Native modules already present. Skipping rebuild." -ForegroundColor Cyan
  }

  Write-Host "Rebuilding native modules for Electron $electronVersion..." -ForegroundColor Cyan
  $rebuildOk = $false
  try {
    $rebuildCli = Join-Path $nativeDir "node_modules\@electron\rebuild\lib\cli.js"
    if (-not (Test-Path $rebuildCli)) { throw "electron-rebuild not found." }
    # Disable Spectre-mitigated library requirement (avoids MSB8040 error)
    $env:npm_config_msbuild_args = "/p:SpectreMitigation=false"
    & node $rebuildCli -v $electronVersion -w "better-sqlite3" | Out-Null
    $env:npm_config_msbuild_args = $null
    $rebuildOk = $true
  }
  catch {
    $env:npm_config_msbuild_args = $null
    Write-Host "electron-rebuild failed: $($_.Exception.Message)" -ForegroundColor Yellow
  }

  if (-not $rebuildOk) {
    Write-Host "Trying prebuilt Electron binaries for better-sqlite3..." -ForegroundColor Yellow
    $bsDir = Join-Path $nativeDir "node_modules\better-sqlite3"
    if (Test-Path $bsDir) {
      Push-Location $bsDir
      $prebuildCli = Join-Path $nativeDir "node_modules\prebuild-install\bin.js"
      if (-not (Test-Path $prebuildCli)) { throw "prebuild-install not found." }
      & node $prebuildCli -r electron -t $electronVersion --tag-prefix=electron-v | Out-Null
      Pop-Location
    }
  }

  $env:ELECTRON_RUN_AS_NODE = "1"
  if (-not (Test-Path $electronExe)) { throw "electron.exe not found." }
  if (-not (Test-Path (Join-Path $nativeDir "node_modules\better-sqlite3"))) {
    throw "better-sqlite3 not installed."
  }
  & $electronExe -e "try{require('./node_modules/better-sqlite3');process.exit(0)}catch(e){console.error(e);process.exit(1)}" | Out-Null
  Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
  if ($LASTEXITCODE -ne 0) { throw "better-sqlite3 failed to load." }

  Pop-Location

  $bsSrc = Join-Path $nativeDir "node_modules\better-sqlite3\build\Release\better_sqlite3.node"
  $bsDstDir = Split-Path $bsDst -Parent
  New-Item -ItemType Directory -Force -Path $bsDstDir | Out-Null
  if (-not (Test-Path $bsSrc)) { throw "better_sqlite3.node not found." }
  Copy-Item -Force $bsSrc (Join-Path $bsDstDir "better_sqlite3.node")

  $ptySrcDir = Join-Path $nativeDir "node_modules\node-pty\prebuilds\$arch"
  $ptyDstRel = Join-Path $appDir "node_modules\node-pty\build\Release"
  New-Item -ItemType Directory -Force -Path $ptyDstPre | Out-Null
  New-Item -ItemType Directory -Force -Path $ptyDstRel | Out-Null

  $ptyFiles = @("pty.node", "conpty.node", "conpty_console_list.node")
  foreach ($f in $ptyFiles) {
    $src = Join-Path $ptySrcDir $f
    if (Test-Path $src) {
      Copy-Item -Force $src (Join-Path $ptyDstPre $f)
      Copy-Item -Force $src (Join-Path $ptyDstRel $f)
    }
  }
}

if (-not $NoLaunch) {
  Write-Header "Resolving Codex CLI"
  $cli = Resolve-CodexCliPath $CodexCliPath
  if (-not $cli) {
    throw "codex.exe not found."
  }

  if (-not (Test-Path $electronExe)) {
    throw "Electron not found at: $electronExe"
  }

  Write-Host "Using electron.exe: $electronExe" -ForegroundColor Green
  Write-Host "Using codex CLI: $cli" -ForegroundColor Green
  Write-Header "Launching Codex"
  $rendererUrl = (New-Object System.Uri (Join-Path $appDir "webview\index.html")).AbsoluteUri
  Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
  $env:ELECTRON_RENDERER_URL = $rendererUrl
  $env:ELECTRON_FORCE_IS_PACKAGED = "1"
  $buildNumber = if ($pkg.PSObject.Properties.Name -contains "codexBuildNumber" -and $pkg.codexBuildNumber) { $pkg.codexBuildNumber } else { "510" }
  $buildFlavor = if ($pkg.PSObject.Properties.Name -contains "codexBuildFlavor" -and $pkg.codexBuildFlavor) { $pkg.codexBuildFlavor } else { "prod" }
  $env:CODEX_BUILD_NUMBER = $buildNumber
  $env:CODEX_BUILD_FLAVOR = $buildFlavor
  $env:BUILD_FLAVOR = $buildFlavor
  $env:NODE_ENV = "production"
  $env:CODEX_CLI_PATH = $cli
  $env:PWD = $appDir
  Set-CoreShellEnvironment
  Add-CommonToolPaths
  Add-GitToPath

  New-Item -ItemType Directory -Force -Path $userDataDir | Out-Null
  New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null

  $launchArgs = @(
    "$appDir",
    "--user-data-dir=`"$userDataDir`"",
    "--disk-cache-dir=`"$cacheDir`""
  )
  if ($EnableLogging) {
    $launchArgs += "--enable-logging"
  }

  Start-Process -FilePath $electronExe -ArgumentList $launchArgs
}
