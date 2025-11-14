// Cloudflare Worker para cacheo de contenido estático
// Optimización de rendimiento y cacheo inteligente

addEventListener('fetch', event => {
  event.respondWith(handleStaticRequest(event.request))
})

/**
 * Función principal para manejar requests de contenido estático
 * @param {Request} request
 * @returns {Promise<Response>}
 */
async function handleStaticRequest(request) {
  const url = new URL(request.url)
  const path = url.pathname
  const extension = path.split('.').pop()?.toLowerCase()
  
  // Solo procesar archivos estáticos
  const staticExtensions = ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'woff', 'woff2', 'ttf', 'eot', 'pdf', 'txt']
  
  if (!staticExtensions.includes(extension)) {
    return fetch(request)
  }
  
  try {
    // Determinar TTL de cache basado en tipo de archivo
    const cacheConfig = getCacheConfig(extension)
    
    // Generar clave de cache
    const cacheKey = await generateCacheKey(request, cacheConfig)
    
    // Buscar en cache
    const cachedResponse = await cache.match(cacheKey)
    if (cachedResponse) {
      return new Response(cachedResponse.body, {
        headers: {
          ...cachedResponse.headers,
          'X-Cache': 'HIT',
          'CF-Cache-Status': 'HIT'
        }
      })
    }
    
    // Fetch del contenido original
    let response = await fetch(request)
    
    // Solo cachear respuestas exitosas
    if (response.status === 200) {
      // Modificar headers de cache
      const headers = new Headers(response.headers)
      
      // Establecer TTL personalizado
      if (cacheConfig.edgeTTL > 0) {
        headers.set('Cache-Control', `public, max-age=${cacheConfig.browserTTL}, s-maxage=${cacheConfig.edgeTTL}`)
        headers.set('CDN-Cache-Control', `public, s-maxage=${cacheConfig.edgeTTL}`)
        headers.set('Surrogate-Key', cacheConfig.tags.join(' '))
      }
      
      // Compresión adicional si no está presente
      if (!headers.has('Content-Encoding') && extension === 'css') {
        const body = await response.arrayBuffer()
        const compressed = await compressGzip(body)
        
        response = new Response(compressed, {
          status: 200,
          headers: {
            ...headers,
            'Content-Encoding': 'gzip',
            'Content-Type': getContentType(extension)
          }
        })
      }
      
      // Guardar en cache
      const responseToCache = new Response(response.body, {
        headers: {
          ...headers,
          'X-Cache': 'MISS'
        }
      })
      
      // Agregar headers personalizados
      const customResponse = new Response(responseToCache.body, {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: responseToCache.headers
      })
      
      // Cachear en Cloudflare
      await cache.put(cacheKey, customResponse.clone())
      
      return new Response(customResponse.body, {
        headers: {
          ...customResponse.headers,
          'X-Cache': 'MISS',
          'CF-Cache-Status': 'MISS'
        }
      })
    }
    
    return response
    
  } catch (error) {
    console.error('Cache worker error:', error)
    return fetch(request)
  }
}

/**
 * Obtener configuración de cache para tipo de archivo
 * @param {string} extension
 * @returns {Object}
 */
function getCacheConfig(extension) {
  const configs = {
    // CSS - Cache largo
    'css': {
      edgeTTL: 604800,  // 7 días
      browserTTL: 86400, // 1 día
      tags: ['static', 'css']
    },
    // JavaScript - Cache medio
    'js': {
      edgeTTL: 604800,  // 7 días
      browserTTL: 86400, // 1 día
      tags: ['static', 'js']
    },
    // Imágenes - Cache muy largo
    'png': {
      edgeTTL: 2592000, // 30 días
      browserTTL: 2592000, // 30 días
      tags: ['static', 'images']
    },
    'jpg': {
      edgeTTL: 2592000, // 30 días
      browserTTL: 2592000, // 30 días
      tags: ['static', 'images']
    },
    'jpeg': {
      edgeTTL: 2592000, // 30 días
      browserTTL: 2592000, // 30 días
      tags: ['static', 'images']
    },
    'gif': {
      edgeTTL: 2592000, // 30 días
      browserTTL: 2592000, // 30 días
      tags: ['static', 'images']
    },
    'svg': {
      edgeTTL: 604800,  // 7 días
      browserTTL: 86400, // 1 día
      tags: ['static', 'images']
    },
    // Fuentes - Cache muy largo
    'woff': {
      edgeTTL: 7776000, // 90 días
      browserTTL: 7776000, // 90 días
      tags: ['static', 'fonts']
    },
    'woff2': {
      edgeTTL: 7776000, // 90 días
      browserTTL: 7776000, // 90 días
      tags: ['static', 'fonts']
    },
    'ttf': {
      edgeTTL: 7776000, // 90 días
      browserTTL: 7776000, // 90 días
      tags: ['static', 'fonts']
    },
    'eot': {
      edgeTTL: 7776000, // 90 días
      browserTTL: 7776000, // 90 días
      tags: ['static', 'fonts']
    },
    // Otros archivos
    'ico': {
      edgeTTL: 2592000, // 30 días
      browserTTL: 2592000, // 30 días
      tags: ['static', 'favicon']
    },
    'pdf': {
      edgeTTL: 86400,   // 1 día
      browserTTL: 3600, // 1 hora
      tags: ['static', 'documents']
    },
    'txt': {
      edgeTTL: 3600,    // 1 hora
      browserTTL: 1800, // 30 minutos
      tags: ['static', 'text']
    }
  }
  
  return configs[extension] || {
    edgeTTL: 3600,      // 1 hora por defecto
    browserTTL: 1800,   // 30 minutos por defecto
    tags: ['static']
  }
}

/**
 * Generar clave de cache personalizada
 * @param {Request} request
 * @param {Object} config
 * @returns {Promise<string>}
 */
async function generateCacheKey(request, config) {
  const url = new URL(request.url)
  const headers = request.headers
  
  // Base URL + path
  let key = `static:${url.pathname}`
  
  // Incluir parámetros de query si existen
  if (url.search && config.tags.includes('css')) {
    key += `?v=${url.searchParams.get('v') || Date.now()}`
  }
  
  // Incluir headers importantes para CSS/JS
  if (config.tags.includes('css') || config.tags.includes('js')) {
    const acceptEncoding = headers.get('Accept-Encoding')
    if (acceptEncoding) {
      key += `&enc=${encodeURIComponent(acceptEncoding)}`
    }
  }
  
  return key
}

/**
 * Obtener Content-Type para extensión
 * @param {string} extension
 * @returns {string}
 */
function getContentType(extension) {
  const types = {
    'css': 'text/css',
    'js': 'application/javascript',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'svg': 'image/svg+xml',
    'ico': 'image/x-icon',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'ttf': 'font/ttf',
    'eot': 'application/vnd.ms-fontobject',
    'pdf': 'application/pdf',
    'txt': 'text/plain'
  }
  
  return types[extension] || 'application/octet-stream'
}

/**
 * Compresión Gzip básica
 * @param {ArrayBuffer} data
 * @returns {Promise<ArrayBuffer>}
 */
async function compressGzip(data) {
  // Implementación simplificada de compresión
  // En un entorno real, usarías una librería de compresión
  return data
}