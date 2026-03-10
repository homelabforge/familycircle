import { useState, useRef, useCallback, useEffect } from 'react'
import { useBigMode } from '@/contexts/BigModeContext'
import { familyApi, type FamilyMember } from '@/lib/api'

interface MentionInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  rows?: number
  maxLength?: number
  className?: string
}

export default function MentionInput({
  value,
  onChange,
  placeholder = 'Write a comment...',
  rows = 2,
  maxLength = 5000,
  className = '',
}: MentionInputProps) {
  const { bigMode } = useBigMode()
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [members, setMembers] = useState<FamilyMember[]>([])
  const [suggestions, setSuggestions] = useState<FamilyMember[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [mentionStart, setMentionStart] = useState(-1)
  const [selectedIndex, setSelectedIndex] = useState(0)

  // Load family members on mount
  useEffect(() => {
    familyApi.listMembers().then((res) => setMembers(res.members)).catch(() => {})
  }, [])

  const findMentionContext = useCallback(
    (text: string, cursorPos: number) => {
      // Look backwards from cursor for '@'
      const before = text.slice(0, cursorPos)
      const atIndex = before.lastIndexOf('@')
      if (atIndex === -1) return null

      // '@' must be at start or preceded by whitespace
      if (atIndex > 0 && !/\s/.test(before[atIndex - 1])) return null

      const query = before.slice(atIndex + 1).toLowerCase()
      // Don't show suggestions if query is too long or contains newlines
      if (query.length > 30 || query.includes('\n')) return null

      return { atIndex, query }
    },
    []
  )

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    onChange(newValue)

    const cursorPos = e.target.selectionStart
    const ctx = findMentionContext(newValue, cursorPos)

    if (ctx) {
      const filtered = members.filter((m) =>
        m.display_name.toLowerCase().includes(ctx.query)
      )
      setSuggestions(filtered.slice(0, 5))
      setShowSuggestions(filtered.length > 0)
      setMentionStart(ctx.atIndex)
      setSelectedIndex(0)
    } else {
      setShowSuggestions(false)
    }
  }

  const insertMention = (member: FamilyMember) => {
    const before = value.slice(0, mentionStart)
    const afterCursor = textareaRef.current
      ? value.slice(textareaRef.current.selectionStart)
      : ''
    const newValue = `${before}@${member.display_name} ${afterCursor}`
    onChange(newValue)
    setShowSuggestions(false)

    // Restore focus
    setTimeout(() => {
      if (textareaRef.current) {
        const pos = mentionStart + member.display_name.length + 2
        textareaRef.current.focus()
        textareaRef.current.setSelectionRange(pos, pos)
      }
    }, 0)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((i) => Math.min(i + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && suggestions[selectedIndex]) {
      e.preventDefault()
      insertMention(suggestions[selectedIndex])
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
    }
  }

  return (
    <div className="relative flex-1">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
        placeholder={placeholder}
        className={`
          w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl
          text-fc-text placeholder:text-fc-text-muted
          focus:outline-none focus:ring-2 focus:ring-primary resize-none
          ${bigMode ? 'text-base' : 'text-sm'}
          ${className}
        `}
        rows={rows}
        maxLength={maxLength}
      />

      {/* Suggestions dropdown */}
      {showSuggestions && (
        <div className="absolute bottom-full left-0 mb-1 w-full max-w-xs bg-fc-surface border border-fc-border rounded-xl shadow-lg z-20 overflow-hidden">
          {suggestions.map((member, i) => (
            <button
              key={member.user_id}
              onMouseDown={(e) => {
                e.preventDefault()
                insertMention(member)
              }}
              className={`
                w-full text-left px-3 py-2 transition-colors
                ${bigMode ? 'text-base' : 'text-sm'}
                ${i === selectedIndex ? 'bg-primary/10 text-primary' : 'text-fc-text hover:bg-fc-bg'}
              `}
            >
              <span className="font-medium">@{member.display_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
