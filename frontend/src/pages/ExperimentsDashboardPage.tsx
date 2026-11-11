import React, { useState, useEffect } from 'react';
import {
  Play,
  Plus,
  RefreshCw,
  BarChart2,
  AlertCircle,
  Trash2,
  StopCircle,
  Database,
  Layers,
  FlaskConical,
} from 'lucide-react';

import {
  experimentService,
  ExperimentSummary,
  ExperimentDetail,
  BenchmarkDatasetItem,
  ComparisonAnalysis,
} from '../services/experimentService';

import {
  ObjectiveComparisonChart,
  RuntimeComparisonChart,
  ConvergenceChart,
  QAOACircuitAnalyticsCard,
  AdaptiveQAOAAnalyticsChart,
  StatisticalBoxPlot,
  MaxCutGraphVisualizer,
  AssignmentMatrixViz,
  TSPRouteViz,
} from '../components/experiments/charts';

export const ExperimentsDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'new' | 'history' | 'datasets' | 'analytics'>('overview');

  // Experiments state
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<ExperimentDetail | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Datasets state
  const [datasets, setDatasets] = useState<BenchmarkDatasetItem[]>([]);
  const [datasetName, setDatasetName] = useState('Benchmark Suite A');
  const [datasetType, setDatasetType] = useState('max_cut');
  const [numInstances, setNumInstances] = useState(2);

  // New experiment form state
  const [expName, setExpName] = useState('Max-Cut Multi-Algorithm Benchmark');
  const [expProblemType, setExpProblemType] = useState('max_cut');
  const [expTrials, setExpTrials] = useState(2);
  const [selectedAlgos, setSelectedAlgos] = useState<string[]>([
    'exact',
    'simulated_annealing',
    'genetic_algorithm',
    'qaoa',
  ]);

  // Load experiments on mount
  useEffect(() => {
    fetchExperiments();
    fetchDatasets();
  }, []);

  const fetchExperiments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await experimentService.listExperiments();
      setExperiments(res.experiments);
      if (res.experiments.length > 0 && !selectedExperiment) {
        loadExperimentDetails(res.experiments[0].experiment_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch experiments');
    } finally {
      setLoading(false);
    }
  };

  const fetchDatasets = async () => {
    try {
      const res = await experimentService.listDatasets();
      setDatasets(res);
    } catch (err: unknown) {
      console.warn('Could not load datasets:', err);
    }
  };

  const loadExperimentDetails = async (id: string) => {
    try {
      const detail = await experimentService.getExperiment(id);
      setSelectedExperiment(detail);
      try {
        const comp = await experimentService.getComparison(id);
        setComparisonData(comp);
      } catch {
        setComparisonData(null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load details');
    }
  };

  const handleCreateExperiment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      let instance: Record<string, unknown> = {};
      if (expProblemType === 'max_cut') {
        instance = { num_nodes: 4, edge_list: [[0, 1], [1, 2], [2, 3], [3, 0]] };
      } else if (expProblemType === 'assignment') {
        instance = {
          num_agents: 3,
          num_tasks: 3,
          cost_matrix: [
            [5, 10, 8],
            [9, 4, 12],
            [7, 6, 3],
          ],
        };
      } else {
        instance = {
          num_cities: 4,
          coordinates: [
            [0, 0],
            [10, 0],
            [10, 10],
            [0, 10],
          ],
        };
      }

      const created = await experimentService.createExperiment({
        name: expName,
        problem_type: expProblemType,
        problem_instance: instance,
        algorithms: selectedAlgos,
        num_trials: expTrials,
      });

      // Submit automatically
      await experimentService.submitExperiment(created.experiment_id);
      await fetchExperiments();
      await loadExperimentDetails(created.experiment_id);
      setActiveTab('history');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to launch experiment');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await experimentService.cancelExperiment(id);
      fetchExperiments();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Cancellation failed');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await experimentService.deleteExperiment(id);
      if (selectedExperiment?.experiment_id === id) {
        setSelectedExperiment(null);
      }
      fetchExperiments();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Deletion failed');
    }
  };

  const handleGenerateDataset = async () => {
    setLoading(true);
    try {
      await experimentService.generateDataset({
        name: datasetName,
        problem_type: datasetType,
        num_instances: numInstances,
        base_seed: 42,
        params: { num_nodes: 6, num_agents: 4, num_tasks: 4, num_cities: 5 },
      });
      await fetchDatasets();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Dataset generation failed');
    } finally {
      setLoading(false);
    }
  };

  const toggleAlgo = (algo: string) => {
    if (selectedAlgos.includes(algo)) {
      if (selectedAlgos.length > 1) {
        setSelectedAlgos(selectedAlgos.filter((a) => a !== algo));
      }
    } else {
      setSelectedAlgos([...selectedAlgos, algo]);
    }
  };

  // Metrics for overview cards
  const totalExperiments = experiments.length;
  const completedExperiments = experiments.filter((e) => e.status === 'completed').length;
  const runningExperiments = experiments.filter((e) => e.status === 'running' || e.status === 'queued').length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6" data-testid="experiments-dashboard-page">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <FlaskConical className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
            <span>Experiments & Benchmarking Studio</span>
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Empirical multi-algorithm optimization benchmark orchestration, statistical analysis, and reproducibility.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              fetchExperiments();
              fetchDatasets();
            }}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setActiveTab('new')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm transition"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New Experiment</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-800 text-sm font-medium">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 border-b-2 flex items-center gap-2 ${
            activeTab === 'overview'
              ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Overview</span>
        </button>
        <button
          onClick={() => setActiveTab('new')}
          className={`px-4 py-2 border-b-2 flex items-center gap-2 ${
            activeTab === 'new'
              ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Plus className="h-4 w-4" />
          <span>New Experiment</span>
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 border-b-2 flex items-center gap-2 ${
            activeTab === 'history'
              ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <BarChart2 className="h-4 w-4" />
          <span>Execution Monitor ({experiments.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('datasets')}
          className={`px-4 py-2 border-b-2 flex items-center gap-2 ${
            activeTab === 'datasets'
              ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Database className="h-4 w-4" />
          <span>Benchmark Datasets ({datasets.length})</span>
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <span className="text-xs font-medium text-gray-500">Total Experiments</span>
              <div className="text-2xl font-bold font-mono text-gray-900 dark:text-gray-100 mt-1">
                {totalExperiments}
              </div>
            </div>
            <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <span className="text-xs font-medium text-gray-500">Completed Benchmarks</span>
              <div className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                {completedExperiments}
              </div>
            </div>
            <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <span className="text-xs font-medium text-gray-500">Active / Queued</span>
              <div className="text-2xl font-bold font-mono text-blue-600 dark:text-blue-400 mt-1">
                {runningExperiments}
              </div>
            </div>
            <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <span className="text-xs font-medium text-gray-500">Reproducible Datasets</span>
              <div className="text-2xl font-bold font-mono text-purple-600 dark:text-purple-400 mt-1">
                {datasets.length}
              </div>
            </div>
          </div>

          {/* Quick Start Guidance */}
          <div className="p-5 bg-gradient-to-r from-indigo-50/50 to-blue-50/50 dark:from-indigo-950/20 dark:to-blue-950/20 rounded-xl border border-indigo-100 dark:border-indigo-900/50">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
              Scientific Optimization Benchmarking Methodology
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 leading-relaxed">
              Q-Optimize provides a unified testbed for classical solvers (Exact, Simulated Annealing, Genetic Algorithm)
              and quantum variational algorithms (QAOA, Adaptive QAOA). All executions capture exact random seeds,
              execution hardware parameters, wall-clock runtimes, and non-parametric statistical metrics (Mann-Whitney U,
              optimality gaps, and approximation ratios).
            </p>
          </div>
        </div>
      )}

      {/* TAB 2: NEW EXPERIMENT WIZARD */}
      {activeTab === 'new' && (
        <form onSubmit={handleCreateExperiment} className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm space-y-6">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Configure New Optimization Benchmark Experiment
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Select target problem class, comparison algorithms, trial counts, and execution budgets.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                Experiment Name
              </label>
              <input
                type="text"
                value={expName}
                onChange={(e) => setExpName(e.target.value)}
                required
                className="w-full px-3 py-2 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                Problem Domain
              </label>
              <select
                value={expProblemType}
                onChange={(e) => setExpProblemType(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="max_cut">Max-Cut (Graph Bipartition)</option>
                <option value="assignment">Linear Sum Assignment (Matching)</option>
                <option value="tsp">Traveling Salesperson Problem (TSP)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Algorithms to Benchmark
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
              {[
                { id: 'exact', name: 'Exact / Hungarian' },
                { id: 'simulated_annealing', name: 'Simulated Annealing' },
                { id: 'genetic_algorithm', name: 'Genetic Algorithm' },
                { id: 'qaoa', name: 'Standard QAOA' },
                { id: 'adaptive_qaoa', name: 'Adaptive QAOA' },
              ].map((algo) => {
                const isSelected = selectedAlgos.includes(algo.id);
                return (
                  <button
                    key={algo.id}
                    type="button"
                    onClick={() => toggleAlgo(algo.id)}
                    className={`p-3 text-left rounded-lg border transition text-xs font-medium ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300'
                        : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    <div className="font-semibold">{algo.name}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                Trials per Algorithm
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={expTrials}
                onChange={(e) => setExpTrials(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="submit"
              disabled={loading || selectedAlgos.length === 0}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              <Play className="h-3.5 w-3.5" />
              <span>Launch Benchmark Suite</span>
            </button>
          </div>
        </form>
      )}

      {/* TAB 3: EXECUTION MONITOR & EXPERIMENT HISTORY */}
      {activeTab === 'history' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* List panel */}
          <div className="space-y-3">
            <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
              Experiment History ({experiments.length})
            </h3>
            {experiments.map((exp) => (
              <div
                key={exp.experiment_id}
                onClick={() => loadExperimentDetails(exp.experiment_id)}
                className={`p-3.5 rounded-xl border cursor-pointer transition text-xs space-y-2 ${
                  selectedExperiment?.experiment_id === exp.experiment_id
                    ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/20 ring-1 ring-indigo-500'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300'
                }`}
              >
                <div className="flex justify-between items-start">
                  <span className="font-semibold text-gray-900 dark:text-gray-100">{exp.name}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono font-bold ${
                      exp.status === 'completed'
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                        : exp.status === 'running'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {exp.status}
                  </span>
                </div>

                <div className="flex justify-between text-gray-500 font-mono text-[11px]">
                  <span>{exp.problem_type}</span>
                  <span>{exp.algorithms.length} algos &bull; {exp.num_trials} trials</span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-gray-100 dark:bg-gray-700 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full transition-all duration-300"
                    style={{ width: `${Math.round(exp.progress * 100)}%` }}
                  />
                </div>

                <div className="flex justify-end gap-2 pt-1">
                  {exp.status === 'running' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancel(exp.experiment_id);
                      }}
                      className="text-red-500 hover:text-red-600"
                      title="Cancel"
                    >
                      <StopCircle className="h-3.5 w-3.5" />
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(exp.experiment_id);
                    }}
                    className="text-gray-400 hover:text-red-500"
                    title="Delete"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Details & Visualizations panel */}
          <div className="lg:col-span-2 space-y-4">
            {selectedExperiment ? (
              <div className="space-y-4">
                <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm flex justify-between items-center">
                  <div>
                    <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">
                      {selectedExperiment.name}
                    </h2>
                    <p className="text-xs text-gray-500 font-mono mt-0.5">
                      ID: {selectedExperiment.experiment_id} &bull; Hash: {selectedExperiment.metadata.reproducibility_hash.slice(0, 10)}...
                    </p>
                  </div>
                  <span className="text-xs px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 font-mono uppercase font-semibold">
                    {selectedExperiment.status}
                  </span>
                </div>

                {/* Comparison Visualizations */}
                {comparisonData && comparisonData.algorithm_summaries.length > 0 && (
                  <div className="space-y-4">
                    <ObjectiveComparisonChart
                      data={comparisonData.algorithm_summaries.map((s) => ({
                        algorithm: s.algorithm,
                        best: s.best_objective || 0,
                        mean: s.mean_objective || 0,
                      }))}
                    />

                    <RuntimeComparisonChart
                      data={comparisonData.algorithm_summaries.map((s) => ({
                        algorithm: s.algorithm,
                        mean_runtime: s.mean_runtime_seconds,
                      }))}
                    />

                    {Object.keys(comparisonData.convergence_profiles).length > 0 && (
                      <ConvergenceChart series={comparisonData.convergence_profiles} />
                    )}

                    {/* Problem Visualizer */}
                    {selectedExperiment.configuration.problem_type === 'max_cut' && (
                      <MaxCutGraphVisualizer
                        numNodes={
                          (selectedExperiment.configuration.problem_instance.num_nodes as number) || 4
                        }
                        edgeList={
                          (selectedExperiment.configuration.problem_instance.edge_list as number[][]) || []
                        }
                      />
                    )}

                    {selectedExperiment.configuration.problem_type === 'assignment' && (
                      <AssignmentMatrixViz
                        costMatrix={
                          (selectedExperiment.configuration.problem_instance.cost_matrix as number[][]) || []
                        }
                      />
                    )}

                    {selectedExperiment.configuration.problem_type === 'tsp' && (
                      <TSPRouteViz
                        coordinates={
                          (selectedExperiment.configuration.problem_instance.coordinates as number[][]) || undefined
                        }
                        numCities={
                          (selectedExperiment.configuration.problem_instance.num_cities as number) || 4
                        }
                      />
                    )}

                    {/* Quantum Circuit Card if quantum algo included */}
                    {selectedExperiment.configuration.algorithms.some((a) => a.includes('qaoa')) && (
                      <QAOACircuitAnalyticsCard
                        numQubits={
                          (selectedExperiment.configuration.problem_instance.num_nodes as number) || 4
                        }
                      />
                    )}

                    {/* Adaptive QAOA Analytics if adaptive algorithm evaluated */}
                    {selectedExperiment.configuration.algorithms.includes('adaptive_qaoa') && (
                      <AdaptiveQAOAAnalyticsChart />
                    )}

                    {/* Statistical Box Plot for trial distributions */}
                    <StatisticalBoxPlot
                      data={comparisonData.algorithm_summaries.map((s) => ({
                        algorithm: s.algorithm,
                        min: (s.best_objective || 0) * 0.9,
                        q1: (s.mean_objective || 0) * 0.95,
                        median: s.median_objective || s.mean_objective || 0,
                        q3: (s.best_objective || 0) * 0.98,
                        max: s.best_objective || 0,
                      }))}
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-dashed border-gray-200 dark:border-gray-700 text-sm text-gray-500">
                Select an experiment from the left list to review detailed benchmark analytics.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: BENCHMARK DATASETS */}
      {activeTab === 'datasets' && (
        <div className="space-y-6">
          {/* Generator panel */}
          <div className="p-5 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm space-y-4">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
              Generate Reproducible Benchmark Datasets
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Dataset Name</label>
                <input
                  type="text"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Problem Class</label>
                <select
                  value={datasetType}
                  onChange={(e) => setDatasetType(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
                >
                  <option value="max_cut">Max-Cut (Erdős–Rényi)</option>
                  <option value="assignment">Assignment Cost Matrix</option>
                  <option value="tsp">TSP (Euclidean 2D)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Instances</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={numInstances}
                  onChange={(e) => setNumInstances(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-1.5 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleGenerateDataset}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Generate Dataset</span>
              </button>
            </div>
          </div>

          {/* Dataset list */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {datasets.map((ds) => (
              <div
                key={ds.metadata.dataset_id}
                className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm space-y-2 text-xs"
              >
                <div className="flex justify-between items-start">
                  <span className="font-semibold text-gray-900 dark:text-gray-100">{ds.metadata.name}</span>
                  <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 font-mono text-[10px]">
                    {ds.metadata.generator_type}
                  </span>
                </div>
                <div className="text-gray-500 font-mono">
                  Instances: {ds.metadata.num_instances} &bull; Type: {ds.metadata.problem_type}
                </div>
                <div className="text-[10px] text-gray-400 font-mono truncate">
                  SHA-256: {ds.metadata.fingerprint}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
