import { useState } from "react"

// Hook para manejo de formularios con validación
export function useForm<T extends Record<string, any>>(initialValues: T) {
  const [values, setValues] = useState<T>(initialValues)
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const setValue = (name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }))
    // Limpiar error cuando el usuario empiece a escribir
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }

  const setError = (name: keyof T, error: string) => {
    setErrors(prev => ({ ...prev, [name]: error }))
  }

  const reset = () => {
    setValues(initialValues)
    setErrors({})
    setIsSubmitting(false)
  }

  const handleSubmit = async (onSubmit: (values: T) => Promise<void> | void) => {
    setIsSubmitting(true)
    try {
      await onSubmit(values)
    } finally {
      setIsSubmitting(false)
    }
  }

  return {
    values,
    errors,
    isSubmitting,
    setValue,
    setError,
    reset,
    handleSubmit,
  }
}

// Hook para manejo de modal/dialog
export function useDialog() {
  const [isOpen, setIsOpen] = useState(false)

  const open = () => setIsOpen(true)
  const close = () => setIsOpen(false)
  const toggle = () => setIsOpen(prev => !prev)

  return {
    isOpen,
    open,
    close,
    toggle,
  }
}

// Hook para manejo de loading states
export function useLoading() {
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState<string>("")

  const startLoading = (message = "Cargando...") => {
    setIsLoading(true)
    setLoadingMessage(message)
  }

  const stopLoading = () => {
    setIsLoading(false)
    setLoadingMessage("")
  }

  return {
    isLoading,
    loadingMessage,
    startLoading,
    stopLoading,
  }
}

// Hook para manejo de toast notifications
export function useToast() {
  const showSuccess = (message: string) => {
    // Importar dinámicamente para evitar problemas de circular dependency
    import('sonner').then(({ toast }) => {
      toast.success(message)
    })
  }

  const showError = (message: string) => {
    import('sonner').then(({ toast }) => {
      toast.error(message)
    })
  }

  const showWarning = (message: string) => {
    import('sonner').then(({ toast }) => {
      toast.warning(message)
    })
  }

  const showInfo = (message: string) => {
    import('sonner').then(({ toast }) => {
      toast.info(message)
    })
  }

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
  }
}

// Hook para manejo de tablas con data
export function useDataTable<T>(data: T[], initialPageSize = 10) {
  const [pageIndex, setPageIndex] = useState(0)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [sorting, setSorting] = useState<Array<{ id: string; desc: boolean }>>([])
  const [columnFilters, setColumnFilters] = useState<Array<{ id: string; value: string }>>([])

  const filteredData = data.filter(item => {
    // Aplicar filtros de columnas
    return columnFilters.every(filter => {
      const value = (item as any)[filter.id]
      return value?.toString().toLowerCase().includes(filter.value.toLowerCase())
    })
  })

  const sortedData = [...filteredData].sort((a, b) => {
    return sorting.reduce((result, sort) => {
      if (result !== 0) return result
      
      const aValue = (a as any)[sort.id]
      const bValue = (b as any)[sort.id]
      
      if (aValue < bValue) return sort.desc ? 1 : -1
      if (aValue > bValue) return sort.desc ? -1 : 1
      return 0
    }, 0)
  })

  const startIndex = pageIndex * pageSize
  const endIndex = startIndex + pageSize
  const paginatedData = sortedData.slice(startIndex, endIndex)

  const pageCount = Math.ceil(sortedData.length / pageSize)

  return {
    data: paginatedData,
    pageIndex,
    pageSize,
    sorting,
    columnFilters,
    setPageIndex,
    setPageSize,
    setSorting,
    setColumnFilters,
    pageCount,
    totalRows: sortedData.length,
  }
}
