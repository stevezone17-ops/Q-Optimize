"""Unit tests for Stage 6.2: Adaptive QAOA Parameter Initialization Strategies."""

import pytest
import numpy as np

from backend.app.solvers.quantum.adaptive.adaptive_config import InitializationStrategyType
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import IncompatibleWarmStartError
from backend.app.solvers.quantum.adaptive.initializers import (
    BaseParameterInitializer,
    RandomInitializer,
    LinearRampInitializer,
    FourierInitializer,
    WarmStartInitializer,
    CustomInitializer,
    ParameterInitializerFactory,
)


def test_random_initializer_dimensions_and_ranges():
    """Verify RandomInitializer bounds and length guarantees."""
    init = RandomInitializer(seed=42)
    for p in [1, 2, 4, 7]:
        gamma, beta = init.initialize(p)
        assert len(gamma) == p
        assert len(beta) == p
        for g in gamma:
            assert 0.0 <= g <= 2.0 * np.pi
        for b in beta:
            assert 0.0 <= b <= np.pi


def test_random_initializer_reproducibility():
    """Verify seed guarantees exact reproducibility."""
    init1 = RandomInitializer(seed=12345)
    init2 = RandomInitializer(seed=12345)
    init3 = RandomInitializer(seed=99999)

    g1, b1 = init1.initialize(3)
    g2, b2 = init2.initialize(3)
    g3, b3 = init3.initialize(3)

    assert g1 == g2
    assert b1 == b2
    assert g1 != g3


def test_linear_ramp_initializer():
    """Verify LinearRampInitializer adiabatic Trotter schedule."""
    ramp = LinearRampInitializer(delta_t=1.0)

    # p = 1: symmetric midpoint
    g1, b1 = ramp.initialize(1)
    assert len(g1) == 1 and len(b1) == 1
    assert g1[0] == pytest.approx(0.5)
    assert b1[0] == pytest.approx(0.5)

    # p = 4: linear progression
    g4, b4 = ramp.initialize(4)
    assert len(g4) == 4 and len(b4) == 4
    # gamma increases
    for i in range(len(g4) - 1):
        assert g4[i] < g4[i + 1]
    # beta decreases
    for i in range(len(b4) - 1):
        assert b4[i] > b4[i + 1]


def test_fourier_initializer_analytical_equivalence():
    """Verify Fourier-domain parameterization against analytical cosine/sine values."""
    fourier = FourierInitializer(q_order=1)
    u = [1.0]
    v = [1.0]
    # For p = 2, l = 1, k = 0: angle = (1 * 1 * pi) / (2 * 2) = pi / 4
    # cos(pi/4) = sqrt(2)/2 ~= 0.70710678
    # sin(pi/4) = sqrt(2)/2 ~= 0.70710678
    gamma, beta = fourier.fourier_to_angles(u, v, p=2)
    assert len(gamma) == 2
    assert len(beta) == 2
    assert gamma[0] == pytest.approx(np.cos(np.pi / 4.0), rel=1e-5)
    assert beta[0] == pytest.approx(np.sin(np.pi / 4.0), rel=1e-5)

    # For l = 2: angle = (1 * 2 * pi) / 4 = pi / 2
    # cos(pi/2) = 0.0, sin(pi/2) = 1.0
    assert gamma[1] == pytest.approx(0.0, abs=1e-6)
    assert beta[1] == pytest.approx(1.0, rel=1e-5)


def test_fourier_initializer_default_coefficients():
    """Verify FourierInitializer runs with default harmonic coefficients."""
    fourier = FourierInitializer(q_order=2)
    gamma, beta = fourier.initialize(p=5)
    assert len(gamma) == 5
    assert len(beta) == 5
    assert all(isinstance(x, float) for x in gamma)
    assert all(isinstance(x, float) for x in beta)


def test_warm_start_initializer_same_depth():
    """Verify WarmStartInitializer preserves exact parameters at same depth."""
    prior_g = [0.12, 0.45]
    prior_b = [0.89, 0.63]
    ws = WarmStartInitializer(prior_gamma=prior_g, prior_beta=prior_b)
    g, b = ws.initialize(p=2)
    assert g == prior_g
    assert b == prior_b


def test_warm_start_initializer_interpolation():
    """Verify WarmStartInitializer interpolates parameters when expanding depth."""
    prior_g = [0.1, 0.9]
    prior_b = [0.8, 0.2]
    ws = WarmStartInitializer(prior_gamma=prior_g, prior_beta=prior_b)
    g, b = ws.initialize(p=4)
    assert len(g) == 4
    assert len(b) == 4
    # Endpoints should match prior endpoints
    assert g[0] == pytest.approx(0.1)
    assert g[-1] == pytest.approx(0.9)
    assert b[0] == pytest.approx(0.8)
    assert b[-1] == pytest.approx(0.2)


def test_warm_start_initializer_missing_inputs_fails():
    """Verify missing inputs raise IncompatibleWarmStartError."""
    ws = WarmStartInitializer()
    with pytest.raises(IncompatibleWarmStartError):
        ws.initialize(2)

    ws_mismatch = WarmStartInitializer(prior_gamma=[0.1, 0.2], prior_beta=[0.1])
    with pytest.raises(IncompatibleWarmStartError):
        ws_mismatch.initialize(2)


def test_custom_initializer():
    """Verify CustomInitializer strict dimension enforcement."""
    cust = CustomInitializer(gamma=[0.1, 0.2], beta=[0.3, 0.4])
    g, b = cust.initialize(2)
    assert g == [0.1, 0.2]
    assert b == [0.3, 0.4]

    with pytest.raises(ValueError, match="dimension mismatch"):
        cust.initialize(3)


def test_parameter_initializer_factory():
    """Verify ParameterInitializerFactory creates proper instances for all types."""
    for init_type in InitializationStrategyType:
        if init_type == InitializationStrategyType.CUSTOM:
            init = ParameterInitializerFactory.get_initializer(
                init_type, gamma=[0.1], beta=[0.2]
            )
        elif init_type == InitializationStrategyType.WARM_START:
            init = ParameterInitializerFactory.get_initializer(
                init_type, prior_gamma=[0.1], prior_beta=[0.2]
            )
        else:
            init = ParameterInitializerFactory.get_initializer(init_type)
        assert isinstance(init, BaseParameterInitializer)

    with pytest.raises(ValueError, match="Unknown initialization strategy"):
        ParameterInitializerFactory.get_initializer("quantum_superposition_xyz")
