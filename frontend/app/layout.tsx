import Link from "next/link";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main>
          <div className="row" style={{ marginBottom: 20 }}>
            <Link href="/prompts">Prompts</Link>
            <Link href="/publish-history">Publish History</Link>
          </div>
          {children}
        </main>
      </body>
    </html>
  );
}
