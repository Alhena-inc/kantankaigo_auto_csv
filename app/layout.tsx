import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'かんたん介護 スケジュール取得',
  description: 'かんたん介護ソフトからスケジュール情報を取得します',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  )
}
