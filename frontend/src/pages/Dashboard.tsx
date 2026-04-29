import { Calendar, CheckCircle2, AlertCircle, Clock, Mail, User } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Badge } from '../components/Badge'
import { api } from '../lib/api'
import type { OnboardingProgress } from '../types'

const ALL_STEPS = [
  { key: 'welcome_email',    label: 'Welcome Email',      icon: Mail },
  { key: 'meeting_manager',  label: 'Meet Manager',        icon: User },
  { key: 'meeting_dept_head',label: 'Meet Dept Head',      icon: User },
  { key: 'meeting_marketing',label: 'Meet Marketing',      icon: User },
  { key: 'meeting_ceo',      label: 'Meet CEO',            icon: User },
  { key: 'meeting_it',       label: 'IT Setup',            icon: User },
  { key: 'meeting_hr',       label: 'HR Check-In',         icon: User },
  { key: 'paperwork_sent',   label: 'Paperwork Sent',      icon: Mail },
  { key: 'i9_escalated',     label: 'I-9 Verification',   icon: AlertCircle },
]

function progressPercent(steps: OnboardingProgress['steps']): number {
  const done = ALL_STEPS.filter(
    s => steps[s.key]?.status === 'completed' || steps[s.key]?.status === 'escalated'
  ).length
  return Math.round((done / ALL_STEPS.length) * 100)
}

function StepIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
  if (status === 'escalated') return <AlertCircle className="h-4 w-4 text-amber-500 shrink-0" />
  return <Clock className="h-4 w-4 text-slate-300 shrink-0" />
}

function OnboardingCard({ record }: { record: OnboardingProgress }) {
  const pct = progressPercent(record.steps)
  const status = record.onboarding_status ?? 'pending'

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-slate-900">{record.employee_name}</p>
          <p className="text-xs text-slate-500 mt-0.5">
            {[record.title, record.department].filter(Boolean).join(' · ')}
          </p>
        </div>
        <Badge status={status} />
      </div>

      {record.hire_date && (
        <div className="flex items-center gap-1.5 mt-3 text-xs text-slate-500">
          <Calendar className="h-3.5 w-3.5" />
          Start: {new Date(record.hire_date).toLocaleDateString()}
        </div>
      )}

      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
          <span>Progress</span>
          <span>{pct}%</span>
        </div>
        <div className="h-1.5 bg-slate-100 rounded-full">
          <div
            className="h-1.5 bg-indigo-500 rounded-full transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <ul className="mt-4 space-y-2">
        {ALL_STEPS.map(step => {
          const s = record.steps[step.key]
          const stepStatus = s?.status ?? 'pending'
          return (
            <li key={step.key} className="flex items-center gap-2">
              <StepIcon status={stepStatus} />
              <span
                className={`text-xs ${stepStatus === 'pending' ? 'text-slate-400' : 'text-slate-700'}`}
              >
                {step.label}
              </span>
              {s?.meeting_time && (
                <span className="ml-auto text-xs text-slate-400 truncate max-w-24">
                  {new Date(s.meeting_time).toLocaleDateString()}
                </span>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function StatCard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-slate-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}

function Skeleton() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 animate-pulse">
      <div className="h-4 bg-slate-100 rounded w-2/3 mb-2" />
      <div className="h-3 bg-slate-100 rounded w-1/3 mb-4" />
      <div className="h-1.5 bg-slate-100 rounded-full mb-4" />
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-3 bg-slate-100 rounded w-full mb-2" />
      ))}
    </div>
  )
}

export function Dashboard() {
  const [records, setRecords] = useState<OnboardingProgress[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.onboarding.list()
      .then(setRecords)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const active = records.filter(r => r.onboarding_status === 'in_progress').length
  const completed = records.filter(r => r.onboarding_status === 'completed').length
  const escalated = records.filter(r =>
    Object.values(r.steps).some(s => s.status === 'escalated')
  ).length
  const avgPct = records.length
    ? Math.round(records.reduce((sum, r) => sum + progressPercent(r.steps), 0) / records.length)
    : 0

  const sorted = [...records].sort((a, b) => {
    const order: Record<string, number> = { in_progress: 0, pending: 1, completed: 2 }
    return (order[a.onboarding_status ?? 'pending'] ?? 1) - (order[b.onboarding_status ?? 'pending'] ?? 1)
  })

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Active Onboardings" value={active} />
        <StatCard label="Completed" value={completed} />
        <StatCard label="With Escalations" value={escalated} />
        <StatCard label="Avg Progress" value={`${avgPct}%`} />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-5 py-4 text-sm mb-6">
          Failed to load onboarding data: {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => <Skeleton key={i} />)}
        </div>
      ) : records.length === 0 && !error ? (
        <div className="text-center py-20 text-slate-400 text-sm">
          No onboarding records yet. Trigger one via <code className="font-mono text-xs">POST /onboarding/trigger</code>.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {sorted.map(r => (
            <OnboardingCard key={r.employee_id} record={r} />
          ))}
        </div>
      )}
    </div>
  )
}
