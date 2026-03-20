/**
 * API client for the Email Hub backend.
 * Reads NEXT_PUBLIC_API_URL from environment — set this in Vercel to your Render URL.
 */

import axios from "axios"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const api = axios.create({ baseURL: BASE_URL })

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token")
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      window.location.href = "/login"
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (email: string, password: string) =>
  api.post("/api/auth/login", new URLSearchParams({ username: email, password }))

export const getMe = () => api.get("/api/auth/me")

// ── Emails ────────────────────────────────────────────────────────────────────
export const getEmails = (params?: Record<string, string | number>) =>
  api.get("/api/emails/", { params })

export const getEmailStats = () => api.get("/api/emails/stats")

export const getEmail = (id: string) => api.get(`/api/emails/${id}`)

// ── Customers ─────────────────────────────────────────────────────────────────
export const getCustomers = (params?: Record<string, string | number>) =>
  api.get("/api/customers/", { params })

export const getCustomer = (id: number) => api.get(`/api/customers/${id}`)

export const getCustomerTimeline = (id: number) =>
  api.get(`/api/customers/${id}/timeline`)

export const updateCustomer = (id: number, data: Record<string, string>) =>
  api.patch(`/api/customers/${id}`, data)

// ── Billing ───────────────────────────────────────────────────────────────────
export const getBilling = (params?: Record<string, string | number>) =>
  api.get("/api/billing/", { params })

export const getBillingSummary = () => api.get("/api/billing/summary")

export const updateBilling = (id: number, data: Record<string, unknown>) =>
  api.patch(`/api/billing/${id}`, data)

// ── Schedule ──────────────────────────────────────────────────────────────────
export const getMeetings = (params?: Record<string, string | number | boolean>) =>
  api.get("/api/schedule/", { params })

export const getUpcomingMeetings = (days = 7) =>
  api.get(`/api/schedule/upcoming?days=${days}`)

export const updateMeeting = (id: number, data: Record<string, unknown>) =>
  api.patch(`/api/schedule/${id}`, data)

// ── Chat ──────────────────────────────────────────────────────────────────────
export const askQuestion = (question: string, context_filter?: string) =>
  api.post("/api/chat/", { question, context_filter })

// ── Admin ─────────────────────────────────────────────────────────────────────
export const getSyncStatus = () => api.get("/api/admin/sync-status")

export const triggerSync = () => api.post("/api/sync/trigger")

export const getUsers = () => api.get("/api/admin/users")

export default api
