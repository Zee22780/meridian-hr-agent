import { useEffect, useState } from 'react'
import { Badge } from '../components/Badge'
import { api } from '../lib/api'
import type { Escalation } from '../types'

const TABS = [
  { label: 'All',      value: undefined },
  { label: 'Open',     value: 'pending' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Rejected', value: 'rejected' },
]

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

interface ResolveModalProps {
  escalation: Escalation
  action: 'resolved' | 'rejected'
  onConfirm: (resolution: string) => void
  onCancel: () => void
}

function ResolveModal({ escalation, action, onConfirm, onCancel }: ResolveModalProps) {
  const [note, setNote] = useState('')
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
        <h2 className="text-base font-semibold text-slate-900 mb-1 capitalize">
          {action === 'resolved' ? 'Resolve' : 'Reject'} Escalation
        </h2>
        <p className="text-sm text-slate-500 mb-4">
          {escalation.employee_name} — {escalation.type}
        </p>
        <textarea
          className="w-full border border-slate-200 rounded-lg px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
          rows={3}
          placeholder="Resolution note (optional)"
          value={note}
          onChange={e => setNote(e.target.value)}
        />
        <div className="flex gap-3 mt-4 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(note)}
            className={`px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors ${
              action === 'resolved'
                ? 'bg-indigo-600 hover:bg-indigo-700'
                : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            {action === 'resolved' ? 'Mark Resolved' : 'Reject'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function Escalations() {
  const [escalations, setEscalations] = useState<Escalation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<string | undefined>(undefined)
  const [modal, setModal] = useState<{ esc: Escalation; action: 'resolved' | 'rejected' } | null>(null)

  const load = (status?: string) => {
    setLoading(true)
    api.escalations.list(status)
      .then(setEscalations)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(activeTab) }, [activeTab])

  const handleConfirm = async (resolution: string) => {
    if (!modal) return
    try {
      await api.escalations.resolve(modal.esc.id, modal.action, resolution || undefined)
      setModal(null)
      load(activeTab)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to update escalation')
    }
  }

  return (
    <div>
      {modal && (
        <ResolveModal
          escalation={modal.esc}
          action={modal.action}
          onConfirm={handleConfirm}
          onCancel={() => setModal(null)}
        />
      )}

      <div className="flex gap-1 mb-6">
        {TABS.map(tab => (
          <button
            key={tab.label}
            onClick={() => setActiveTab(tab.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.value
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-5 py-4 text-sm mb-6">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm min-w-[860px]">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-4 py-3">Employee</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-4 py-3">Type</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-4 py-3">Reason</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-4 py-3">Priority</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-4 py-3">Status</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-4 py-3">Date</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              [...Array(4)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  {[...Array(7)].map((_, j) => (
                    <td key={j} className="px-4 py-4">
                      <div className="h-3 bg-slate-100 rounded w-24" />
                    </td>
                  ))}
                </tr>
              ))
            ) : escalations.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-slate-400 text-sm">
                  No escalations found.
                </td>
              </tr>
            ) : (
              escalations.map(esc => (
                <tr key={esc.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-4 font-medium text-slate-900">
                    {esc.employee_name ?? '—'}
                  </td>
                  <td className="px-4 py-4 text-slate-700">{esc.type}</td>
                  <td className="px-4 py-4 text-slate-700 max-w-[200px] truncate">{esc.reason}</td>
                  <td className="px-4 py-4">
                    <Badge status={['high', 'urgent', 'critical'].includes(esc.severity) ? 'escalated' : 'pending'} />
                  </td>
                  <td className="px-4 py-4">
                    <Badge status={esc.status === 'pending' ? 'open' : esc.status} />
                  </td>
                  <td className="px-4 py-4 text-slate-500 text-xs whitespace-nowrap">
                    {formatDate(esc.created_at)}
                  </td>
                  <td className="px-4 py-4">
                    {esc.status === 'pending' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => setModal({ esc, action: 'resolved' })}
                          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
                        >
                          Resolve
                        </button>
                        <button
                          onClick={() => setModal({ esc, action: 'rejected' })}
                          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                    {esc.status !== 'open' && esc.resolution && (
                      <p className="text-xs text-slate-400 max-w-xs truncate">{esc.resolution}</p>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
