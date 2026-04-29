import { useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'

const TITLES: Record<string, string> = {
  '/dashboard':   'Onboarding Dashboard',
  '/escalations': 'Escalation Queue',
  '/audit':       'Audit Log',
  '/chat':        'New Hire Chat',
}

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const { pathname } = useLocation()
  const title = TITLES[pathname] ?? 'Meridian'

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <div className="ml-60">
        <header className="sticky top-0 z-10 flex items-center px-8 py-4 bg-white border-b border-slate-200">
          <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
        </header>
        <main className="px-8 py-8 max-w-7xl mx-auto">{children}</main>
      </div>
    </div>
  )
}
