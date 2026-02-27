import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Family Dashboard",
  description: "Our family hub",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background antialiased">
        {children}
      </body>
    </html>
  );
}
