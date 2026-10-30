param(
    [string]$HostIP = "",
    [int]$Port = 8000,
    [int]$Requests = 100,
    [int]$Rounds = 5,
    [string]$Distro = "Debian"
)

$ErrorActionPreference = "Stop"

$Praktikum = $PSScriptRoot
$Root = Split-Path -Parent $Praktikum
$RepoRoot = Split-Path -Parent $Root
$Skrip = Join-Path $Praktikum "rpc_l14_wsl.py"
$Hasil = Join-Path $Praktikum "hasil"
$Log = Join-Path $Hasil "l1_4_wsl.txt"
$HostDariPengguna = -not [string]::IsNullOrWhiteSpace($HostIP)
New-Item -ItemType Directory -Force -Path $Hasil | Out-Null

if (-not (Test-Path -LiteralPath $Skrip)) {
    throw "Skrip tidak ditemukan: $Skrip"
}

$SkripUntukWsl = $Skrip.Replace("\", "/")
$SkripWsl = (& wsl -d $Distro -- wslpath -a $SkripUntukWsl | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $SkripWsl) {
    throw "Gagal memetakan path ke WSL. Pastikan distro '$Distro' tersedia."
}

if (-not $HostIP) {
    $Rute = & wsl -d $Distro -- ip route | Out-String
    $BarisDefault = ($Rute -split "`r?`n" | Where-Object { $_ -match '^default\s' } | Select-Object -First 1)
    if ($BarisDefault -match 'via\s+(\S+)') {
        $HostIP = $Matches[1]
    }
}
if (-not $HostIP) {
    throw "Tidak bisa menentukan IP Windows. Isi parameter -HostIP."
}

$ServerProcess = $null
$StartedServer = $false
$Listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

if (-not $Listener) {
    $Python = Join-Path $Root "venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $Python)) {
        $Python = Join-Path $RepoRoot "venv\Scripts\python.exe"
    }
    if (-not (Test-Path -LiteralPath $Python)) {
        $Python = "python"
    }

    $ServerProcess = Start-Process -FilePath $Python `
        -ArgumentList @("praktikum1\server_kalkulator.py", "--host", "0.0.0.0", "--port", "$Port") `
        -WorkingDirectory $Root -PassThru -WindowStyle Hidden
    $StartedServer = $true

    $Siap = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 250
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
            $Siap = $true
            break
        }
        if ($ServerProcess.HasExited) {
            break
        }
    }

    if (-not $Siap) {
        if (-not $ServerProcess.HasExited) {
            Stop-Process -Id $ServerProcess.Id -Force
        }
        throw "Server XML-RPC tidak siap di port $Port."
    }
}

$Header = @(
    "L1.4 WSL - Windows host ${HostIP}:${Port}, ${Requests} request x ${Rounds} putaran",
    "Waktu: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "Distro: $Distro",
    ""
) -join [Environment]::NewLine

$HomeWsl = (& wsl -d $Distro -- printenv HOME | Out-String).Trim()
$SkripJalan = $SkripWsl
if ($HomeWsl) {
    $SkripHomeWsl = "$HomeWsl/rpc_l14_wsl.py"
    & wsl -d $Distro -- cp $SkripWsl $SkripHomeWsl | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $SkripJalan = $SkripHomeWsl
    }
}

$ArgumenWsl = @($SkripJalan, "--port", "$Port", "--requests", "$Requests", "--rounds", "$Rounds")
if ($HostDariPengguna) {
    $ArgumenWsl += @("--host", $HostIP)
}

try {
    $Keluaran = & wsl -d $Distro -- python3 @ArgumenWsl 2>&1
    $Kode = $LASTEXITCODE
    $Teks = ($Keluaran | Out-String)
    Set-Content -LiteralPath $Log -Value ($Header + $Teks) -Encoding utf8
    Write-Output $Teks

    if ($Kode -ne 0) {
        throw "Benchmark gagal (exit $Kode). Lihat $Log."
    }
}
finally {
    if ($StartedServer -and $ServerProcess -and -not $ServerProcess.HasExited) {
        Stop-Process -Id $ServerProcess.Id -Force
    }
}
