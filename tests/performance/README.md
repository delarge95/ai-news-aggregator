# Performance Tests Suite

Suite completa de tests de carga y performance para el sistema AI News Aggregator.

## 📋 Descripción

Esta suite incluye tests de performance que evalúan:

- **Load Tests**: Carga normal y alta con Locust
- **Performance Tests**: Endpoints críticos del sistema
- **Stress Tests**: Rate limiting y carga extrema
- **Database Performance**: Queries de base de datos
- **Frontend Performance**: Core Web Vitals y UX

## 🏗️ Estructura

```
tests/performance/
├── load_test.py                    # Tests de carga con Locust
├── performance_test.py            # Tests de endpoints críticos
├── api_stress_test.py             # Stress tests y rate limiting
├── database_performance.py        # Tests de base de datos
├── frontend_performance.py        # Tests de frontend y Core Web Vitals
├── load_scenarios_config.py       # Configuración y reportes automáticos
├── test_runner.py                 # Orquestador principal
├── performance_config.yaml        # Configuración por defecto
└── README.md                      # Esta documentación
```

## 🚀 Instalación

### Dependencias

```bash
# Instalar dependencias de performance
pip install locust aiohttp asyncpg psycopg2-binary schedule pyyaml

# O desde requirements.txt
pip install -r requirements-performance.txt
```

### Dependencias específicas por test

```bash
# Para load tests (Locust)
pip install locust

# Para performance tests (HTTP)
pip install aiohttp requests

# Para database tests
pip install asyncpg psycopg2-binary

# Para frontend tests (simulados)
pip install aiohttp

# Para configuración y automatización
pip install schedule pyyaml
```

## ⚡ Uso Rápido

### Ejecutar suite completa

```bash
# Ejecutar todos los tests
python test_runner.py --environment staging --create-reports-dir

# Con configuración personalizada
python test_runner.py --config my_config.yaml --environment production
```

### Ejecutar tests individuales

```bash
# Load tests únicamente
locust -f load_test.py --host http://localhost:8000

# Performance tests
python performance_test.py --host localhost:8000

# Stress tests
python api_stress_test.py --host localhost:8000

# Database tests
python database_performance.py --host localhost --user postgres

# Frontend tests
python frontend_performance.py --host localhost:3000
```

## 📊 Tests Disponibles

### 1. Load Tests (`load_test.py`)

Simula usuarios reales accediendo a la aplicación.

**Tipos de usuarios:**
- `NewsApiUser`: Usuario típico leyendo artículos
- `AdminUser`: Usuario administrador
- `CrawlerUser`: Bot/crawler escaneando contenido

**Endpoints testados:**
- GET `/api/v1/articles` - Lista de artículos
- GET `/api/v1/search` - Búsqueda de artículos
- GET `/api/v1/articles/{id}` - Detalle de artículo
- GET `/api/v1/users/{id}/news` - Feed personalizado
- GET `/health` - Health check

**Uso:**
```bash
# Load test básico
locust -f load_test.py --host http://localhost:8000

# Load test headless
locust -f load_test.py --host http://localhost:8000 \
  --headless --users 50 --spawn-rate 5 --run-time 10m
```

### 2. Performance Tests (`performance_test.py`)

Evalúa latencia y throughput de endpoints críticos.

**Métricas calculadas:**
- Response time (avg, min, max, p50, p95, p99)
- Throughput (RPS)
- Error rate
- Performance score (0-100)

**Uso:**
```bash
python performance_test.py --host localhost:8000 --output perf_report.json
```

### 3. Stress Tests (`api_stress_test.py`)

Testa comportamiento bajo carga extrema y rate limiting.

**Escenarios incluidos:**
- Normal Load Test (10 RPS, 5 usuarios)
- High Load Test (50 RPS, 20 usuarios)
- Extreme Load Test (100 RPS, 50 usuarios)
- Rate Limit Enforcement (20 RPS con rate limiting)

**Uso:**
```bash
python api_stress_test.py --host localhost:8000 --output stress_report.json
```

### 4. Database Performance (`database_performance.py`)

Evalúa performance de queries de base de datos.

**Queries testadas:**
- Paginación de artículos
- Búsqueda por texto
- Agregaciones de analytics
- Queries de usuarios
- Performance de connection pool

**Uso:**
```bash
python database_performance.py \
  --host localhost --port 5432 \
  --database ai_news_db --user postgres \
  --password your_password
```

### 5. Frontend Performance (`frontend_performance.py`)

Evalúa Core Web Vitals y métricas de UX.

**Core Web Vitals medidos:**
- LCP (Largest Contentful Paint)
- FID (First Input Delay)
- CLS (Cumulative Layout Shift)
- FCP (First Contentful Paint)
- TTFB (Time to First Byte)

**Otras métricas:**
- Accessibility score
- Image optimization score
- Performance score

**Uso:**
```bash
python frontend_performance.py \
  --host localhost:3000 \
  --pages "/" "/articles" "/search" "/dashboard"
```

## ⚙️ Configuración

### Archivo de Configuración Principal

`performance_config.yaml`:

```yaml
test_name: "AI News Aggregator Performance Tests"
base_environment: "staging"

environments:
  development:
    api_host: "localhost:8000"
    frontend_host: "localhost:3000"
    database:
      host: "localhost"
      port: 5432
      database: "ai_news_db"
      user: "postgres"
      password: "password"
  
  staging:
    api_host: "staging-api.example.com"
    frontend_host: "staging-frontend.example.com"
    database:
      host: "staging-db.example.com"
      port: 5432
      database: "ai_news_staging"
      user: "staging_user"
      password: "staging_password"
  
  production:
    api_host: "api.example.com"
    frontend_host: "frontend.example.com"
    database:
      host: "db.example.com"
      port: 5432
      database: "ai_news_prod"
      user: "prod_user"
      password: "prod_password"

thresholds:
  response_time_p95_ms: 1000
  error_rate_percent: 2.0
  success_rate_percent: 95.0
  throughput_rps: 10.0
  database_query_time_ms: 500
  frontend_lcp_ms: 2500
  frontend_fid_ms: 100
  frontend_cls_score: 0.1

alerts:
  enabled: true
  email_recipients:
    - "admin@example.com"
    - "devops@example.com"
  slack_webhook: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  cooldown_minutes: 15

reporting:
  output_formats: ["json", "html"]
  storage_path: "./reports"
  retention_days: 30
  auto_archive: true
  include_charts: true

scheduled_runs:
  "0 9 * * 1": "Normal Load Test"      # Lunes 9am
  "0 14 * * 3": "High Load Test"       # Miércoles 2pm  
  "0 2 * * 6": "Endurance Test"        # Sábado 2am
```

### Configurar Escenarios de Carga

Los escenarios se definen en `load_scenarios_config.py`:

```python
# Escenario de carga normal
LoadScenarioConfig(
    name="Normal Load Test",
    type="load",
    target_rps=20,
    duration_minutes=30,
    concurrent_users=10,
    endpoints=["/api/v1/articles", "/api/v1/search"],
    weight_distribution={"/api/v1/articles": 60, "/api/v1/search": 40},
    success_criteria={
        "avg_response_time_ms": 500,
        "error_rate_percent": 1.0
    }
)
```

## 📈 Métricas y Thresholds

### Thresholds Críticos

| Métrica | Warning | Critical | Acción |
|---------|---------|----------|--------|
| Response Time P95 | 800ms | 1200ms | Optimizar endpoints |
| Error Rate | 2% | 5% | Investigar fallos |
| Success Rate | 95% | 90% | Revisar disponibilidad |
| Database Query Time | 500ms | 1000ms | Optimizar queries |
| Frontend LCP | 2.5s | 4s | Optimizar carga |
| Frontend CLS | 0.1 | 0.25 | Evitar layout shifts |

### Core Web Vitals

- **LCP (Largest Contentful Paint)**: < 2.5s (Bueno), 2.5-4s (Mejorable), >4s (Malo)
- **FID (First Input Delay)**: < 100ms (Bueno), 100-300ms (Mejorable), >300ms (Malo)  
- **CLS (Cumulative Layout Shift)**: < 0.1 (Bueno), 0.1-0.25 (Mejorable), >0.25 (Malo)

## 🔔 Alertas

### Tipos de Alertas

1. **Performance Degradation**
   - Response time > threshold
   - Throughput < threshold

2. **Error Rate**
   - Error rate > 5%
   - Success rate < 95%

3. **Resource Utilization**
   - Database health score < 70
   - Connection pool utilization > 80%

4. **Frontend Performance**
   - Core Web Vitals en rojo
   - Accessibility score < 60

### Configurar Notificaciones

```yaml
alerts:
  enabled: true
  email_recipients:
    - "admin@example.com"
    - "devops@example.com"
  slack_webhook: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  cooldown_minutes: 15
```

## 📁 Reportes

### Formatos de Salida

- **JSON**: Reportes estructurados para análisis
- **HTML**: Reportes visuales con gráficos
- **CSV**: Datos para análisis en Excel/Sheets

### Ubicación de Reportes

```
reports/
├── load_test_staging_20241206_140000.html
├── load_test_staging_stats.csv
├── performance_test_results.json
├── stress_test_report.json
├── database_performance_report.json
├── frontend_performance_report.json
└── performance_test_results_20241206_140000.json
```

### Contenido del Reporte

Cada reporte incluye:

1. **Resumen Ejecutivo**
   - Status general
   - Score de performance
   - Tiempo de ejecución
   - Alertas generadas

2. **Métricas Detalladas**
   - Response times
   - Throughput
   - Error rates
   - Success rates

3. **Análisis por Componente**
   - Load tests
   - Endpoints críticos
   - Database performance
   - Frontend performance

4. **Recomendaciones**
   - Acciones sugeridas
   - Próximos pasos
   - Priorización de mejoras

## 🔄 Automatización

### Tests Programados

Ejecutar tests automáticamente:

```bash
# Configurar tests programados
python load_scenarios_config.py create-config --output my_config.json

# Ejecutar programador
python load_scenarios_config.py run-scheduled --config my_config.json
```

### Integración CI/CD

**GitHub Actions example:**

```yaml
name: Performance Tests
on:
  schedule:
    - cron: '0 9 * * 1'  # Lunes 9am
  workflow_dispatch:

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-performance.txt
    
    - name: Run Performance Tests
      run: |
        python test_runner.py \
          --environment staging \
          --create-reports-dir \
          --output performance_results.json
    
    - name: Upload Reports
      uses: actions/upload-artifact@v2
      with:
        name: performance-reports
        path: reports/
```

## 🛠️ Troubleshooting

### Problemas Comunes

**1. Error de conexión a la base de datos**
```bash
# Verificar conectividad
psql -h localhost -U postgres -d ai_news_db -c "SELECT 1;"
```

**2. Load tests muy lentos**
- Reducir número de usuarios concurrentes
- Aumentar spawn rate gradualmente
- Verificar límites de rate limiting

**3. Memory leaks en endurance tests**
- Monitorear uso de memoria
- Verificar connection pool
- Revisar cleanup de recursos

**4. Frontend tests fallan**
- Verificar que el frontend esté corriendo
- Comprobar URLs de páginas
- Validar headers de respuesta

### Logs Detallados

```bash
# Habilitar logs verbose
python test_runner.py --verbose --environment staging

# Logs específicos
tail -f performance_tests.log
```

### Debug de Performance

**Profiling de endpoints:**
```python
# En performance_test.py, agregar:
import cProfile
cProfile.run('await test_endpoint_performance("/api/v1/articles")')
```

**Monitor de recursos:**
```bash
# Monitor de sistema durante tests
htop
iotop
netstat -i
```

## 📚 Referencias

### Documentación

- [Locust Documentation](https://docs.locust.io/)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [asyncpg Documentation](https://asyncpg.readthedocs.io/)
- [Core Web Vitals](https://web.dev/vitals/)

### Herramientas Adicionales

- **k6**: Alternative a Locust para load testing
- **Artillery**: Load testing como código
- **JMeter**: Testing enterprise
- **Gatling**: Load testing de alta performance

### Best Practices

1. **Siempre ejecutar en entorno de staging primero**
2. **Monitorear recursos del sistema durante tests**
3. **Configurar alertas para producción**
4. **Guardar baselines de performance**
5. **Ejecutar tests regularmente**
6. **Documentar cambios de performance**

## 🤝 Contribuir

Para agregar nuevos tests o mejorar existentes:

1. Seguir la estructura de módulos existente
2. Incluir métricas relevantes
3. Configurar thresholds apropiados
4. Agregar documentación
5. Incluir en el orquestador principal

### Ejemplo de Nuevo Test

```python
# tests/performance/custom_test.py
import asyncio
from performance_test import PerformanceTestRunner, TestConfig

class CustomTestSuite:
    async def test_custom_endpoint(self):
        config = TestConfig(
            name="Custom Endpoint Test",
            base_url="http://localhost:8000",
            concurrent_users=5,
            requests_per_user=10
        )
        
        runner = PerformanceTestRunner(config)
        result = await runner.test_endpoint_performance(
            "/api/v1/custom", "GET"
        )
        return result
```

Luego agregar al orquestador:

```python
# En test_runner.py
async def _run_custom_tests(self):
    # Lógica del test custom
    pass
```

## 📞 Soporte

Para issues o preguntas:

- Revisar logs en `performance_tests.log`
- Consultar reportes generados
- Verificar configuración de entorno
- Crear issue en el repositorio

---

**Última actualización**: Diciembre 2024  
**Versión**: 1.0.0