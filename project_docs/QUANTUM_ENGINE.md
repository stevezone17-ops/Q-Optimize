# Quantum Optimization Engine

## Purpose
Implement QAOA for supported combinatorial optimization problems using Qiskit and simulation. Clearly label simulator results; simulation is not quantum hardware execution.

## QUBO convention
Document one convention consistently, for example:
\[
E(x)=x^TQx+c,\quad x_i\in\{0,1\}.
\]
Specify full-matrix versus upper-triangular storage and avoid double-counting off-diagonal terms.

## QUBO-to-Ising
Use spin variables `s_i ∈ {-1,+1}` and document the convention:
\[
x_i=(1-s_i)/2.
\]
Substitute into the QUBO, collect constant, linear, and pairwise terms, and test energy equivalence exhaustively on small instances.

## QAOA
For cost Hamiltonian `H_C` and mixer `H_M`:
\[
|\gamma,\beta\rangle =
e^{-i\beta_pH_M}e^{-i\gamma_pH_C}\cdots
e^{-i\beta_1H_M}e^{-i\gamma_1H_C}|+\rangle^{\otimes n}.
\]
A classical optimizer updates parameters to minimize expected cost. Measurements are mapped to candidates and independently evaluated.

## Configuration
Record QAOA depth `p`, shots, optimizer, initial parameters, iteration/evaluation budget, seed, simulator backend, noise model, timeout, and resource limits.

## Adaptive QAOA research
Define each adaptation rule explicitly. Candidate strategies include multi-start initialization, warm starts when justified, and layer-wise initialization. Compare with a baseline under equivalent evaluation budgets. Do not call a strategy adaptive unless its update rule is implemented and documented.

## Output
Return best measured bitstring, counts/distribution, independently computed objective and feasibility, convergence trace, circuit depth/gate counts where available, shots, depth, optimizer, seed, simulator/library versions, noise settings, warnings, and limitations.

## Correctness
Test Hamiltonian signs, bitstring mapping, energy offsets, objective direction, penalty coefficients, and exact small-instance comparisons. State-vector simulation scales exponentially with qubit count; impose limits.
