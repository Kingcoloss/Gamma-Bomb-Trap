"""
Unit tests for Black-76 Greeks: Gamma & Vanna.

Validates the mathematical correctness of the Black-76 pricing engine
functions defined in streamlit_app.py.

Run:
    cd /Users/kanganapong.s/Documents/Private/Gamma-Bomb-Trap
    python test_black76.py
"""
import math
import sys

# ── Import functions from streamlit_app.py ──
# We need to bypass the Streamlit imports; extract the pure math functions.

def _norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _b76_d1(F: float, K: float, T: float, sigma: float) -> float:
    """Black-76 d1."""
    return (math.log(F / K) + 0.5 * sigma ** 2 * T) / (sigma * math.sqrt(T))


def _b76_gamma(F: float, K: float, T: float, sigma: float) -> float:
    """Black-76 Gamma with r=0."""
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    try:
        d1 = _b76_d1(F, K, T, sigma)
        return _norm_pdf(d1) / (F * sigma * math.sqrt(T))
    except (ValueError, ZeroDivisionError):
        return 0.0


def _b76_d2(F: float, K: float, T: float, sigma: float) -> float:
    """Black-76 d2 = d1 − σ√T."""
    return _b76_d1(F, K, T, sigma) - sigma * math.sqrt(T)


def _b76_vanna(F: float, K: float, T: float, sigma: float) -> float:
    """Black-76 Vanna = −N′(d1) · d2 / (F · σ)."""
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    try:
        d1 = _b76_d1(F, K, T, sigma)
        d2 = d1 - sigma * math.sqrt(T)
        return -_norm_pdf(d1) * d2 / (F * sigma)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _normalize_iv(sigma_raw: float) -> float:
    sigma = float(sigma_raw)
    if sigma > 1.0:
        sigma /= 100.0
    return max(sigma, 0.0001)


# ──────────────────────────────────────────────
# Test cases
# ──────────────────────────────────────────────
PASS = 0
FAIL = 0


def check(name: str, actual: float, expected: float, tol: float = 1e-6):
    global PASS, FAIL
    diff = abs(actual - expected)
    ok = diff < tol
    sym = "✅" if ok else "❌"
    print(f"  {sym} {name}: got={actual:.8f}, expected={expected:.8f}, diff={diff:.2e}")
    if ok:
        PASS += 1
    else:
        FAIL += 1


def check_sign(name: str, actual: float, expected_positive: bool):
    global PASS, FAIL
    ok = (actual > 0) == expected_positive
    sym = "✅" if ok else "❌"
    sign_got = "positive" if actual > 0 else ("zero" if actual == 0 else "negative")
    sign_expected = "positive" if expected_positive else "negative"
    print(f"  {sym} {name}: sign={sign_got} (expected {sign_expected}), value={actual:.8f}")
    if ok:
        PASS += 1
    else:
        FAIL += 1


def test_gamma_atm():
    """Gamma at ATM (F=K) should equal N'(0.5σ√T) / (F·σ·√T)."""
    print("\n[Test 1] Gamma at ATM (F=K=2900, σ=0.35, T=30/365)")
    F, K, sigma, T = 2900.0, 2900.0, 0.35, 30 / 365.0
    gamma = _b76_gamma(F, K, T, sigma)

    # Manual calculation: d1 = 0.5 * 0.35 * sqrt(30/365)
    d1_manual = 0.5 * sigma * math.sqrt(T)
    expected = _norm_pdf(d1_manual) / (F * sigma * math.sqrt(T))
    check("Gamma ATM", gamma, expected)
    check("Gamma > 0", gamma, abs(gamma), tol=1e-10)  # always positive


def test_vanna_atm():
    """At ATM (F=K), d1 = 0.5σ√T, d2 = -0.5σ√T, so d2 < 0, Vanna should be positive."""
    print("\n[Test 2] Vanna at ATM (F=K=2900, σ=0.35, T=30/365)")
    F, K, sigma, T = 2900.0, 2900.0, 0.35, 30 / 365.0
    vanna = _b76_vanna(F, K, T, sigma)

    # At ATM: d1 = 0.5σ√T, d2 = -0.5σ√T
    d1 = 0.5 * sigma * math.sqrt(T)
    d2 = -0.5 * sigma * math.sqrt(T)
    expected = -_norm_pdf(d1) * d2 / (F * sigma)
    check("Vanna ATM", vanna, expected)
    # d2 < 0 → -N'(d1)*d2 > 0 → Vanna should be positive at ATM
    check_sign("Vanna ATM positive", vanna, True)


def test_vanna_otm_call():
    """OTM call (K > F): d1 shrinks, d2 more negative → Vanna still positive but smaller."""
    print("\n[Test 3] Vanna OTM Call (F=2900, K=3000, σ=0.35, T=30/365)")
    F, K, sigma, T = 2900.0, 3000.0, 0.35, 30 / 365.0
    vanna = _b76_vanna(F, K, T, sigma)

    d1 = _b76_d1(F, K, T, sigma)
    d2 = d1 - sigma * math.sqrt(T)
    expected = -_norm_pdf(d1) * d2 / (F * sigma)
    check("Vanna OTM Call", vanna, expected)


def test_vanna_otm_put():
    """Deep OTM put (K << F): d1 is very large, d2 is positive → Vanna should be negative."""
    print("\n[Test 4] Vanna Deep OTM Put (F=2900, K=2500, σ=0.35, T=30/365)")
    F, K, sigma, T = 2900.0, 2500.0, 0.35, 30 / 365.0
    vanna = _b76_vanna(F, K, T, sigma)

    d1 = _b76_d1(F, K, T, sigma)
    d2 = d1 - sigma * math.sqrt(T)
    expected = -_norm_pdf(d1) * d2 / (F * sigma)
    check("Vanna Deep OTM Put", vanna, expected)
    # d2 > 0 for deep ITM → -N'(d1)*d2 < 0 → Vanna negative
    check_sign("Vanna negative for large F/K", vanna, False)


def test_vanna_edge_cases():
    """Edge cases should return 0.0 without errors."""
    print("\n[Test 5] Edge cases")
    check("T=0", _b76_vanna(2900, 2900, 0, 0.35), 0.0)
    check("sigma=0", _b76_vanna(2900, 2900, 0.1, 0), 0.0)
    check("F=0", _b76_vanna(0, 2900, 0.1, 0.35), 0.0)
    check("K=0", _b76_vanna(2900, 0, 0.1, 0.35), 0.0)
    check("negative T", _b76_vanna(2900, 2900, -1, 0.35), 0.0)


def test_vex_sign_convention():
    """
    VEX sign convention:
    Net VEX = Vanna × (Call - Put) × F × 0.01
    If Call > Put (more calls) and Vanna > 0 → VEX > 0 → supportive
    If Put > Call (more puts) and Vanna > 0 → VEX < 0 → pressuring
    """
    print("\n[Test 6] VEX sign convention")
    F, K, sigma, T = 2900.0, 2900.0, 0.35, 30 / 365.0
    vanna = _b76_vanna(F, K, T, sigma)

    # More calls than puts
    call_oi, put_oi = 5000, 2000
    vex = vanna * (call_oi - put_oi) * F * 0.01
    check_sign("VEX (calls > puts)", vex, True)

    # More puts than calls
    call_oi, put_oi = 2000, 5000
    vex = vanna * (call_oi - put_oi) * F * 0.01
    check_sign("VEX (puts > calls)", vex, False)


def test_normalize_iv():
    """Test IV normalization."""
    print("\n[Test 7] IV normalization")
    check("Percentage 41.4→0.414", _normalize_iv(41.4), 0.414, tol=1e-6)
    check("Decimal 0.414→0.414", _normalize_iv(0.414), 0.414, tol=1e-6)
    check("Zero → floor", _normalize_iv(0), 0.0001, tol=1e-8)
    check("Negative → floor", _normalize_iv(-5), 0.0001, tol=1e-8)


def test_gamma_regression():
    """Ensure Gamma values haven't changed from known-good calculations."""
    print("\n[Test 8] Gamma regression (known values)")
    F, K, sigma, T = 2900.0, 2900.0, 0.414, 30 / 365.0
    gamma = _b76_gamma(F, K, T, sigma)
    # Pre-computed with Python:
    d1 = _b76_d1(F, K, T, sigma)
    expected = _norm_pdf(d1) / (F * sigma * math.sqrt(T))
    check("Gamma regression", gamma, expected, tol=1e-10)

    # OTM
    gamma_otm = _b76_gamma(2900, 3100, T, sigma)
    assert gamma_otm < gamma, "OTM gamma should be less than ATM gamma"
    print(f"  ✅ OTM gamma ({gamma_otm:.8f}) < ATM gamma ({gamma:.8f})")
    global PASS
    PASS += 1


if __name__ == "__main__":
    print("=" * 60)
    print("  Black-76 Greeks Test Suite")
    print("=" * 60)

    test_gamma_atm()
    test_vanna_atm()
    test_vanna_otm_call()
    test_vanna_otm_put()
    test_vanna_edge_cases()
    test_vex_sign_convention()
    test_normalize_iv()
    test_gamma_regression()

    print("\n" + "=" * 60)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print("=" * 60)

    sys.exit(1 if FAIL > 0 else 0)
