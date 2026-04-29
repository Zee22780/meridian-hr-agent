import type { AuditLogResponse, ChatResponse, Escalation, OnboardingProgress } from '../types'

const BASE = 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? res.statusText)
  }
  return res.json()
}

export const api = {
  onboarding: {
    list: () => request<OnboardingProgress[]>('/onboarding'),
    get: (id: string) => request<OnboardingProgress>(`/onboarding/${id}`),
  },

  escalations: {
    list: (status?: string) =>
      request<Escalation[]>(`/escalations${status ? `?status=${status}` : ''}`),
    resolve: (id: string, status: 'resolved' | 'rejected', resolution?: string) =>
      request(`/escalations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status, resolution }),
      }),
  },

  audit: {
    list: (page = 1, pageSize = 50, actionType?: string) =>
      request<AuditLogResponse>(
        `/audit-log?page=${page}&page_size=${pageSize}${actionType ? `&action_type=${actionType}` : ''}`
      ),
  },

  chat: {
    send: (question: string, employee_id: string) =>
      request<ChatResponse>('/chat', {
        method: 'POST',
        body: JSON.stringify({ question, employee_id }),
      }),
  },
}
