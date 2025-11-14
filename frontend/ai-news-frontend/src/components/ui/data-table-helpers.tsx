import { ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ColumnDef } from "@tanstack/react-table"

// Este archivo contiene utilidades y helpers para la DataTable
export interface NewsItem {
  id: string
  title: string
  description: string
  category: string
  status: "published" | "draft" | "archived"
  createdAt: Date
  updatedAt: Date
  author: string
  tags: string[]
  source: string
}

// Columna básica con sorting
export function createTextColumn<TData, TValue>(
  accessorKey: keyof TData,
  header: string
): ColumnDef<TData, TValue> {
  return {
    accessorKey: accessorKey as string,
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        {header}
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
  }
}

// Columna con badge/status
export function createStatusColumn<TData, TValue>(
  accessorKey: keyof TData,
  header: string,
  getStatusColor: (value: any) => "default" | "secondary" | "destructive" | "success" | "warning" | "info"
): ColumnDef<TData, TValue> {
  return {
    accessorKey: accessorKey as string,
    header: header,
    cell: ({ row }) => {
      const value = row.getValue(accessorKey as string)
      const variant = getStatusColor(value)
      return (
        <Badge variant={variant}>
          {value as string}
        </Badge>
      )
    },
  }
}

// Columna con tags/chips
export function createTagsColumn<TData, TValue>(
  accessorKey: keyof TData,
  header: string
): ColumnDef<TData, TValue> {
  return {
    accessorKey: accessorKey as string,
    header: header,
    cell: ({ row }) => {
      const value = row.getValue(accessorKey as string) as string[]
      return (
        <div className="flex flex-wrap gap-1">
          {value.map((tag, index) => (
            <Badge key={index} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      )
    },
  }
}

// Columna con fecha formateada
export function createDateColumn<TData, TValue>(
  accessorKey: keyof TData,
  header: string,
  format: "date" | "datetime" = "date"
): ColumnDef<TData, TValue> {
  return {
    accessorKey: accessorKey as string,
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        {header}
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }) => {
      const value = row.getValue(accessorKey as string) as Date
      const formatted = format === "datetime" 
        ? new Intl.DateTimeFormat('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          }).format(value)
        : new Intl.DateTimeFormat('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
          }).format(value)
      
      return <div className="text-sm">{formatted}</div>
    },
  }
}

// Función helper para crear columnas de ejemplo para NewsItem
export function createNewsColumns(): ColumnDef<NewsItem>[] {
  return [
    {
      accessorKey: "title",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Título
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue("title")}</div>
      ),
    },
    {
      accessorKey: "author",
      header: "Autor",
      cell: ({ row }) => (
        <div className="text-sm">{row.getValue("author")}</div>
      ),
    },
    {
      accessorKey: "category",
      header: "Categoría",
    },
    {
      accessorKey: "status",
      header: "Estado",
      cell: ({ row }) => {
        const status = row.getValue("status") as string
        const variant = status === "published" ? "success" : 
                       status === "draft" ? "warning" : "destructive"
        return <Badge variant={variant}>{status}</Badge>
      },
    },
    {
      accessorKey: "createdAt",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Creado
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const date = row.getValue("createdAt") as Date
        return (
          <div className="text-sm">
            {new Intl.DateTimeFormat('es-ES', {
              year: 'numeric',
              month: 'short',
              day: 'numeric'
            }).format(date)}
          </div>
        )
      },
    },
  ]
}
