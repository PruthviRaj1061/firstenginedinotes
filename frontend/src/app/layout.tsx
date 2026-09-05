import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Content Engine MVP",
  description: "Production-Grade AI Content Ingestion, Mode Processing & Extraction Pipeline",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-gray-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
