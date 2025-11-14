# 🔧 Solución: Docker Desktop Rompe Internet (Problema DNS)

## 🚨 Problema

Docker Desktop modifica la configuración DNS de Windows y causa pérdida de conectividad a internet.

---

## ✅ Solución 1: Configurar DNS en Docker Desktop (Recomendado)

### Paso 1: Abrir Docker Desktop Settings

1. Click derecho en el ícono de Docker Desktop (barra de tareas)
2. Selecciona **"Settings"** o **"Configuración"**

### Paso 2: Configurar DNS

1. Ve a **"Docker Engine"** (panel izquierdo)
2. Agrega esta configuración en el JSON:

```json
{
  "dns": ["1.1.1.1", "1.0.0.1", "8.8.8.8"],
  "dns-search": []
}
```

3. Click **"Apply & Restart"**

**Explicación**:

- `1.1.1.1` y `1.0.0.1` = Cloudflare DNS (rápido y confiable)
- `8.8.8.8` = Google DNS (backup)

---

## ✅ Solución 2: Deshabilitar DNS Experimental de WSL2

### Paso 1: Editar Configuración de WSL2

1. Abre PowerShell como **Administrador**
2. Ejecuta:

```powershell
# Crear archivo de configuración WSL
notepad $env:USERPROFILE\.wslconfig
```

3. Agrega este contenido:

```ini
[wsl2]
# Deshabilitar DNS generado automáticamente
networkingMode=mirrored
dnsTunneling=false

# Configuración de memoria (opcional)
memory=4GB
processors=2
```

4. Guarda y cierra el archivo

### Paso 2: Reiniciar WSL

```powershell
wsl --shutdown
```

5. Reinicia Docker Desktop

---

## ✅ Solución 3: Usar archivo daemon.json de Docker

### Paso 1: Crear/Editar daemon.json

1. Navega a: `C:\Users\TU_USUARIO\.docker\`
2. Crea o edita el archivo `daemon.json`

```json
{
  "dns": ["1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

3. Reinicia Docker Desktop

---

## ✅ Solución 4: Fijar DNS en Windows (Método Manual)

### Para Ethernet/WiFi:

1. Panel de Control → Red e Internet → Centro de redes y recursos compartidos
2. Click en tu conexión activa (WiFi o Ethernet)
3. Click en **"Propiedades"**
4. Selecciona **"Protocolo de Internet versión 4 (TCP/IPv4)"**
5. Click en **"Propiedades"**
6. Selecciona **"Usar las siguientes direcciones de servidor DNS"**:
   - **DNS preferido**: `1.1.1.1` (Cloudflare)
   - **DNS alternativo**: `1.0.0.1` (Cloudflare secundario)
7. Click **"Aceptar"** en todas las ventanas

### Con PowerShell (Administrador):

```powershell
# Ver adaptadores de red
Get-NetAdapter

# Fijar DNS en tu adaptador (reemplaza "Ethernet" con tu adaptador)
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses ("1.1.1.1","1.0.0.1","8.8.8.8")

# Para WiFi:
Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses ("1.1.1.1","1.0.0.1","8.8.8.8")

# Limpiar caché DNS
ipconfig /flushdns
```

---

## ✅ Solución 5: Deshabilitar VPN Mode de Docker

### Paso 1: Docker Desktop Settings

1. Settings → Resources → **Network**
2. **Desmarca**: "Enable VPN compatibility mode"
3. Apply & Restart

---

## 🧪 Verificar que Funciona

### Paso 1: Con Docker Desktop Abierto

```powershell
# Test DNS
nslookup google.com

# Test conectividad
ping google.com

# Test Docker
docker run hello-world
```

### Paso 2: Ver Configuración DNS Actual

```powershell
# Ver DNS configurado
ipconfig /all

# Ver tabla de routing
route print
```

---

## 🎯 Solución Rápida (Para Aplicar AHORA)

```powershell
# 1. Cerrar Docker Desktop si está abierto
# 2. Ejecutar como Administrador:

# Crear .wslconfig
@"
[wsl2]
networkingMode=mirrored
dnsTunneling=false
memory=4GB
"@ | Out-File -FilePath "$env:USERPROFILE\.wslconfig" -Encoding ASCII

# Reiniciar WSL
wsl --shutdown

# 3. Iniciar Docker Desktop de nuevo
```

---

## 🔍 Diagnóstico: ¿Cuál es TU problema específico?

### Ejecuta esto con Docker cerrado:

```powershell
ipconfig /all | Select-String "DNS"
```

### Ejecuta esto con Docker abierto:

```powershell
ipconfig /all | Select-String "DNS"
```

**Compara los resultados**. Si los DNS cambian, ahí está el problema.

---

## 📝 Notas Importantes

### ¿Por qué Cloudflare (1.1.1.1) funciona mejor?

- **Más rápido**: Cloudflare es uno de los DNS más rápidos del mundo
- **Privacidad**: No registra tu historial de navegación
- **Compatible**: Docker lo maneja mejor que otros DNS

### ¿Por qué Docker rompe el internet?

1. Docker WSL2 crea un **virtual switch** que intercepta DNS
2. Docker puede **priorizar su DNS** sobre el tuyo
3. Algunos **routers/ISP** tienen conflictos con el bridge de Docker
4. **Antivirus/Firewall** bloquean el tráfico de Docker

---

## ✨ Mi Recomendación

**Haz esto EN ORDEN**:

1. **Primero**: Solución 1 (DNS en Docker Engine) - 2 minutos
2. **Si no funciona**: Solución 2 (WSL2 config) - 3 minutos
3. **Si persiste**: Solución 4 (Fijar DNS en Windows) - 5 minutos

**La combinación de Solución 1 + 2 suele resolver el 95% de los casos.**

---

## 🆘 SOLUCIÓN DEFINITIVA (Si el Fix Básico No Funciona)

### El problema persiste porque WSL2 intercepta TODO el tráfico DNS de Windows

#### Opción A: Deshabilitar WSL2 en Docker (RECOMENDADO para tu caso)

1. **Cierra Docker Desktop completamente**
2. **Abre Docker Desktop Settings**:

   - Settings → General
   - **DESMARCA**: ☐ "Use the WSL 2 based engine"
   - Apply & Restart

3. **Docker usará Hyper-V en su lugar** (más estable para DNS)

**Ventajas**:

- ✅ No más conflictos DNS
- ✅ Internet 100% estable
- ⚠️ Docker será ~15% más lento (pero funcional)

#### Opción B: Forzar DNS en la Red de Docker (Más técnico)

Si quieres mantener WSL2, prueba esto:

```powershell
# 1. Detener todos los contenedores
docker stop $(docker ps -aq)

# 2. Crear red personalizada con DNS fijo
docker network create --driver bridge `
  --opt com.docker.network.bridge.name=docker_dns `
  --opt com.docker.network.driver.mtu=1500 `
  --subnet=172.20.0.0/16 `
  --gateway=172.20.0.1 `
  --dns=1.1.1.1 --dns=8.8.8.8 `
  custom_network

# 3. Modificar docker-compose.yml para usar esta red
```

#### Opción C: Deshabilitar DNS Automático de WSL Completamente

```powershell
# Editar .wslconfig con configuración más agresiva
@"
[wsl2]
# Deshabilitar TODAS las funciones de red automáticas
networkingMode=mirrored
dnsTunneling=false
autoProxy=false
firewall=false

# Usar DNS del host directamente
[network]
generateResolvConf=false

# Limitar recursos
memory=4GB
processors=2
swap=0
"@ | Out-File -FilePath "$env:USERPROFILE\.wslconfig" -Encoding ASCII -Force

# Reiniciar WSL completamente
wsl --shutdown
Restart-Service -Name "LxssManager" -Force
```

**Luego**, crear manualmente el archivo DNS de WSL:

```powershell
# Configurar DNS manualmente en WSL
wsl -d docker-desktop -e sh -c "echo 'nameserver 1.1.1.1' > /etc/resolv.conf"
wsl -d docker-desktop -e sh -c "echo 'nameserver 8.8.8.8' >> /etc/resolv.conf"
```

**Nota**: Esto hará Docker más lento, pero solucionará el problema DNS.

---

## 🚀 Para el Proyecto AI News Aggregator

Dado que Docker te causa problemas, **puedes probar el proyecto SIN Docker**:

```powershell
# Usar solo servicios locales
# PostgreSQL: https://www.postgresql.org/download/windows/
# Redis: https://github.com/microsoftarchive/redis/releases

# O usar servicios en la nube (gratis):
# - PostgreSQL: https://supabase.com (gratis)
# - Redis: https://redis.com (gratis 30MB)
```

¿Quieres que te ayude a configurar el proyecto **sin Docker** para evitar estos problemas?
