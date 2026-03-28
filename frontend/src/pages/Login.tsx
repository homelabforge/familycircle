import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Users, Mail, KeyRound, UserPlus, ArrowRight, Eye, EyeOff, Lock } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '@/contexts/AuthContext'
import { useBigMode } from '@/contexts/BigModeContext'
import {
  loginSchema,
  registerSchema,
  forgotPasswordSchema,
  resetPasswordSchema,
  type LoginInput,
  type RegisterInput,
  type ForgotPasswordInput,
  type ResetPasswordInput,
} from '@/lib/schemas'
import type { z } from 'zod'

type View = 'main' | 'login' | 'register' | 'forgot' | 'reset'

type RegisterFormValues = z.input<typeof registerSchema>
type ResetFormValues = z.input<typeof resetPasswordSchema>

// Password input component - defined outside to prevent re-renders
function PasswordInput({
  value,
  onChange,
  placeholder,
  inputClassName,
  show,
  onToggleShow,
}: {
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder: string
  inputClassName: string
  show: boolean
  onToggleShow: () => void
}) {
  return (
    <div className="relative">
      <input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={inputClassName}
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

export default function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login, register, forgotPassword, resetPassword } = useAuth()
  const { bigMode } = useBigMode()

  const [view, setView] = useState<View>(() => {
    // If reset token in URL, go to reset view
    return searchParams.get('reset_token') ? 'reset' : 'main'
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // Form hooks
  const loginForm = useForm<z.input<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })
  const registerForm = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      family_code: '',
      display_name: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  })
  const forgotForm = useForm<z.input<typeof forgotPasswordSchema>>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  })
  const resetForm = useForm<ResetFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: '', confirmPassword: '' },
  })

  // Get reset token from URL
  const resetToken = searchParams.get('reset_token')

  const handleLogin = loginForm.handleSubmit(async (data: LoginInput) => {
    setError('')
    try {
      await login(data.email, data.password)
      navigate('/')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Login failed')
    }
  })

  const handleRegister = registerForm.handleSubmit(async (data: RegisterInput) => {
    setError('')
    try {
      await register(data.family_code, data.email, data.password, data.display_name)
      navigate('/')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Registration failed')
    }
  })

  const handleForgotPassword = forgotForm.handleSubmit(async (data: ForgotPasswordInput) => {
    setError('')
    setSuccess('')
    try {
      const devToken = await forgotPassword(data.email)
      setSuccess('If an account exists with this email, a password reset link has been sent.')
      // In dev mode, auto-redirect with token
      if (devToken) {
        navigate(`/login?reset_token=${devToken}`)
        setView('reset')
        setSuccess('Dev mode: Using reset token directly')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to request password reset')
    }
  })

  const handleResetPassword = resetForm.handleSubmit(async (data: ResetPasswordInput) => {
    setError('')
    if (!resetToken) {
      setError('No reset token found. Please request a new password reset link.')
      return
    }
    try {
      await resetPassword(resetToken, data.password)
      navigate('/')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to reset password')
    }
  })

  const inputClass = `
    w-full px-4 py-3 rounded-xl
    bg-fc-surface border border-fc-border
    text-fc-text placeholder:text-fc-muted
    focus:outline-none focus:ring-2 focus:ring-primary/50
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
    hover:opacity-90 transition-opacity
    flex items-center justify-center gap-2
    ${bigMode ? 'text-xl' : 'text-base'}
    disabled:opacity-50 disabled:cursor-not-allowed
  `

  const secondaryButtonClass = `
    w-full py-3 rounded-xl font-semibold
    bg-primary text-white
    hover:opacity-90 transition-colors
    flex items-center justify-center gap-2
    ${bigMode ? 'text-xl' : 'text-base'}
  `

  const linkClass = `text-primary hover:underline ${bigMode ? 'text-lg' : 'text-sm'}`

  const errorTextClass = `text-error ${bigMode ? 'text-sm' : 'text-xs'} mt-1`

  const resetAndChangeView = (newView: View) => {
    setView(newView)
    setError('')
    setSuccess('')
    setShowPassword(false)
    setShowConfirmPassword(false)
    loginForm.reset()
    registerForm.reset()
    forgotForm.reset()
    resetForm.reset()
  }

  // Helper: show error only after form submission
  const fieldError = (
    formErrors: Record<string, { message?: string } | undefined>,
    field: string,
    isSubmitted: boolean,
  ): string | undefined => {
    return isSubmitted ? formErrors[field]?.message : undefined
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-fc-bg px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
            <Users className="w-8 h-8 text-primary" />
          </div>
          <h1 className={`font-bold text-fc-text ${bigMode ? 'text-3xl' : 'text-2xl'}`}>
            FamilyCircle
          </h1>
          <p className={`text-fc-muted mt-2 ${bigMode ? 'text-lg' : 'text-base'}`}>
            Family event coordination
          </p>
        </div>

        {/* Error/Success messages */}
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-4 rounded-xl bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400">
            {success}
          </div>
        )}

        {/* Main menu */}
        {view === 'main' && (
          <div className="space-y-4">
            <button onClick={() => resetAndChangeView('login')} className={buttonClass}>
              <KeyRound className="w-5 h-5" />
              Sign In
            </button>
            <button onClick={() => resetAndChangeView('register')} className={secondaryButtonClass}>
              <UserPlus className="w-5 h-5" />
              Join a Family
            </button>
          </div>
        )}

        {/* Login form */}
        {view === 'login' && (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Email Address
              </label>
              <input
                type="email"
                value={loginForm.watch('email')}
                onChange={(e) => loginForm.setValue('email', e.target.value)}
                placeholder="you@family.com"
                className={fieldError(loginForm.formState.errors, 'email', loginForm.formState.isSubmitted) ? inputErrorClass : inputClass}
              />
              {fieldError(loginForm.formState.errors, 'email', loginForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{loginForm.formState.errors.email?.message}</p>
              )}
            </div>
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Password
              </label>
              <PasswordInput
                value={loginForm.watch('password')}
                onChange={(e) => loginForm.setValue('password', e.target.value)}
                placeholder="Your password"
                inputClassName={fieldError(loginForm.formState.errors, 'password', loginForm.formState.isSubmitted) ? inputErrorClass : inputClass}
                show={showPassword}
                onToggleShow={() => setShowPassword(!showPassword)}
              />
              {fieldError(loginForm.formState.errors, 'password', loginForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{loginForm.formState.errors.password?.message}</p>
              )}
            </div>
            <button type="submit" disabled={loginForm.formState.isSubmitting} className={buttonClass}>
              {loginForm.formState.isSubmitting ? 'Signing in...' : 'Sign In'}
              <ArrowRight className="w-5 h-5" />
            </button>
            <div className="text-center">
              <button
                type="button"
                onClick={() => resetAndChangeView('forgot')}
                className={linkClass}
              >
                Forgot your password?
              </button>
            </div>
            <button type="button" onClick={() => resetAndChangeView('main')} className={secondaryButtonClass}>
              Back
            </button>
          </form>
        )}

        {/* Register form */}
        {view === 'register' && (
          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Family Code
              </label>
              <input
                type="text"
                value={registerForm.watch('family_code')}
                onChange={(e) => registerForm.setValue('family_code', e.target.value.toUpperCase())}
                placeholder="ABCDEF-12"
                className={fieldError(registerForm.formState.errors, 'family_code', registerForm.formState.isSubmitted) ? inputErrorClass : inputClass}
              />
              {fieldError(registerForm.formState.errors, 'family_code', registerForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{registerForm.formState.errors.family_code?.message}</p>
              )}
              <p className={`text-fc-muted mt-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                Ask your family admin for the code
              </p>
            </div>
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Your Name
              </label>
              <input
                type="text"
                value={registerForm.watch('display_name')}
                onChange={(e) => registerForm.setValue('display_name', e.target.value)}
                placeholder="Grandma Rose"
                className={fieldError(registerForm.formState.errors, 'display_name', registerForm.formState.isSubmitted) ? inputErrorClass : inputClass}
              />
              {fieldError(registerForm.formState.errors, 'display_name', registerForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{registerForm.formState.errors.display_name?.message}</p>
              )}
            </div>
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Email Address
              </label>
              <input
                type="email"
                value={registerForm.watch('email')}
                onChange={(e) => registerForm.setValue('email', e.target.value)}
                placeholder="you@family.com"
                className={fieldError(registerForm.formState.errors, 'email', registerForm.formState.isSubmitted) ? inputErrorClass : inputClass}
              />
              {fieldError(registerForm.formState.errors, 'email', registerForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{registerForm.formState.errors.email?.message}</p>
              )}
            </div>
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Password
              </label>
              <PasswordInput
                value={registerForm.watch('password')}
                onChange={(e) => registerForm.setValue('password', e.target.value)}
                placeholder="At least 6 characters"
                inputClassName={fieldError(registerForm.formState.errors, 'password', registerForm.formState.isSubmitted) ? inputErrorClass : inputClass}
                show={showPassword}
                onToggleShow={() => setShowPassword(!showPassword)}
              />
              {fieldError(registerForm.formState.errors, 'password', registerForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{registerForm.formState.errors.password?.message}</p>
              )}
            </div>
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Confirm Password
              </label>
              <PasswordInput
                value={registerForm.watch('confirmPassword')}
                onChange={(e) => registerForm.setValue('confirmPassword', e.target.value)}
                placeholder="Confirm your password"
                inputClassName={fieldError(registerForm.formState.errors, 'confirmPassword', registerForm.formState.isSubmitted) ? inputErrorClass : inputClass}
                show={showConfirmPassword}
                onToggleShow={() => setShowConfirmPassword(!showConfirmPassword)}
              />
              {fieldError(registerForm.formState.errors, 'confirmPassword', registerForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{registerForm.formState.errors.confirmPassword?.message}</p>
              )}
            </div>
            <button type="submit" disabled={registerForm.formState.isSubmitting} className={buttonClass}>
              {registerForm.formState.isSubmitting ? 'Creating Account...' : 'Join Family'}
              <ArrowRight className="w-5 h-5" />
            </button>
            <div className="text-center">
              <span className={`text-fc-muted ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Already have an account?{' '}
              </span>
              <button
                type="button"
                onClick={() => resetAndChangeView('login')}
                className={linkClass}
              >
                Sign in
              </button>
            </div>
            <button type="button" onClick={() => resetAndChangeView('main')} className={secondaryButtonClass}>
              Back
            </button>
          </form>
        )}

        {/* Forgot password form */}
        {view === 'forgot' && (
          <form onSubmit={handleForgotPassword} className="space-y-4">
            <div className="text-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-2">
                <Mail className="w-6 h-6 text-primary" />
              </div>
              <h2 className={`font-semibold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
                Reset Password
              </h2>
              <p className={`text-fc-muted mt-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Enter your email and we&apos;ll send you a reset link
              </p>
            </div>
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Email Address
              </label>
              <input
                type="email"
                value={forgotForm.watch('email')}
                onChange={(e) => forgotForm.setValue('email', e.target.value)}
                placeholder="you@family.com"
                className={fieldError(forgotForm.formState.errors, 'email', forgotForm.formState.isSubmitted) ? inputErrorClass : inputClass}
              />
              {fieldError(forgotForm.formState.errors, 'email', forgotForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{forgotForm.formState.errors.email?.message}</p>
              )}
            </div>
            <button type="submit" disabled={forgotForm.formState.isSubmitting} className={buttonClass}>
              {forgotForm.formState.isSubmitting ? 'Sending...' : 'Send Reset Link'}
              <ArrowRight className="w-5 h-5" />
            </button>
            <button type="button" onClick={() => resetAndChangeView('login')} className={secondaryButtonClass}>
              Back to Sign In
            </button>
          </form>
        )}

        {/* Reset password form */}
        {view === 'reset' && (
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div className="text-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-2">
                <Lock className="w-6 h-6 text-primary" />
              </div>
              <h2 className={`font-semibold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
                Set New Password
              </h2>
              <p className={`text-fc-muted mt-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Enter your new password below
              </p>
            </div>
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                New Password
              </label>
              <PasswordInput
                value={resetForm.watch('password')}
                onChange={(e) => resetForm.setValue('password', e.target.value)}
                placeholder="At least 6 characters"
                inputClassName={fieldError(resetForm.formState.errors, 'password', resetForm.formState.isSubmitted) ? inputErrorClass : inputClass}
                show={showPassword}
                onToggleShow={() => setShowPassword(!showPassword)}
              />
              {fieldError(resetForm.formState.errors, 'password', resetForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{resetForm.formState.errors.password?.message}</p>
              )}
            </div>
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
                Confirm New Password
              </label>
              <PasswordInput
                value={resetForm.watch('confirmPassword')}
                onChange={(e) => resetForm.setValue('confirmPassword', e.target.value)}
                placeholder="Confirm your new password"
                inputClassName={fieldError(resetForm.formState.errors, 'confirmPassword', resetForm.formState.isSubmitted) ? inputErrorClass : inputClass}
                show={showConfirmPassword}
                onToggleShow={() => setShowConfirmPassword(!showConfirmPassword)}
              />
              {fieldError(resetForm.formState.errors, 'confirmPassword', resetForm.formState.isSubmitted) && (
                <p className={errorTextClass}>{resetForm.formState.errors.confirmPassword?.message}</p>
              )}
            </div>
            <button type="submit" disabled={resetForm.formState.isSubmitting} className={buttonClass}>
              {resetForm.formState.isSubmitting ? 'Resetting...' : 'Reset Password'}
              <ArrowRight className="w-5 h-5" />
            </button>
            <button type="button" onClick={() => resetAndChangeView('login')} className={secondaryButtonClass}>
              Back to Sign In
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
