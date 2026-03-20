"use client"

import { useEffect, useState } from "react"
import AppShell from "@/components/AppShell"
import { getMeetings, updateMeeting } from "@/lib/api"
import { Calendar, MapPin, Clock, Users, CheckCircle, XCircle } from "lucide-react"

export default function SchedulePage() {
  const [meetings, setMeetings] = useState<any[]>([])
  const [filter, setFilter] = useState("")
  const [loading, setLoading] = useState(true)

  const load = async (status = "") => {
    setLoading(true)
    const res = await getMeetings(status ? { status } : { upcoming_only: false })
    setMeetings(res.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const confirm = async (id: number) => {
    await updateMeeting(id, { status: "confirmed" })
    load(filter)
  }

  const cancel = async (id: number) => {
    await updateMeeting(id, { status: "cancelled" })
    load(filter)
  }

  return (
    <AppShell>
      <div className="p-8 max-w-6xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Schedule</h2>

        {/* Filters */}
        <div className="flex gap-2 mb-6">
          {["", "requested", "confirmed", "cancelled", "completed"].map((s) => (
            <button
              key={s}
              onClick={() => { setFilter(s); load(s) }}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                filter === s ? "bg-indigo-600 text-white" : "bg-white border border-gray-200 text-gray-600 hover:border-indigo-300"
              }`}
            >
              {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 animate-pulse">
                <div className="h-4 bg-gray-100 rounded w-1/3 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {meetings.map((m) => (
              <div key={m.id} className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-sm transition-shadow">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">{m.title || "Meeting"}</h3>
                      <StatusBadge status={m.status} />
                    </div>
                    {m.customer_name && (
                      <p className="text-sm text-indigo-600 mb-2">{m.customer_name}</p>
                    )}
                    {m.description && (
                      <p className="text-sm text-gray-500 mb-3">{m.description}</p>
                    )}
                    <div className="flex flex-wrap gap-4 text-xs text-gray-400">
                      {m.scheduled_at && (
                        <span className="flex items-center gap-1">
                          <Calendar size={12} />
                          {new Date(m.scheduled_at).toLocaleDateString("en-US", {
                            weekday: "short", month: "short", day: "numeric", year: "numeric",
                          })}
                          {" "}at{" "}
                          {new Date(m.scheduled_at).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}
                        </span>
                      )}
                      {m.duration_minutes && (
                        <span className="flex items-center gap-1">
                          <Clock size={12} /> {m.duration_minutes} min
                        </span>
                      )}
                      {m.location && (
                        <span className="flex items-center gap-1">
                          <MapPin size={12} /> {m.location}
                        </span>
                      )}
                      {m.attendees && (
                        <span className="flex items-center gap-1">
                          <Users size={12} /> {m.attendees}
                        </span>
                      )}
                    </div>
                  </div>

                  {m.status === "requested" && (
                    <div className="flex gap-2 shrink-0">
                      <button
                        onClick={() => confirm(m.id)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-emerald-50 text-emerald-700 text-xs font-medium rounded-lg hover:bg-emerald-100 transition"
                      >
                        <CheckCircle size={13} /> Confirm
                      </button>
                      <button
                        onClick={() => cancel(m.id)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 text-xs font-medium rounded-lg hover:bg-red-100 transition"
                      >
                        <XCircle size={13} /> Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {meetings.length === 0 && (
              <div className="text-center py-16 text-gray-400">
                <Calendar size={40} className="mx-auto mb-3 opacity-30" />
                <p>No meetings found. They'll appear here as scheduling emails are synced.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    requested: "bg-amber-100 text-amber-700",
    confirmed: "bg-emerald-100 text-emerald-700",
    cancelled: "bg-red-100 text-red-700",
    completed: "bg-gray-100 text-gray-500",
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || "bg-gray-100 text-gray-500"}`}>
      {status}
    </span>
  )
}
