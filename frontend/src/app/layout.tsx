import './globals.css';
import type { Metadata, Viewport } from 'next';
export const metadata: Metadata = { title: 'MARKETPILOT AI', description: 'AI-powered market intelligence and paper trading workspace', manifest: '/manifest.json' };
export const viewport: Viewport = { themeColor: '#080d18', width: 'device-width', initialScale: 1 };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) { return <html lang="en"><body>{children}</body></html>; }
