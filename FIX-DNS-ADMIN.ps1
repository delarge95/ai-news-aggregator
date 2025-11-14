# Script para Fijar DNS y Solucionar Problema de Docker
# EJECUTAR COMO ADMINISTRADOR

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "SOLUCIONANDO PROBLEMA DNS DE DOCKER - EJECUTAR COMO ADMIN" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

# Paso 1: Identificar adaptador activo
Write-Host ""
Write-Host "[1/5] Identificando adaptador de red activo..." -ForegroundColor Green
$adapter = Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1
Write-Host "    Adaptador encontrado: $($adapter.Name)" -ForegroundColor White

# Paso 2: Configurar DNS en el adaptador
Write-Host ""
Write-Host "[2/5] Configurando DNS de Cloudflare (1.1.1.1)..." -ForegroundColor Green
try {
    Set-DnsClientServerAddress -InterfaceAlias $adapter.Name -ServerAddresses ("1.1.1.1","1.0.0.1","8.8.8.8")
    Write-Host "    OK - DNS configurado correctamente" -ForegroundColor Green
}
catch {
    Write-Host "    ERROR: $_" -ForegroundColor Red
    Write-Host "    Intenta ejecutar este script como Administrador" -ForegroundColor Yellow
    Pause
    exit
}

# Paso 3: Limpiar cache DNS
Write-Host ""
Write-Host "[3/5] Limpiando cache DNS..." -ForegroundColor Green
ipconfig /flushdns | Out-Null
Write-Host "    OK - Cache DNS limpiada" -ForegroundColor Green

# Paso 4: Configurar WSL2
Write-Host ""
Write-Host "[4/5] Configurando WSL2 para prevenir conflictos..." -ForegroundColor Green
$wslConfig = @"
[wsl2]
networkingMode=mirrored
dnsTunneling=false
autoProxy=false
firewall=false

[network]
generateResolvConf=false

memory=4GB
processors=2
swap=0
"@
$wslConfig | Out-File -FilePath "$env:USERPROFILE\.wslconfig" -Encoding ASCII -Force
Write-Host "    OK - Archivo .wslconfig creado" -ForegroundColor Green

# Paso 5: Reiniciar WSL
Write-Host ""
Write-Host "[5/5] Reiniciando WSL..." -ForegroundColor Green
wsl --shutdown
Start-Sleep -Seconds 3
Write-Host "    OK - WSL reiniciado" -ForegroundColor Green

# Verificar configuracion
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VERIFICACION DE CONFIGURACION" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "DNS Configurado:" -ForegroundColor Green
Get-DnsClientServerAddress -InterfaceAlias $adapter.Name | Select-Object -ExpandProperty ServerAddresses | ForEach-Object {
    Write-Host "  -> $_" -ForegroundColor White
}

Write-Host ""
Write-Host "Probando conectividad..." -ForegroundColor Green
$ping = Test-Connection -ComputerName google.com -Count 2 -ErrorAction SilentlyContinue
if ($ping) {
    Write-Host "  OK - Internet funcionando correctamente" -ForegroundColor Green
} else {
    Write-Host "  ERROR - Sin conexion a internet" -ForegroundColor Red
}

# Instrucciones finales
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "PROXIMOS PASOS" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. ABRE DOCKER DESKTOP (si no esta abierto)" -ForegroundColor White
Write-Host ""
Write-Host "2. VE A SETTINGS:" -ForegroundColor White
Write-Host "   - Click en el icono de engranaje (Settings)" -ForegroundColor Gray
Write-Host "   - Ve a Docker Engine en el menu izquierdo" -ForegroundColor Gray
Write-Host ""
Write-Host "3. AGREGA ESTA CONFIGURACION AL JSON:" -ForegroundColor White
Write-Host ""
Write-Host '   {' -ForegroundColor Yellow
Write-Host '     "dns": ["1.1.1.1", "1.0.0.1", "8.8.8.8"],' -ForegroundColor Yellow
Write-Host '     "dns-search": []' -ForegroundColor Yellow
Write-Host '   }' -ForegroundColor Yellow
Write-Host ""
Write-Host "4. CLICK EN Apply and Restart" -ForegroundColor White
Write-Host ""
Write-Host "5. ESPERA 30 segundos a que Docker se reinicie" -ForegroundColor White
Write-Host ""
Write-Host "6. VERIFICA QUE FUNCIONA:" -ForegroundColor White
Write-Host "   - Abre PowerShell" -ForegroundColor Gray
Write-Host "   - Ejecuta: ping google.com" -ForegroundColor Gray
Write-Host "   - Si funciona, el problema esta resuelto" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "SI EL PROBLEMA PERSISTE:" -ForegroundColor Red
Write-Host ""
Write-Host "Opcion 1: Deshabilitar WSL2 en Docker" -ForegroundColor Yellow
Write-Host "  - Docker Settings -> General" -ForegroundColor Gray
Write-Host "  - DESMARCA: Use the WSL 2 based engine" -ForegroundColor Gray
Write-Host "  - Apply and Restart" -ForegroundColor Gray
Write-Host ""
Write-Host "Opcion 2: Usar el proyecto sin Docker" -ForegroundColor Yellow
Write-Host "  - Puedo ayudarte a configurar PostgreSQL y Redis localmente" -ForegroundColor Gray
Write-Host "  - O usar servicios en la nube (Supabase/Redis Cloud)" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona cualquier tecla para cerrar..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
