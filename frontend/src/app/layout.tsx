import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Providers } from "./providers"
import Link from "next/link"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Availo — Trusted Resource Sharing Platform",
  description: "Institutional equipment sharing with automated AI condition inspection and cryptographically signed smart contracts.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-slate-50 text-slate-900 flex flex-col`}>
        <Providers>
          <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-lg shadow-sm">
                  A
                </span>
                <span className="font-bold text-xl tracking-tight text-gray-900">Availo</span>
              </Link>

              <nav className="flex items-center gap-6 text-sm font-medium text-gray-600">
                <Link href="/resources" className="hover:text-blue-600 transition">
                  Browse Resources
                </Link>
                <Link href="/bookings" className="hover:text-blue-600 transition">
                  My Bookings
                </Link>
                <Link href="/dashboard" className="hover:text-blue-600 transition">
                  Dashboard
                </Link>
                <Link href="/admin" className="text-purple-600 hover:text-purple-700 transition">
                  Admin Portal
                </Link>
                <Link
                  href="/login"
                  className="px-3.5 py-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-xs font-semibold transition"
                >
                  Account
                </Link>
              </nav>
            </div>
          </header>

          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          <footer className="border-t border-gray-200 bg-white py-6 text-center text-xs text-gray-400">
            Availo © 2026 · AI Automated Resource Sharing Platform · National Hackathon Edition
          </footer>
        </Providers>
      </body>
    </html>
  )
}
