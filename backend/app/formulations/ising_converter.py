"""QUBO to Ising spin Hamiltonian conversion."""

from typing import Dict, Any, List, Tuple, Union
from backend.app.domain.formulations.models import QuboModel, IsingModel


class IsingConverter:
    """
    Converts a canonical upper-triangular QUBO model to an equivalent Ising spin Hamiltonian:
    Spin convention:
        x_i = (1 - Z_i) / 2  where Z_i in {-1, +1}
    Transformation equations:
        For QUBO: E(x) = sum_i a_i * x_i + sum_{i < j} b_ij * x_i * x_j + c
        Equivalent Ising: H(Z) = C + sum_i h_i * Z_i + sum_{i < j} J_ij * Z_i * Z_j
        where:
            h_i = - a_i / 2 - 1/4 * sum_{j != i} b_{min(i,j), max(i,j)}
            J_ij = b_ij / 4   (for i < j)
            C = c + 1/2 * sum_i a_i + 1/4 * sum_{i < j} b_ij
    Energy equivalence guarantee:
        E_QUBO(x) == H_Ising(Z) for all corresponding configurations x in {0,1}^n, Z in {-1,+1}^n.
    """

    @staticmethod
    def qubo_to_ising(qubo: QuboModel) -> IsingModel:
        var_order = qubo.variable_order
        n = len(var_order)
        var_to_idx = {v: i for i, v in enumerate(var_order)}

        # Extract numerical arrays
        # a_i: linear coefficients
        a = [0.0] * n
        for v_name, coef in qubo.linear_terms.items():
            if v_name in var_to_idx:
                a[var_to_idx[v_name]] = float(coef)

        # b_ij: quadratic coefficients for i < j
        b: Dict[Tuple[int, int], float] = {}
        for key, coef in qubo.quadratic_terms.items():
            if "," in key:
                v1, v2 = key.split(",", 1)
                if v1 in var_to_idx and v2 in var_to_idx:
                    i = var_to_idx[v1]
                    j = var_to_idx[v2]
                    idx_i, idx_j = min(i, j), max(i, j)
                    b[(idx_i, idx_j)] = float(coef)

        c = float(qubo.offset)

        # 1. Compute constant offset C
        # C = c + 1/2 * sum_i a_i + 1/4 * sum_{i < j} b_ij
        sum_a = sum(a)
        sum_b = sum(b.values())
        ising_offset = c + 0.5 * sum_a + 0.25 * sum_b

        # 2. Compute local fields h_i
        # h_i = - a_i / 2 - 1/4 * sum_{j != i} b_{min(i,j), max(i,j)}
        h = [0.0] * n
        for i in range(n):
            sum_b_incident = 0.0
            for j in range(n):
                if i != j:
                    pair = (min(i, j), max(i, j))
                    if pair in b:
                        sum_b_incident += b[pair]
            h[i] = - 0.5 * a[i] - 0.25 * sum_b_incident

        # 3. Compute couplings J_ij
        # J_ij = b_ij / 4
        j_couplings: Dict[Tuple[int, int], float] = {}
        for (i, j), b_val in b.items():
            j_couplings[(i, j)] = 0.25 * b_val

        # 4. Spin mapping and dictionaries
        spin_names = [f"Z_{v}" for v in var_order]
        spin_mapping = {var_order[i]: spin_names[i] for i in range(n)}

        local_fields_dict = {
            spin_names[i]: round(h[i], 6)
            for i in range(n)
            if abs(h[i]) > 1e-12
        }

        couplings_dict = {
            f"{spin_names[i]},{spin_names[j]}": round(j_val, 6)
            for (i, j), j_val in sorted(j_couplings.items())
            if abs(j_val) > 1e-12
        }

        # 5. Build LaTeX expression
        latex_parts = []
        if abs(ising_offset) > 1e-9:
            latex_parts.append(f"{ising_offset:+.4f}")
        for s_name, h_val in sorted(local_fields_dict.items()):
            latex_parts.append(f"{h_val:+.4f} \\, {s_name}")
        for pair_key, j_val in sorted(couplings_dict.items()):
            s1, s2 = pair_key.split(",")
            latex_parts.append(f"{j_val:+.4f} \\, {s1}{s2}")

        latex_expr = "H = " + (" ".join(latex_parts) if latex_parts else "0.0")

        metadata = {
            "num_spins": n,
            "num_local_fields": len(local_fields_dict),
            "num_couplings": len(couplings_dict),
            "qubo_offset": c,
            "ising_offset": round(ising_offset, 6),
            "convention": "x_i = (1 - Z_i) / 2 with Z_i in {-1, +1}",
        }

        return IsingModel(
            variable_order=spin_names,
            local_fields=local_fields_dict,
            couplings=couplings_dict,
            offset=round(ising_offset, 6),
            spin_mapping=spin_mapping,
            latex_expression=latex_expr,
            metadata=metadata,
        )

    @staticmethod
    def evaluate_energy(ising: IsingModel, z: Union[List[int], Dict[str, int]]) -> float:
        """
        Evaluate exact Ising Hamiltonian energy H(Z) = C + sum_i h_i Z_i + sum_{i < j} J_ij Z_i Z_j
        for spin assignment Z with Z_i in {-1, +1}.
        """
        spin_order = ising.variable_order
        n = len(spin_order)
        spin_to_idx = {s: i for i, s in enumerate(spin_order)}

        z_vec = [1] * n
        if isinstance(z, list):
            if len(z) != n:
                raise ValueError(f"Spin vector length ({len(z)}) does not match spin count ({n})")
            for idx, val in enumerate(z):
                if val not in (-1, 1):
                    raise ValueError(f"Spin value at index {idx} must be -1 or +1, got {val}")
                z_vec[idx] = val
        elif isinstance(z, dict):
            for s_name, val in z.items():
                if s_name in spin_to_idx:
                    idx = spin_to_idx[s_name]
                    if val not in (-1, 1):
                        raise ValueError(f"Spin '{s_name}' must be -1 or +1, got {val}")
                    z_vec[idx] = val
        else:
            raise TypeError(f"Unsupported spin configuration type: {type(z).__name__}")

        energy = float(ising.offset)

        # Local fields: sum_i h_i * Z_i
        for s_name, h_val in ising.local_fields.items():
            idx = spin_to_idx[s_name]
            energy += h_val * z_vec[idx]

        # Couplings: sum_{i < j} J_ij * Z_i * Z_j
        for pair_key, j_val in ising.couplings.items():
            s1, s2 = pair_key.split(",", 1)
            idx1 = spin_to_idx[s1]
            idx2 = spin_to_idx[s2]
            energy += j_val * z_vec[idx1] * z_vec[idx2]

        return energy

    @staticmethod
    def binary_to_spin(x_vec: List[int]) -> List[int]:
        """Convert binary assignment x in {0, 1}^n to spin vector Z in {-1, +1}^n via Z_i = 1 - 2*x_i."""
        return [1 - 2 * int(xi) for xi in x_vec]

    @staticmethod
    def spin_to_binary(z_vec: List[int]) -> List[int]:
        """Convert spin vector Z in {-1, +1}^n to binary assignment x in {0, 1}^n via x_i = (1 - Z_i) / 2."""
        return [(1 - int(zi)) // 2 for zi in z_vec]
