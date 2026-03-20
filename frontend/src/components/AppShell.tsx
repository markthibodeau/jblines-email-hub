"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Sidebar from "./Sidebar"

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<{ name: string; role: string } | null>(null)
  const router = useRouter()

  useEffect(() => {
    const stored = localStorage.getItem("user")
    const token = localStorage.getItem("token")
    if (!token || !stored) {
      router.push("/login")
      return
    }
    setUser(JSON.parse(stored))
  }, [router])

  if (!user) return (
    <div className="flex items-center justify-center h-screen text-gray-400">
      Loading...
    </div>
  )

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar user={user} />
      <main className="flex-1 overflow-y-auto bg-gray-50">
        {children}
      </main>
    </div>
  )
}
