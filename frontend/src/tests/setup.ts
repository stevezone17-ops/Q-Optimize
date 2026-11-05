import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Default mock for global.fetch in tests
global.fetch = vi.fn().mockImplementation((url: string) => {
  if (url.includes('/validate')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          is_valid: true,
          status: 'valid',
          issues: [],
          variables: [{ name: 'x_v', var_type: 'binary', count: 4, bounds: [0, 1], description: 'test' }],
          constraints: [],
          metadata: {},
          validated_at: new Date().toISOString(),
        }),
    })
  }
  if (url.includes('/evaluate')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          problem_type: 'max_cut',
          objective_sense: 'maximize',
          objective_value: 14.0,
          is_feasible: true,
          violations: [],
          details: {
            crossing_edge_count: 4,
            total_edge_count: 5,
            cut_fraction: 0.8,
            partition_0: ['A', 'C'],
            partition_1: ['B', 'D'],
          },
          evaluated_at: new Date().toISOString(),
        }),
    })
  }
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
  })
})

afterEach(() => {
  cleanup()
})
