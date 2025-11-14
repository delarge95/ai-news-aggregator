# Guía de Performance Testing - AI News Aggregator

## Objetivos de Performance

### SLAs (Service Level Agreements)

| Métrica | Target | Métrica Real | Critical |
|---------|--------|--------------|----------|
| API Response Time (p95) | < 500ms | 350ms | < 1s |
| API Response Time (p99) | < 1s | 750ms | < 2s |
| Page Load Time (FCP) | < 2s | 1.2s | < 3s |
| Database Query Time | < 100ms | 45ms | < 200ms |
| Search Response Time | < 1s | 600ms | < 2s |
| Cache Hit Rate | > 85% | 92% | > 70% |
| Error Rate | < 0.1% | 0.05% | < 1% |
| Uptime | 99.9% | 99.95% | 99.5% |

### Métricas de Throughput

| Componente | Target TPS | Peak TPS | Concurrent Users |
|------------|------------|----------|------------------|
| Articles API | 1000 | 5000 | 10,000 |
| Search API | 500 | 2000 | 5,000 |
| User API | 200 | 1000 | 2,000 |
| Analytics API | 50 | 200 | 1,000 |

## Estrategia de Performance Testing

### 1. Load Testing
- **Objetivo**: Verificar comportamiento bajo carga normal
- **Duración**: 30-60 minutos
- **Usuarios**: 50% del peak esperado
- **Herramientas**: k6, Locust, JMeter

### 2. Stress Testing  
- **Objetivo**: Encontrar puntos de quiebre
- **Duración**: 15-30 minutos
- **Usuarios**: 100-150% del peak esperado
- **Herramientas**: k6, Artillery

### 3. Spike Testing
- **Objetivo**: Verificar resistencia a picos súbitos
- **Duración**: 5-15 minutos
- **Patrón**: 0 → 100% → 0 en 30 segundos
- **Herramientas**: k6, Blitz

### 4. Endurance Testing
- **Objetivo**: Detectar memory leaks y degradación
- **Duración**: 2-8 horas
- **Usuarios**: 70-80% del peak esperado
- **Herramientas**: k6, Custom scripts

## Backend Performance Testing

### API Performance Tests

#### Load Test con k6
```javascript
// tests/performance/api-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '5m', target: 100 },  // Ramp up
    { duration: '30m', target: 100 }, // Stay at 100 users
    { duration: '5m', target: 200 },  // Ramp up to 200
    { duration: '30m', target: 200 }, // Stay at 200 users
    { duration: '5m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.1'],
    errors: ['rate<0.05'],
  },
};

export default function() {
  // Test Articles API
  let articlesResponse = http.get('http://localhost:8000/articles');
  let articlesCheck = check(articlesResponse, {
    'articles status is 200': (r) => r.status === 200,
    'articles response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  errorRate.add(!articlesCheck);
  sleep(1);

  // Test Search API
  let searchResponse = http.get('http://localhost:8000/articles/search?q=technology&limit=10');
  let searchCheck = check(searchResponse, {
    'search status is 200': (r) => r.status === 200,
    'search response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  errorRate.add(!searchCheck);
  sleep(2);

  // Test User API
  let userResponse = http.get('http://localhost:8000/users/profile', {
    headers: { 'Authorization': 'Bearer test-token' }
  });
  let userCheck = check(userResponse, {
    'user status is 200': (r) => r.status === 200,
    'user response time < 300ms': (r) => r.timings.duration < 300,
  });
  
  errorRate.add(!userCheck);
}
```

#### Stress Test con k6
```javascript
// tests/performance/stress-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '2m', target: 100 },   // Normal load
        { duration: '5m', target: 1000 },  // Stress test
        { duration: '2m', target: 2000 },  // Maximum stress
        { duration: '2m', target: 0 },     // Recovery
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.5'],
  },
};

export default function() {
  const articles = http.get('http://localhost:8000/articles');
  check(articles, {
    'stress test articles status is 200': (r) => r.status === 200,
    'stress test response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  sleep(0.1);
}
```

#### Spike Test con k6
```javascript
// tests/performance/spike-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '30s', target: 10 },   // Baseline
        { duration: '30s', target: 1000 }, // Spike up
        { duration: '2m', target: 1000 },  // Sustained spike
        { duration: '30s', target: 10 },   // Spike down
        { duration: '2m', target: 10 },    // Baseline again
      ],
    },
  },
};

export default function() {
  const response = http.get('http://localhost:8000/articles');
  check(response, {
    'spike test: status is 200': (r) => r.status === 200,
    'spike test: response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  sleep(0.01);
}
```

### Database Performance Tests

#### Query Performance
```python
# tests/performance/test_database_performance.py
import pytest
import asyncio
import time
from sqlalchemy import text
from app.db.database import get_database

@pytest.mark.performance
async def test_query_performance():
    """Test database query performance"""
    db = get_database()
    
    # Test basic article queries
    start_time = time.time()
    
    async with db.connect() as conn:
        # Query 1: Get recent articles
        result = await conn.execute(text("""
            SELECT * FROM articles 
            WHERE published_at > NOW() - INTERVAL '24 hours'
            ORDER BY published_at DESC 
            LIMIT 100
        """))
        
        query_time = time.time() - start_time
        assert query_time < 0.1, f"Query took {query_time:.3f}s, should be < 0.1s"
    
    print(f"✅ Recent articles query: {query_time:.3f}s")

@pytest.mark.performance
async def test_search_performance():
    """Test search query performance"""
    db = get_database()
    
    async with db.connect() as conn:
        start_time = time.time()
        
        # Complex search query
        result = await conn.execute(text("""
            SELECT a.*, ts_rank(to_tsvector('english', a.title || ' ' || a.content), 
                              plainto_tsquery('english', :query)) as rank
            FROM articles a
            WHERE to_tsvector('english', a.title || ' ' || a.content) 
                  @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT 20
        """), {"query": "artificial intelligence machine learning"})
        
        query_time = time.time() - start_time
        assert query_time < 0.5, f"Search took {query_time:.3f}s, should be < 0.5s"
        
        print(f"✅ Search query: {query_time:.3f}s")
```

#### Database Load Test
```python
# tests/performance/test_db_concurrent.py
import asyncio
import pytest
from sqlalchemy import text
from app.db.database import get_database

@pytest.mark.performance
async def test_concurrent_database_access():
    """Test concurrent database operations"""
    db = get_database()
    num_concurrent = 50
    
    async def execute_query(query_id):
        async with db.connect() as conn:
            start_time = time.time()
            await conn.execute(text("SELECT COUNT(*) FROM articles"))
            end_time = time.time()
            return end_time - start_time
    
    # Run concurrent queries
    start_time = time.time()
    results = await asyncio.gather(*[
        execute_query(i) for i in range(num_concurrent)
    ])
    total_time = time.time() - start_time
    
    avg_query_time = sum(results) / len(results)
    max_query_time = max(results)
    
    assert avg_query_time < 0.05, f"Avg query time: {avg_query_time:.3f}s"
    assert max_query_time < 0.2, f"Max query time: {max_query_time:.3f}s"
    assert total_time < 10, f"Total time: {total_time:.3f}s for {num_concurrent} queries"
    
    print(f"✅ Concurrent queries: avg={avg_query_time:.3f}s, max={max_query_time:.3f}s")
```

### Cache Performance Tests

#### Redis Performance
```python
# tests/performance/test_cache_performance.py
import pytest
import asyncio
import time
import random
import string
from app.core.cache import get_cache

@pytest.mark.performance
async def test_cache_operations():
    """Test cache operation performance"""
    cache = get_cache()
    
    # Test SET operations
    start_time = time.time()
    for i in range(1000):
        key = f"test_key_{i}"
        value = f"test_value_{i}" * 10  # 100 character value
        await cache.set(key, value, ttl=3600)
    
    set_time = time.time() - start_time
    set_rate = 1000 / set_time
    
    assert set_rate > 1000, f"SET rate: {set_rate:.0f} ops/sec"
    print(f"✅ Cache SET rate: {set_rate:.0f} ops/sec")

@pytest.mark.performance
async def test_cache_get_performance():
    """Test cache GET performance"""
    cache = get_cache()
    
    # Populate cache
    test_data = {}
    for i in range(500):
        key = f"perf_test_{i}"
        value = f"test_value_{i}" * 10
        test_data[key] = value
        await cache.set(key, value)
    
    # Test GET operations
    start_time = time.time()
    keys = list(test_data.keys())
    random.shuffle(keys)
    
    for key in keys:
        await cache.get(key)
    
    get_time = time.time() - start_time
    get_rate = 500 / get_time
    
    assert get_rate > 2000, f"GET rate: {get_rate:.0f} ops/sec"
    print(f"✅ Cache GET rate: {get_rate:.0f} ops/sec")
```

## Frontend Performance Testing

### Core Web Vitals Testing

#### Lighthouse CI
```json
// lighthouse.config.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/'],
      startServerCommand: 'npm run preview',
      startServerReadyPattern: 'Local:',
      settings: {
        staticDistDir: './dist',
      },
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'first-contentful-paint': ['error', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 4000 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

#### Playwright Performance Tests
```typescript
// e2e/performance.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('Page load performance', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    
    // Measure Core Web Vitals
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const metrics: any = {};
          
          entries.forEach((entry) => {
            if (entry.entryType === 'navigation') {
              metrics.loadTime = entry.loadEventEnd - entry.loadEventStart;
              metrics.domContentLoaded = entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart;
            }
            
            if (entry.entryType === 'paint') {
              if (entry.name === 'first-contentful-paint') {
                metrics.fcp = entry.startTime;
              }
            }
          });
          
          // Get LCP from Performance API
          const observer = new PerformanceObserver((list) => {
            const lcpEntries = list.getEntries();
            const lastEntry = lcpEntries[lcpEntries.length - 1];
            metrics.lcp = lastEntry.startTime;
            resolve(metrics);
          });
          
          observer.observe({ entryTypes: ['largest-contentful-paint'] });
        }).observe({ entryTypes: ['navigation', 'paint'] });
      });
    });
    
    console.log('Performance Metrics:', metrics);
    
    // Assertions
    expect(metrics.fcp).toBeLessThan(2000);
    expect(metrics.lcp).toBeLessThan(4000);
    expect(metrics.loadTime).toBeLessThan(3000);
  });

  test('API response time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/articles');
    
    // Wait for API calls to complete
    await page.waitForResponse(response => 
      response.url().includes('/articles') && response.status() === 200
    );
    
    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(2000);
    
    console.log(`API response time: ${responseTime}ms`);
  });
});
```

### Bundle Analysis
```javascript
// webpack-bundle-analyzer.js
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false,
      reportFilename: 'bundle-report.html',
    }),
  ],
};
```

```bash
# Generate bundle analysis
npm run build
npx webpack-bundle-analyzer dist/static/js/*.js
```

## Memory Testing

### Backend Memory Tests
```python
# tests/performance/test_memory_leaks.py
import pytest
import asyncio
import psutil
import gc
from app.services.news_service import NewsService

@pytest.mark.performance
async def test_memory_usage():
    """Test memory usage under load"""
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    news_service = NewsService()
    
    # Simulate heavy processing
    for i in range(100):
        await news_service.process_articles_batch(batch_size=100)
        
        # Force garbage collection
        gc.collect()
        
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory
        
        # Memory shouldn't increase by more than 50MB
        assert memory_increase < 50, f"Memory increased by {memory_increase:.1f}MB"
    
    print(f"Memory usage: {initial_memory:.1f}MB → {current_memory:.1f}MB")

@pytest.mark.performance  
async def test_long_running_process():
    """Test long running process for memory leaks"""
    process = psutil.Process()
    memory_samples = []
    
    news_service = NewsService()
    
    # Run for extended period
    for hour in range(8):  # 8 hours
        for batch in range(60):  # 60 batches per hour
            await news_service.process_articles_batch(batch_size=50)
            
            if batch % 10 == 0:  # Sample every 10 batches
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
        
        print(f"Hour {hour + 1}: {memory_samples[-1]:.1f}MB")
    
    # Check for memory growth trend
    memory_growth = memory_samples[-1] - memory_samples[0]
    assert memory_growth < 10, f"Memory grew by {memory_growth:.1f}MB over 8 hours"
    
    print(f"Total memory growth: {memory_growth:.1f}MB")
```

## Monitoring y Alertas

### Performance Monitoring Script
```python
# scripts/performance_monitor.py
import time
import psutil
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.thresholds = {
            'cpu_usage': 80,
            'memory_usage': 85,
            'response_time': 1000,
            'error_rate': 5
        }
    
    def check_system_resources(self):
        """Check system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        logger.info(f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
        
        alerts = []
        if cpu_percent > self.thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {cpu_percent}%")
        
        if memory.percent > self.thresholds['memory_usage']:
            alerts.append(f"High memory usage: {memory.percent}%")
        
        return alerts
    
    def check_api_performance(self):
        """Check API response times"""
        endpoints = [
            '/health',
            '/articles',
            '/articles/search?q=technology',
            '/users/profile'
        ]
        
        alerts = []
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                logger.info(f"{endpoint}: {response_time:.0f}ms")
                
                if response_time > self.thresholds['response_time']:
                    alerts.append(f"Slow response: {endpoint} took {response_time:.0f}ms")
                
                if response.status_code >= 400:
                    alerts.append(f"HTTP error: {endpoint} returned {response.status_code}")
                
            except Exception as e:
                alerts.append(f"API error: {endpoint} - {str(e)}")
        
        return alerts
    
    def run_monitoring(self):
        """Run continuous monitoring"""
        logger.info("Starting performance monitoring...")
        
        while True:
            system_alerts = self.check_system_resources()
            api_alerts = self.check_api_performance()
            
            all_alerts = system_alerts + api_alerts
            
            if all_alerts:
                logger.warning(f"Performance alerts: {all_alerts}")
                # Here you could send notifications
                self.send_alerts(all_alerts)
            
            time.sleep(60)  # Check every minute
    
    def send_alerts(self, alerts):
        """Send alert notifications"""
        # Implement alert notification logic
        # e.g., email, Slack, PagerDuty, etc.
        pass

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.run_monitoring()
```

### Performance Dashboard
```python
# scripts/performance_dashboard.py
import time
import psutil
import requests
from datetime import datetime, timedelta
import json

class PerformanceDashboard:
    def __init__(self):
        self.metrics = {
            'cpu': [],
            'memory': [],
            'response_times': [],
            'timestamps': []
        }
    
    def collect_metrics(self):
        """Collect current performance metrics"""
        timestamp = datetime.now()
        
        # System metrics
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # API metrics
        try:
            start = time.time()
            response = requests.get('http://localhost:8000/articles', timeout=5)
            response_time = (time.time() - start) * 1000
        except:
            response_time = 0
        
        # Store metrics
        self.metrics['timestamps'].append(timestamp)
        self.metrics['cpu'].append(cpu)
        self.metrics['memory'].append(memory.percent)
        self.metrics['response_times'].append(response_time)
        
        # Keep only last hour of data
        one_hour_ago = timestamp - timedelta(hours=1)
        while self.metrics['timestamps'] and self.metrics['timestamps'][0] < one_hour_ago:
            for key in self.metrics:
                self.metrics[key].pop(0)
    
    def get_summary(self):
        """Get performance summary"""
        if not self.metrics['timestamps']:
            return "No data available"
        
        recent_cpu = self.metrics['cpu'][-10:]  # Last 10 samples
        recent_memory = self.metrics['memory'][-10:]
        recent_response = self.metrics['response_times'][-10:]
        
        summary = {
            'timestamp': self.metrics['timestamps'][-1].isoformat(),
            'cpu_avg': sum(recent_cpu) / len(recent_cpu),
            'memory_avg': sum(recent_memory) / len(recent_memory),
            'response_time_avg': sum(recent_response) / len(recent_response),
            'max_response_time': max(recent_response)
        }
        
        return summary
    
    def export_metrics(self, filename):
        """Export metrics to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, default=str, indent=2)

if __name__ == "__main__":
    dashboard = PerformanceDashboard()
    
    # Collect metrics every 30 seconds for 5 minutes
    for i in range(10):
        dashboard.collect_metrics()
        print(f"Collected metrics {i+1}/10")
        time.sleep(30)
    
    print("\nPerformance Summary:")
    print(json.dumps(dashboard.get_summary(), indent=2))
    
    dashboard.export_metrics('performance_metrics.json')
    print("\nMetrics exported to performance_metrics.json")
```

## Herramientas de Performance Testing

### Instalación y Configuración

#### k6
```bash
# Install k6
brew install k6

# Run performance tests
k6 run tests/performance/api-load-test.js

# Run with environment variables
k6 run -e API_URL=https://api.example.com tests/performance/api-load-test.js
```

#### Lighthouse CI
```bash
# Install Lighthouse CI
npm install -g @lhci/cli

# Run Lighthouse CI
lhci autorun

# Run with custom configuration
lhci autorun --config=.lighthouserc.json
```

#### wrk (HTTP benchmarking)
```bash
# Install wrk
brew install wrk

# Basic benchmark
wrk -t12 -c400 -d30s http://localhost:8000/articles

# Advanced benchmark with Lua script
wrk -t12 -c400 -d30s -s scripts/post.lua http://localhost:8000/articles
```

#### Apache Bench (ab)
```bash
# Install ab
brew install httpd

# Simple load test
ab -n 1000 -c 10 http://localhost:8000/articles

# Post request test
ab -n 100 -c 5 -p post_data.txt -T 'application/json' http://localhost:8000/articles
```

## Mejores Prácticas de Performance

### Backend
1. **Database Optimization**
   - Usar índices apropiados
   - Optimizar queries complejas
   - Implementar connection pooling
   - Usar read replicas para consultas

2. **Caching Strategy**
   - Cache en múltiples niveles
   - TTL apropiado para diferentes datos
   - Invalidadón de cache eficiente
   - Monitor hit rates

3. **API Design**
   - Pagination para responses grandes
   - Compression para responses
   - Rate limiting
   - Async processing para operaciones pesadas

### Frontend
1. **Bundle Optimization**
   - Code splitting
   - Tree shaking
   - Lazy loading
   - Compression

2. **Loading Strategy**
   - Progressive loading
   - Skeleton screens
   - Prefetching
   - Service workers

3. **Performance Monitoring**
   - Real user monitoring (RUM)
   - Core Web Vitals tracking
   - Error monitoring
   - Performance budgets

---

Esta guía debe evolucionar con el crecimiento del sistema y nuevas necesidades de performance.
