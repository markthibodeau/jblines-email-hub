"use client"

import { useState, useRef, useEffect } from "react"
import AppShell from "@/components/AppShell"
import { askQuestion } from "@/lib/api"
import { Send, Bot, User, Loader2, Sparkles } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
  emailsUsed?: number
}

const SUGGESTIONS = [
  "What invoices are currently overdue?",
  "Who has meetings scheduled this week?",
  "Show me all emails from Acme Corp",
  "What's our total pending billing?",
  "Which customers contacted us most recently?",
  "Are there any urgent emails I should know about?",
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState("")
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const send = async (question: string) => {
    if (!question.trim() || loading) return
    setInput("")
    setMessages((prev) => [...prev, { role: "user", content: question }])
    setLoading(true)

    try {
      const res = await askQuestion(question, filter || undefined)
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.answer, emailsUsed: res.data.emails_used },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I ran into an error. Please try again." },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col h-full max-w-3xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={20} className="text-indigo-500" />
            <h2 className="text-2xl font-bold text-gray-900">Ask Claude</h2>
          </div>
          <p className="text-gray-500 text-sm">Ask anything about your customers, billing, or schedule.</p>
        </div>

        {/* Context filter */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {["", "customer", "billing", "schedule"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                filter === f
                  ? "bg-indigo-600 text-white"
                  : "bg-white border border-gray-200 text-gray-600 hover:border-indigo-300"
              }`}
            >
              {f === "" ? "All emails" : f.charAt(0).toUpperCase() + f.slice(1) + " only"}
            </button>
          ))}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-0">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Bot size={40} className="text-gray-200 mx-auto mb-4" />
              <p className="text-gray-400 text-sm mb-6">Try asking a question about your email data</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="text-left px-4 py-3 bg-white border border-gray-100 rounded-xl text-sm text-gray-600 hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot size={15} className="text-indigo-600" />
                </div>
              )}
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-indigo-600 text-white rounded-tr-sm"
                  : "bg-white border border-gray-100 text-gray-800 rounded-tl-sm"
              }`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.emailsUsed !== undefined && (
                  <p className="text-xs text-gray-400 mt-2 border-t border-gray-50 pt-2">
                    Searched {msg.emailsUsed} email records
                  </p>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
                  <User size={15} className="text-white" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
                <Bot size={15} className="text-indigo-600" />
              </div>
              <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                <Loader2 size={16} className="text-indigo-400 animate-spin" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={(e) => { e.preventDefault(); send(input) }}
          className="flex gap-3 bg-white border border-gray-200 rounded-xl p-2 focus-within:border-indigo-400 transition-colors"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about customers, billing, meetings..."
            className="flex-1 px-3 py-2 text-sm outline-none text-gray-800 placeholder-gray-400"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-lg px-4 py-2 transition-colors"
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </AppShell>
  )
}
