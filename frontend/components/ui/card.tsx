import { type HTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  header?: string
  headerRight?: React.ReactNode
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, header, headerRight, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('panel flex flex-col', className)}
        {...props}
      >
        {header && (
          <div className="panel-header">
            <span>{header}</span>
            {headerRight && <span>{headerRight}</span>}
          </div>
        )}
        <div className="panel-body">{children}</div>
      </div>
    )
  },
)
Card.displayName = 'Card'

interface CardContentProps extends HTMLAttributes<HTMLDivElement> {
  padding?: boolean
}

const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, padding = true, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(padding && 'panel-body', className)}
        {...props}
      >
        {children}
      </div>
    )
  },
)
CardContent.displayName = 'CardContent'

export { Card, CardContent }
