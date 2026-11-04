import React, { useState } from 'react'
import { NavigationItemKey, ProblemType } from '../types'
import { useBackendHealth } from '../hooks/useBackendHealth'
import { AppLayout } from '../components/layout/AppLayout'
import { LandingPage } from '../pages/LandingPage'
import { OverviewPage } from '../pages/OverviewPage'
import { ProblemBuilderPage } from '../pages/ProblemBuilderPage'
import { FormulationStudioPage } from '../pages/FormulationStudioPage'
import { QuantumLabPage } from '../pages/QuantumLabPage'
import { ClassicalLabPage } from '../pages/ClassicalLabPage'
import { ComparisonLabPage } from '../pages/ComparisonLabPage'
import { MyExperimentsPage } from '../pages/MyExperimentsPage'
import { LearnPage } from '../pages/LearnPage'
import { SettingsPage } from '../pages/SettingsPage'

export const App: React.FC = () => {
  const [view, setView] = useState<'landing' | 'workspace'>('landing')
  const [activeTab, setActiveTab] = useState<NavigationItemKey>('overview')
  const [, setSelectedProblemType] = useState<ProblemType>('max_cut')

  const { health, status, refetch } = useBackendHealth()

  const handleSelectProblemType = (type: ProblemType) => {
    setSelectedProblemType(type)
    setActiveTab('problem-builder')
  }

  if (view === 'landing') {
    return <LandingPage onEnterWorkspace={() => setView('workspace')} />
  }

  return (
    <AppLayout
      activeTab={activeTab}
      onSelectTab={setActiveTab}
      onOpenLanding={() => setView('landing')}
      healthStatus={status}
      backendVersion={health?.version}
    >
      {activeTab === 'overview' && (
        <OverviewPage
          onNavigate={setActiveTab}
          onSelectProblemType={handleSelectProblemType}
          healthStatus={status}
          backendVersion={health?.version}
        />
      )}

      {activeTab === 'problem-builder' && <ProblemBuilderPage />}

      {activeTab === 'formulation-studio' && <FormulationStudioPage />}

      {activeTab === 'quantum-lab' && <QuantumLabPage />}

      {activeTab === 'classical-lab' && <ClassicalLabPage />}

      {activeTab === 'comparison-lab' && <ComparisonLabPage />}

      {activeTab === 'my-experiments' && <MyExperimentsPage />}

      {activeTab === 'learn' && <LearnPage />}

      {activeTab === 'settings' && (
        <SettingsPage
          healthStatus={status}
          healthData={health}
          onRefetchHealth={refetch}
        />
      )}
    </AppLayout>
  )
}

export default App
