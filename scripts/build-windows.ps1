[CmdletBinding()]
param(
    [string]$PythonExecutable,
    [switch]$SmokeTest,
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$SigningCertificateThumbprint,
    [uri]$TimestampUrl,
    [string]$SignToolPath
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Build the Windows package on Windows.' }

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE): $Program $Arguments" }
}

function Resolve-SignTool {
    param([string]$ExecutablePath)

    if ($ExecutablePath) {
        $Tool = Get-Item -LiteralPath $ExecutablePath
        if ($Tool.PSIsContainer) { throw 'SignToolPath must point to the SignTool executable.' }
        return $Tool.FullName
    }
    $Tool = Get-Command -Name 'signtool.exe' -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($Tool) { return $Tool.Source }

    $ProgramFiles = ${env:ProgramFiles(x86)}
    if ($ProgramFiles) {
        $KitsBin = Join-Path $ProgramFiles 'Windows Kits\10\bin'
        $Tool = Get-ChildItem -Path (Join-Path $KitsBin '*\x64\signtool.exe') -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Directory.Parent.Name -match '^\d+(\.\d+){3}$' } |
            Sort-Object -Property { [version]$_.Directory.Parent.Name } -Descending |
            Select-Object -First 1
        if ($Tool) { return $Tool.FullName }
    }
    throw 'SignTool was not found. Install the Windows SDK or pass -SignToolPath.'
}

function Confirm-CompassSignature {
    param([string]$Tool, [string]$Executable, [string]$ExpectedThumbprint)

    Invoke-Checked $Tool @('verify', '/pa', '/all', '/tw', '/v', $Executable)
    $Signature = Get-AuthenticodeSignature -LiteralPath $Executable
    if ($Signature.Status -ne 'Valid' -or $Signature.SignerCertificate.Thumbprint -ne $ExpectedThumbprint -or
        -not $Signature.TimeStamperCertificate) {
        throw 'The packaged executable does not have a valid timestamped signature from the selected publisher.'
    }
}

function Test-PackagedStartup {
    param([string]$Executable)

    $App = Start-Process -FilePath $Executable -PassThru
    try {
        $Deadline = [DateTime]::UtcNow.AddSeconds(30)
        do {
            Start-Sleep -Milliseconds 250
            $App.Refresh()
            if ($App.HasExited) { throw "Compass exited unexpectedly: $($App.ExitCode)" }
            if ($App.MainWindowTitle -eq 'Compass could not start') {
                throw 'Compass displayed a startup error.'
            }
            if ($App.MainWindowHandle -ne [IntPtr]::Zero -and $App.MainWindowTitle -eq 'Compass') {
                Start-Sleep -Seconds 2
                $App.Refresh()
                if ($App.HasExited) { throw "Compass exited unexpectedly: $($App.ExitCode)" }
                if ($App.MainWindowTitle -eq 'Compass') { return }
            }
        } while ([DateTime]::UtcNow -lt $Deadline)
        throw 'Compass did not open a window within 30 seconds.'
    } finally {
        if (-not $App.HasExited) {
            if (-not $App.CloseMainWindow() -or -not $App.WaitForExit(5000)) {
                $App.Kill()
                $App.WaitForExit()
            }
        }
        $App.Dispose()
    }
}

$Signer = $null
if ($SigningCertificateThumbprint) {
    if (-not $TimestampUrl -or -not $TimestampUrl.IsAbsoluteUri -or
        $TimestampUrl.Scheme -notin @('http', 'https') -or $TimestampUrl.UserInfo) {
        throw 'Signing requires an absolute HTTP or HTTPS RFC 3161 -TimestampUrl without credentials.'
    }
    $Thumbprint = $SigningCertificateThumbprint.ToUpperInvariant()
    $Certificate = Get-Item -LiteralPath "Cert:\CurrentUser\My\$Thumbprint" -ErrorAction SilentlyContinue
    if (-not $Certificate -or -not $Certificate.HasPrivateKey) {
        throw 'The selected code-signing certificate and its signing key must be accessible through Cert:\CurrentUser\My.'
    }
    $Signer = Resolve-SignTool $SignToolPath
} elseif ($TimestampUrl -or $SignToolPath) {
    throw 'Signing requires -SigningCertificateThumbprint.'
}

$Repository = Split-Path $PSScriptRoot -Parent
$BuildDirectory = Join-Path ([IO.Path]::GetTempPath()) "compass-build-$([Guid]::NewGuid())"
$Venv = Join-Path $BuildDirectory 'venv'
if ($PythonExecutable) {
    $Launcher = (Get-Command $PythonExecutable -CommandType Application | Select-Object -First 1).Source
    $LauncherArguments = @()
} else {
    $Launcher = 'py'
    $LauncherArguments = @('-3.14')
}

Push-Location $Repository
try {
    $Version = (Get-Content -LiteralPath 'VERSION' -Raw).Trim()
    if ($Version -notmatch '^\d+\.\d+\.\d+(rc\d+)?$') { throw 'VERSION must contain a Compass release version.' }
    $CheckPlatform = 'import sys, sysconfig; sys.exit(sys.version_info[:2] != (3, 14) or sys.version_info[:3] < (3, 14, 10) or sysconfig.get_platform() != sys.argv[1])'
    try {
        Invoke-Checked $Launcher ($LauncherArguments + @('-I', '-c', $CheckPlatform, 'win-amd64'))
    } catch {
        throw "Requires Windows x64 CPython 3.14.10 or a newer 3.14 maintenance release. $_"
    }
    Invoke-Checked $Launcher ($LauncherArguments + @('-I', '-m', 'venv', $Venv))
    $Python = Join-Path $Venv 'Scripts\python.exe'

    $PipInstall = @('-I', '-m', 'pip', '--isolated', '--disable-pip-version-check', 'install', '--require-hashes', '--only-binary=:all:')
    Invoke-Checked $Python ($PipInstall + @('-r', 'requirements-windows-bootstrap.lock'))
    # pywebview depends on proxy-tools, which upstream distributes only as a source archive.
    Invoke-Checked $Python ($PipInstall + @(
        '--no-build-isolation', '--no-cache-dir', '--no-binary=proxy-tools', '-r', 'requirements-windows-x64.lock'
    ))
    Invoke-Checked $Python @('-I', '-m', 'pip', 'check')
    Invoke-Checked $Python @('scripts\sync_catalog.py', '--check')
    Invoke-Checked $Python @('-m', 'unittest', 'discover', '-s', 'tests', '-v')
    if ($SmokeTest) {
        $SmokeSource = Join-Path $BuildDirectory 'smoke source #1 %23'
        $SmokeScripts = New-Item -ItemType Directory -Path (Join-Path $SmokeSource 'scripts') -Force
        Copy-Item -LiteralPath 'main.py', 'VERSION', 'compass', 'ui' -Destination $SmokeSource -Recurse
        Copy-Item -LiteralPath 'scripts\smoke_desktop.py' -Destination $SmokeScripts.FullName
        Invoke-Checked $Python @((Join-Path $SmokeScripts.FullName 'smoke_desktop.py'))
    }
    Invoke-Checked $Python @(
        '-I', '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed', '--onedir',
        '--name', 'Compass', '--icon', 'packaging\windows\Compass.ico',
        '--add-data', 'ui;ui', '--add-data', 'VERSION;.', 'main.py'
    )

    $Package = (Resolve-Path -LiteralPath 'dist\Compass').Path
    $AndroidBridge = Join-Path $Package '_internal\webview\lib\pywebview-android.jar'
    if (Test-Path -LiteralPath $AndroidBridge) {
        Remove-Item -LiteralPath $AndroidBridge
    }
    Invoke-Checked $Python @('-I', 'scripts\collect_notices.py', 'build\Compass\Analysis-00.toc', $Package)
    $SignatureNotice = 'Compass.exe in this package is unsigned.'
    if ($Signer) {
        Invoke-Checked $Signer @(
            'sign', '/s', 'My', '/sha1', $Thumbprint, '/fd', 'SHA256',
            '/tr', $TimestampUrl.AbsoluteUri, '/td', 'SHA256', (Join-Path $Package 'Compass.exe')
        )
        $SignatureNotice = 'Compass.exe has a timestamped Authenticode publisher signature.'
    }
    $PortableReadme = Get-Content -LiteralPath 'scripts\WINDOWS-PORTABLE.txt' -Raw
    Set-Content -LiteralPath (Join-Path $Package 'README.txt') -Encoding ASCII -NoNewline -Value (
        $PortableReadme.Replace('@COMPASS_SIGNATURE_STATUS@', $SignatureNotice)
    )
    $Release = New-Item -ItemType Directory -Path 'dist\release' -Force
    $ArchiveName = "Compass-$Version-Windows-x64.zip"
    if (-not $Signer -and $Version -notmatch 'rc\d+$') {
        $ArchiveName = "Compass-$Version-Windows-x64-unsigned.zip"
    }
    $Archive = Join-Path $Release.FullName $ArchiveName
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $StagedArchive = Join-Path $BuildDirectory $ArchiveName
    [IO.Compression.ZipFile]::CreateFromDirectory($Package, $StagedArchive, [IO.Compression.CompressionLevel]::Optimal, $true)
    if ($SmokeTest -or $Signer) {
        $Extracted = Join-Path $BuildDirectory 'smoke unpack #1 %23'
        [IO.Compression.ZipFile]::ExtractToDirectory($StagedArchive, $Extracted)
        $PackagedExe = Join-Path $Extracted 'Compass\Compass.exe'
        if ($Signer) { Confirm-CompassSignature $Signer $PackagedExe $Thumbprint }
        if ($SmokeTest) { Test-PackagedStartup $PackagedExe }
    }
    $Hash = (Get-FileHash -LiteralPath $StagedArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    Move-Item -LiteralPath $StagedArchive -Destination $Archive -Force
    Set-Content -LiteralPath "$Archive.sha256" -Value "$Hash  $ArchiveName" -Encoding ASCII
    Write-Host "$SignatureNotice Windows package: $Archive"
} finally {
    Pop-Location
    if (Test-Path -LiteralPath $BuildDirectory) {
        Remove-Item -LiteralPath $BuildDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}
