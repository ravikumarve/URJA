import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'font-data inline-flex items-center justify-center text-xs font-bold uppercase tracking-wider border-2 transition-all duration-200',
  {
    variants: {
      variant: {
        primary:
          'border-tactical-orange bg-tactical-orange text-void hover:bg-transparent hover:text-tactical-orange',
        outline:
          'border-border-hard bg-transparent text-sand-bright hover:border-sand-muted hover:bg-surface-mid',
        ghost:
          'border-transparent bg-transparent text-sand-muted hover:bg-surface-light hover:text-sand-bright',
      },
      size: {
        sm: 'h-8 px-3',
        md: 'h-10 px-5',
        lg: 'h-12 px-7 text-sm',
      },
    },
    defaultVariants: {
      variant: 'outline',
      size: 'md',
    },
  },
)

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  },
)
Button.displayName = 'Button'

export { Button, buttonVariants }
