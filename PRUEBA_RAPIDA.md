# 🧪 AI News Aggregator - Prueba Rápida

## Problema Encontrado: Docker Registry Connection

Docker no puede conectarse a Docker Hub para descargar imágenes:

```
Error: dial tcp: lookup registry-1.docker.io: no such host
```

Esto puede ser por:

1. Problema temporal de red/DNS
2. Docker Desktop aún inicializando completamente
3. Configuración de proxy/firewall

---

## ✅ Solución Alternativa: Ejecutar Localmente

### Opción 1: Frontend Solo (Verificar UI)

```powershell
cd e:\Portafolios-aplicaciones_laborales-plan_de_estudio\job-search-strategy\projects\ai-news-aggregator\frontend\ai-news-frontend

# Instalar dependencias (primera vez)
npm install

# O con pnpm si lo tienes
pnpm install

# Ejecutar en modo desarrollo
npm run dev
```

**Acceso**: http://localhost:5173 (o el puerto que Vite indique)

**Lo que funcionará:**

- ✅ UI completa y navegación
- ✅ Componentes y diseño
- ✅ Responsividad
- ❌ API calls (backend no está corriendo)

---

### Opción 2: Backend Solo (Verificar API)

```powershell
cd e:\Portafolios-aplicaciones_laborales-plan_de_estudio\job-search-strategy\projects\ai-news-aggregator\backend

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar backend
uvicorn app.main:app --reload --port 8000
```

**Acceso**:

- API: http://localhost:8000
- Docs: http://localhost:8000/docs

**Nota**: Necesitarás PostgreSQL y Redis corriendo (puedes usar el Redis que ya tienes)

---

### Opción 3: Esperar y Reintentar Docker (Recomendado)

Si el problema es temporal:

```powershell
# Espera 2-3 minutos para que Docker Desktop termine de inicializar
# Luego reintenta:

cd e:\Portafolios-aplicaciones_laborales-plan_de_estudio\job-search-strategy\projects\ai-news-aggregator

# Reintentar pull de imágenes
docker pull postgres:15
docker pull redis:7-alpine

# Si funciona, levantar todo
docker-compose up -d
```

---

## 🎯 Recomendación Rápida

**Para demo/verificación rápida del proyecto:**

1. **Frontend solo** (5 minutos):

   ```powershell
   cd frontend\ai-news-frontend
   npm install
   npm run dev
   ```

   Abre http://localhost:5173 y verifica la UI

2. **Documentación** (ya disponible):
   - Lee `README.md` - muy completo
   - Revisa `PROYECTO_COMPLETADO.md`
   - Explora `docs/` para arquitectura

---

## 📊 Estado Actual

| Componente     | Estado           | Nota                                |
| -------------- | ---------------- | ----------------------------------- |
| Docker Desktop | ✅ Corriendo     | Pero sin acceso a registry          |
| Python 3.14    | ✅ Instalado     | Listo para backend                  |
| Node.js 22     | ✅ Instalado     | Listo para frontend                 |
| Redis          | ✅ Corriendo     | Puerto 6379 (contenedor ara_redis)  |
| PostgreSQL     | ❌ No disponible | Necesita instalación local o Docker |
| Frontend Code  | ✅ Completo      | Listo para ejecutar                 |
| Backend Code   | ✅ Completo      | Listo para ejecutar                 |

---

## 🚀 Comando Rápido Recomendado

**Probar solo el Frontend ahora:**

```powershell
cd e:\Portafolios-aplicaciones_laborales-plan_de_estudio\job-search-strategy\projects\ai-news-aggregator\frontend\ai-news-frontend
npm install
npm run dev
```

Esto te permitirá ver:

- ✅ Diseño completo de la aplicación
- ✅ Navegación y routing
- ✅ Componentes UI profesionales
- ✅ Dashboard y visualizaciones
- ✅ Sistema de búsqueda (UI)

**Tiempo estimado**: 2-3 minutos para instalación, luego inmediato.

---

**¿Quieres que ejecute el frontend ahora o prefieres esperar a resolver Docker?**
