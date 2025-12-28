import { useBigMode } from '@/contexts/BigModeContext'

interface FormFieldProps {
  label: string
  error?: string
  children: React.ReactNode
  required?: boolean
  hint?: string
}

export default function FormField({ label, error, children, required, hint }: FormFieldProps) {
  const { bigMode } = useBigMode()

  return (
    <div className="space-y-1">
      <label className={`block font-medium text-fc-text ${bigMode ? 'text-lg' : 'text-sm'}`}>
        {label}
        {required && <span className="text-error ml-1">*</span>}
      </label>
      {children}
      {hint && !error && (
        <p className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>{hint}</p>
      )}
      {error && (
        <p className={`text-error ${bigMode ? 'text-sm' : 'text-xs'}`}>{error}</p>
      )}
    </div>
  )
}
