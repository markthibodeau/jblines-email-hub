"use client"

import { useEffect, useState } from "react"
import AppShell from "@/components/AppShell"
import { getBilling, getBillingSummary, updateBilling } from "@/lib/api"
import { DollarSign, CheckCircle, Clock, AlertTriangle } from "lucide-react"

export default function BillingPage() {
  const [records, setRecords] = useState<any[]>([])
  const [summary, setSummary] = useState<any>({})
  const [filter, setFilter] = useState("")
  const [loading, setLoading] = useState(true)

  const load = async (status = "") => {
    setLoading(true)
    const [billRes, sumRes] = await Promise.all([
      getBilling(status ? { status } : {}),
      getBillingSummary(),
    ])
    setRecords(billRes.data)
    setSummary(sumRes.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const markPaid = async (id: number) => {
    await updateBilling(id, { status: "paid", paid_date: new Date().toISOString() })
    load(filter)
  }

  const totalPending = summary.pending?.total || 0
  const totalPaid = summary.paid?.total || 0
  const totalOverdue = summary.overdue?.total || 0

  return (
    <AppShell>
      <div className="p-8 max-w-6xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Billing</h2>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-xl border border-amber-100 p-5">
            <div className="flex items-center gap-2 mb-1">
              <Clock size={16} className="text-amber-500" />
              <span className="text-sm text-gray-500">Pending</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">${totalPending.toLocaleString()}</p>
            <p className="text-xs text-gray-400 mt-1">{summary.pending?.count || 0} invoices</p>
          </div>
          <div className="bg-white rounded-xl border border-emerald-100 p-5">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle size={16} className="text-emerald-500" />
              <span className="text-sm text-gray-500">Collected</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">${totalPaid.toLocaleString()}</p>
            <p className="text-xs text-gray-400 mt-1">{summary.paid?.count || 0} payments</p>
          </div>
          <div className="bg-white rounded-xl border border-red-100 p-5">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle size={16} className="text-red-500" />
              <span className="text-sm text-gray-500">Overdue</span>
            </div>
            <p className="text-2xl font-bold text-red-600">${totalOverdue.toLocaleString()}</p>
            <p className="text-xs text-gray-400 mt-1">{summary.overdue?.count || 0} invoices</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-5">
          {["", "pending", "paid", "overdue", "cancelled"].map((s) => (
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

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Customer</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Type</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Amount</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Invoice #</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Due</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i}>
                    {[...Array(7)].map((_, j) => (
                      <td key={j} className="px-5 py-4">
                        <div className="h-4 bg-gray-100 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : records.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-4">
                    <p className="font-medium text-gray-900">{b.customer_name || "Unknown"}</p>
                    <p className="text-xs text-gray-400">{b.customer_email}</p>
                  </td>
                  <td className="px-5 py-4 capitalize text-gray-600">{b.billing_type}</td>
                  <td className="px-5 py-4 font-medium text-gray-900">
                    {b.amount ? `$${b.amount.toLocaleString()}` : "—"}
                  </td>
                  <td className="px-5 py-4 text-gray-500">{b.invoice_number || "—"}</td>
                  <td className="px-5 py-4 text-gray-500">
                    {b.due_date ? new Date(b.due_date).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge status={b.status} />
                  </td>
                  <td className="px-5 py-4 text-right">
                    {b.status === "pending" && (
                      <button
                        onClick={() => markPaid(b.id)}
                        className="text-xs text-emerald-600 hover:text-emerald-800 font-medium"
                      >
                        Mark paid
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && records.length === 0 && (
            <div className="text-center py-16 text-gray-400">
              <DollarSign size={40} className="mx-auto mb-3 opacity-30" />
              <p>No billing records found.</p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-amber-100 text-amber-700",
    paid: "bg-emerald-100 text-emerald-700",
    overdue: "bg-red-100 text-red-700",
    cancelled: "bg-gray-100 text-gray-500",
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || "bg-gray-100 text-gray-500"}`}>
      {status}
    </span>
  )
}
