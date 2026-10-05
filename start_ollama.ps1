<#
.SYNOPSIS
    Starts Ollama bound to 0.0.0.0:11434 with CORS enabled, allowing external connections from iPhone and local devices.

.DESCRIPTION
    This script:
    1. Sets OLLAMA_HOST=0.0.0.0:11434 for the current session.
    2. Sets OLLAMA_ORIGINS=* to allow web and mobile app cross-origin access.
    3. Checks Windows Firewall rule for port 11434.
    4. Displays your local IPv4 address for mobile configuration.
    5. Starts the Ollama server.
#>

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Ollama External Network Launcher (0.0.0.0:11434)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Configure Environment Variables for this process
$env:OLLAMA_HOST = "0.0.0.0:11434"
$env:OLLAMA_ORIGINS = "*"

# Ensure Ollama install location is present in current session PATH
$ollamaDir = "$env:LOCALAPPDATA\Programs\Ollama"
if (Test-Path $ollamaDir) {
    if ($env:PATH -notlike "*$ollamaDir*") {
        $env:PATH = "$ollamaDir;$env:PATH"
    }
}

Write-Host "`n[+] Environment configured:" -ForegroundColor Green
Write-Host "    OLLAMA_HOST    = $env:OLLAMA_HOST"
Write-Host "    OLLAMA_ORIGINS = $env:OLLAMA_ORIGINS"

# 2. Tip for permanent configuration
Write-Host "`n[i] Note: To make 0.0.0.0 permanent across all Windows reboots, run:" -ForegroundColor DarkGray
Write-Host "    [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')" -ForegroundColor DarkGray
Write-Host "    [System.Environment]::SetEnvironmentVariable('OLLAMA_ORIGINS', '*', 'User')" -ForegroundColor DarkGray

# 3. Check Windows Firewall rule
Write-Host "`n[+] Checking Windows Firewall for Port 11434..." -ForegroundColor Yellow
$rule = Get-NetFirewallRule -DisplayName "Ollama Local Network Access" -ErrorAction SilentlyContinue
if (-not $rule) {
    # Check if any rule covers 11434
    $portRule = Get-NetFirewallPortFilter | Where-Object { $_.LocalPort -eq "11434" } -ErrorAction SilentlyContinue
    if ($portRule) {
        Write-Host "    [OK] Inbound rule for port 11434 already exists." -ForegroundColor Green
    } else {
        Write-Host "    [!] Inbound firewall rule for port 11434 was not detected." -ForegroundColor Yellow
        Write-Host "    If your iPhone cannot connect, run this command in an Administrator PowerShell:" -ForegroundColor Yellow
        Write-Host "    New-NetFirewallRule -DisplayName 'Ollama Local Network Access' -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow" -ForegroundColor White
    }
} else {
    Write-Host "    [OK] Firewall rule 'Ollama Local Network Access' is active." -ForegroundColor Green
}

# 4. Display Local IPv4 for iPhone setup
Write-Host "`n[+] Finding your local Wi-Fi / Ethernet IPv4 address..." -ForegroundColor Green
$ips = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.InterfaceAlias -notlike "*Loopback*" -and 
    $_.InterfaceAlias -notlike "*vEthernet*" -and 
    $_.IPAddress -notlike "169.254.*" 
}

foreach ($item in $ips) {
    Write-Host "    * Interface: $($item.InterfaceAlias) -> http://$($item.IPAddress):11434" -ForegroundColor Cyan
}

Write-Host "`n--> On your iPhone (in Enchanted or Reins), enter the address above!" -ForegroundColor Magenta
Write-Host "----------------------------------------------------------"

# 5. Check if Ollama is already running
$existingProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($existingProcess) {
    Write-Host "`n[!] An existing Ollama process is currently running (PID: $($existingProcess.Id))." -ForegroundColor Yellow
    Write-Host "    If it was started without OLLAMA_HOST=0.0.0.0, close the Ollama tray icon" -ForegroundColor Yellow
    Write-Host "    or kill the process before starting this script." -ForegroundColor Yellow
    $ans = Read-Host "Would you like to stop the existing Ollama process and restart? (Y/N)"
    if ($ans -eq "Y" -or $ans -eq "y") {
        Stop-Process -Name "ollama" -Force
        Start-Sleep -Seconds 1
    }
}

# 6. Start Ollama
Write-Host "`n[>] Starting Ollama server on 0.0.0.0:11434 (Press Ctrl+C to stop)..." -ForegroundColor Green
try {
    & ollama serve
} catch {
    Write-Host "[!] Error launching 'ollama serve': $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "    Please ensure Ollama is installed and added to PATH." -ForegroundColor Red
    Write-Host "    Download installer from: https://ollama.com/download/windows" -ForegroundColor Red
}
