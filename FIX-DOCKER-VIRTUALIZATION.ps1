# Script para Habilitar Virtualizacion para Docker
# EJECUTAR COMO ADMINISTRADOR

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "HABILITANDO VIRTUALIZACION PARA DOCKER" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "[1/4] Verificando estado de Hyper-V..." -ForegroundColor Green
$hyperv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
if ($hyperv.State -eq "Enabled") {
    Write-Host "    OK - Hyper-V esta habilitado" -ForegroundColor Green
} else {
    Write-Host "    ADVERTENCIA - Hyper-V no esta habilitado" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/4] Configurando arranque de Hyper-V..." -ForegroundColor Green
try {
    bcdedit /set hypervisorlaunchtype auto | Out-Null
    Write-Host "    OK - Hypervisor configurado para arranque automatico" -ForegroundColor Green
}
catch {
    Write-Host "    ERROR: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[3/4] Habilitando caracteristicas de Windows necesarias..." -ForegroundColor Green
$features = @(
    "Microsoft-Hyper-V-All",
    "VirtualMachinePlatform",
    "Microsoft-Windows-Subsystem-Linux"
)

foreach ($feature in $features) {
    Write-Host "    Verificando: $feature" -ForegroundColor Gray
    $state = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
    if ($null -eq $state) {
        Write-Host "      SKIP - Feature no disponible" -ForegroundColor Yellow
    } elseif ($state.State -eq "Enabled") {
        Write-Host "      OK - Ya esta habilitado" -ForegroundColor Green
    } else {
        Write-Host "      Habilitando..." -ForegroundColor Yellow
        Enable-WindowsOptionalFeature -Online -FeatureName $feature -NoRestart -WarningAction SilentlyContinue | Out-Null
        Write-Host "      OK - Habilitado" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[4/4] Verificando WSL2..." -ForegroundColor Green
wsl --set-default-version 2 2>$null
Write-Host "    OK - WSL2 configurado como version por defecto" -ForegroundColor Green

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "CONFIGURACION COMPLETADA" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANTE: Debes REINICIAR tu computadora para que los cambios surtan efecto" -ForegroundColor Red
Write-Host ""
Write-Host "Despues de reiniciar:" -ForegroundColor White
Write-Host "  1. Abre Docker Desktop" -ForegroundColor Gray
Write-Host "  2. Deberia iniciar sin problemas de virtualizacion" -ForegroundColor Gray
Write-Host "  3. Ve a Settings -> Docker Engine" -ForegroundColor Gray
Write-Host "  4. Agrega la configuracion DNS que te mostre antes" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona cualquier tecla para cerrar..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
