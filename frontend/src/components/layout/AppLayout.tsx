import React, { useState } from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { NavigationItemKey } from '../../types'
import { HealthStatus } from '../../hooks/useBackendHealth'

interface AppLayoutProps {
  activeTab: NavigationItemKey
  onSelectTab: (tab: NavigationItemKey) => void
  onOpenLanding: () => void
  healthStatus: HealthStatus
  backendVersion?: string
  children: React.ReactNode
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  activeTab,
  onSelectTab,
  onOpenLanding,
  healthStatus,
  backendVersion,
  children,
}) => {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false)

  return (
    <div className="flex h-screen bg-midnight-950 text-scientific-text overflow-hidden font-sans relative">
      {/* Accessible skip link for keyboard/screen-reader users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-scientific-accent focus:text-midnight-950 focus:font-semibold focus:rounded focus:outline-none focus:ring-2 focus:ring-white"
      >
        Skip to main content
      </a>

      {/* Mobile Backdrop Overlay */}
      {isMobileNavOpen && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-xs z-30 md:hidden"
          onClick={() => setIsMobileNavOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        healthStatus={healthStatus}
        backendVersion={backendVersion}
        isOpen={isMobileNavOpen}
        onClose={() => setIsMobileNavOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          activeTab={activeTab}
          onSelectTab={onSelectTab}
          onOpenLanding={onOpenLanding}
          onToggleMobileNav={() => setIsMobileNavOpen(!isMobileNavOpen)}
        />
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto bg-midnight-950/50 p-4 sm:p-6 focus:outline-none"
        >
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  )
}
