import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'RAG Pipeline - Legal Document Analysis',
  description: 'Advanced RAG Pipeline for Legal Document Analysis with Enhanced Case Metadata',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#374151',
              color: '#fff',
              border: '1px solid #4b5563',
            },
          }}
        />
      </body>
    </html>
  )
}
