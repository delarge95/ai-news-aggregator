# Sistema de Componentes UI

Sistema completo de componentes UI reutilizables para el proyecto AI News Aggregator, construido con React, TypeScript, Tailwind CSS y Radix UI.

## Características

- ✅ **Theme Provider** con soporte dark/light mode
- ✅ **Button variants** (primary, secondary, ghost, outline, link, destructive)
- ✅ **Input components** con validación
- ✅ **Modal/Dialog system** completo
- ✅ **Toast notifications** con Sonner
- ✅ **Loading states** (spinner, skeleton, progress)
- ✅ **DataTable** con sorting/pagination
- ✅ **Tag/Chip components** para categorías
- ✅ **Badge components** para status
- ✅ **Layout components** (Card, Panel, Container)

## Instalación

Los componentes ya están configurados en el proyecto. Solo necesitas importar desde `@/components/ui`:

```typescript
import { Button, Card, Dialog, Badge } from "@/components/ui"
```

## Componentes

### 1. Theme Provider

Maneja el tema claro/oscuro de la aplicación.

```tsx
import { ThemeProvider, useTheme } from "@/components/ui"

function App() {
  const { theme, setTheme } = useTheme()
  
  return (
    <ThemeProvider>
      <button onClick={() => setTheme("dark")}>Dark</button>
    </ThemeProvider>
  )
}
```

### 2. Button

Variantes disponibles: `default`, `secondary`, `outline`, `ghost`, `link`, `destructive`

Tamaños: `default`, `sm`, `lg`, `icon`

```tsx
<Button variant="default" size="lg">
  Primary Button
</Button>

<Button variant="outline" size="sm">
  Small Outline
</Button>

<Button variant="ghost">
  Ghost Button
</Button>
```

### 3. Inputs

#### Input básico
```tsx
<Input 
  placeholder="Enter text..." 
  error="Error message" // opcional
/>
```

#### SearchInput
```tsx
<SearchInput 
  placeholder="Search..."
  onClear={() => console.log('cleared')}
  loading={false}
/>
```

#### DateInput
```tsx
<DateInput 
  placeholder="Select date"
  onChange={(date) => console.log(date)}
  format="dd/MM/yyyy"
  minDate={new Date()}
  maxDate={new Date('2025-12-31')}
/>
```

#### Textarea
```tsx
<Textarea 
  placeholder="Enter description..."
  rows={4}
  error="Error message" // opcional
/>
```

#### Label
```tsx
<Label htmlFor="input-id">Label Text</Label>
<Input id="input-id" />
```

### 4. Dialog/Modal

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui"

<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>Description text</DialogDescription>
    </DialogHeader>
    <div>Content</div>
    <DialogFooter>
      <Button>Save</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### 5. Toast Notifications

```tsx
import { toast } from "sonner"
import { Toaster } from "@/components/ui"

toast.success("Operation successful!")
toast.error("An error occurred")
toast.warning("Warning message")
toast.info("Information message")

// En tu App component
<Toaster />
```

### 6. Loading States

#### Spinner
```tsx
<Spinner size="sm" />
<Spinner size="md" />
<Spinner size="lg" />
<Spinner size="xl" label="Cargando..." />
<Spinner color="white" />
```

#### Skeleton básico
```tsx
<Skeleton className="h-4 w-[250px]" />
<Skeleton className="h-4 w-[200px]" />
```

#### Skeleton avanzadas
```tsx
<TextLineSkeleton lines={4} />
<CardSkeleton />
<TableRowSkeleton columns={4} />
```

#### Progress
```tsx
<Progress value={75} />
<Progress value={progress} className="w-full" />
```

### 7. Badge (Status)

Variantes: `default`, `secondary`, `outline`, `success`, `warning`, `info`, `destructive`

```tsx
<Badge variant="success">Published</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="destructive">Failed</Badge>
```

#### Badge con iconos automáticos
```tsx
<Badge showIcon>Default</Badge>
<Badge variant="success" showIcon>Success</Badge>
<Badge variant="warning" showIcon>Warning</Badge>
<Badge variant="info" showIcon>Info</Badge>
```

#### Badge con iconos personalizados
```tsx
<Badge icon={<RocketIcon />}>Launch</Badge>
<Badge icon={<StarIcon />}>Featured</Badge>
<Badge icon={<span>🚀</span>}>Custom Emoji</Badge>
```

### 8. Tag/Chip (Categorías)

#### Tags (Redondos)
Variantes: `default`, `secondary`, `success`, `warning`, `info`, `outline`, `purple`, `pink`, `orange`, `gray`

```tsx
<Tag>React</Tag>
<Tag variant="success">Machine Learning</Tag>
<Tag variant="warning">Beta</Tag>
<Tag variant="purple">AI</Tag>
<Tag removable onRemove={() => console.log('removed')}>
  Removable Tag
</Tag>
```

#### Chips (Rectangulares)
Variantes: `default`, `secondary`, `success`, `warning`, `info`, `outline`

```tsx
<Chip>Frontend</Chip>
<Chip variant="success">API</Chip>
<Chip variant="warning">Beta</Chip>
<Chip removable onRemove={() => console.log('removed')}>
  Removable Chip
</Chip>
```

### 9. Layout Components

#### Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description</CardDescription>
  </CardHeader>
  <CardContent>
    Card content goes here
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

#### Panel
```tsx
<Panel>
  <PanelHeader>
    <PanelTitle>Panel Title</PanelTitle>
    <PanelDescription>Panel description</PanelDescription>
  </PanelHeader>
  <PanelContent>
    Panel content
  </PanelContent>
  <PanelFooter>
    <Button>Action</Button>
  </PanelFooter>
</Panel>
```

#### Container
```tsx
<Container size="lg">
  <div>Content</div>
</Container>
```

Tamaños disponibles: `sm`, `md`, `lg`, `xl`, `2xl`, `full`

### 10. DataTable

Componente avanzado con sorting, filtrado y paginación.

```tsx
import { DataTable, createNewsColumns, NewsItem } from "@/components/ui"

const columns = createNewsColumns() // o crea tus propias columnas
const data: NewsItem[] = [...]

<DataTable 
  columns={columns} 
  data={data}
  searchPlaceholder="Search news..."
  pageSizeOptions={[10, 20, 50, 100]}
/>
```

#### Crear columnas personalizadas

```tsx
import { ColumnDef } from "@tanstack/react-table"
import { Button } from "@/components/ui"
import { ArrowUpDown } from "lucide-react"

const columns: ColumnDef<NewsItem>[] = [
  {
    accessorKey: "title",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Title
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue("title")}</div>
    ),
  },
  // más columnas...
]
```

## Funciones Helper

### DataTable Helpers

```tsx
import { createTextColumn, createStatusColumn, createTagsColumn, createDateColumn } from "@/components/ui"

// Crear columna de texto con sorting
createTextColumn<NewsItem, string>("title", "Title")

// Crear columna con badge/status
createStatusColumn<NewsItem, string>(
  "status", 
  "Status", 
  (value) => value === "published" ? "success" : "warning"
)

// Crear columna con tags
createTagsColumn<NewsItem, string[]>("tags", "Tags")

// Crear columna con fecha
createDateColumn<NewsItem, Date>("createdAt", "Created", "datetime")
```

## Ejemplo de Uso Completo

Ver el archivo `components-demo.tsx` para un ejemplo completo de todos los componentes en funcionamiento.

## Estructura de Archivos

```
src/components/ui/
├── index.ts                    # Exportaciones principales
├── theme-provider.tsx         # Theme provider
├── button.tsx                 # Button component
├── input.tsx                  # Input component
├── search-input.tsx           # SearchInput component
├── date-input.tsx             # DateInput component
├── textarea.tsx               # Textarea component
├── label.tsx                  # Label component
├── dialog.tsx                 # Dialog/Modal
├── select.tsx                 # Select component
├── badge.tsx                  # Badge component (con iconos)
├── tag.tsx                    # Tag/Chip component (expandido)
├── spinner.tsx                # Loading spinner (mejorado)
├── skeleton.tsx               # Loading skeleton (expandido)
├── progress.tsx               # Progress bar
├── card.tsx                   # Card component
├── panel.tsx                  # Panel component
├── container.tsx              # Container component
├── data-table.tsx             # DataTable component
├── data-table-helpers.tsx     # DataTable helpers
├── toast.tsx                  # Toast component (base)
├── use-toast.ts               # Toast hook
├── toaster.tsx               # Toast notifications
└── components-demo.tsx       # Demo completo
```

## Tecnologías Utilizadas

- **React 18** - Framework base
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Styling
- **Radix UI** - Componentes accesibles
- **Sonner** - Notificaciones toast
- **@tanstack/react-table** - Tablas avanzadas
- **class-variance-authority** - Variantes de componentes
- **lucide-react** - Iconos

## Accesibilidad

Todos los componentes siguen las mejores prácticas de accesibilidad:

- Navegación por teclado completa
- ARIA labels y roles apropiados
- Soporte para lectores de pantalla
- Contraste de colores adecuado
- Estados de focus visibles

## Customización

### Colores del tema

Los colores se definen en `src/index.css` usando variables CSS:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  /* ... más variables */
}
```

### Personalización de componentes

Usa las props `className` para aplicar estilos adicionales:

```tsx
<Button className="bg-blue-500 hover:bg-blue-600">
  Custom Button
</Button>
```

## Mejores Prácticas

1. **Importación**: Usa siempre `import { Component } from "@/components/ui"`
2. **Variantes**: Elige la variante más apropiada para el contexto
3. **Accesibilidad**: Siempre incluye labels para inputs
4. **Estados de carga**: Usa skeleton para mejor UX
5. **Mensajes de error**: Proporciona feedback claro al usuario
6. **Responsividad**: Los componentes son responsive por defecto

## Soporte de Navegadores

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Soporte móvil completo
