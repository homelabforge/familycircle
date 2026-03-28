import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, ArrowRight, CheckCircle, Eye, EyeOff, Shield, Copy, Check } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '@/contexts/AuthContext'
import { useBigMode } from '@/contexts/BigModeContext'
import { useTheme } from '@/contexts/ThemeContext'
import { setupSchema, type SetupInput } from '@/lib/schemas'
import { settingsApi } from '@/lib/api'
import type { z } from 'zod'

type SetupFormValues = z.input<typeof setupSchema>

function PasswordInput({
  value,
  onChange,
  placeholder,
  hasError,
  show,
  onToggleShow,
  autoFocus,
  inputClassName,
  inputErrorClassName,
}: {
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder: string
  hasError: boolean
  show: boolean
  onToggleShow: () => void
  autoFocus?: boolean
  inputClassName: string
  inputErrorClassName: string
}) {
  return (
    <div className="relative">
      <input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={hasError ? inputErrorClassName : inputClassName}
      />
      <button
        type="button"
        tabIndex={-1}
        onMouseDown={(e) => e.preventDefault()}
        onClick={onToggleShow}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-fc-muted hover:text-fc-text"
      >
        {show ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
      </button>
    </div>
  )
}

export default function Setup() {
  const navigate = useNavigate()
  const { setup } = useAuth()
  const { bigMode } = useBigMode()
  const { theme } = useTheme()

  const [step, setStep] = useState(1)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [familyCode, setFamilyCode] = useState('')
  const [copied, setCopied] = useState(false)

  const {
    watch,
    setValue,
    setError: setFieldError,
    clearErrors,
    handleSubmit,
    formState: { errors, isSubmitting, isSubmitted },
  } = useForm<SetupFormValues>({
    resolver: zodResolver(setupSchema),
    defaultValues: {
      display_name: '',
      email: '',
      password: '',
      confirmPassword: '',
      family_name: '',
    },
  })

  const values = watch()

  const handleStepSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (step === 1) {
      // Validate family name only
      if (!values.family_name.trim()) {
        setFieldError('family_name', { message: 'Please enter your family name' })
        return
      }
      clearErrors()
      setStep(2)
      return
    }

    if (step === 2) {
      // Validate display name only
      if (!values.display_name.trim()) {
        setFieldError('display_name', { message: 'Please enter your name' })
        return
      }
      clearErrors()
      setStep(3)
      return
    }

    if (step === 3) {
      // Validate email only
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!values.email.trim()) {
        setFieldError('email', { message: 'Please enter your email' })
        return
      }
      if (!emailRegex.test(values.email)) {
        setFieldError('email', { message: 'Please enter a valid email address' })
        return
      }
      clearErrors()
      setStep(4)
      return
    }

    // Step 4: Full validation and submit
    await handleSubmit(async (data: SetupInput) => {
      setError('')
      try {
        const result = await setup(data.email, data.password, data.display_name, data.family_name)
        setFamilyCode(result.familyCode)

        // Sync current local preferences to the new account
        try {
          await settingsApi.updateUserPreferences({ theme, big_mode: bigMode })
        } catch {
          // Ignore - preferences will use defaults
        }

        setStep(5) // Success step
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Setup failed')
      }
    })(e)
  }

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(familyCode)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = familyCode
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const inputClass = `
    w-full px-4 py-3 rounded-xl
    bg-fc-surface border border-fc-border
    text-fc-text placeholder:text-fc-muted
    focus:outline-none focus:ring-2 focus:ring-fc-primary/50
    ${bigMode ? 'text-xl' : 'text-base'}
  `

  const inputErrorClass = `
    w-full px-4 py-3 rounded-xl
    bg-fc-surface border border-error
    text-fc-text placeholder:text-fc-muted
    focus:outline-none focus:ring-2 focus:ring-error/50
    ${bigMode ? 'text-xl' : 'text-base'}
  `

  const buttonClass = `
    w-full py-3 rounded-xl font-semibold
    bg-primary text-white
    hover:bg-primary-hover transition-colors
    flex items-center justify-center gap-2
    ${bigMode ? 'text-xl' : 'text-base'}
    disabled:opacity-50 disabled:cursor-not-allowed
  `

  const errorTextClass = `text-error ${bigMode ? 'text-sm' : 'text-xs'} mt-1`

  // Success step - show family code
  if (step === 5) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-fc-bg px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-green-500/20 mb-4">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h1 className={`font-bold text-fc-text ${bigMode ? 'text-3xl' : 'text-2xl'}`}>
              Welcome, {values.display_name}!
            </h1>
            <p className={`text-fc-muted mt-2 ${bigMode ? 'text-lg' : 'text-base'}`}>
              Your family circle is ready
            </p>
          </div>

          {/* Family code card */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
            <h2 className={`font-semibold text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-base'}`}>
              Your Family Code
            </h2>
            <p className={`text-fc-muted mb-4 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Share this code with family members so they can join your circle
            </p>
            <div className="flex items-center gap-2">
              <div className={`
                flex-1 px-4 py-3 rounded-xl bg-fc-bg border-2 border-dashed border-fc-border
                font-mono font-bold text-center tracking-wider
                ${bigMode ? 'text-2xl' : 'text-xl'}
              `}>
                {familyCode}
              </div>
              <button
                type="button"
                onClick={handleCopyCode}
                className={`
                  p-3 rounded-xl
                  ${copied ? 'bg-green-500/20 text-green-500' : 'bg-fc-primary/20 text-fc-primary'}
                  hover:opacity-80 transition-all
                `}
              >
                {copied ? <Check className="w-6 h-6" /> : <Copy className="w-6 h-6" />}
              </button>
            </div>
            {copied && (
              <p className={`text-green-500 text-center mt-2 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                Copied to clipboard!
              </p>
            )}
          </div>

          <button onClick={() => navigate('/')} className={buttonClass}>
            Go to Dashboard
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-fc-bg px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-fc-primary/10 mb-4">
            <Users className="w-8 h-8 text-fc-primary" />
          </div>
          <h1 className={`font-bold text-fc-text ${bigMode ? 'text-3xl' : 'text-2xl'}`}>
            Welcome to FamilyCircle
          </h1>
          <p className={`text-fc-muted mt-2 ${bigMode ? 'text-lg' : 'text-base'}`}>
            Let's set up your family circle
          </p>
        </div>

        {/* Super admin notice */}
        <div className="mb-6 p-4 rounded-xl bg-fc-primary/10 border border-fc-primary/20">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-fc-primary flex-shrink-0 mt-0.5" />
            <div>
              <p className={`font-semibold text-fc-primary ${bigMode ? 'text-base' : 'text-sm'}`}>
                You're creating the admin account
              </p>
              <p className={`text-fc-text mt-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                As the first user, you'll have full administrator access to manage all families and settings.
              </p>
            </div>
          </div>
        </div>

        {/* Progress indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={`
                w-10 h-10 rounded-full flex items-center justify-center
                ${s < step ? 'bg-primary text-white' : ''}
                ${s === step ? 'bg-primary/20 text-primary border-2 border-primary' : ''}
                ${s > step ? 'bg-fc-surface text-fc-muted' : ''}
                ${bigMode ? 'text-lg' : 'text-sm'}
              `}
            >
              {s < step ? <CheckCircle className="w-5 h-5" /> : s}
            </div>
          ))}
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400">
            {error}
          </div>
        )}

        <form onSubmit={handleStepSubmit} className="space-y-4">
          {/* Step 1: Family Name */}
          {step === 1 && (
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                What's your family name?
              </label>
              <input
                type="text"
                value={values.family_name}
                onChange={(e) => setValue('family_name', e.target.value)}
                placeholder="The Smith Family"
                autoFocus
                className={errors.family_name ? inputErrorClass : inputClass}
              />
              {errors.family_name && <p className={errorTextClass}>{errors.family_name.message}</p>}
              {!errors.family_name && (
                <p className={`text-fc-muted mt-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  This will be the name of your family circle
                </p>
              )}
            </div>
          )}

          {/* Step 2: Display Name */}
          {step === 2 && (
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                What's your name?
              </label>
              <input
                type="text"
                value={values.display_name}
                onChange={(e) => setValue('display_name', e.target.value)}
                placeholder="Your name"
                autoFocus
                className={errors.display_name ? inputErrorClass : inputClass}
              />
              {errors.display_name && <p className={errorTextClass}>{errors.display_name.message}</p>}
              {!errors.display_name && (
                <p className={`text-fc-muted mt-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  This is how family members will see you
                </p>
              )}
            </div>
          )}

          {/* Step 3: Email */}
          {step === 3 && (
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                What's your email?
              </label>
              <input
                type="email"
                value={values.email}
                onChange={(e) => setValue('email', e.target.value)}
                placeholder="you@email.com"
                autoFocus
                className={errors.email ? inputErrorClass : inputClass}
              />
              {errors.email && <p className={errorTextClass}>{errors.email.message}</p>}
              {!errors.email && (
                <p className={`text-fc-muted mt-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  We'll use this for login and notifications
                </p>
              )}
            </div>
          )}

          {/* Step 4: Password */}
          {step === 4 && (
            <>
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                  Create a password
                </label>
                <PasswordInput
                  value={values.password}
                  onChange={(e) => setValue('password', e.target.value)}
                  placeholder="At least 6 characters"
                  hasError={!!(isSubmitted && errors.password)}
                  show={showPassword}
                  onToggleShow={() => setShowPassword(!showPassword)}
                  autoFocus
                  inputClassName={inputClass}
                  inputErrorClassName={inputErrorClass}
                />
                {isSubmitted && errors.password && (
                  <p className={errorTextClass}>{errors.password.message}</p>
                )}
              </div>
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                  Confirm password
                </label>
                <PasswordInput
                  value={values.confirmPassword}
                  onChange={(e) => setValue('confirmPassword', e.target.value)}
                  placeholder="Confirm your password"
                  hasError={!!(isSubmitted && errors.confirmPassword)}
                  show={showConfirmPassword}
                  onToggleShow={() => setShowConfirmPassword(!showConfirmPassword)}
                  inputClassName={inputClass}
                  inputErrorClassName={inputErrorClass}
                />
                {isSubmitted && errors.confirmPassword && (
                  <p className={errorTextClass}>{errors.confirmPassword.message}</p>
                )}
              </div>
              <p className={`text-fc-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                As the administrator, you'll need a password to manage your family circle
              </p>
            </>
          )}

          <button type="submit" disabled={isSubmitting} className={buttonClass}>
            {step < 4 ? 'Continue' : isSubmitting ? 'Setting up...' : 'Create Family Circle'}
            <ArrowRight className="w-5 h-5" />
          </button>

          {step > 1 && (
            <button
              type="button"
              onClick={() => {
                clearErrors()
                setStep(step - 1)
              }}
              className={`
                w-full py-3 rounded-xl font-semibold
                text-fc-muted hover:text-fc-text transition-colors
                ${bigMode ? 'text-xl' : 'text-base'}
              `}
            >
              Back
            </button>
          )}
        </form>
      </div>
    </div>
  )
}
