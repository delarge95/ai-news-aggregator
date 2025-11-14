import * as React from "react"
import { Search, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "./input"
import { Button } from "./button"

export interface SearchInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  error?: string
  onClear?: () => void
  clearable?: boolean
  loading?: boolean
}

const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  ({ className, error, onClear, clearable = true, loading = false, value, ...props }, ref) => {
    const [internalValue, setInternalValue] = React.useState(value || "")
    const hasValue = (value || internalValue) && (value || internalValue).toString().length > 0

    React.useEffect(() => {
      setInternalValue(value || "")
    }, [value])

    const handleClear = () => {
      if (onClear) {
        onClear()
      } else {
        setInternalValue("")
      }
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setInternalValue(e.target.value)
      if (props.onChange) {
        props.onChange(e)
      }
    }

    return (
      <div className="relative space-y-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={ref}
            type="search"
            className={cn(
              "pl-10",
              clearable && hasValue && "pr-10",
              error && "border-destructive focus-visible:ring-destructive",
              className
            )}
            value={value || internalValue}
            onChange={handleChange}
            {...props}
          />
          {loading && (
            <div className="absolute right-8 top-1/2 h-4 w-4 -translate-y-1/2">
              <div className="animate-spin rounded-full border-2 border-current border-t-transparent" />
            </div>
          )}
          {clearable && hasValue && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2"
              onClick={handleClear}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}
      </div>
    )
  }
)
SearchInput.displayName = "SearchInput"

export { SearchInput }