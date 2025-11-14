# Sistema de Navegación - AI News Aggregator

Este documento describe el sistema completo de navegación y routing implementado para la aplicación AI News Aggregator.

## 🚀 Características Implementadas

### 1. **App.tsx con Routing Principal**
- Configuración de React Router con lazy loading
- Rutas principales y rutas protegidas
- Manejo de error boundaries
- Suspense para carga asíncrona

### 2. **Layout Component**
- Estructura principal con header, sidebar, footer y breadcrumbs
- Manejo responsive para desktop y móvil
- Scroll automático al cambiar de ruta

### 3. **Header/Navbar Responsive**
- Logo y branding
- Navegación principal con highlighting de ruta activa
- Barra de búsqueda funcional
- Menú de usuario con notificaciones
- Hamburger menu para móvil

### 4. **Sidebar con Navegación**
- Navegación por secciones principales y cuenta
- Indicadores visuales de rutas protegidas
- Overlay en móvil con cierre automático
- Navegación por teclado accesible

### 5. **Protected Routes**
- Protección de rutas sensibles (/profile, /settings, /privacy)
- Redirección automática al login si no está autenticado
- Mensajes de acceso restringido personalizados

### 6. **Breadcrumbs**
- Generación automática basada en la ruta actual
- Navegación rápida entre secciones
- Iconos de inicio y separadores
- Soporte para rutas personalizadas

### 7. **Página 404 y Error Boundaries**
- Página de error 404 personalizada con navegación de recuperación
- Error boundary específico para routing
- Detalles técnicos en modo desarrollo
- Botones de recuperación (recargar, ir al inicio)

### 8. **Lazy Loading de Componentes**
- Carga asíncrona de todas las páginas
- Loading states con suspense
- Componentes dinámicos para Settings y Privacy
- Optimización del rendimiento de la aplicación

### 9. **Scroll to Top**
- Scroll automático en cambios de ruta
- Componente reutilizable ScrollToTop
- Configuración de comportamiento (smooth/auto)

### 10. **Mobile Navigation con Hamburger Menu**
- Sidebar overlay en dispositivos móviles
- Touch-friendly con tap-to-close
- Responsive breakpoints configurables
- Estados de navegación persistentes

## 📁 Estructura de Archivos

```
src/
├── components/
│   ├── layout/
│   │   └── Layout.tsx              # Layout principal con header/sidebar/footer
│   ├── navigation/
│   │   ├── Header.tsx              # Header con navegación responsive
│   │   ├── Sidebar.tsx             # Sidebar con navegación lateral
│   │   └── Breadcrumbs.tsx         # Navegación breadcrumbs
│   ├── common/
│   │   ├── ProtectedRoute.tsx      # Protección de rutas
│   │   ├── ScrollToTop.tsx         # Scroll automático
│   │   ├── Loading.tsx             # Componente de carga
│   │   ├── PageTransition.tsx      # Transiciones de página
│   │   └── RoutingErrorBoundary.tsx # Manejo de errores
│   └── ErrorBoundary.tsx           # Error boundary general
├── pages/
│   ├── Home.tsx                    # Página principal
│   ├── News.tsx                    # Página de noticias
│   ├── Trends.tsx                  # Página de tendencias
│   ├── Resources.tsx               # Página de recursos
│   ├── Profile.tsx                 # Página de perfil (protegida)
│   ├── Login.tsx                   # Página de login
│   └── NotFound.tsx                # Página 404
├── hooks/
│   ├── use-mobile.tsx              # Detección de dispositivo móvil
│   └── use-route.tsx               # Hook para información de rutas
├── lib/
│   ├── utils.ts                    # Utilidades generales
│   └── navigation.ts               # Utilidades de navegación
├── types/
│   └── index.ts                    # Tipos TypeScript
└── App.tsx                         # Aplicación principal con routing
```

## 🛠️ Tecnologías Utilizadas

- **React Router DOM v6**: Para el sistema de routing
- **React 18**: Componentes y hooks modernos
- **TypeScript**: Tipado estático
- **Tailwind CSS**: Estilos responsive
- **Lucide React**: Iconos modernos
- **Radix UI**: Componentes accesibles

## 📱 Responsive Design

### Desktop (768px+)
- Sidebar fijo siempre visible
- Navegación horizontal en header
- Breadcrumbs siempre visibles
- Transiciones suaves

### Mobile (< 768px)
- Hamburger menu en header
- Sidebar overlay con overlay oscuro
- Navegación touch-friendly
- Breadcrumbs simplificados

## 🔐 Rutas Protegidas

Las siguientes rutas requieren autenticación:
- `/profile` - Perfil de usuario
- `/settings` - Configuración
- `/privacy` - Privacidad

## 🎨 Características UX/UI

- **Estados de carga**: Loading spinners con mensajes descriptivos
- **Transiciones**: Animaciones suaves entre páginas
- **Error handling**: Mensajes de error informativos con opciones de recuperación
- **Accesibilidad**: Navegación por teclado y ARIA labels
- **Performance**: Lazy loading y code splitting

## 🚀 Instalación y Uso

```bash
# Instalar dependencias
npm install

# Ejecutar en desarrollo
npm run dev

# Build para producción
npm run build
```

## 📝 Configuración

### Configuración de Rutas
Las rutas están configuradas en `src/lib/navigation.ts`:

```typescript
export const NAVIGATION_CONFIG: NavigationItem[] = [
  { id: 'home', label: 'Inicio', path: '/' },
  { id: 'news', label: 'Noticias', path: '/news' },
  // ... más rutas
];
```

### Breakpoints Responsivos
Modificables en `src/hooks/use-mobile.tsx`:

```typescript
const MOBILE_BREAKPOINT = 768;
```

### Lazy Loading
Todos los componentes de página están configurados con lazy loading:

```typescript
const Home = React.lazy(() => import('./pages/Home'));
```

## 🔧 Personalización

### Agregar Nueva Ruta
1. Crear componente en `src/pages/`
2. Agregar a la configuración en `src/App.tsx`
3. Opcionalmente, proteger con `ProtectedRoute`
4. Agregar al breadcrumb mapping si es necesario

### Modificar Navegación
1. Editar `src/lib/navigation.ts` para agregar rutas
2. Actualizar Header y Sidebar si es necesario
3. Configurar breadcrumbs automáticos

### Estilos
- Utilizar clases de Tailwind CSS
- Mantener consistencia con el sistema de diseño
- Responsive-first approach

## 🎯 Próximos Pasos

- [ ] Integrar sistema de autenticación real
- [ ] Agregar analytics de navegación
- [ ] Implementar prefetching de rutas
- [ ] Mejorar transiciones con Framer Motion
- [ ] Agregar service worker para caché offline
- [ ] Implementar persistencia de estado de navegación

---

Este sistema de navegación proporciona una base sólida y escalable para la aplicación AI News Aggregator, con todas las características modernas esperadas en una aplicación web profesional.