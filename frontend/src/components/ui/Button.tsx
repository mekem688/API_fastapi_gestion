import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { Loader2 } from 'lucide-react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'
type Size    = 'sm' | 'md' | 'lg'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
}

const cls: Record<Variant, string> = {
  primary:   'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800',
  secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50',
  danger:    'bg-red-600 text-white hover:bg-red-700',
  ghost:     'text-gray-600 hover:bg-gray-100',
}
const sizes: Record<Size, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-9 px-4 text-sm',
  lg: 'h-11 px-6 text-base',
}

const Button = forwardRef<HTMLButtonElement, Props>(
  ({ variant = 'primary', size = 'md', loading, children, className = '', disabled, ...rest }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium
        transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1
        disabled:opacity-50 disabled:cursor-not-allowed
        ${cls[variant]} ${sizes[size]} ${className}`}
      {...rest}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  ),
)
Button.displayName = 'Button'
export default Button
