# Endpoints de Gestión de Usuarios

Esta documentación describe los endpoints de gestión de usuarios implementados para el sistema AI News Aggregator.

## Base URL
```
http://localhost:8000/api/v1/users
```

## Autenticación

Todos los endpoints (excepto registro y login) requieren autenticación JWT. Incluir el token en el header:
```
Authorization: Bearer <token>
```

## Endpoints

### 1. Registro de Usuario
- **URL**: `POST /register`
- **Descripción**: Registrar un nuevo usuario
- **Body**:
```json
{
  "username": "juan_perez",
  "email": "juan@example.com",
  "password": "mi_password_123",
  "full_name": "Juan Pérez"
}
```
- **Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "username": "juan_perez",
    "email": "juan@example.com",
    "full_name": "Juan Pérez",
    "is_active": true,
    "is_superuser": false,
    "role": "user",
    "avatar_url": null,
    "last_login": null,
    "created_at": "2025-11-06T03:03:36Z"
  }
}
```

### 2. Login de Usuario
- **URL**: `POST /login`
- **Descripción**: Iniciar sesión y obtener token
- **Body**:
```json
{
  "username": "juan_perez",
  "password": "mi_password_123"
}
```
- **Response**: Mismo formato que registro

### 3. Perfil del Usuario
- **URL**: `GET /me`
- **Descripción**: Obtener perfil del usuario actual
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Datos del usuario actual

### 4. Actualizar Perfil
- **URL**: `PUT /me`
- **Descripción**: Actualizar perfil del usuario actual
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "full_name": "Juan Carlos Pérez",
  "email": "juan.carlos@example.com"
}
```

### 5. Obtener Preferencias
- **URL**: `GET /preferences`
- **Descripción**: Obtener preferencias del usuario actual
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "preferred_sources": ["newsapi", "guardian"],
  "blocked_sources": ["nytimes"],
  "preferred_topics": ["tecnologia", "ai", "machine-learning"],
  "ignored_topics": ["politica"],
  "sentiment_preference": "positive",
  "reading_level": "mixed",
  "notification_frequency": "daily",
  "language": "es",
  "timezone": "UTC",
  "created_at": "2025-11-06T03:03:36Z",
  "updated_at": "2025-11-06T03:03:36Z"
}
```

### 6. Actualizar Preferencias
- **URL**: `PUT /preferences`
- **Descripción**: Actualizar preferencias del usuario
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "preferred_sources": ["newsapi", "guardian", "nytimes"],
  "blocked_sources": [],
  "preferred_topics": ["tecnologia", "inteligencia-artificial", "startups"],
  "ignored_topics": [],
  "sentiment_preference": "positive",
  "reading_level": "mixed",
  "notification_frequency": "realtime",
  "language": "es",
  "timezone": "Europe/Madrid"
}
```

### 7. Obtener Marcadores
- **URL**: `GET /bookmarks`
- **Descripción**: Obtener artículos guardados del usuario
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "article_id": "uuid",
    "title": "Título del artículo guardado",
    "url": "https://example.com/article",
    "notes": "Nota personal sobre este artículo",
    "tags": ["ai", "machine-learning"],
    "created_at": "2025-11-06T03:03:36Z"
  }
]
```

### 8. Guardar Artículo
- **URL**: `POST /bookmarks`
- **Descripción**: Guardar un artículo en marcadores
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "article_id": "uuid-del-articulo",
  "title": "Título del artículo",
  "url": "https://example.com/article",
  "notes": "Artículo muy interesante sobre IA",
  "tags": ["artificial-intelligence", "research"]
}
```

### 9. Eliminar Marcador
- **URL**: `DELETE /bookmarks/{bookmark_id}`
- **Descripción**: Eliminar un artículo de marcadores
- **Headers**: `Authorization: Bearer <token>`

## Endpoints de Administrador

### 10. Obtener Todos los Usuarios
- **URL**: `GET /admin/users`
- **Descripción**: Obtener lista de todos los usuarios (solo superusuarios)
- **Headers**: `Authorization: Bearer <token>` (superusuario)
- **Response**: Lista de usuarios con sus datos

### 11. Activar/Desactivar Usuario
- **URL**: `PUT /admin/users/{user_id}/activate`
- **Descripción**: Alternar estado activo de un usuario (solo superusuarios)
- **Headers**: `Authorization: Bearer <token>` (superusuario)

## Códigos de Estado

- `200` - Operación exitosa
- `201` - Recurso creado exitosamente
- `400` - Error en los datos enviados
- `401` - No autorizado (token inválido o ausente)
- `403` - Prohibido (sin permisos suficientes)
- `404` - Recurso no encontrado
- `500` - Error interno del servidor

## Ejemplo de Uso con cURL

### Registro
```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "maria_garcia",
    "email": "maria@example.com",
    "password": "password123",
    "full_name": "María García"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "maria_garcia",
    "password": "password123"
  }'
```

### Obtener Perfil (con token)
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Actualizar Preferencias
```bash
curl -X PUT "http://localhost:8000/api/v1/users/preferences" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_sources": ["newsapi", "guardian"],
    "preferred_topics": ["tecnologia", "ia"]
  }'
```

## Configuración de Seguridad

### Variables de Entorno Requeridas
```bash
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Consideraciones de Seguridad
- La contraseña se hashea usando bcrypt
- Los tokens JWT expiran automáticamente
- Solo los superusuarios pueden acceder a endpoints administrativos
- Todas las operaciones requieren autenticación excepto registro y login
- Los marcadores son únicos por usuario y artículo