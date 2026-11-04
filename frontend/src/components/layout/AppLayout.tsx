import React from 'react'
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
  return (
    <div className="flex h-screen bg-midnight-950 text-scientific-text overflow-hidden font-sans">
      <Sidebar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        healthStatus={healthStatus}
        backendVersion={backendVersion}
      />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          activeTab={activeTab}
          onSelectTab={onSelectTab}
          onOpenLanding={onOpenLanding}
        />
        <main className="flex-1 overflow-y-auto bg-midnight-950/50 p-6">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  )
}
