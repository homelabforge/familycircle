import { Heart, Github, ExternalLink } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'

export default function About() {
  const { bigMode } = useBigMode()

  return (
    <div className="container mx-auto px-4 py-6">
      <BackButton />

      <div className="mt-4">
        <div className="flex items-center gap-4 mb-8">
          <Heart className={`text-primary ${bigMode ? 'w-14 h-14' : 'w-12 h-12'}`} />
          <div>
            <h1
              className={`
                font-bold text-fc-text
                ${bigMode ? 'text-3xl' : 'text-2xl'}
              `}
            >
              Family<span className="text-primary">Circle</span>
            </h1>
            <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
              Version 1.0.0
            </p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Description */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
            <h2
              className={`
                font-semibold text-fc-text mb-3
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              About
            </h2>
            <p className={`text-fc-text-muted ${bigMode ? 'text-lg leading-relaxed' : 'leading-relaxed'}`}>
              FamilyCircle is a family event coordination platform designed specifically for
              elderly users who need simple, password-free access to manage family gatherings,
              Secret Santa exchanges, and potluck dinners.
            </p>
          </div>

          {/* Features */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
            <h2
              className={`
                font-semibold text-fc-text mb-3
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              Features
            </h2>
            <ul className={`space-y-2 text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
              <li className="flex items-center gap-2">
                <span className="text-primary">•</span>
                Magic link authentication - no passwords needed
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary">•</span>
                Secret Santa with smart assignment algorithm
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary">•</span>
                Potluck coordination with dietary tracking
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary">•</span>
                Simple RSVP tracking
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary">•</span>
                Gift wishlists
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary">•</span>
                Anonymous messaging
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary">•</span>
                Big Mode for enhanced readability
              </li>
            </ul>
          </div>

          {/* Links */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
            <h2
              className={`
                font-semibold text-fc-text mb-3
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              Links
            </h2>
            <div className="space-y-3">
              <a
                href="https://www.homelabforge.io"
                target="_blank"
                rel="noopener noreferrer"
                className={`
                  flex items-center gap-2 text-primary hover:text-primary-hover transition-colors
                  ${bigMode ? 'text-lg' : ''}
                `}
              >
                <ExternalLink className="w-5 h-5" />
                HomeLabForge Website
              </a>
              <a
                href="https://github.com/homelabforge"
                target="_blank"
                rel="noopener noreferrer"
                className={`
                  flex items-center gap-2 text-primary hover:text-primary-hover transition-colors
                  ${bigMode ? 'text-lg' : ''}
                `}
              >
                <Github className="w-5 h-5" />
                GitHub Repository
              </a>
            </div>
          </div>

          {/* License */}
          <div className="text-center text-fc-text-muted py-4">
            <p className={bigMode ? 'text-base' : 'text-sm'}>
              MIT License • Made with ❤️ by HomeLabForge
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
