# Run from the extracted Noemorph-Windows portable package.
# Requires Windows x64, installed Python 3.14 x64, and Microsoft WebView2.
param(
    [string]$Python = 'python',
    [switch]$ServerOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir = Join-Path $root 'Noemorph'
$frontend = Join-Path $appDir 'frontend\dist\index.html'
$requirements = Join-Path $appDir 'requirements.txt'
$wheelhouse = Join-Path $root 'wheelhouse'
$runtime = Join-Path $root '.runtime\venv'
$venvPython = Join-Path $runtime 'Scripts\python.exe'

if (-not (Test-Path $frontend)) {
    throw 'The prebuilt web interface is missing. Restore the complete release ZIP.'
}
if (-not (Test-Path $requirements) -or -not (Test-Path $wheelhouse)) {
    throw 'Offline requirements or wheelhouse are missing. Restore the complete release ZIP.'
}

& $Python -c "import platform,sys; assert sys.version_info[:2] == (3,14), 'Python 3.14 is required'; assert platform.architecture()[0] == '64bit', '64-bit Python is required'"
if ($LASTEXITCODE -ne 0) { throw 'A working 64-bit Python 3.14 executable is required. Pass -Python with its path.' }

if (-not (Test-Path $venvPython)) {
    Write-Host 'Preparing a contained Python environment...'
    & $Python -m venv $runtime
    if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
}

Write-Host 'Installing locked dependencies from bundled wheels (no network)...'
& $venvPython -m pip install --disable-pip-version-check --no-input --no-index --find-links $wheelhouse -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Offline wheel installation failed. Check Python version and release integrity.' }
& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'The contained Python dependency environment is inconsistent.' }

$launcherArgs = @('--skip-python-bootstrap', '--skip-build')
if ($ServerOnly) { $launcherArgs += '--server-only' }
& $venvPython (Join-Path $appDir 'Noemorph.py') @launcherArgs
exit $LASTEXITCODE
