import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MAGE-Doc",
  description: "Multimodal Agentic RAG for long-PDF reasoning.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

