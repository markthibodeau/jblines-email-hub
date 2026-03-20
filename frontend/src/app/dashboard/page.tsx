"use client"

import { useEffect, useState } from "react"
import AppShell from "@/components/AppShell"
import { getEmailStats, getBillingSummary, getUpcomingMeetings } from "@/lib/api"
import { Mail, Users, DollarSign, Calendar, TrendingUp, AlertCircle, RefreshCw } from "lucide-react"
import { triggerSync } from "@/lib/api"

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null)
  const [billing, setBilling] = useState<any>(null)
  const [meetings, setMeetings] = useState<any[]>([])
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    Promise.all([
      getEmailStats().then((r) => setStats(r.data)),
      getBillingSummary().then((r) => setBilling(r.data)),
      getUpcomingMeetings(7).then((r) => setMeetings(r.data)),
    ])
  }, [])

  const handleSync = async () => {
    setSyncing(true)
    await triggerSync()
    setTimeout(() => setSyncing(false), 3000)
  }

  const totalPending = billing?.pending?.total || 0
  const totalPaid = billing?.paid?.total || 0
  const urgentCount = stats?.by_sentiment?.urgent || 0

  return (
    <AppShell>
      <div className="p-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
            <p className="text-gray-500 text-sm mt-1">All inboxes · Live data</p>
          </div>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-60 transition"
          >
            <RefreshCw size={15} className={syncing ? "animate-spin" : ""} />
            {syncing ? "Syncing..." : "Sync Now"}
          </button>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Total Emails"
            value={stats?.total_emails?.toLocaleString() || "—"}
            icon={<Mail size={20} className="text-indigo-500" />}
            bg="bg-indigo-50"
          />
          <StatCard
            label="Urgent Emails"
            value={urgentCount}
            icon={<AlertCircle size={20} className="text-red-500" />}
            bg="bg-red-50"
            highlight={urgentCount > 0}
          />
          <StatCard
            label="Pending Billing"
            value={`$${totalPending.toLocaleString()}`}
            icon={<DollarSign size={20} className="text-amber-500" />}
            bg="bg-amber-50"
          />
          <StatCard
            label="Upcoming Meetings"
            value={meetings.length}
            icon={<Calendar size={20} className="text-emerald-500" />}
            bg="bg-emerald-50"
          />
        </div>

        {/* Two column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Email breakdown by category */}
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Emails by Category</h3>
            {stats?.by_category ? (
              <div className="space-y-3">
                {Object.entries(stats.by_category).map(([cat, count]: any) => (
                  <div key={cat} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`w-2.5 h-2.5 rounded-full ${categoryColor(cat)}`} />
                      <span className="text-sm text-gray-700 capitalize">{cat}</span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            ) : <Skeleton lines={4} />}
          </div>

          {/* Upcoming meetings */}
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Upcoming Meetings (7 days)</h3>
            {meetings.length === 0 ? (
              <p className="text-sm text-gray-400">No meetings scheduled in the next 7 days.</p>
            ) : (
              <div className="space-y-3">
                {meetings.slice(0, 6).map((m) => (
                  <div key={m.id} className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{m.title || "Meeting"}</p>
                      <p className="text-xs text-gray-400">{m.customer_name || m.attendees}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-xs font-medium text-indigo-600">
                        {m.scheduled_at ? new Date(m.scheduled_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "TBD"}
                      </p>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${statusBadge(m.status)}`}>
                        {m.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Inbox breakdown */}
          <div className="bg-white rounded-xl border border-gray-100 p-6 lg:col-span-2">
            <h3 className="font-semibold text-gray-900 mb-4">Emails by Inbox</h3>
            {stats?.by_inbox ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {stats.by_inbox.map((row: any) => (
                  <div key={row.inbox} className="bg-gray-50 rounded-lg px-4 py-3">
                    <p className="text-xs text-gray-500 truncate">{row.inbox}</p>
                    <p className="text-lg font-bold text-gray-900 mt-1">{row.count.toLocaleString()}</p>
                  </div>
                ))}
              </div>
            ) : <Skeleton lines={2} />}
          </div>
        </div>
      </div>
    </AppShell>
  )
}

function StatCard({ label, value, icon, bg, highlight = false }: any) {
  return (
    <div className={`bg-white rounded-xl border ${highlight ? "border-red-200" : "border-gray-100"} p-5`}>
      <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center mb-3`}>{icon}</div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}

function Skeleton({ lines }: { lines: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-4 bg-gray-100 rounded animate-pulse" />
      ))}
    </div>
  )
}

function categoryColor(cat: string) {
  return { customer: "bg-blue-400", billing: "bg-amber-400", schedule: "bg-emerald-400", general: "bg-gray-300" }[cat] || "bg-gray-300"
}

function statusBadge(status: string) {
  return { confirmed: "bg-emerald-100 text-emerald-700", requested: "bg-amber-100 text-amber-700", cancelled: "bg-red-100 text-red-700" }[status] || "bg-gray-100 text-gray-600"
}
