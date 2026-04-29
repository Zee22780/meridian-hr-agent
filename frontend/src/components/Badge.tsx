interface BadgeProps {
  status: string
  className?: string
}

const CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  completed:    { bg: 'bg-green-100',  text: 'text-green-700',  label: 'Completed' },
  in_progress:  { bg: 'bg-blue-100',   text: 'text-blue-700',   label: 'In Progress' },
  pending:      { bg: 'bg-slate-100',  text: 'text-slate-600',  label: 'Pending' },
  escalated:    { bg: 'bg-amber-100',  text: 'text-amber-700',  label: 'Escalated' },
  open:         { bg: 'bg-red-100',    text: 'text-red-700',    label: 'Open' },
  resolved:     { bg: 'bg-green-100',  text: 'text-green-700',  label: 'Resolved' },
  rejected:     { bg: 'bg-slate-100',  text: 'text-slate-600',  label: 'Rejected' },
  success:      { bg: 'bg-green-100',  text: 'text-green-700',  label: 'Success' },
  failed:       { bg: 'bg-red-100',    text: 'text-red-700',    label: 'Failed' },
}

export function Badge({ status, className = '' }: BadgeProps) {
  const cfg = CONFIG[status.toLowerCase()] ?? {
    bg: 'bg-slate-100',
    text: 'text-slate-600',
    label: status,
  }
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text} ${className}`}
    >
      {cfg.label}
    </span>
  )
}
