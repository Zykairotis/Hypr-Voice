'use client';

import { ContextDashboard } from '@/app/components/context/ContextDashboard';
import { ThemeProvider } from 'next-themes';

export default function ContextPage() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <div className="container mx-auto py-6 px-4">
        <ContextDashboard />
      </div>
    </ThemeProvider>
  );
}
