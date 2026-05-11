import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ManScout | Mantle Turing Test 2026",
  description:
    "ManScout: Autonomous AI agent that scans Mantle wallets, profiles profitable traders, and copy-trades autonomously.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${geist.className} bg-[#080C14] text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}
