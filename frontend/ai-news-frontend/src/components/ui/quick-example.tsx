import React from "react"
import { 
  ThemeProvider, 
  useTheme,
  Button, 
  Input, 
  Textarea, 
  Label,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Badge,
  Tag,
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
  Progress,
  DataTable,
  createNewsColumns,
  NewsItem,
  Toaster,
  useForm,
  useDialog,
  useLoading,
  useToast
} from "./ui"
import { toast } from "sonner"

// Ejemplo de uso de Theme Provider
function ThemeExample() {
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

// Ejemplo de uso de formularios con validación
function FormExample() {
  const { values, errors, setValue, handleSubmit } = useForm({
    name: "",
    email: "",
    message: ""
  })

  const onSubmit = async (formData: any) => {
    toast.success(`Formulario enviado: ${formData.name}`)
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(onSubmit) }} className="space-y-4">
      <div>
        <Label htmlFor="name">Nombre</Label>
        <Input
          id="name"
          value={values.name}
          onChange={(e) => setValue("name", e.target.value)}
          error={errors.name}
          placeholder="Tu nombre"
        />
      </div>
      
      <div>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          value={values.email}
          onChange={(e) => setValue("email", e.target.value)}
          error={errors.email}
          placeholder="tu@email.com"
        />
      </div>
      
      <div>
        <Label htmlFor="message">Mensaje</Label>
        <Textarea
          id="message"
          value={values.message}
          onChange={(e) => setValue("message", e.target.value)}
          placeholder="Tu mensaje..."
          rows={3}
        />
      </div>
      
      <Button type="submit">Enviar</Button>
    </form>
  )
}

// Ejemplo de uso de Dialog/Modal
function DialogExample() {
  const { isOpen, open, close } = useDialog()

  return (
    <>
      <Button onClick={open}>Abrir Modal</Button>
      
      <Dialog open={isOpen} onOpenChange={close}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Confirmar Acción</DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que quieres realizar esta acción?
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p>Esta acción no se puede deshacer.</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={close}>
              Cancelar
            </Button>
            <Button variant="destructive" onClick={() => {
              toast.success("Acción confirmada")
              close()
            }}>
              Confirmar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

// Ejemplo de uso de Loading States
function LoadingExample() {
  const { isLoading, startLoading, stopLoading } = useLoading()
  const [progress, setProgress] = React.useState(0)

  const simulateLoading = async () => {
    startLoading("Procesando datos...")
    
    // Simular progreso
    for (let i = 0; i <= 100; i += 10) {
      setProgress(i)
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    stopLoading()
    toast.success("Proceso completado")
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button onClick={simulateLoading} disabled={isLoading}>
          {isLoading ? <Spinner size="sm" /> : "Simular Carga"}
        </Button>
      </div>
      
      <div className="space-y-2">
        <div className="text-sm">Progreso: {progress}%</div>
        <Progress value={progress} />
      </div>
      
      {isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      )}
    </div>
  )
}

// Ejemplo de uso de Badge y Tag
function StatusExample() {
  const statuses = [
    { label: "Publicado", variant: "success" as const },
    { label: "Borrador", variant: "warning" as const },
    { label: "Archivado", variant: "destructive" as const },
    { label: "Revisión", variant: "info" as const }
  ]

  const categories = [
    "IA",
    "Machine Learning", 
    "Deep Learning",
    "NLP",
    "Computer Vision"
  ]

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-sm font-medium mb-2">Estados:</h4>
        <div className="flex flex-wrap gap-2">
          {statuses.map((status, index) => (
            <Badge key={index} variant={status.variant}>
              {status.label}
            </Badge>
          ))}
        </div>
      </div>
      
      <div>
        <h4 className="text-sm font-medium mb-2">Categorías:</h4>
        <div className="flex flex-wrap gap-2">
          {categories.map((category, index) => (
            <Tag key={index} variant={index % 2 === 0 ? "default" : "secondary"}>
              {category}
            </Tag>
          ))}
        </div>
      </div>
    </div>
  )
}

// Ejemplo de uso de DataTable
function TableExample() {
  const sampleData: NewsItem[] = [
    {
      id: "1",
      title: "Avances en ChatGPT-4",
      description: "Nuevas capacidades del modelo de lenguaje",
      category: "IA",
      status: "published",
      createdAt: new Date("2024-01-15"),
      updatedAt: new Date("2024-01-16"),
      author: "Juan Pérez",
      tags: ["LLM", "OpenAI"],
      source: "TechNews"
    },
    {
      id: "2",
      title: "Regulación de IA en Europa",
      description: "Nueva legislación europea sobre IA",
      category: "Regulación",
      status: "draft", 
      createdAt: new Date("2024-01-14"),
      updatedAt: new Date("2024-01-14"),
      author: "María García",
      tags: ["Legislación", "Europa"],
      source: "EU News"
    }
  ]

  return (
    <DataTable 
      columns={createNewsColumns()} 
      data={sampleData}
      searchPlaceholder="Buscar noticias..."
    />
  )
}

// Ejemplo principal que muestra todos los componentes
export default function QuickExample() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="ai-news-theme">
      <Container size="lg" className="py-8 space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">Ejemplo Rápido - Componentes UI</h1>
          <p className="text-muted-foreground">
            Demostración rápida de todos los componentes disponibles
          </p>
        </div>

        {/* Theme Provider */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Tema (Light/Dark Mode)</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <ThemeExample />
          </PanelContent>
        </Panel>

        {/* Formulario */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Formulario con Validación</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <FormExample />
          </PanelContent>
        </Panel>

        {/* Dialog */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Modal/Dialog</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <DialogExample />
          </PanelContent>
        </Panel>

        {/* Loading States */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Estados de Carga</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <LoadingExample />
          </PanelContent>
        </Panel>

        {/* Status Components */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Badges y Tags</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <StatusExample />
          </PanelContent>
        </Panel>

        {/* Card Examples */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Tarjeta de Noticia</CardTitle>
              <CardDescription>Descripción de la noticia</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Badge variant="success">Publicado</Badge>
                <Tag>IA</Tag>
                <Tag variant="info">Machine Learning</Tag>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Información del Sistema</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Badge variant="success">En línea</Badge>
                <span className="text-sm text-muted-foreground">Última actualización: hace 2 min</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* DataTable */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Tabla de Datos</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <TableExample />
          </PanelContent>
        </Panel>

        <Toaster />
      </Container>
    </ThemeProvider>
  )
}
