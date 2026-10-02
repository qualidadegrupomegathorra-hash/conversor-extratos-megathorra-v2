$ErrorActionPreference = 'SilentlyContinue'

function Emit-IfExists([string]$Path) {
    if ($Path -and (Test-Path -LiteralPath $Path -PathType Leaf)) {
        (Resolve-Path -LiteralPath $Path).Path
        exit 0
    }
}

# 1) PATH atual
$cmd = Get-Command tesseract.exe -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source) { Emit-IfExists $cmd.Source }

# 2) Locais comuns de instalação
$candidates = @(
    "$env:ProgramFiles\Tesseract-OCR\tesseract.exe",
    "${env:ProgramFiles(x86)}\Tesseract-OCR\tesseract.exe",
    "$env:LOCALAPPDATA\Programs\Tesseract-OCR\tesseract.exe",
    "$env:LOCALAPPDATA\Tesseract-OCR\tesseract.exe",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links\tesseract.exe"
)
foreach ($candidate in $candidates) { Emit-IfExists $candidate }

# 3) Registro do Windows (instaladores MSI/EXE, inclusive UB-Mannheim)
$registryRoots = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
foreach ($root in $registryRoots) {
    Get-ItemProperty $root | Where-Object { $_.DisplayName -match 'Tesseract' } | ForEach-Object {
        if ($_.InstallLocation) {
            Emit-IfExists (Join-Path $_.InstallLocation 'tesseract.exe')
        }
        if ($_.DisplayIcon) {
            $icon = ($_.DisplayIcon -replace ',\d+$','').Trim('"')
            if ($icon -match 'tesseract\.exe$') { Emit-IfExists $icon }
        }
    }
}

# 4) Pacotes instalados pelo WinGet em escopo de usuário
$wingetPackages = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages"
if (Test-Path -LiteralPath $wingetPackages) {
    $found = Get-ChildItem -LiteralPath $wingetPackages -Filter tesseract.exe -File -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    Emit-IfExists $found
}

exit 1
