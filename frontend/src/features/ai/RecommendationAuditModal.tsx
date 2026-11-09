import React from 'react'
import { X, History } from 'lucide-react'
import { SolverRecommendation } from '../../types'

interface RecommendationAuditModalProps {
  isOpen: boolean
  onClose: () => void
  currentRecommendation: SolverRecommendation | null
  historicalRecommendations?: SolverRecommendation[]
  onSelectHistorical?: (rec: SolverRecommendation) => void
}

export const RecommendationAuditModal: React.FC<RecommendationAuditModalProps> = ({
  isOpen,
  onClose,
  currentRecommendation,
  historicalRecommendations = [],
  onSelectHistorical,
}) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" data-testid="recommendation-audit-modal">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-800/50">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            <h3 className="font-semibold text-slate-100 text-sm">Solver Recommendation Audit History</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-700/50 transition-colors"
            data-testid="close-audit-modal-btn"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs text-slate-300">
          {currentRecommendation && (
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-lg p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200 text-sm">Active Session Recommendation</span>
                <span className="text-[11px] text-slate-400">
                  {new Date(currentRecommendation.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded font-medium">
                  {currentRecommendation.recommended_solver}
                </span>
                <span className="text-slate-400">
                  Confidence: {(currentRecommendation.confidence_score * 100).toFixed(1)}%
                </span>
                <span className="text-slate-400 capitalize">
                  Source: {currentRecommendation.recommendation_source.replace(/_/g, ' ')}
                </span>
              </div>
              <p className="text-slate-400 text-[11px] leading-relaxed">{currentRecommendation.explanation}</p>
            </div>
          )}

          <div className="space-y-2">
            <h4 className="font-semibold text-slate-200 text-xs">Past Problem Recommendation Audits</h4>
            {historicalRecommendations.length === 0 ? (
              <p className="text-slate-500 italic py-4 text-center">
                No past recommendation audits recorded for this instance. New recommendations are logged automatically.
              </p>
            ) : (
              <div className="space-y-2">
                {historicalRecommendations.map((hist, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-slate-800/40 border border-slate-800 rounded-lg flex items-center justify-between hover:border-slate-700 transition-colors"
                  >
                    <div>
                      <div className="font-medium text-slate-200">{hist.recommended_solver}</div>
                      <div className="text-[11px] text-slate-400">
                        {new Date(hist.timestamp).toLocaleString()} • {hist.recommendation_source}
                      </div>
                    </div>
                    {onSelectHistorical && (
                      <button
                        onClick={() => onSelectHistorical(hist)}
                        className="px-2.5 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-xs transition-colors"
                      >
                        Inspect
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-800/30 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  )
}
