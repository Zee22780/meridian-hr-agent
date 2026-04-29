import { AlertTriangle, ClipboardList, LayoutDashboard, MessageSquare } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/escalations', label: 'Escalations', icon: AlertTriangle },
  { to: '/audit', label: 'Audit Log', icon: ClipboardList },
  { to: '/chat', label: 'New Hire Chat', icon: MessageSquare },
]

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-slate-900 flex flex-col">
      <div className="px-6 py-6 flex items-center gap-2.5">
        <span className="w-2 h-2 rounded-full bg-indigo-500" />
        <span className="text-white text-lg font-bold tracking-tight">Meridian</span>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        <p className="px-3 pt-2 pb-1 text-xs font-medium text-slate-500 uppercase tracking-widest">
          Main
        </p>
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-6 py-5 border-t border-slate-800">
        <p className="text-xs text-slate-500">Meridian HR Agent</p>
        <p className="text-xs text-slate-600 mt-0.5">Phase 6 · MVP</p>
      </div>
    </aside>
  )
}
