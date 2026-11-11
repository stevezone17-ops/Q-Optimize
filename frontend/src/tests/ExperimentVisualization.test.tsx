import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import {
  ObjectiveComparisonChart,
  RuntimeComparisonChart,
  ConvergenceChart,
  ScalabilityChart,
  QAOACircuitAnalyticsCard,
  AdaptiveQAOAAnalyticsChart,
  StatisticalBoxPlot,
  MaxCutGraphVisualizer,
  AssignmentMatrixViz,
  TSPRouteViz,
} from '../components/experiments/charts';

describe('Experiment Visualization Components', () => {
  it('renders ObjectiveComparisonChart correctly with data', () => {
    const data = [
      { algorithm: 'exact', best: 10, mean: 10 },
      { algorithm: 'simulated_annealing', best: 9.5, mean: 8.8 },
    ];
    render(<ObjectiveComparisonChart data={data} optimalValue={10} />);
    expect(screen.getByTestId('objective-comparison-chart')).toBeInTheDocument();
    expect(screen.getByText(/Optimum: 10.00/i)).toBeInTheDocument();
  });

  it('renders RuntimeComparisonChart correctly', () => {
    const data = [
      { algorithm: 'exact', mean_runtime: 0.05 },
      { algorithm: 'genetic_algorithm', mean_runtime: 0.25 },
    ];
    render(<RuntimeComparisonChart data={data} />);
    expect(screen.getByTestId('runtime-comparison-chart')).toBeInTheDocument();
  });

  it('renders ConvergenceChart with multi-algorithm curves', () => {
    const series = {
      simulated_annealing: [2.0, 5.0, 8.0, 10.0],
      genetic_algorithm: [1.5, 4.0, 7.5, 9.0],
    };
    render(<ConvergenceChart series={series} />);
    expect(screen.getByTestId('convergence-chart')).toBeInTheDocument();
  });

  it('renders ScalabilityChart across problem sizes', () => {
    const data = [
      { problem_size: 4, algorithm: 'sa', mean_runtime_seconds: 0.01 },
      { problem_size: 8, algorithm: 'sa', mean_runtime_seconds: 0.04 },
    ];
    render(<ScalabilityChart data={data} />);
    expect(screen.getByTestId('scalability-chart')).toBeInTheDocument();
  });

  it('renders QAOACircuitAnalyticsCard with quantum specs', () => {
    render(
      <QAOACircuitAnalyticsCard
        numQubits={6}
        circuitDepth={12}
        numLayersP={3}
        cnotCount={18}
        totalGates={42}
        shots={2048}
      />
    );
    expect(screen.getByTestId('qaoa-circuit-analytics-card')).toBeInTheDocument();
    expect(screen.getByText('p = 3')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
  });

  it('renders AdaptiveQAOAAnalyticsChart with depth steps', () => {
    render(<AdaptiveQAOAAnalyticsChart finalP={4} totalAdaptations={3} />);
    expect(screen.getByTestId('adaptive-qaoa-analytics-chart')).toBeInTheDocument();
    expect(screen.getByText('Final p = 4')).toBeInTheDocument();
  });

  it('renders StatisticalBoxPlot with quartiles', () => {
    const data = [
      { algorithm: 'sa', min: 5, q1: 7, median: 8, q3: 9, max: 10, ciLower: 7.2, ciUpper: 8.8 },
    ];
    render(<StatisticalBoxPlot data={data} />);
    expect(screen.getByTestId('statistical-box-plot')).toBeInTheDocument();
  });

  it('renders MaxCutGraphVisualizer with partitions', () => {
    render(
      <MaxCutGraphVisualizer
        numNodes={4}
        edgeList={[[0, 1], [1, 2], [2, 3], [3, 0]]}
        solutionPartition={[0, 1, 0, 1]}
      />
    );
    expect(screen.getByTestId('max-cut-visualizer')).toBeInTheDocument();
  });

  it('renders AssignmentMatrixViz with cost matrix and matching', () => {
    render(
      <AssignmentMatrixViz
        costMatrix={[
          [10, 5],
          [4, 12],
        ]}
        assignments={[1, 0]}
      />
    );
    expect(screen.getByTestId('assignment-matrix-viz')).toBeInTheDocument();
  });

  it('renders TSPRouteViz with city tour', () => {
    render(
      <TSPRouteViz
        numCities={4}
        coordinates={[[0, 0], [10, 0], [10, 10], [0, 10]]}
        tour={[0, 1, 2, 3]}
      />
    );
    expect(screen.getByTestId('tsp-route-viz')).toBeInTheDocument();
  });
});
