import React, { useState } from "react"
import { 
  Button,
  Input,
  Textarea,
  Label,
  SearchInput,
  DateInput,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Badge,
  Tag,
  Chip,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Panel,
  PanelHeader,
  PanelTitle,
  PanelContent,
  Container,
  Spinner,
  Skeleton,
  TextLineSkeleton,
  CardSkeleton,
  Progress,
  DataTable,
  createNewsColumns,
  NewsItem,
  Toaster,
  useTheme
} from "@/components/ui"
import { toast } from "sonner"

const ThemeToggle = () => {
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex gap-2">
      <Button 
        variant={theme === "light" ? "default" : "outline"}
        size="sm"
        onClick={() => setTheme("light")}
      >
        Claro
      </Button>
      <Button 
        variant={theme === "dark" ? "default" : "outline"}
        size="sm"
        onClick={() => setTheme("dark")}
      >
        Oscuro
      </Button>
      <Button 
        variant={theme === "system" ? "default" : "outline"}
        size="sm"
        onClick={() => setTheme("system")}
      >
        Sistema
      </Button>
    </div>
  )
}

// Datos de ejemplo para la tabla
const sampleNews: NewsItem[] = [
  {
    id: "1",
    title: "Avances en Inteligencia Artificial 2024",
    description: "Los últimos desarrollos en IA que están revolucionando la industria.",
    category: "Tecnología",
    status: "published",
    createdAt: new Date("2024-01-15"),
    updatedAt: new Date("2024-01-16"),
    author: "Juan Pérez",
    tags: ["AI", "Machine Learning", "Innovación"],
    source: "TechNews"
  },
  {
    id: "2", 
    title: "Nuevas Regulaciones de IA en Europa",
    description: "La UE aprueba nuevas leyes para regular el uso de la inteligencia artificial.",
    category: "Regulación",
    status: "published",
    createdAt: new Date("2024-01-14"),
    updatedAt: new Date("2024-01-14"),
    author: "María García",
    tags: ["Regulación", "Europa", "Políticas"],
    source: "EU News"
  },
  {
    id: "3",
    title: "Startup de IA Recebe Investimento Milionário",
    description: "Uma nova startup de inteligência artificial levanta $50M em financiamento Série A.",
    category: "Negócios",
    status: "draft",
    createdAt: new Date("2024-01-13"),
    updatedAt: new Date("2024-01-13"),
    author: "Carlos Silva",
    tags: ["Startup", "Investimento", "Financiamento"],
    source: "Business AI"
  }
]

export default function ComponentsDemo() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [progress, setProgress] = useState(65)

  const showToast = (message: string) => {
    toast.success(message)
  }

  const handleLoadingExample = () => {
    showToast("Simulando carregamento...")
    setTimeout(() => {
      showToast("Operação concluída com sucesso!")
    }, 2000)
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <Container size="2xl" className="space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">Sistema de Componentes UI</h1>
          <ThemeToggle />
        </div>

        {/* Theme Provider Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>1. Theme Provider (Dark/Light Mode)</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <p className="text-muted-foreground">
              Este componente demuestra el soporte para temas claro/oscuro usando el Theme Provider.
            </p>
          </PanelContent>
        </Panel>

        {/* Buttons Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>2. Botones (Button Variants)</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <div className="flex flex-wrap gap-4">
              <Button onClick={() => showToast("Botón primario")}>Primario</Button>
              <Button variant="secondary">Secundario</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="link">Link</Button>
              <Button variant="destructive" onClick={() => showToast("Acción destructiva")}>Destructivo</Button>
              <Button size="sm">Pequeño</Button>
              <Button size="lg">Grande</Button>
              <Button size="icon">
                <span className="sr-only">Icono</span>
                🔔
              </Button>
            </div>
          </PanelContent>
        </Panel>

        {/* Inputs Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>3. Componentes de Entrada (Input con Validación)</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Nombre</Label>
                <Input id="name" placeholder="Ingresa tu nombre" />
              </div>
              <div>
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="email@ejemplo.com" error="Formato de email inválido" />
              </div>
            </div>
            
            <div>
              <Label htmlFor="search">Búsqueda</Label>
              <SearchInput 
                id="search"
                placeholder="Buscar en noticias..." 
                onClear={() => toast.info("Búsqueda limpiada")}
              />
            </div>
            
            <div>
              <Label htmlFor="date">Fecha</Label>
              <DateInput 
                id="date"
                placeholder="Seleccionar fecha"
                onChange={(date) => {
                  if (date) {
                    toast.success(`Fecha seleccionada: ${date.toLocaleDateString()}`)
                  }
                }}
              />
            </div>
            
            <div>
              <Label htmlFor="description">Descripción</Label>
              <Textarea 
                id="description" 
                placeholder="Escribe una descripción..."
                rows={3}
              />
            </div>
          </PanelContent>
        </Panel>

        {/* Modal/Dialog Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>4. Modal/Dialog System</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button>Abrir Modal</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Editar Perfil</DialogTitle>
                  <DialogDescription>
                    Haz cambios a tu perfil aquí. Haz clic en guardar cuando hayas terminado.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="name" className="text-right">
                      Nombre
                    </Label>
                    <Input id="name" defaultValue="Juan Pérez" className="col-span-3" />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="username" className="text-right">
                      Usuario
                    </Label>
                    <Input id="username" defaultValue="@juanperez" className="col-span-3" />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="submit" onClick={() => setDialogOpen(false)}>
                    Guardar cambios
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </PanelContent>
        </Panel>

        {/* Badge/Status Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>5. Badge Components (Status con Iconos)</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div>
              <h4 className="mb-2">Badges con Iconos Automáticos:</h4>
              <div className="flex flex-wrap gap-2">
                <Badge showIcon>Default</Badge>
                <Badge variant="secondary" showIcon>Secundario</Badge>
                <Badge variant="outline">Outline</Badge>
                <Badge variant="success" showIcon>Éxito</Badge>
                <Badge variant="warning" showIcon>Advertencia</Badge>
                <Badge variant="info" showIcon>Información</Badge>
                <Badge variant="destructive" showIcon>Destructivo</Badge>
              </div>
            </div>
            
            <div>
              <h4 className="mb-2">Badges con Iconos Personalizados:</h4>
              <div className="flex flex-wrap gap-2">
                <Badge icon={<span>🚀</span>}>Lanzamiento</Badge>
                <Badge icon={<span>⭐</span>}>Destacado</Badge>
                <Badge icon={<span>🔥</span>} variant="warning">Tendencia</Badge>
                <Badge icon={<span>💡</span>} variant="info">Nuevo</Badge>
              </div>
            </div>
          </PanelContent>
        </Panel>

        {/* Tags/Chips Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>6. Tag/Chip Components (Categorías)</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div>
              <h4 className="mb-2">Tags (Redondos):</h4>
              <div className="flex flex-wrap gap-2">
                <Tag>React</Tag>
                <Tag variant="secondary">TypeScript</Tag>
                <Tag variant="success">Python</Tag>
                <Tag variant="info">Machine Learning</Tag>
                <Tag variant="warning">Experimental</Tag>
                <Tag variant="outline">Outline Tag</Tag>
                <Tag variant="purple">IA</Tag>
                <Tag variant="pink">Vue.js</Tag>
                <Tag removable onRemove={() => showToast("Tag removido")}>
                  Removible
                </Tag>
              </div>
            </div>
            
            <div>
              <h4 className="mb-2">Chips (Rectangulares):</h4>
              <div className="flex flex-wrap gap-2">
                <Chip>Frontend</Chip>
                <Chip variant="secondary">Backend</Chip>
                <Chip variant="outline">Diseño</Chip>
                <Chip variant="success">API</Chip>
                <Chip variant="warning">BETA</Chip>
                <Chip variant="info">Tendencia</Chip>
                <Chip removable onRemove={() => showToast("Chip removido")}>
                  Removible
                </Chip>
              </div>
            </div>
          </PanelContent>
        </Panel>

        {/* Loading States Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>7. Loading States (Spinner, Skeleton, Progress)</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-6">
            <div>
              <h4 className="mb-2">Spinners:</h4>
              <div className="flex items-center gap-4">
                <Spinner size="sm" label="Cargando..." />
                <Spinner size="md" />
                <Spinner size="lg" color="white" />
              </div>
            </div>
            
            <div>
              <h4 className="mb-2">Skeleton Lines:</h4>
              <TextLineSkeleton lines={4} />
            </div>
            
            <div>
              <h4 className="mb-2">Card Skeleton:</h4>
              <div className="w-80">
                <CardSkeleton />
              </div>
            </div>
            
            <div>
              <h4 className="mb-2">Progress: {progress}%</h4>
              <Progress value={progress} className="w-full" />
              <Button 
                className="mt-2" 
                size="sm" 
                onClick={() => setProgress(Math.min(100, progress + 10))}
              >
                Incrementar 10%
              </Button>
            </div>

            <Button onClick={handleLoadingExample}>
              Simular Carga
            </Button>
          </PanelContent>
        </Panel>

        {/* Layout Components Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>8. Layout Components (Card, Panel, Container)</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Tarjeta Simple</CardTitle>
                  <CardDescription>
                    Una tarjeta básica con header, título y descripción.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p>Contenido de la tarjeta con información importante.</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Tarjeta de Estado</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="success">En línea</Badge>
                    <span className="text-sm text-muted-foreground">Última actualización: hace 2 min</span>
                  </div>
                  <p>Sistema funcionando correctamente.</p>
                </CardContent>
              </Card>
            </div>
          </PanelContent>
        </Panel>

        {/* DataTable Demo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>9. DataTable (Sorting/Pagination)</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <DataTable 
              columns={createNewsColumns()} 
              data={sampleNews}
              searchPlaceholder="Buscar noticias..."
            />
          </PanelContent>
        </Panel>

        {/* Toast Notifications */}
        <Panel>
          <PanelHeader>
            <PanelTitle>10. Toast Notifications</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => toast.success("Operación exitosa!")}>
                Mostrar Éxito
              </Button>
              <Button variant="destructive" onClick={() => toast.error("Ha ocurrido un error")}>
                Mostrar Error
              </Button>
              <Button variant="outline" onClick={() => toast.info("Información importante")}>
                Mostrar Info
              </Button>
              <Button variant="secondary" onClick={() => toast.warning("Advertencia")}>
                Mostrar Advertencia
              </Button>
            </div>
          </PanelContent>
        </Panel>

        <Toaster />
      </Container>
    </div>
  )
}
