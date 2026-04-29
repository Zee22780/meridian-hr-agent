export interface StepStatus {
  status: string
  timestamp?: string
  meeting_time?: string
}

export interface OnboardingProgress {
  employee_id: string
  employee_name: string
  email: string
  department: string | null
  title: string | null
  hire_date: string | null
  onboarding_status: string | null
  steps: Record<string, StepStatus>
  last_updated: string | null
}

export interface Escalation {
  id: string
  employee_id: string
  employee_name: string | null
  type: string
  severity: string
  reason: string
  context: Record<string, unknown> | null
  assigned_to: string | null
  status: string
  created_at: string
  resolved_at: string | null
  resolution: string | null
}

export interface AuditLogEntry {
  id: string
  agent_name: string
  action_type: string
  employee_id: string | null
  input: Record<string, unknown> | null
  output: Record<string, unknown> | null
  timestamp: string
  status: string
  error: string | null
}

export interface AuditLogResponse {
  items: AuditLogEntry[]
  total: number
  page: number
  page_size: number
}

export interface ChatResponse {
  answer: string
  confidence_score: number | null
  escalated: boolean
  tool_calls: Record<string, unknown>[]
}

export interface MockEmployee {
  id: string
  name: string
}
