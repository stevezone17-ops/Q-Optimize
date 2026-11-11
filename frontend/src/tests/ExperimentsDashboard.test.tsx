import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ExperimentsDashboardPage } from '../pages/ExperimentsDashboardPage';
import { experimentService } from '../services/experimentService';

// Mock experimentService
vi.mock('../services/experimentService', () => ({
  experimentService: {
    listExperiments: vi.fn().mockResolvedValue({
      experiments: [
        {
          experiment_id: 'exp-123',
          name: 'Synthetic MaxCut Test',
          status: 'completed',
          problem_type: 'max_cut',
          algorithms: ['exact', 'simulated_annealing'],
          num_trials: 2,
          progress: 1.0,
          created_at: '2026-11-11T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    }),
    getExperiment: vi.fn().mockResolvedValue({
      experiment_id: 'exp-123',
      name: 'Synthetic MaxCut Test',
      status: 'completed',
      configuration: {
        algorithms: ['exact', 'simulated_annealing'],
        problem_type: 'max_cut',
        problem_instance: { num_nodes: 4, edge_list: [[0, 1], [1, 2]] },
        num_trials: 2,
        resource_budget: {},
        description: 'Test description',
        tags: ['benchmark'],
      },
      metadata: {
        created_at: '2026-11-11T00:00:00Z',
        python_version: '3.12.3',
        reproducibility_hash: 'abcdef1234567890',
      },
      results: [],
      progress: 1.0,
    }),
    getComparison: vi.fn().mockResolvedValue({
      problem_type: 'max_cut',
      problem_instance_summary: { size: 4 },
      algorithm_summaries: [
        {
          algorithm: 'exact',
          num_trials: 1,
          best_objective: 4.0,
          mean_objective: 4.0,
          mean_runtime_seconds: 0.01,
          feasibility_rate: 1.0,
        },
      ],
      pairwise_significance: [],
      convergence_profiles: {},
      runtime_breakdowns: {},
    }),
    listDatasets: vi.fn().mockResolvedValue([
      {
        metadata: {
          dataset_id: 'ds-1',
          name: 'Erdos-Renyi Graph Suite',
          problem_type: 'max_cut',
          generator_type: 'erdos_renyi',
          fingerprint: '1234567890abcdef',
          num_instances: 5,
          created_at: '2026-11-11T00:00:00Z',
        },
        instances: [],
      },
    ]),
    createExperiment: vi.fn().mockResolvedValue({ experiment_id: 'exp-new' }),
    submitExperiment: vi.fn().mockResolvedValue({ experiment_id: 'exp-new', status: 'queued', progress: 0.0 }),
    cancelExperiment: vi.fn().mockResolvedValue({ experiment_id: 'exp-123', status: 'cancelled' }),
    deleteExperiment: vi.fn().mockResolvedValue(undefined),
    generateDataset: vi.fn().mockResolvedValue({}),
  },
}));

describe('ExperimentsDashboardPage', () => {
  it('renders overview tab with metrics and title', async () => {
    render(<ExperimentsDashboardPage />);
    expect(screen.getByText('Experiments & Benchmarking Studio')).toBeInTheDocument();
    expect(screen.getByText('Total Experiments')).toBeInTheDocument();
    await waitFor(() => {
      expect(experimentService.listExperiments).toHaveBeenCalled();
    });
  });

  it('switches to new experiment tab and submits form', async () => {
    render(<ExperimentsDashboardPage />);
    const buttons = screen.getAllByRole('button', { name: /New Experiment/i });
    fireEvent.click(buttons[0]);

    expect(screen.getByText(/Configure New Optimization Benchmark Experiment/i)).toBeInTheDocument();
    const submitBtn = screen.getByRole('button', { name: /Launch Benchmark Suite/i });
    expect(submitBtn).toBeInTheDocument();

    const form = submitBtn.closest('form');
    expect(form).not.toBeNull();
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(experimentService.createExperiment).toHaveBeenCalled();
    });
  });

  it('switches to history monitor tab and displays experiment details', async () => {
    render(<ExperimentsDashboardPage />);
    await waitFor(() => {
      expect(experimentService.listExperiments).toHaveBeenCalled();
    });

    const historyTabBtn = screen.getByRole('button', { name: /Execution Monitor/i });
    fireEvent.click(historyTabBtn);

    const matches = await screen.findAllByText(/Synthetic MaxCut Test/i);
    expect(matches.length).toBeGreaterThan(0);
  });

  it('switches to benchmark datasets tab', async () => {
    render(<ExperimentsDashboardPage />);
    const datasetsTabBtn = screen.getByRole('button', { name: /Benchmark Datasets/i });
    fireEvent.click(datasetsTabBtn);

    expect(await screen.findByText(/Generate Reproducible Benchmark Datasets/i)).toBeInTheDocument();
    expect(await screen.findByText('Erdos-Renyi Graph Suite')).toBeInTheDocument();
  });
});
