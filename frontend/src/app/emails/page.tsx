"use client"

import { useEffect, useState, useCallback } from "react"
import AppShell from "@/components/AppShell"
import { getEmails, getEmail } from "@/lib/api"
import { Mail, Search, RefreshCw, Lock, Inbox, X, ChevronLeft, ChevronRight } from "lucide-react"
import { formatDistanceToNow } from "date-fns"

const INBOXES = ["all", "sales@jblines.com", "asphalt@jblines.com", "estimates@jblines.com", "operations@jblines.com", "accounts@jblines.com"]
const CATEGORIES = ["all", "customer", "billing", "schedule", "general"]

const categoryBadge: Record<string, string> = {
  customer: "bg-blue-100 text-blue-700",
  billing: "bg-amber-100 text-amber-700",
  schedule: "bg-emerald-100 text-emerald-700",
  general: "bg-gray-100 text-gray-600",
}

const sentimentBadge: Record<string, string> = {
  urgent: "bg-red-100 text-red-700",
  negative: "bg-orange-100 text-orange-700",
  neutral: "bg-gray-100 text-gray-600",
  positive: "bg-green-100 text-green-700",
}

export default function EmailsPage() {
  const [emails, setEmails] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEmail, setSelectedEmail] = useState<any>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [inbox, setInbox] = useState("all")
  const [category, setCategory] = useState("all")
  const [search, setSearch] = useState("")
  const [searchInput, setSearchInput] = useState("")
  const [offset, setOffset] = useState(0)
  const limit = 50

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { limit, offset }
      if (inbox !== "all") params.inbox = inbox
      if (category !== "all") params.category = category
      if (search) params.search = search
      const res = await getEmails(params)
      setEmails(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [inbox, category, search, offset])

  useEffect(() => { load() }, [load])

  const openEmail = async (email: any) => {
    setSelectedEmail(email)
    if (!email.body_text && !email.is_redacted) {
      setLoadingDetail(true)
      try {
        const res = await getEmail(email.id)
        setSelectedEmail(res.data)
      } catch {}
      setLoadingDetail(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setOffset(0)
    setSearch(searchInput)
  }

  return (
    <AppShell>
      <div className="flex h-screen overflow-hidden">
        {/* Left panel — email list */}
        <div className={`flex flex-col ${selectedEmail ? "w-[420px] shrink-0" : "flex-1"} border-r border-gray-200 overflow-hidden`}>
          {/* Toolbar */}
          <div className="p-4 border-b border-gray-100 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">Emails</h2>
              <button onClick={load} className="p-1.5 text-gray-400 hover:text-indigo-600 rounded transition">
                <RefreshCw size={15} />
              </button>
            </div>

            {/* Search */}
            <form onSubmit={handleSearch} className="flex gap-2">
              <div className="relative flex-1">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Search emails..."
                  className="w-full pl-8 pr-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
              </div>
              <button type="submit" className="px-3 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700">Go</button>
            </form>

            {/* Inbox filter */}
            <div className="flex gap-1 overflow-x-auto pb-1">
              {INBOXES.map(i => (
                <button
                  key={i}
                  onClick={() => { setInbox(i); setOffset(0) }}
                  className={`shrink-0 px-2.5 py-1 rounded-full text-xs font-medium transition ${inbox === i ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
                >
                  {i === "all" ? "All Inboxes" : i.split("@")[0]}
                </button>
              ))}
            </div>

            {/* Category filter */}
            <div className="flex gap-1">
              {CATEGORIES.map(c => (
                <button
                  key={c}
                  onClick={() => { setCategory(c); setOffset(0) }}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition ${category === c ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
                >
                  {c === "all" ? "All" : c.charAt(0).toUpperCase() + c.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Email list */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-4 space-y-3">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="animate-pulse space-y-1.5">
                    <div className="h-3 bg-gray-100 rounded w-2/3" />
                    <div className="h-3 bg-gray-100 rounded w-full" />
                    <div className="h-3 bg-gray-100 rounded w-1/3" />
                  </div>
                ))}
              </div>
            ) : emails.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                <Inbox size={36} className="mb-3 opacity-30" />
                <p className="text-sm">No emails found</p>
                {(inbox !== "all" || category !== "all" || search) && (
                  <button onClick={() => { setInbox("all"); setCategory("all"); setSearch(""); setSearchInput(""); }} className="mt-2 text-xs text-indigo-500 hover:underline">
                    Clear filters
                  </button>
                )}
              </div>
            ) : (
              emails.map((email) => (
                <button
                  key={email.id}
                  onClick={() => openEmail(email)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-indigo-50 transition-colors ${selectedEmail?.id === email.id ? "bg-indigo-50" : email.is_read ? "bg-white" : "bg-blue-50"}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className={`text-sm font-medium truncate ${email.is_read ? "text-gray-700" : "text-gray-900"}`}>
                      {email.sender_name || email.sender}
                    </span>
                    <span className="text-xs text-gray-400 shrink-0">
                      {formatDistanceToNow(new Date(email.received_at), { addSuffix: true })}
                    </span>
                  </div>
                  <p className={`text-sm truncate mb-1 ${email.is_read ? "text-gray-500" : "text-gray-800 font-medium"}`}>
                    {email.subject || "(no subject)"}
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 truncate flex-1">{email.body_snippet}</span>
                    <div className="flex gap-1 shrink-0">
                      {email.is_redacted && <span title="Private inbox"><Lock size={11} className="text-gray-400" /></span>}
                      {email.category && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${categoryBadge[email.category] || "bg-gray-100 text-gray-600"}`}>
                          {email.category}
                        </span>
                      )}
                      {email.ai_sentiment && email.ai_sentiment !== "neutral" && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${sentimentBadge[email.ai_sentiment] || ""}`}>
                          {email.ai_sentiment}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-gray-300 mt-1 truncate">{email.inbox}</p>
                </button>
              ))
            )}
          </div>

          {/* Pagination */}
          {!loading && emails.length > 0 && (
            <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 text-xs text-gray-500">
              <span>{offset + 1}–{offset + emails.length}</span>
              <div className="flex gap-1">
                <button onClick={() => setOffset(Math.max(0, offset - limit))} disabled={offset === 0} className="p-1 rounded hover:bg-gray-100 disabled:opacity-30">
                  <ChevronLeft size={14} />
                </button>
                <button onClick={() => setOffset(offset + limit)} disabled={emails.length < limit} className="p-1 rounded hover:bg-gray-100 disabled:opacity-30">
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right panel — email detail */}
        {selectedEmail && (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Detail header */}
            <div className="flex items-start gap-4 p-6 border-b border-gray-100">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <h3 className="text-lg font-semibold text-gray-900">{selectedEmail.subject || "(no subject)"}</h3>
                  {selectedEmail.category && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${categoryBadge[selectedEmail.category] || "bg-gray-100 text-gray-600"}`}>
                      {selectedEmail.category}
                    </span>
                  )}
                  {selectedEmail.ai_sentiment && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${sentimentBadge[selectedEmail.ai_sentiment] || "bg-gray-100 text-gray-600"}`}>
                      {selectedEmail.ai_sentiment}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-500 space-y-0.5">
                  <p><span className="font-medium text-gray-700">From:</span> {selectedEmail.sender_name ? `${selectedEmail.sender_name} <${selectedEmail.sender}>` : selectedEmail.sender}</p>
                  <p><span className="font-medium text-gray-700">To:</span> {selectedEmail.inbox}</p>
                  <p><span className="font-medium text-gray-700">Date:</span> {new Date(selectedEmail.received_at).toLocaleString()}</p>
                </div>
                {selectedEmail.ai_summary && (
                  <div className="mt-3 p-3 bg-indigo-50 rounded-lg border border-indigo-100">
                    <p className="text-xs font-semibold text-indigo-700 mb-1">AI Summary</p>
                    <p className="text-sm text-indigo-800">{selectedEmail.ai_summary}</p>
                  </div>
                )}
              </div>
              <button onClick={() => setSelectedEmail(null)} className="p-1.5 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100 shrink-0">
                <X size={18} />
              </button>
            </div>

            {/* Email body */}
            <div className="flex-1 overflow-y-auto p-6">
              {loadingDetail ? (
                <div className="space-y-2 animate-pulse">
                  {[...Array(6)].map((_, i) => <div key={i} className="h-4 bg-gray-100 rounded" style={{ width: `${70 + Math.random() * 30}%` }} />)}
                </div>
              ) : selectedEmail.is_redacted ? (
                <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                  <Lock size={32} className="mb-3 opacity-40" />
                  <p className="text-sm font-medium">Content redacted</p>
                  <p className="text-xs mt-1">This is a private inbox. Only admins can view full content.</p>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {selectedEmail.body_text || selectedEmail.body_snippet || <span className="text-gray-400 italic">No content available</span>}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty state when no email selected */}
        {!selectedEmail && !loading && emails.length > 0 && (
          <div className="hidden" />
        )}
      </div>
    </AppShell>
  )
}
