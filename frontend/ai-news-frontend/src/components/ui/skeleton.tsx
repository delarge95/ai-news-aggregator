import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const skeletonVariants = cva(
  "animate-pulse rounded-md bg-muted",
  {
    variants: {
      variant: {
        default: "bg-muted",
        secondary: "bg-muted-foreground/10",
        accent: "bg-accent",
        destructive: "bg-destructive/10",
      },
      size: {
        sm: "h-4",
        md: "h-6",
        lg: "h-8",
        xl: "h-12",
        "2xl": "h-16",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

export interface SkeletonProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof skeletonVariants> {}

function Skeleton({
  className,
  variant,
  size,
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(skeletonVariants({ variant, size }), className)}
      {...props}
    />
  )
}

// Text line skeleton for loading text content
function TextLineSkeleton({ 
  lines = 3, 
  width = "100%", 
  height = "1rem", 
  gap = "0.5rem" 
}: {
  lines?: number
  width?: string
  height?: string
  gap?: string
}) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={cn(
            index === lines - 1 ? "w-3/4" : "w-full"
          )}
          style={{ height }}
        />
      ))}
    </div>
  )
}

// Card skeleton for loading card content
function CardSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-48 w-full" />
      <div className="space-y-2">
        <Skeleton className="h-6 w-3/4" />
        <TextLineSkeleton lines={2} height="1rem" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-6 w-20" />
      </div>
    </div>
  )
}

// Table row skeleton for loading table rows
function TableRowSkeleton({ 
  columns = 4, 
  height = "2.5rem" 
}: { 
  columns?: number 
  height?: string 
}) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, index) => (
        <td key={index} className="px-4 py-2">
          <Skeleton 
            className={cn(
              index === 0 ? "h-4 w-24" : "h-4 w-full",
              index === columns - 1 && "w-16"
            )}
            style={{ height }}
          />
        </td>
      ))}
    </tr>
  )
}

export { 
  Skeleton, 
  TextLineSkeleton, 
  CardSkeleton, 
  TableRowSkeleton, 
  skeletonVariants 
}
