import './globals.css';
import type { Metadata, Viewport } from 'next';
import PwaRegister from './PwaRegister';

export const metadata: Metadata = {
  title: 'MARKETPILOT AI',
  description: 'AI-powered market intelligence and paper trading workspace',
  manifest: '/manifest.json',
  applicationName: 'MARKETPILOT AI',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'MarketPilot'
  },
  icons: {
    icon: '/icon.svg',
    shortcut: '/icon.svg',
    apple: '/icon.svg'
  }
};

export const viewport: Viewport = {
  themeColor: '#080d18',
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover'
};

export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body><PwaRegister />{children}</body></html>;
}
