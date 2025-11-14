// Cloudflare Worker para AI News Aggregator
// Procesamiento inteligente de API y caching

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

/**
 * Función principal para manejar requests
 * @param {Request} request
 * @returns {Promise<Response>}
 */
async function handleRequest(request) {
  const url = new URL(request.url)
  const path = url.pathname
  
  // Solo procesar requests API
  if (!path.startsWith('/api/')) {
    return fetch(request)
  }
  
  // Headers para el request
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
    'Access-Control-Max-Age': '86400'
  }
  
  // Manejar OPTIONS requests
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers })
  }
  
  try {
    // Validación de rate limiting
    const rateLimitResult = await checkRateLimit(request)
    if (!rateLimitResult.allowed) {
      return new Response(JSON.stringify({
        error: 'Rate limit exceeded',
        retry_after: rateLimitResult.retryAfter
      }), {
        status: 429,
        headers: { ...headers, 'Content-Type': 'application/json' }
      })
    }
    
    // Validación de seguridad
    const securityCheck = await validateSecurity(request)
    if (!securityCheck.valid) {
      return new Response(JSON.stringify({
        error: 'Security validation failed'
      }), {
        status: 403,
        headers: { ...headers, 'Content-Type': 'application/json' }
      })
    }
    
    // Procesar según el tipo de endpoint
    if (path.startsWith('/api/articles')) {
      return await handleArticlesRequest(request)
    } else if (path.startsWith('/api/search')) {
      return await handleSearchRequest(request)
    } else if (path.startsWith('/api/analytics')) {
      return await handleAnalyticsRequest(request)
    } else {
      // Proxy directo al backend
      return await proxyToBackend(request)
    }
    
  } catch (error) {
    console.error('Worker error:', error)
    return new Response(JSON.stringify({
      error: 'Internal server error'
    }), {
      status: 500,
      headers: { ...headers, 'Content-Type': 'application/json' }
    })
  }
}

/**
 * Verificar rate limiting
 * @param {Request} request
 * @returns {Promise<Object>}
 */
async function checkRateLimit(request) {
  const ip = request.headers.get('CF-Connecting-IP')
  const path = new URL(request.url).pathname
  
  // Configuración de límites por endpoint
  const limits = {
    '/api/articles': { requests: 100, window: 60 }, // 100 req/min
    '/api/search': { requests: 30, window: 60 },    // 30 req/min
    '/api/analytics': { requests: 10, window: 60 }, // 10 req/min
    'default': { requests: 50, window: 60 }         // 50 req/min
  }
  
  const limit = limits[path] || limits['default']
  
  // Verificar en KV storage (Cloudflare KV)
  const key = `rate_limit:${ip}:${path}`
  
  try {
    // Obtener contador actual
    const current = await KV_RATE_LIMIT.get(key, 'json')
    const now = Date.now()
    
    if (current && current.window === limit.window) {
      if (current.count >= limit.requests) {
        return {
          allowed: false,
          retryAfter: Math.ceil(limit.window * 60) // Segundos
        }
      }
      // Incrementar contador
      await KV_RATE_LIMIT.put(key, JSON.stringify({
        count: current.count + 1,
        window: limit.window,
        firstRequest: current.firstRequest
      }))
    } else {
      // Nuevo periodo
      await KV_RATE_LIMIT.put(key, JSON.stringify({
        count: 1,
        window: limit.window,
        firstRequest: now
      }))
    }
    
    return { allowed: true }
    
  } catch (error) {
    console.error('Rate limit check error:', error)
    // En caso de error, permitir el request
    return { allowed: true }
  }
}

/**
 * Validaciones de seguridad
 * @param {Request} request
 * @returns {Promise<Object>}
 */
async function validateSecurity(request) {
  const headers = request.headers
  const userAgent = headers.get('User-Agent') || ''
  const referer = headers.get('Referer') || ''
  
  // Verificar User-Agent
  if (!userAgent || userAgent.length < 10) {
    return { valid: false, reason: 'Invalid User-Agent' }
  }
  
  // Verificar patrones maliciosos en URL
  const url = new URL(request.url)
  const suspiciousPatterns = [
    /(\.\.\/)/,           // Path traversal
    /(<|>|%3C|%3E)/,      // XSS attempts
    /union.*select/i,     // SQL injection
    /script.*src/i,       // Script injection
    /javascript:/i        // JavaScript protocol
  ]
  
  for (const pattern of suspiciousPatterns) {
    if (pattern.test(url.toString()) || pattern.test(userAgent)) {
      console.log('Suspicious request blocked:', url.toString())
      return { valid: false, reason: 'Suspicious pattern detected' }
    }
  }
  
  // Verificar Cloudflare security score
  const securityScore = headers.get('CF-Request-Assessment')
  if (securityScore === 'threat') {
    return { valid: false, reason: 'Threat detected by Cloudflare' }
  }
  
  return { valid: true }
}

/**
 * Manejar requests de artículos
 * @param {Request} request
 * @returns {Promise<Response>}
 */
async function handleArticlesRequest(request) {
  const url = new URL(request.url)
  const cacheKey = `articles:${url.search}`
  
  // Verificar cache
  const cached = await CACHE.get(cacheKey)
  if (cached) {
    return new Response(cached, {
      headers: {
        'Content-Type': 'application/json',
        'X-Cache': 'HIT',
        'Cache-Control': 'public, max-age=300' // 5 minutos
      }
    })
  }
  
  // Proxy al backend
  const response = await proxyToBackend(request)
  
  // Cachear respuesta exitosa
  if (response.status === 200) {
    const responseClone = response.clone()
    const data = await responseClone.text()
    
    await CACHE.put(cacheKey, data, {
      expirationTtl: 300 // 5 minutos
    })
  }
  
  return response
}

/**
 * Manejar requests de búsqueda
 * @param {Request} request
 * @returns {Promise<Response>}
 */
async function handleSearchRequest(request) {
  if (request.method === 'GET') {
    const url = new URL(request.url)
    const query = url.searchParams.get('q')
    
    if (query) {
      // Cache basado en query
      const cacheKey = `search:${encodeURIComponent(query)}`
      const cached = await CACHE.get(cacheKey)
      
      if (cached) {
        return new Response(cached, {
          headers: {
            'Content-Type': 'application/json',
            'X-Cache': 'HIT',
            'Cache-Control': 'public, max-age=600' // 10 minutos
          }
        })
      }
    }
  }
  
  return await proxyToBackend(request)
}

/**
 * Manejar requests de analytics
 * @param {Request} request
 * @returns {Promise<Response>}
 */
async function handleAnalyticsRequest(request) {
  // Analytics no se cachea para mantener datos actualizados
  return await proxyToBackend(request)
}

/**
 * Proxy al backend
 * @param {Request} request
 * @returns {Promise<Response>}
 */
async function proxyToBackend(request) {
  const url = new URL(request.url)
  
  // Cambiar el hostname al backend interno
  url.host = 'backend.internal'
  url.protocol = 'http:'
  
  // Headers para el proxy
  const headers = new Headers(request.headers)
  headers.set('Host', 'backend.internal')
  headers.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP'))
  headers.set('X-Forwarded-Proto', 'https')
  headers.set('X-Real-IP', request.headers.get('CF-Connecting-IP'))
  
  return fetch(url.toString(), {
    method: request.method,
    headers: headers,
    body: request.body
  })
}