import * as React from "react"
import { Calendar } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "./input"
import { Button } from "./button"
import { Popover, PopoverContent, PopoverTrigger } from "./popover"
import { Calendar as CalendarComponent } from "./calendar"
import { format } from "date-fns"
import { es } from "date-fns/locale"

export interface DateInputProps {
  value?: Date
  onChange?: (date: Date | undefined) => void
  placeholder?: string
  error?: string
  disabled?: boolean
  className?: string
  format?: string
  minDate?: Date
  maxDate?: Date
}

const DateInput = React.forwardRef<HTMLButtonElement, DateInputProps>(
  ({ 
    value, 
    onChange, 
    placeholder = "Seleccionar fecha",
    error,
    disabled,
    className,
    format: formatString = "dd/MM/yyyy",
    minDate,
    maxDate,
    ...props 
  }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false)
    const [selectedDate, setSelectedDate] = React.useState<Date | undefined>(value)

    React.useEffect(() => {
      setSelectedDate(value)
    }, [value])

    const handleDateChange = (date: Date | undefined) => {
      setSelectedDate(date)
      onChange?.(date)
      setIsOpen(false)
    }

    const formatDate = (date: Date | undefined) => {
      if (!date) return ""
      return format(date, formatString, { locale: es })
    }

    return (
      <div className="space-y-2">
        <Popover open={isOpen} onOpenChange={setIsOpen}>
          <PopoverTrigger asChild>
            <Button
              ref={ref}
              variant="outline"
              className={cn(
                "w-full justify-start text-left font-normal",
                !selectedDate && "text-muted-foreground",
                error && "border-destructive",
                className
              )}
              disabled={disabled}
              {...props}
            >
              <Calendar className="mr-2 h-4 w-4" />
              {selectedDate ? formatDate(selectedDate) : placeholder}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <CalendarComponent
              mode="single"
              selected={selectedDate}
              onSelect={handleDateChange}
              disabled={(date) => {
                if (minDate && date < minDate) return true
                if (maxDate && date > maxDate) return true
                return false
              }}
              initialFocus
              locale={es}
            />
          </PopoverContent>
        </Popover>
        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}
      </div>
    )
  }
)
DateInput.displayName = "DateInput"

export { DateInput }