import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CatalogIQ – AI Product Enrichment",
  description:
    "Enterprise AI Product Enrichment, Validation & Governance System for B2B Distributor Catalogs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
