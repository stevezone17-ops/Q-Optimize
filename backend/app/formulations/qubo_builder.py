"""Canonical QUBO builder with strict upper-triangular matrix conventions."""

import math
from typing import List, Dict, Tuple, Optional, Any, Union
from backend.app.domain.formulations.models import QuboModel


class QuboBuilder:
    """
    Builder and representation for Quadratic Unconstrained Binary Optimization (QUBO) problems.
    Mathematical formulation:
        min E(x) = x^T Q x + c = sum_i Q_ii x_i + sum_{i < j} Q_ij x_i x_j + c
    Upper-triangular convention:
        - Only terms with index i <= j are stored.
        - Linear terms are stored on the diagonal: Q_ii.
        - Quadratic cross-terms are stored in the strict upper-triangle: Q_ij (i < j).
        - Calling add_quadratic(u, v, val) with u > v automatically routes to (v, u).
        - Constant offset c is preserved separately.
    """

    def __init__(self, variable_order: List[str]):
        if not variable_order:
            raise ValueError("Variable order list cannot be empty.")
        if len(variable_order) != len(set(variable_order)):
            raise ValueError(f"Variable names must be unique. Received: {variable_order}")

        self.variable_order: List[str] = [str(v).strip() for v in variable_order]
        self._var_to_idx: Dict[str, int] = {v: i for i, v in enumerate(self.variable_order)}
        self.n: int = len(self.variable_order)

        # Storage:
        # linear: idx -> float
        # quadratic: (idx_i, idx_j) -> float with idx_i < idx_j
        self._linear: Dict[int, float] = {}
        self._quadratic: Dict[Tuple[int, int], float] = {}
        self._offset: float = 0.0
        self.penalties: Dict[str, float] = {}
        self.assumptions: List[str] = []
        self.metadata: Dict[str, Any] = {}

    @property
    def num_variables(self) -> int:
        return self.n

    def get_variable_index(self, var: str) -> int:
        if var not in self._var_to_idx:
            raise KeyError(f"Variable '{var}' is not in variable order: {self.variable_order}")
        return self._var_to_idx[var]

    def add_offset(self, val: float) -> None:
        """Add constant scalar offset c to the objective."""
        val_f = float(val)
        if not math.isfinite(val_f):
            raise ValueError(f"QUBO offset must be a finite number, got {val_f}")
        self._offset += val_f

    def add_linear(self, var: str, val: float) -> None:
        """
        Add coefficient to linear term x_i (diagonal Q_ii).
        Since x_i^2 = x_i for x_i in {0, 1}, linear terms belong on the diagonal.
        """
        idx = self.get_variable_index(var)
        val_f = float(val)
        if not math.isfinite(val_f):
            raise ValueError(f"Linear coefficient for '{var}' must be finite, got {val_f}")
        self._linear[idx] = self._linear.get(idx, 0.0) + val_f

    def add_quadratic(self, var1: str, var2: str, val: float) -> None:
        """
        Add coefficient to quadratic cross-term x_i * x_j.
        If var1 == var2, it is treated as a linear term (since x_i^2 = x_i).
        If var1 != var2, it is routed to the canonical upper-triangular pair (min(i,j), max(i,j)).
        """
        idx1 = self.get_variable_index(var1)
        idx2 = self.get_variable_index(var2)
        val_f = float(val)
        if not math.isfinite(val_f):
            raise ValueError(f"Quadratic coefficient for ('{var1}', '{var2}') must be finite, got {val_f}")

        if idx1 == idx2:
            self._linear[idx1] = self._linear.get(idx1, 0.0) + val_f
        else:
            i = min(idx1, idx2)
            j = max(idx1, idx2)
            self._quadratic[(i, j)] = self._quadratic.get((i, j), 0.0) + val_f

    def add_penalty_square(self, linear_terms: Dict[str, float], constant: float, multiplier: float) -> None:
        """
        Add quadratic penalty term of the form:
            multiplier * (sum_k a_k x_k + constant)^2
        Expanding:
            (sum_k a_k x_k + c)^2 = sum_k a_k^2 x_k^2 + 2 sum_{k < l} a_k a_l x_k x_l + 2 c sum_k a_k x_k + c^2
        Since x_k^2 = x_k:
            = sum_k (a_k^2 + 2 c a_k) x_k + 2 sum_{k < l} a_k a_l x_k x_l + c^2
        Multiplied by multiplier.
        """
        mult = float(multiplier)
        if not math.isfinite(mult):
            raise ValueError(f"Penalty multiplier must be finite, got {mult}")

        const_f = float(constant)
        # Constant offset contribution: multiplier * c^2
        self.add_offset(mult * (const_f ** 2))

        vars_list = list(linear_terms.keys())
        # Linear contributions: multiplier * (a_k^2 + 2 * c * a_k)
        for var in vars_list:
            a_k = float(linear_terms[var])
            linear_contrib = mult * (a_k ** 2 + 2.0 * const_f * a_k)
            self.add_linear(var, linear_contrib)

        # Quadratic cross-term contributions: multiplier * 2 * a_k * a_l
        for idx_k in range(len(vars_list)):
            for idx_l in range(idx_k + 1, len(vars_list)):
                var_k = vars_list[idx_k]
                var_l = vars_list[idx_l]
                a_k = float(linear_terms[var_k])
                a_l = float(linear_terms[var_l])
                quad_contrib = mult * 2.0 * a_k * a_l
                self.add_quadratic(var_k, var_l, quad_contrib)

    def to_dense_upper_triangular_matrix(self) -> List[List[float]]:
        """Construct full n x n upper-triangular matrix."""
        mat = [[0.0 for _ in range(self.n)] for _ in range(self.n)]
        for i, val in self._linear.items():
            mat[i][i] = val
        for (i, j), val in self._quadratic.items():
            mat[i][j] = val
        return mat

    def to_dense_symmetric_matrix(self) -> List[List[float]]:
        """
        Construct full n x n symmetric matrix Q_sym:
            Q_sym[i][i] = Q[i][i]
            Q_sym[i][j] = Q_sym[j][i] = Q[i][j] / 2  (for i != j)
        Satisfies: x^T Q_sym x = x^T Q_upper x.
        """
        mat = [[0.0 for _ in range(self.n)] for _ in range(self.n)]
        for i, val in self._linear.items():
            mat[i][i] = val
        for (i, j), val in self._quadratic.items():
            half_val = val / 2.0
            mat[i][j] = half_val
            mat[j][i] = half_val
        return mat

    def to_dict_coefficients(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Return human-readable linear and quadratic term dictionaries using variable names."""
        linear_dict = {
            self.variable_order[i]: round(val, 6)
            for i, val in sorted(self._linear.items())
            if abs(val) > 1e-12
        }
        quad_dict = {
            f"{self.variable_order[i]},{self.variable_order[j]}": round(val, 6)
            for (i, j), val in sorted(self._quadratic.items())
            if abs(val) > 1e-12
        }
        return linear_dict, quad_dict

    def evaluate_energy(self, x: Union[List[int], Dict[str, int], str]) -> float:
        """
        Evaluate exact scalar energy E(x) = x^T Q x + c for candidate binary assignment x.
        Accepts:
            - Ordered binary list: [0, 1, 0, 1]
            - Variable name mapping: {"x_0": 0, "x_1": 1}
            - Binary string: "0101"
        """
        x_vec: List[int] = [0] * self.n

        if isinstance(x, str):
            clean_str = x.strip()
            if len(clean_str) != self.n:
                raise ValueError(f"Binary string length ({len(clean_str)}) must match variable count ({self.n})")
            for idx, ch in enumerate(clean_str):
                if ch not in ('0', '1'):
                    raise ValueError(f"Invalid character in bitstring: '{ch}'")
                x_vec[idx] = int(ch)
        elif isinstance(x, list):
            if len(x) != self.n:
                raise ValueError(f"Vector length ({len(x)}) must match variable count ({self.n})")
            for idx, val in enumerate(x):
                if val not in (0, 1):
                    raise ValueError(f"Value at index {idx} must be binary 0 or 1, got {val}")
                x_vec[idx] = int(val)
        elif isinstance(x, dict):
            for var_name, val in x.items():
                if var_name in self._var_to_idx:
                    idx = self._var_to_idx[var_name]
                    if val not in (0, 1, 0.0, 1.0, True, False):
                        raise ValueError(f"Variable '{var_name}' must have binary value 0 or 1, got {val}")
                    x_vec[idx] = 1 if (val == 1 or val is True) else 0
        else:
            raise TypeError(f"Unsupported candidate assignment type: {type(x).__name__}")

        # Linear terms: sum_i Q_ii * x_i
        energy = self._offset
        for i, val in self._linear.items():
            if x_vec[i] == 1:
                energy += val

        # Quadratic cross-terms: sum_{i < j} Q_ij * x_i * x_j
        for (i, j), val in self._quadratic.items():
            if x_vec[i] == 1 and x_vec[j] == 1:
                energy += val

        return energy

    def build_model(self) -> QuboModel:
        """Compile and return the complete Pydantic QuboModel."""
        linear_dict, quad_dict = self.to_dict_coefficients()
        dense_matrix = self.to_dense_upper_triangular_matrix()

        # Compute metadata statistics
        non_zeros = len(linear_dict) + len(quad_dict)
        total_possible = self.n + (self.n * (self.n - 1)) // 2
        density = (non_zeros / total_possible) if total_possible > 0 else 0.0

        meta = {
            "num_variables": self.n,
            "num_linear_terms": len(linear_dict),
            "num_quadratic_terms": len(quad_dict),
            "total_non_zero_terms": non_zeros,
            "matrix_density": round(density, 4),
            "constant_offset": self._offset,
            **self.metadata,
        }

        return QuboModel(
            variable_order=self.variable_order,
            linear_terms=linear_dict,
            quadratic_terms=quad_dict,
            offset=self._offset,
            matrix=dense_matrix,
            penalties=self.penalties,
            assumptions=self.assumptions,
            metadata=meta,
        )
