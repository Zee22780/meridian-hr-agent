import { Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'

const EMPLOYEES = [
  { id: 'EMP001', name: 'Jordan Rivera' },
  { id: 'EMP002', name: 'Marcus Chen' },
  { id: 'EMP003', name: 'Aisha Thompson' },
  { id: 'EMP004', name: 'Luca Moretti' },
  { id: 'EMP005', name: 'Priya Nair' },
  { id: 'EMP006', name: 'Diana Walsh' },
  { id: 'EMP007', name: 'Robert Kim' },
  { id: 'EMP008', name: 'Sofia Nguyen' },
  { id: 'EMP009', name: 'Tom Adler' },
  { id: 'EMP010', name: 'Nadia Osei' },
  { id: 'EMP011', name: 'Alex Park' },
]

const SUGGESTED = [
  'How do I enroll in benefits?',
  'What should I bring on day one?',
  'How does PTO work?',
  'What is the remote work policy?',
]

interface Message {
  role: 'user' | 'agent'
  text: string
  confidence?: number | null
  escalated?: boolean
}

function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {pct}% confidence
    </span>
  )
}

function IdentityGate({ onSelect }: { onSelect: (id: string, name: string) => void }) {
  const [selected, setSelected] = useState('')

  const handleStart = () => {
    const emp = EMPLOYEES.find(e => e.id === selected)
    if (emp) onSelect(emp.id, emp.name)
  }

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 w-full max-w-md text-center">
        <div className="w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">👋</span>
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-1">Welcome to Meridian</h2>
        <p className="text-sm text-slate-500 mb-6">
          Ask me anything about your onboarding, benefits, policies, and more.
        </p>
        <div className="text-left mb-4">
          <label className="block text-xs font-medium text-slate-600 mb-1.5">
            Who are you?
          </label>
          <select
            value={selected}
            onChange={e => setSelected(e.target.value)}
            className="w-full border border-slate-200 rounded-lg px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white"
          >
            <option value="">Select your name...</option>
            {EMPLOYEES.map(e => (
              <option key={e.id} value={e.id}>{e.name}</option>
            ))}
          </select>
        </div>
        <button
          onClick={handleStart}
          disabled={!selected}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
          Start chatting →
        </button>
      </div>
    </div>
  )
}

export function Chat() {
  const [employeeId, setEmployeeId] = useState<string | null>(null)
  const [firstName, setFirstName] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSelect = (id: string, name: string) => {
    setEmployeeId(id)
    setFirstName(name.split(' ')[0])
    setMessages([
      {
        role: 'agent',
        text: `Hi ${name.split(' ')[0]}! 👋 I'm here to help you get settled at Meridian. Ask me anything about your onboarding, benefits, time off, remote work, or anything else on your mind.`,
      },
    ])
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text: string) => {
    if (!text.trim() || !employeeId || loading) return
    setShowSuggestions(false)
    setMessages(prev => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const res = await api.chat.send(text, employeeId)
      setMessages(prev => [
        ...prev,
        {
          role: 'agent',
          text: res.answer,
          confidence: res.confidence_score,
          escalated: res.escalated,
        },
      ])
    } catch (e: unknown) {
      setMessages(prev => [
        ...prev,
        {
          role: 'agent',
          text: "I'm having trouble right now. Please try again or reach out to HR directly.",
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send(input)
    }
  }

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`
    }
  }

  if (!employeeId) {
    return <IdentityGate onSelect={handleSelect} />
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="bg-white rounded-xl border border-slate-200 flex flex-col flex-1 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <p className="text-sm font-semibold text-slate-900">
            Hi {firstName} — ask me anything about your first days at Meridian
          </p>
          <p className="text-xs text-slate-400 mt-0.5">Logged in as {EMPLOYEES.find(e => e.id === employeeId)?.name}</p>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'user' ? (
                <div className="max-w-md bg-indigo-600 text-white rounded-2xl rounded-br-sm px-4 py-3 text-sm">
                  {msg.text}
                </div>
              ) : (
                <div className="max-w-2xl bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-slate-700 space-y-2">
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                  <div className="flex items-center gap-2 flex-wrap">
                    {msg.confidence != null && (
                      <ConfidenceBadge score={msg.confidence} />
                    )}
                    {msg.escalated && (
                      <a
                        href="mailto:hr@meridian.com"
                        className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors"
                      >
                        Connect with HR →
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3">
                <div className="flex gap-1.5 items-center h-5">
                  <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}

          {showSuggestions && !loading && (
            <div className="flex flex-wrap gap-2 mt-2">
              {SUGGESTED.map(s => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-100 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="px-6 py-4 border-t border-slate-100">
          <div className="flex items-end gap-3">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              className="flex-1 resize-none border border-slate-200 rounded-lg px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent overflow-hidden"
              style={{ minHeight: '42px', maxHeight: '120px' }}
            />
            <button
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors shrink-0"
            >
              <Send className="h-4 w-4" />
              Send
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  )
}
