import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { CheckCircle, XCircle, AlertCircle, Info, AlertTriangle, Clock, User, Tag, Star } from "lucide-react"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground border-border",
        success:
          "border-transparent bg-green-500 text-white hover:bg-green-500/80",
        warning:
          "border-transparent bg-yellow-500 text-white hover:bg-yellow-500/80",
        info:
          "border-transparent bg-blue-500 text-white hover:bg-blue-500/80",
      },
      size: {
        sm: "px-2 py-0.5 text-xs",
        md: "px-2.5 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode
  showIcon?: boolean
}

function Badge({ 
  className, 
  variant, 
  size, 
  icon, 
  showIcon = false, 
  children, 
  ...props 
}: BadgeProps) {
  const getDefaultIcon = () => {
    if (showIcon) {
      switch (variant) {
        case "success":
          return <CheckCircle className="h-3 w-3" />
        case "destructive":
          return <XCircle className="h-3 w-3" />
        case "warning":
          return <AlertTriangle className="h-3 w-3" />
        case "info":
          return <Info className="h-3 w-3" />
        default:
          return <Tag className="h-3 w-3" />
      }
    }
    return null
  }

  const iconElement = icon || (showIcon ? getDefaultIcon() : null)

  return (
    <div className={cn(badgeVariants({ variant, size }), className)} {...props}>
      {iconElement && <span className="mr-1">{iconElement}</span>}
      {children}
    </div>
  )
}

export { Badge, badgeVariants }