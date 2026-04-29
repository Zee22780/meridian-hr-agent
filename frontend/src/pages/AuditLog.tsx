import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Badge } from '../components/Badge'
import { api } from '../lib/api'
import type { AuditLogEntry } from '../types'

const PAGE_SIZE = 25

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function InputCell({ data }: { data: Record<string, unknown> | null }) {
  if (!data) return <span className="text-slate-400">—</span>
  const entries = Object.entries(data).slice(0, 2)
  return (
    <span className="text-xs text-slate-500 font-mono">
      {entries.map(([k, v]) => `${k}: ${String(v).slice(0, 30)}`).join(', ')}
      {Object.keys(data).length > 2 && '…'}
    </span>
  )
}

export function AuditLog() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    api.audit.list(page, PAGE_SIZE)
      .then(data => {
        setEntries(data.items)
        setTotal(data.total)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [page])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-slate-500">{total} total entries</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-5 py-4 text-sm mb-6">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-6 py-3">Timestamp</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-6 py-3">Agent</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-6 py-3">Action / Tool</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-6 py-3">Input</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-6 py-3">Status</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide px-6 py-3">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              [...Array(8)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  {[...Array(6)].map((_, j) => (
                    <td key={j} className="px-6 py-4">
                      <div className="h-3 bg-slate-100 rounded w-24" />
                    </td>
                  ))}
                </tr>
              ))
            ) : entries.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-slate-400 text-sm">
                  No audit log entries yet.
                </td>
              </tr>
            ) : (
              entries.map(entry => (
                <tr key={entry.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-3 text-xs text-slate-500 whitespace-nowrap">
                    {formatDate(entry.timestamp)}
                  </td>
                  <td className="px-6 py-3 text-xs text-slate-600">{entry.agent_name}</td>
                  <td className="px-6 py-3 font-medium text-slate-900 font-mono text-xs">
                    {entry.action_type}
                  </td>
                  <td className="px-6 py-3 max-w-xs">
                    <InputCell data={entry.input} />
                  </td>
                  <td className="px-6 py-3">
                    <Badge status={entry.status} />
                  </td>
                  <td className="px-6 py-3 text-xs text-red-500 max-w-xs truncate">
                    {entry.error ?? '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-slate-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
