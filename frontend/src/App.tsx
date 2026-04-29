import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AuditLog } from './pages/AuditLog'
import { Chat } from './pages/Chat'
import { Dashboard } from './pages/Dashboard'
import { Escalations } from './pages/Escalations'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={<Layout><Dashboard /></Layout>}
        />
        <Route
          path="/escalations"
          element={<Layout><Escalations /></Layout>}
        />
        <Route
          path="/audit"
          element={<Layout><AuditLog /></Layout>}
        />
        <Route
          path="/chat"
          element={<Layout><Chat /></Layout>}
        />
      </Routes>
    </BrowserRouter>
  )
}
