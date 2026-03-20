"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import AppShell from "@/components/AppShell"
import { getCustomer, getCustomerTimeline, updateCustomer } from "@/lib/api"
import { ArrowLeft, Mail, Building2, Phone, Clock, User, DollarSign, Calendar, Edit2, Check, X } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import Link from "next/link"

const categoryBadge: Record<string, string> = {
  customer: "bg-blue-100 text-blue-700",
  billing: "bg-amber-100 text-amber-700",
  schedule: "bg-emerald-100 text-emerald-700",
  general: "bg-gray-100 text-gray-600",
}

export default function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [customer, setCustomer] = useState<any>(null)
  const [timeline, setTimeline] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<string | null>(null)
  const [editValue, setEditValue] = useState("")

  useEffect(() => {
    if (!id) return
    Promise.all([
      getCustomer(Number(id)).then(r => setCustomer(r.data)),
      getCustomerTimeline(Number(id)).then(r => setTimeline(r.data)),
    ]).finally(() => setLoading(false))
  }, [id])

  const startEdit = (field: string, value: string) => {
    setEditing(field)
    setEditValue(value || "")
  }

  const saveEdit = async () => {
    if (!editing) return
    try {
      await updateCustomer(Number(id), { [editing]: editValue })
      setCustomer((prev: any) => ({ ...prev, [editing]: editValue }))
    } catch (e) {
      console.error(e)
    }
    setEditing(null)
  }

  if (loading) {
    return (
      <AppShell>
        <div className="p-8 max-w-4xl mx-auto space-y-4 animate-pulse">
          <div className="h-8 bg-gray-100 rounded w-1/3" />
          <div className="h-24 bg-gray-100 rounded" />
        </div>
      </AppShell>
    )
  }

  if (!customer) {
    return (
      <AppShell>
        <div className="p-8 text-center text-gray-400">
          <User size={40} className="mx-auto mb-3 opacity-30" />
          <p>Customer not found.</p>
          <Link href="/customers" className="text-indigo-600 text-sm hover:underline mt-2 inline-block">← Back to customers</Link>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="p-8 max-w-4xl mx-auto">
        {/* Back */}
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-6 transition">
          <ArrowLeft size={15} /> Back to customers
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Customer card */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-14 h-14 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-xl">
                  {(customer.name || customer.email)[0].toUpperCase()}
                </div>
                <div>
                  <p className="font-bold text-gray-900">{customer.name || customer.email}</p>
                  <p className="text-xs text-gray-400">{customer.email}</p>
                </div>
              </div>

              <div className="space-y-3">
                {/* Company */}
                <EditableField
                  icon={<Building2 size={14} className="text-gray-400" />}
                  label="Company"
                  field="company"
                  value={customer.company}
                  editing={editing}
                  editValue={editValue}
                  onEdit={startEdit}
                  onChange={setEditValue}
                  onSave={saveEdit}
                  onCancel={() => setEditing(null)}
                />
                {/* Phone */}
                <EditableField
                  icon={<Phone size={14} className="text-gray-400" />}
                  label="Phone"
                  field="phone"
                  value={customer.phone}
                  editing={editing}
                  editValue={editValue}
                  onEdit={startEdit}
                  onChange={setEditValue}
                  onSave={saveEdit}
                  onCancel={() => setEditing(null)}
                />
                {/* Notes */}
                <EditableField
                  icon={<Edit2 size={14} className="text-gray-400" />}
                  label="Notes"
                  field="notes"
                  value={customer.notes}
                  editing={editing}
                  editValue={editValue}
                  onEdit={startEdit}
                  onChange={setEditValue}
                  onSave={saveEdit}
                  onCancel={() => setEditing(null)}
                  multiline
                />
              </div>

              <div className="mt-5 pt-4 border-t border-gray-50 space-y-1.5">
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <Mail size={12} />
                  <span>{customer.email_count} emails</span>
                </div>
                {customer.last_contact && (
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Clock size={12} />
                    <span>Last contact {formatDistanceToNow(new Date(customer.last_contact), { addSuffix: true })}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-5">Email Timeline</h3>
              {timeline.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <Mail size={32} className="mx-auto mb-3 opacity-30" />
                  <p className="text-sm">No emails yet</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                  {timeline.map((item: any) => (
                    <div key={item.id} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className="w-2 h-2 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                        <div className="w-px flex-1 bg-gray-100 mt-1" />
                      </div>
                      <div className="flex-1 min-w-0 pb-4">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-gray-400">
                            {formatDistanceToNow(new Date(item.received_at), { addSuffix: true })}
                          </span>
                          <span className="text-xs text-gray-300">·</span>
                          <span className="text-xs text-gray-400">{item.inbox}</span>
                          {item.category && (
                            <span className={`text-xs px-1.5 py-0.5 rounded ${categoryBadge[item.category] || "bg-gray-100 text-gray-500"}`}>
                              {item.category}
                            </span>
                          )}
                        </div>
                        <p className="text-sm font-medium text-gray-800 truncate">{item.subject || "(no subject)"}</p>
                        {item.ai_summary ? (
                          <p className="text-xs text-indigo-600 mt-0.5">{item.ai_summary}</p>
                        ) : item.body_snippet ? (
                          <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{item.body_snippet}</p>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}

function EditableField({ icon, label, field, value, editing, editValue, onEdit, onChange, onSave, onCancel, multiline = false }: any) {
  const isEditing = editing === field

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1">
        {icon}
        <span className="text-xs text-gray-400 font-medium">{label}</span>
        {!isEditing && (
          <button onClick={() => onEdit(field, value)} className="ml-auto p-0.5 text-gray-300 hover:text-indigo-500 opacity-0 group-hover:opacity-100 transition">
            <Edit2 size={11} />
          </button>
        )}
      </div>
      {isEditing ? (
        <div className="flex gap-1">
          {multiline ? (
            <textarea
              value={editValue}
              onChange={e => onChange(e.target.value)}
              rows={3}
              className="flex-1 text-sm border border-indigo-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
              autoFocus
            />
          ) : (
            <input
              value={editValue}
              onChange={e => onChange(e.target.value)}
              className="flex-1 text-sm border border-indigo-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
              autoFocus
              onKeyDown={e => { if (e.key === 'Enter') onSave(); if (e.key === 'Escape') onCancel(); }}
            />
          )}
          <button onClick={onSave} className="p-1 text-emerald-600 hover:bg-emerald-50 rounded"><Check size={14} /></button>
          <button onClick={onCancel} className="p-1 text-gray-400 hover:bg-gray-100 rounded"><X size={14} /></button>
        </div>
      ) : (
        <button onClick={() => onEdit(field, value)} className="w-full text-left text-sm text-gray-700 hover:text-indigo-600 transition min-h-[1.5rem]">
          {value || <span className="text-gray-300 italic">Click to add</span>}
        </button>
      )}
    </div>
  )
}
