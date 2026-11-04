import React, { useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { HealthStatus } from '../hooks/useBackendHealth'
import { healthService } from '../services/healthService'
import { BackendHealthResponse } from '../types'
import { CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react'

interface SettingsPageProps {
  healthStatus: HealthStatus
  healthData: BackendHealthResponse | null
  onRefetchHealth: () => void
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  healthStatus,
  healthData,
  onRefetchHealth,
}) => {
  const [apiUrl, setApiUrl] = useState(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  )
  const [testResult, setTestResult] = useState<string | null>(null)
  const [isTesting, setIsTesting] = useState(false)

  const handleTestConnection = async () => {
    setIsTesting(true)
    setTestResult(null)
    try {
      const data = await healthService.getHealth()
      setTestResult(`Successfully connected to ${data.service} (v${data.version}) in ${data.environment} mode.`)
      onRefetchHealth()
    } catch (err) {
      setTestResult(`Connection failed: ${(err as Error).message}`)
    } finally {
      setIsTesting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Backend API Configuration */}
        <Card className="bg-midnight-900/60 border-scientific-border space-y-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="accent">Networking</Badge>
              {healthStatus === 'connected' ? (
                <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> Live
                </span>
              ) : (
                <span className="text-[10px] text-rose-400 font-mono flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> Disconnected
                </span>
              )}
            </div>
            <CardTitle className="mt-2">Backend API Service</CardTitle>
            <CardDescription>
              Configures the base URL for the FastAPI REST server.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="API Base URL (VITE_API_BASE_URL)"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="font-mono text-xs"
              helperText="Default development endpoint: http://localhost:8000/api/v1"
            />

            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleTestConnection}
                isLoading={isTesting}
                leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
              >
                Test Connection
              </Button>
            </div>

            {testResult && (
              <p className={`text-xs font-mono p-2.5 rounded border ${
                testResult.startsWith('Successfully')
                  ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                  : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
              }`}>
                {testResult}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Database & Storage Status */}
        <Card className="bg-midnight-900/60 border-scientific-border space-y-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="violet">Persistence</Badge>
              <Badge variant="outline">MongoDB / Memory</Badge>
            </div>
            <CardTitle className="mt-2">Database Abstraction</CardTitle>
            <CardDescription>
              MongoDB connector with graceful in-memory development fallback:
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 font-mono text-xs">
            <div className="p-3 rounded bg-midnight-950 border border-scientific-border space-y-1">
              <div className="flex justify-between text-scientific-muted">
                <span>Storage Engine:</span>
                <span className="text-white font-semibold">
                  {healthData?.database?.engine || 'in_memory_fallback'}
                </span>
              </div>
              <div className="flex justify-between text-scientific-muted">
                <span>Connection Status:</span>
                <span className={healthData?.database?.connected ? 'text-emerald-400' : 'text-amber-400'}>
                  {healthData?.database?.connected ? 'Connected' : 'In-Memory Local Mode'}
                </span>
              </div>
              {healthData?.database?.message && (
                <div className="text-[11px] text-slate-400 pt-1">
                  {healthData.database.message}
                </div>
              )}
            </div>

            <p className="text-scientific-muted leading-relaxed">
              When MongoDB is running on port 27017, documents persist across server restarts.
              In development without MongoDB, an in-memory manager guarantees zero disruption.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Environment Diagnostic */}
      <Card className="bg-midnight-900/60 border-scientific-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>System & Dependency Environment</CardTitle>
            <Badge variant="gold">Phase 1 Foundation</Badge>
          </div>
          <CardDescription>
            Runtime environment and framework specifications:
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 rounded bg-midnight-950 border border-scientific-border">
              <span className="text-scientific-muted text-[10px] block">Frontend Framework</span>
              <span className="text-white font-semibold">React 18 & Vite</span>
            </div>
            <div className="p-3 rounded bg-midnight-950 border border-scientific-border">
              <span className="text-scientific-muted text-[10px] block">Backend Framework</span>
              <span className="text-white font-semibold">FastAPI & Pydantic v2</span>
            </div>
            <div className="p-3 rounded bg-midnight-950 border border-scientific-border">
              <span className="text-scientific-muted text-[10px] block">Python Runtime</span>
              <span className="text-white font-semibold">Python 3.12</span>
            </div>
            <div className="p-3 rounded bg-midnight-950 border border-scientific-border">
              <span className="text-scientific-muted text-[10px] block">Design System</span>
              <span className="text-white font-semibold">Tailwind CSS & Dark First</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
