import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'

export default function NotFound() {
  const { bigMode } = useBigMode()

  return (
    <div className="min-h-screen flex items-center justify-center bg-fc-bg px-4">
      <div className="text-center">
        <h1
          className={`font-bold text-fc-text mb-4 ${bigMode ? 'text-7xl' : 'text-6xl'}`}
        >
          404
        </h1>
        <h2
          className={`font-semibold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
        >
          Page Not Found
        </h2>
        <p className={`text-fc-text-muted mb-8 ${bigMode ? 'text-lg' : ''}`}>
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => window.history.back()}
            className={`
              flex items-center justify-center gap-2
              border border-fc-border text-fc-text rounded-xl
              hover:bg-fc-surface transition-colors
              ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
            `}
          >
            <ArrowLeft className="w-5 h-5" />
            Go Back
          </button>
          <Link
            to="/"
            className={`
              flex items-center justify-center gap-2
              bg-primary text-white rounded-xl
              hover:bg-primary-hover transition-colors
              ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
            `}
          >
            <Home className="w-5 h-5" />
            Go Home
          </Link>
        </div>
      </div>
    </div>
  )
}
