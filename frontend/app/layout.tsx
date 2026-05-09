import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Stock Intelligence Platform",
  description: "Real-time trading research dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0a0f] text-[#e8e8f0] antialiased">
        {children}
      </body>
    </html>
  );
}
