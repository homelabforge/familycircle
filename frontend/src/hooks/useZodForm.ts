import { useState, useCallback } from 'react'
import { z } from 'zod'

export interface FieldErrors {
  [key: string]: string | undefined
}

export interface UseZodFormResult<T> {
  /** Current form values */
  values: T
  /** Field-level error messages */
  errors: FieldErrors
  /** Whether the form has been submitted at least once */
  touched: boolean
  /** Whether the form is currently submitting */
  submitting: boolean
  /** Update a single field value */
  setValue: <K extends keyof T>(field: K, value: T[K]) => void
  /** Update multiple field values at once */
  setValues: (values: Partial<T>) => void
  /** Reset form to initial values and clear errors */
  reset: (newValues?: T) => void
  /** Validate and submit the form */
  handleSubmit: (onSubmit: (data: T) => Promise<void>) => (e?: React.FormEvent) => Promise<void>
  /** Validate a single field */
  validateField: <K extends keyof T>(field: K) => boolean
  /** Validate all fields without submitting */
  validate: () => boolean
  /** Clear all errors */
  clearErrors: () => void
  /** Set a specific field error manually */
  setFieldError: (field: string, message: string) => void
}

export function useZodForm<T extends z.ZodType>(
  schema: T,
  initialValues: z.infer<T>
): UseZodFormResult<z.infer<T>> {
  type FormValues = z.infer<T>

  const [values, setValuesState] = useState<FormValues>(initialValues)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [touched, setTouched] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const setValue = useCallback(<K extends keyof FormValues>(field: K, value: FormValues[K]) => {
    setValuesState((prev) => ({ ...(prev as object), [field]: value }) as FormValues)
    // Clear field error when user starts typing
    setErrors((prev) => {
      if (prev[field as string]) {
        const next = { ...prev }
        delete next[field as string]
        return next
      }
      return prev
    })
  }, [])

  const setValues = useCallback((newValues: Partial<FormValues>) => {
    setValuesState((prev) => ({ ...(prev as object), ...newValues }) as FormValues)
  }, [])

  const reset = useCallback((newValues?: FormValues) => {
    setValuesState(newValues ?? initialValues)
    setErrors({})
    setTouched(false)
  }, [initialValues])

  const clearErrors = useCallback(() => {
    setErrors({})
  }, [])

  const setFieldError = useCallback((field: string, message: string) => {
    setErrors((prev) => ({ ...prev, [field]: message }))
  }, [])

  const validate = useCallback((): boolean => {
    const result = schema.safeParse(values)
    if (result.success) {
      setErrors({})
      return true
    }

    const fieldErrors: FieldErrors = {}
    for (const issue of result.error.issues) {
      const path = issue.path.join('.')
      if (!fieldErrors[path]) {
        fieldErrors[path] = issue.message
      }
    }
    setErrors(fieldErrors)
    return false
  }, [schema, values])

  const validateField = useCallback(<K extends keyof FormValues>(field: K): boolean => {
    const result = schema.safeParse(values)
    if (result.success) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field as string]
        return next
      })
      return true
    }

    const fieldError = result.error.issues.find(
      (issue) => issue.path[0] === field
    )
    if (fieldError) {
      setErrors((prev) => ({ ...prev, [field as string]: fieldError.message }))
      return false
    }

    setErrors((prev) => {
      const next = { ...prev }
      delete next[field as string]
      return next
    })
    return true
  }, [schema, values])

  const handleSubmit = useCallback(
    (onSubmit: (data: FormValues) => Promise<void>) =>
      async (e?: React.FormEvent) => {
        e?.preventDefault()
        setTouched(true)

        const result = schema.safeParse(values)
        if (!result.success) {
          const fieldErrors: FieldErrors = {}
          for (const issue of result.error.issues) {
            const path = issue.path.join('.')
            if (!fieldErrors[path]) {
              fieldErrors[path] = issue.message
            }
          }
          setErrors(fieldErrors)
          return
        }

        setErrors({})
        setSubmitting(true)
        try {
          await onSubmit(result.data)
        } finally {
          setSubmitting(false)
        }
      },
    [schema, values]
  )

  return {
    values,
    errors,
    touched,
    submitting,
    setValue,
    setValues,
    reset,
    handleSubmit,
    validateField,
    validate,
    clearErrors,
    setFieldError,
  }
}

/**
 * Helper component props for form fields with validation
 */
export interface FormFieldProps {
  error?: string
  touched?: boolean
}

/**
 * Get error message for a field if touched
 */
export function getFieldError(
  errors: FieldErrors,
  field: string,
  touched: boolean
): string | undefined {
  return touched ? errors[field] : undefined
}
