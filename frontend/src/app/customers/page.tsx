"use client"

import { useEffect, useState } from "react"
import AppShell from "@/components/AppShell"
import { getCustomers } from "@/lib/api"
import { Search, User, Building2, Phone, Clock } from "lucide-react"
import Link from "next/link"

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)

  const load = async (q = "") => {
    setLoading(true)
    const res = await getCustomers(q ? { search: q } : {})
    setCustomers(res.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    load(search)
  }

  return (
    <AppShell>
      <div className="p-8 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Customers</h2>
            <p className="text-sm text-gray-500 mt-1">{customers.length} contacts found</p>
          </div>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search customers..."
                className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 w-64"
              />
            </div>
            <button type="submit" className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
              Search
            </button>
          </form>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 animate-pulse">
                <div className="h-4 bg-gray-100 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {customers.map((c) => (
              <Link key={c.id} href={`/customers/${c.id}`}>
                <div className="bg-white rounded-xl border border-gray-100 p-5 hover:border-indigo-200 hover:shadow-sm transition-all cursor-pointer">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-semibold">
                      {(c.name || c.email)[0].toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold text-gray-900 truncate">{c.name || c.email}</p>
                      <p className="text-xs text-gray-400 truncate">{c.email}</p>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    {c.company && (
                      <div className="flex items-center gap-1.5 text-xs text-gray-500">
                        <Building2 size={12} /> {c.company}
                      </div>
                    )}
                    {c.phone && (
                      <div className="flex items-center gap-1.5 text-xs text-gray-500">
                        <Phone size={12} /> {c.phone}
                      </div>
                    )}
                    <div className="flex items-center gap-1.5 text-xs text-gray-400">
                      <Clock size={12} />
                      {c.last_contact ? `Last contact ${new Date(c.last_contact).toLocaleDateString()}` : "No contact yet"}
                      <span className="ml-auto bg-gray-50 px-2 py-0.5 rounded text-gray-500">{c.email_count} emails</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
            {customers.length === 0 && (
              <div className="col-span-3 text-center py-16 text-gray-400">
                <User size={40} className="mx-auto mb-3 opacity-30" />
                <p>No customers found. They'll appear here as emails are synced.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  )
}
