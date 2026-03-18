# Concept: Rule of 16 + Fourth-Order Polynomial PnL Attribution

> **วัตถุประสงค์**: ประเมินความเหมาะสมของ Rule of 16 และ Fourth-Order Polynomial
> สำหรับคำนวณ PnL ของ Dealer, Market Maker, Hedge Fund บน Gold Futures (GC)
> โดยอ้างอิงจาก GEX–GTBR data ที่มีอยู่ในระบบ

---

## 1. สถานะปัจจุบัน (Baseline)

### 1.1 Greeks ที่คำนวณอยู่แล้ว (Black-76, r = 0)

| Greek | สูตร | ใช้งานใน |
|-------|------|----------|
| **Gamma (Γ)** | N′(d₁) / (F·σ·√T) | GEX, GTBR, V-GTBR |
| **Theta (θ)** | −F·σ·N′(d₁) / (2√T) | V-GTBR (Carr & Wu) |
| **Vanna** | −N′(d₁)·d₂ / σ | V-GTBR, Net Vanna |
| **Volga** | Vega·(d₁·d₂) / σ | V-GTBR, Net Volga |

### 1.2 GTBR ปัจจุบัน — Quadratic (2nd Order)

**Standard GTBR** (symmetric):
```
ΔF_daily = F · σ / √365
Range = [F − ΔF, F + ΔF]
```

**V-GTBR** (Carr & Wu 2020, quadratic in ΔF):
```
½Γ·(ΔF)² + Vanna·Δσ·(ΔF) + [θ/365 + ½Volga·(Δσ)²] = 0
```

> ✅ ปัจจุบันใช้ **calendar days (√365)** และ **2nd-order polynomial**

### 1.3 Portfolio Aggregate Greeks (ใช้จริงใน V-GTBR)

```
net_gamma_total  = Σ Γ_K × (Call_K − Put_K)         [ไม่คูณ F²×0.01]
net_theta_total  = Σ θ_K × (Call_K − Put_K)
net_vanna_total  = Σ Vanna_K × (Call_K − Put_K)      [directional]
net_volga_total  = Σ Volga_K × (Call_K + Put_K)       [symmetric]
```

---

## 2. Rule of 16 — การนำมาใช้

### 2.1 หลักการ

```
σ_daily ≈ σ_annual / √252 ≈ σ_annual / 16
Expected Daily Move = F × (IV / 16)
```

| เปรียบเทียบ | ปัจจุบัน (Calendar) | Rule of 16 (Trading) |
|-------------|--------------------|-----------------------|
| ตัวหาร | √365 ≈ 19.10 | √252 ≈ 15.87 ≈ 16 |
| σ_daily (IV=20%) | F × 0.0105 | F × 0.0126 |
| Range กว้างกว่า | — | **+20%** |

### 2.2 ความเหมาะสมต่อผู้เล่นแต่ละกลุ่ม

#### Dealer (Short Gamma เป็นหลัก)
- **เหมาะสมมาก** ✅
- Dealer hedge ในวัน trading เท่านั้น — ใช้ trading days ตรงกับ hedging frequency
- Rule of 16 ให้ breakeven range กว้างกว่า → **conservative estimate** สำหรับ PnL
- **PnL threshold**: ถ้า |ΔF_actual| > F×IV/16 → Dealer ขาดทุน (gamma loss > theta income)

#### Market Maker (Delta-Neutral, Spread Income)
- **เหมาะสม** ✅
- MM ต้องการ quick mental math สำหรับ risk limits ระหว่างวัน
- F × IV/16 = expected daily move = **breakeven ของ gamma P&L**
- ใช้ร่วมกับ bid-ask spread income เพื่อคำนวณ net P&L

#### Hedge Fund (Directional Gamma)
- **เหมาะสมบางส่วน** ⚠️
- HF อาจไม่ได้ delta-hedge ทุกวัน → trading days basis อาจไม่ match frequency
- แต่มีประโยชน์เป็น **reference level** สำหรับเทียบ realized vs implied move
- **Variance Risk Premium**: Realized Vol / (IV/16) → วัด edge ของ gamma strategy

#### Prop Firm Trader (Momentum + Structure Exploitation)
- **เหมาะสมมาก** ✅
- Prop Trader ต่างจาก MM ตรงที่ **"ไม่ต้องรับซื้อทุกราคา"** — เลือกจุดเข้าได้
- ใช้ประโยชน์จาก **ความเจ็บปวดของ Dealer** (Inelastic Demand) เป็นจุดเข้าเทรด
- ใช้ GTBR เป็น **"Kill Zones"** เพื่อดักจับ Momentum หน้างาน
  แทนการรับความเสี่ยงต่อเนื่องเหมือน MM/Dealer
- **Rule of 16 application**:
  - 1σ (F×IV/16) = **Position Sizing** — กำหนดขนาดสัญญาพื้นฐาน
  - 2σ = **Stop-Loss / Mean-Reversion Entry** — จุดตัดขาดทุนหรือสวนเทรนด์
  - 3σ = **Take-Profit / Climax** — จุดปิดกำไรสูงสุด, เริ่ม Hedge tail risk
  - 4σ–5σ = **Stress Testing** — ประเมินความเสียหายสูงสุด (Black Swan scenario)
- **จุดศูนย์กลางที่ดีที่สุด**: **DGC** — สะท้อนจุดที่ Dealer มีแรงจูงใจ Pin ราคาสูงสุด
  ทำให้เห็น "แรงดึงดูด" ของราคาที่แท้จริง

### 2.3 1σ–5σ Calculation (Rule of 16 + Vol Surface)

#### 2.3.1 Base SD (Symmetric — Rule of 16)

```
SD_base = F × σ_ATM / √252 ≈ F × σ_ATM / 16
```

| σ Level | สูตร Symmetric | Probability | การใช้งาน |
|---------|---------------|-------------|-----------|
| **1σ** | Mean ± 1.0 × SD_base | ~68.2% | Position Sizing, Daily BE |
| **2σ** | Mean ± 2.0 × SD_base | ~95.4% | Stop-Loss, Swing Limit |
| **3σ** | Mean ± 3.0 × SD_base | ~99.7% | Take-Profit, Tail Hedge |
| **4σ** | Mean ± 4.0 × SD_base | ~99.994% | Stress Test, Margin Buffer |
| **5σ** | Mean ± 5.0 × SD_base | ~99.99994% | Black Swan, Death Point |

#### 2.3.2 Asymmetric SD (+ Vol Surface Polynomial)

เมื่อรวม Polynomial Vol Surface จะได้ range **ไม่สมมาตร** ตาม Skew จริง:

```
สำหรับแต่ละ nσ (n = 1..5):
  ΔF_up   = n × SD_base                         (ราคาเป้าหมายฝั่งบน)
  ΔF_down = n × SD_base                         (ราคาเป้าหมายฝั่งล่าง)

  δ_up   = N(d1(F + ΔF_up, K_ATM, σ_ATM, T))   (delta ที่ราคาบน)
  δ_down = N(d1(F − ΔF_down, K_ATM, σ_ATM, T)) (delta ที่ราคาล่าง)

  σ_up   = D₀ + D₁·δ_up + ... + D₄·δ_up⁴       (IV จาก polynomial ฝั่งบน)
  σ_down = D₀ + D₁·δ_down + ... + D₄·δ_down⁴   (IV จาก polynomial ฝั่งล่าง)

  SD_up   = F × σ_up / √252                      (SD ปรับแล้วฝั่งบน)
  SD_down = F × σ_down / √252                     (SD ปรับแล้วฝั่งล่าง)

  Upper_nσ = Mean + n × SD_up                     (ขอบบนไม่สมมาตร)
  Lower_nσ = Mean − n × SD_down                   (ขอบล่างไม่สมมาตร)
```

> **Gold (Positive Skew)**: σ_up > σ_down → ขอบบนกว้างกว่าขอบล่าง
> (Call Skew ทำให้ Gamma Squeeze ฝั่งขาขึ้นเกิดได้ง่ายกว่า)

#### 2.3.3 Multiple Center Options (Mean Value)

แต่ละ Center ตอบคำถามต่างกัน — เลือกตาม use-case:

| # | Center (Mean) | ค่า | คำถามที่ตอบ | เหมาะกับ |
|---|---------------|-----|-----------|---------|
| 1 | **ATM** | F (Futures Price) | ราคาปัจจุบันเป็นหลัก (สถิติบริสุทธิ์) | Beginner, Quick Reference |
| 2 | **Composite Flip** | Lowest Flip Point | ตลาดเปลี่ยน Regime ที่ไหน? | Regime Detection |
| 3 | **DGC Wall** | (+Wall + −Wall) / 2 | จุดสมดุลโครงสร้าง Hedging | Structural Analysis |
| 4 | **DGC V-GTBR** | V-GTBR Midpoint | Dealer มี Profit สูงสุดที่ไหน? (Carr & Wu Vertex) | **Prop Firm (แนะนำ)** |
| 5 | **Polynomial DGC** | Numerical vertex จาก PnL(ΔF) + Vol Surface | จุด Pin ที่แท้จริง (รวม Skew dynamics) | Expert / Quant Desk |

**ตัวอย่าง** (F=3000, IV=20%, DTE=25):

```
SD_base = 3000 × 0.20 / 16 = 37.50 points

                ATM Center (3000)       DGC Center (3012)
                ─────────────────       ─────────────────
  1σ (68%)    [2962.5, 3037.5]        [2974.5, 3049.5]
  2σ (95%)    [2925.0, 3075.0]        [2937.0, 3087.0]
  3σ (99.7%)  [2887.5, 3112.5]        [2899.5, 3124.5]
  4σ (99.99%) [2850.0, 3150.0]        [2862.0, 3162.0]
  5σ (100%)   [2812.5, 3187.5]        [2824.5, 3199.5]

  + Vol Surface Polynomial Adjustment (Gold Positive Skew):
  1σ Asymmetric:  [2964.2, 3039.8]    (ขอบบนกว้างกว่า +2.3 pts)
  2σ Asymmetric:  [2928.1, 3079.4]    (ขอบบนกว้างกว่า +4.4 pts)
  3σ Asymmetric:  [2892.3, 3118.9]    (ขอบบนกว้างกว่า +6.4 pts)
```

> ⚠️ ค่าตัวอย่างเป็น illustrative — ต้องคำนวณจาก actual polynomial coefficients

#### 2.3.4 Implementation

```python
# ใน core/use_cases/sd_range.py — NEW

from core.domain.vol_surface import fit_vol_surface, eval_vol_at_delta
from core.domain.constants import TRADING_DAYS_PER_YEAR
import math
from scipy.stats import norm

def calculate_sd_ranges(
    F: float,
    atm_iv: float,
    T: float,
    center: float,
    poly_coeffs: list[float] | None = None,
    max_sigma: int = 5,
) -> list[dict]:
    """Calculate 1σ–5σ price ranges.

    Args:
        F: Futures price
        atm_iv: ATM implied volatility (decimal)
        T: Time to expiry (years)
        center: Mean value (ATM, DGC, Flip, etc.)
        poly_coeffs: D₀…D₄ from vol surface fit (None = symmetric)
        max_sigma: Maximum sigma level (default 5)

    Returns:
        List of dicts with lo, hi, lo_asym, hi_asym per sigma level.
    """
    sd_base = F * atm_iv / math.sqrt(TRADING_DAYS_PER_YEAR)
    sqrt_T = math.sqrt(T)
    results = []

    for n in range(1, max_sigma + 1):
        row = {
            "sigma": n,
            "lo_sym": center - n * sd_base,
            "hi_sym": center + n * sd_base,
        }

        if poly_coeffs is not None:
            # Asymmetric: evaluate polynomial IV at each bound
            delta_up = norm.cdf(
                (math.log(F / (center + n * sd_base))
                 + 0.5 * atm_iv**2 * T) / (atm_iv * sqrt_T)
            )
            delta_down = norm.cdf(
                (math.log(F / (center - n * sd_base))
                 + 0.5 * atm_iv**2 * T) / (atm_iv * sqrt_T)
            )
            iv_up = eval_vol_at_delta(poly_coeffs, delta_up)
            iv_down = eval_vol_at_delta(poly_coeffs, delta_down)
            sd_up = F * iv_up / math.sqrt(TRADING_DAYS_PER_YEAR)
            sd_down = F * iv_down / math.sqrt(TRADING_DAYS_PER_YEAR)
            row["hi_asym"] = center + n * sd_up
            row["lo_asym"] = center - n * sd_down
        else:
            row["hi_asym"] = row["hi_sym"]
            row["lo_asym"] = row["lo_sym"]

        results.append(row)

    return results
```

### 2.4 Implementation Plan (Rule of 16)

```python
# ใน core/domain/constants.py
TRADING_DAYS_PER_YEAR = 252
RULE_OF_16 = math.sqrt(TRADING_DAYS_PER_YEAR)  # ≈ 15.87

# ใน core/use_cases/gtbr.py — เพิ่ม trading-day basis
def calculate_gtbr_rule16(F: float, atm_iv: float) -> tuple[float, float]:
    """Rule of 16: Expected daily move on trading-day basis."""
    sigma = normalize_iv(atm_iv)
    daily_move = F * sigma / RULE_OF_16
    return (F - daily_move, F + daily_move)
```

### 2.5 ประโยชน์เชิง PnL ที่ได้

| Metric | สูตร | ความหมาย |
|--------|------|----------|
| **Dealer Daily PnL** | θ/252 − ½Γ·(ΔF_realized)² | Theta income vs Gamma cost (trading-day basis) |
| **Breakeven Move** | F × σ / 16 | ถ้า realized move = ค่านี้ → PnL = 0 |
| **Gamma PnL Ratio** | (ΔF_realized / ΔF_breakeven)² | >1 = gamma loss, <1 = theta profit |
| **Variance Premium** | (IV/16)² − RealizedVar | Positive = short gamma has edge |

---

## 3. Fourth-Order Polynomial — การขยาย PnL Model

### 3.1 จาก Quadratic สู่ Quartic

**ปัจจุบัน (2nd Order)** — Taylor expansion ตัดที่ Gamma:
```
PnL ≈ θ·δt + ½Γ·(δF)² + Vanna·δF·δσ + ½Volga·(δσ)²
```

**Fourth-Order Expansion** — เพิ่ม Speed + Fourth Derivative:
```
PnL ≈ θ·δt
     + ½Γ·(δF)²                           ← 2nd order (มีอยู่แล้ว)
     + ⅙·Speed·(δF)³                      ← 3rd order (NEW)
     + 1/24·Snap·(δF)⁴                    ← 4th order (NEW)
     + Vanna·δF·δσ                         ← cross-term (มีอยู่แล้ว)
     + ½Volga·(δσ)²                        ← vol² (มีอยู่แล้ว)
     + ½·Vanna₂·(δF)²·δσ                  ← 3rd order cross (NEW)
     + ⅙·Volga₂·(δσ)³                     ← vol³ (optional)
```

### 3.2 Greeks ใหม่ที่ต้องเพิ่ม

#### Speed (dΓ/dF) — Third Derivative of Price
```
Speed = dΓ/dF = −Γ/F · [1 + d₁/(σ√T)]

หรือเขียนเต็ม:
Speed = −N′(d₁) · [1/(F²·σ·√T)] · [1 + d₁/(σ√T)]
```

**ความหมาย**: Speed วัดว่า Gamma เปลี่ยนเร็วแค่ไหนเมื่อราคาขยับ
- Speed > 0 ที่ด้าน low-strike → Gamma เพิ่มเมื่อราคาตก (dealer ต้อง sell more)
- Speed < 0 ที่ด้าน high-strike → Gamma ลดเมื่อราคาขึ้น

#### Snap (d⁴V/dF⁴) — Fourth Derivative
```
Snap = d(Speed)/dF = Γ/F² · [(d₁² − 1)/(σ²T) + 3d₁/(F·σ√T) + 2/F²]
```

**ความหมาย**: Snap วัด curvature ของ Gamma — บอกว่า hedging pressure จะ accelerate/decelerate แค่ไหน

#### Vanna₂ (∂²Γ/∂F∂σ) — Cross Gamma-Vol
```
Vanna₂ = ∂Vanna/∂F = −Vanna/F · [1 + d₁/(σ√T)] + N′(d₁)·d₂/(F·σ²)
```

### 3.3 Quartic PnL Equation (Set PnL = 0, solve for δF)

```
a₄·(δF)⁴ + a₃·(δF)³ + a₂·(δF)² + a₁·(δF) + a₀ = 0
```

| Coefficient | สูตร | Greek Source |
|-------------|------|-------------|
| **a₄** | 1/24 · Net_Snap | Snap (4th deriv) |
| **a₃** | 1/6 · Net_Speed + ½·Net_Vanna₂·Δσ | Speed + Vanna₂ cross |
| **a₂** | ½ · Net_Gamma | Gamma (เหมือนเดิม) |
| **a₁** | Net_Vanna · Δσ | Vanna (เหมือนเดิม) |
| **a₀** | θ/T_basis + ½·Net_Volga·(Δσ)² | Theta + Volga (เหมือนเดิม) |

> T_basis = 1/252 (Rule of 16) หรือ 1/365 (Calendar)

### 3.4 Quartic Solver

```python
import numpy as np

def solve_quartic_pnl(a4, a3, a2, a1, a0, F):
    """Solve 4th-order PnL = 0 for breakeven δF values."""
    coeffs = [a4, a3, a2, a1, a0]
    roots = np.roots(coeffs)

    # เอาเฉพาะ real roots
    real_roots = roots[np.isreal(roots)].real

    # Filter: เอาเฉพาะ roots ที่สมเหตุสมผล (|δF| < 20% of F)
    valid = real_roots[np.abs(real_roots) < 0.20 * F]

    if len(valid) >= 2:
        lo = F + np.min(valid)
        hi = F + np.max(valid)
        return lo, hi
    elif len(valid) == 1:
        # fallback: symmetric around single root
        return F + valid[0], F - valid[0]
    else:
        return None  # fallback to quadratic V-GTBR
```

### 3.5 ความเหมาะสมต่อผู้เล่นแต่ละกลุ่ม

#### Dealer (⭐ เหมาะสมที่สุด)
- Dealer hedge แบบ discrete → higher-order terms matter เมื่อ move ใหญ่
- **Speed term** → บอก hedging acceleration cost (ต้อง rebalance เร็วขึ้น)
- **Snap term** → tail-risk PnL ที่ quadratic ประมาณไม่ถึง
- **σ-Zone mapping**: Speed effect สำคัญที่ **>2σ** (Hedging Pressure Zone)
  Snap effect สำคัญที่ **>3σ** (Inelastic Demand / Kill Zone)
- **PnL Benefit**: ±5–15% accuracy improvement ที่ >2σ moves

#### Market Maker (✅ เหมาะสม)
- MM ต้องการ precise breakeven เพื่อ set bid-ask spread
- 4th-order ให้ **asymmetric breakeven** ที่แม่นกว่า
- **Key insight**: Speed ≠ 0 → breakeven ไม่สมมาตร → spread ควรกว้างขึ้นด้าน downside
- **σ-Zone mapping**: ใช้ quartic BE ร่วมกับ **1σ (safe zone)** เพื่อ set bid-ask
  ที่คุ้มค่าต่อ gamma cost — spread ≥ quartic BE distance
- **PnL Benefit**: Better spread pricing, ลด adverse selection

#### Hedge Fund (✅ เหมาะสม สำหรับ tail strategies)
- HF ที่ trade gamma explicitly ได้ประโยชน์จาก **non-linear PnL surface**
- 4th-order shows **where gamma convexity works for/against** the position
- **Key insight**: ที่ >3σ move, quartic model อาจแสดง PnL reversal ที่ quadratic ไม่เห็น
- **σ-Zone mapping**: ใช้ **3σ–5σ range** ร่วมกับ Vol Surface เพื่อ size tail hedges
  — VRP (Variance Risk Premium) = Implied Var − Realized Var ต้องเป็นบวกเพื่อ justify strategy
- **PnL Benefit**: Better sizing of tail hedges, optimal strike selection

#### Prop Firm Trader (✅ เหมาะสม — Kill Zone Exploitation)
- Prop Trader ใช้ quartic BE เป็น **Kill Zone boundaries** ที่แม่นกว่า quadratic
- **Speed term** → บอก **momentum acceleration direction** เมื่อ Dealer ถูกบีบ
  - Net Speed > 0 → downside momentum จะเร่งตัว (ขายรอด้านล่าง)
  - Net Speed < 0 → upside momentum จะเร่งตัว (ซื้อรอด้านบน)
- **Key insight**: Quartic BE ไม่สมมาตร → Prop Trader เห็นว่า
  **ฝั่งไหนของ Kill Zone ที่ Dealer จะเจ็บตัวมากกว่า** → เข้าเทรดด้านนั้น
- **σ-Zone mapping**:
  - เข้าเทรดที่ **2σ boundary** (Dealer เริ่ม Rebalance เชิงรุก = momentum เริ่ม)
  - Take profit ที่ **3σ boundary** (Climax = Dealer forced hedge สุดขีด)
  - Stop-loss ภายใน **1σ** (ตลาดกลับ safe zone = thesis ผิด)
- **PnL Benefit**: Precise kill zone targeting, asymmetric risk/reward per skew direction

### 3.6 เปรียบเทียบ Breakeven Range

```
สมมติ: F=3000, IV=20%, DTE=25, Net_Vanna=−0.5, Net_Volga=1.2, ΔIV=+2%

Quadratic V-GTBR (ปัจจุบัน):
  Daily:  [2968.5, 3033.2]     ← asymmetric จาก Vanna/Volga
  Shift:  +0.85

Quartic (เพิ่ม Speed + Snap):
  Daily:  [2965.8, 3034.7]     ← กว้างกว่าด้าน upside (Speed effect)
  Shift:  +0.45                ← Speed ลด Vanna shift บางส่วน

ความแตกต่าง:
  Downside: −2.7 points (quartic กว้างกว่า → dealer loss เพิ่ม 2.7 pts)
  Upside:   +1.5 points (quartic กว้างกว่า → range กว้างขึ้น)
```

> ⚠️ ค่าตัวอย่างเป็น illustrative — ต้องคำนวณจาก actual portfolio Greeks

---

## 4. PnL Attribution Framework — แบ่งตามผู้เล่น

> **หลักการ Aggregation** (จาก Section 11):
> - Γ, θ, Volga → **(Call + Put) OI** [symmetric risk]
> - Vanna → **(Call − Put) OI** [directional risk]
> - คูณ −1 ถ้าคำนวณจากมุม Dealer (ผู้ขาย Options)

### 4.1 Dealer PnL (Short Gamma Default)

**สถานะ**: ขายทั้ง Call และ Put → Short Gamma เป็นหลัก
**เป้าหมาย**: เก็บ Theta (ค่าเช่าเวลา) ให้ชนะ Gamma cost
**σ-Zone**: Profitable ใน **1σ** (Safe Zone), ขาดทุนเมื่อ **>2σ**

```
Dealer_PnL = −[½Γ·(δF)² + ⅙·Speed·(δF)³ + 1/24·Snap·(δF)⁴]   ← Gamma family (cost)
           + |θ|·δt                                                ← Theta income
           − Vanna·δF·Δσ                                          ← Shadow Delta cost
           − ½Volga·(Δσ)²                                         ← Vol-of-Vol cost
```

> Note: Γ, θ, Volga ใช้ aggregate ด้วย (Call+Put) — total book risk
> Vanna ใช้ aggregate ด้วย (Call−Put) — net directional shift

**เงื่อนไขกำไร (Rule of 16 integrated)**:
```
|θ|/252 > ½Γ·(F·σ/16)² + higher-order terms
```

**Regime ที่ได้จาก GEX data**:
- `net_composite_gex ≥ 0` → **LONG γ regime** → Dealer กดราคา (mean-revert)
- `net_composite_gex < 0` → **SHORT γ regime** → Dealer ขยายราคา (trend-follow)

**Vol Surface Enhancement**:
- ใช้ Dynamic Δσ(ΔF) จาก polynomial (Section 12)
  แทน fixed ΔIV proxy → Vanna/Volga cost แม่นยำตาม Skew
- Kill Zone ชัดเจนขึ้น: polynomial แสดง asymmetric loss profile ตาม Gold's Call Skew

### 4.2 Market Maker PnL (Spread + Gamma)

**สถานะ**: เหมือน Dealer + มี Spread Income เพิ่มเติม
**เป้าหมาย**: Spread Income > Gamma Cost → net positive
**σ-Zone**: ใช้ **1σ** (Rule of 16) เพื่อ set minimum spread

```
MM_PnL = Spread_Income                                           ← bid-ask × volume
       + Dealer_PnL                                               ← same gamma/theta
       + Inventory_PnL                                            ← directional risk
```

**Rule of 16 application**:
```
Min_Spread ≥ 2 × [½Γ·(F·σ/16)² − |θ|/252] / Expected_Volume
```
→ MM ต้อง set spread กว้างพอ cover gamma cost

**Vol Surface Enhancement**:
- Quartic BE บอกว่า **spread ควรกว้างขึ้นด้านไหน** (ด้านที่ Speed สูงกว่า)
- Gold Positive Skew → upside spread กว้างกว่า downside
  (Gamma Squeeze ฝั่งขาขึ้นรุนแรงกว่า → adverse selection สูงกว่า)

### 4.3 Hedge Fund PnL (Strategic Gamma)

**สถานะ**: Long Options เป็นหลัก → Long Gamma (ได้จากราคาเคลื่อนไหว)
**เป้าหมาย**: Gamma + Convexity Gain > Theta Cost (Premium Paid)
**σ-Zone**: จ่าย Theta ใน **1σ**, เก็บกำไรเมื่อ **>2σ**, Bonus ที่ **>3σ** (tail payoff)

```
HF_PnL = Position × [½Γ·(δF)² + ⅙·Speed·(δF)³ + 1/24·Snap·(δF)⁴]
        − Premium_Paid                                            ← theta cost (|θ|/252)
        + Vanna·δF·Δσ × direction                                ← vol-spot correlation
        + Convexity_Bonus                                         ← 3rd + 4th-order payoff
```

**Optimal entry (จาก GEX data)**:
```
Buy gamma at: GEX_Flip (dealer neutral → vol expansion likely)
Take profit at: ±Wall (dealer forced hedging → momentum exhausts)
Size by: Quartic breakeven distance / Risk budget
```

**Vol Surface Enhancement**:
- **VRP (Variance Risk Premium)** = (IV/16)² − Realized Var
  ถ้า VRP > 0 → Short Gamma มี edge (HF ควรระวังเมื่อ Long Gamma)
  ถ้า VRP < 0 → Long Gamma มี edge (HF ควรซื้อ Options)
- Polynomial Vol Surface ช่วยหา **optimal strike** สำหรับ tail hedge
  (strike ที่ Wing IV ยังถูกเทียบกับ tail risk จริง)

### 4.4 Prop Firm Trader PnL (Kill Zone Exploitation)

**สถานะ**: ไม่มี permanent book — เลือกจุดเข้าจากโครงสร้าง GEX
**เป้าหมาย**: ดักจับ Momentum เมื่อ Dealer ถูกบีบ (Inelastic Demand)
**σ-Zone**: เข้าที่ **2σ**, TP ที่ **3σ**, SL ภายใน **1σ**

```
Prop_PnL = Futures_PnL × Lot_Size                               ← directional P&L
         + Timing_Edge                                            ← เข้าตอน dealer forced hedge
         − Slippage_Cost                                          ← execution cost

โดยที่:
  Futures_PnL = |ΔF_entry→exit|
  Timing_Edge = f(GEX_Regime, Kill_Zone_proximity, Speed_sign)
```

**Entry / Exit Logic (Rule of 16 + Quartic + Vol Surface)**:

```
ENTRY CONDITIONS (เข้าเทรด):
  1. ราคาแตะ 2σ boundary (Rule of 16 basis)         ← Dealer เริ่มเจ็บ
  2. GEX Regime = SHORT γ (net_composite_gex < 0)    ← Dealer เป็น momentum trader
  3. Net Speed sign ชี้ทิศ momentum                   ← 3rd-order confirmation
     - Speed > 0 → Short entry (downside momentum)
     - Speed < 0 → Long entry (upside momentum)
  4. Block Trade ปรากฏที่ Kill Zone                   ← Smart Money confirmation

EXIT CONDITIONS (ออกเทรด):
  TP: ราคาแตะ 3σ boundary                             ← Dealer forced hedge climax
  SL: ราคากลับเข้า 1σ                                 ← thesis ผิด, safe zone restored

POSITION SIZING (Rule of 16):
  Risk_Per_Trade = Account × 1%
  Stop_Distance = |Entry − 1σ_boundary|
  Lot_Size = Risk_Per_Trade / Stop_Distance
```

**Vol Surface Enhancement**:
- Polynomial ให้ **asymmetric kill zone** → Prop Trader เห็นว่า
  ฝั่งไหน Dealer เจ็บมากกว่า (wider quartic BE = more forced hedge)
- Gold Positive Skew:
  - **Long entry** (ฝั่งขาขึ้น): kill zone กว้างกว่า → momentum แรงกว่า → **R:R ดีกว่า**
  - **Short entry** (ฝั่งขาลง): kill zone แคบกว่า → ต้องรอ IV spike confirm (Vanna effect)
- **DGC as magnet**: เมื่อ TP hit แล้ว ราคามักวิ่งกลับหา DGC
  → Prop Trader ที่เข้าใจ DGC สามารถ **flip position** ที่ 3σ กลับมา mean-revert

### 4.5 สรุปเปรียบเทียบ PnL ทุกผู้เล่น

| ผู้เล่น | สถานะหลัก | กำไรจาก | ขาดทุนจาก | σ-Zone ที่สำคัญ | Vol Surface ช่วยเรื่อง |
|---------|----------|---------|----------|----------------|----------------------|
| **Dealer** | Short γ | Theta (1σ) | Gamma (>2σ) + Vanna/Volga | 1σ Safe, 2σ Pressure | Asymmetric loss profile |
| **MM** | Short γ + Spread | Theta + Spread | Gamma + Adverse Selection | 1σ Spread pricing | Directional spread adjustment |
| **HF** | Long γ | Gamma (>2σ) + Tail (>3σ) | Theta (daily) | 2σ–5σ Payoff zone | Optimal wing strike, VRP |
| **Prop Firm** | Directional (no permanent) | Momentum (2σ→3σ) | SL in 1σ | 2σ Entry, 3σ TP, 1σ SL | Kill zone asymmetry, DGC magnet |

**Zero-sum check**:
```
Dealer_Loss (>2σ) ≈ HF_Gain + Prop_Gain
Dealer_Profit (1σ) ≈ HF_Theta_Cost + MM_Spread_to_HF
Prop_Profit = Momentum capture from Dealer forced hedge
```

---

## 5. Data Flow หลัง Update Formula

```
CSV (CME)
  ↓
filter_session_data()
  ↓
calculate_gex_analysis()
  → GexResult { flip, walls, net_gamma, net_theta, net_vanna, net_volga }
  ↓ เพิ่มใหม่:
  → + net_speed_total = Σ Speed_K × (Call_K − Put_K)
  → + net_snap_total  = Σ Snap_K × (Call_K − Put_K)
  ↓
calculate_gtbr_rule16(F, atm_iv)                    ← NEW: Rule of 16 breakeven
  → (lo_r16, hi_r16)
  ↓
calculate_quartic_gtbr(                              ← NEW: 4th-order solver
    F, atm_iv, dte,
    net_gamma, net_theta,
    net_vanna, net_volga,
    net_speed, net_snap,                             ← NEW Greeks
    delta_iv
  )
  → QuarticGtbrResult { lo_daily, hi_daily, lo_expiry, hi_expiry, shift }
  ↓
calculate_participant_pnl(                           ← NEW: PnL attribution
    regime, delta_f, delta_iv,
    net_gamma, net_theta,
    net_vanna, net_volga,
    net_speed, net_snap
  )
  → DealerPnL, MmPnL, HfPnL, PropPnL
  ↓
calculate_sd_ranges(F, atm_iv, T, center, poly_coeffs)  ← NEW: 1σ–5σ ranges
  → [{ sigma, lo_sym, hi_sym, lo_asym, hi_asym }] × 5
  ↓
Render: new metrics + PnL cards + σ-zone chart bands
```

---

## 6. สรุปความเหมาะสม

| Feature | Dealer | Market Maker | Hedge Fund | Prop Firm | ระดับความจำเป็น |
|---------|--------|-------------|------------|-----------|----------------|
| **Rule of 16** | ✅ Trading-day BE | ✅ Spread sizing | ⚠️ Reference | ✅ Position sizing + σ-zones | **สูง** |
| **1σ–5σ Ranges** | ✅ Safe/Kill zone | ✅ Spread zone | ✅ Payoff zone | ✅ Entry/TP/SL levels | **สูง** |
| **Vol Surface** | ✅ Asymmetric loss | ✅ Directional spread | ✅ Wing strike pick | ✅ Kill zone asymmetry | **สูง** |
| **Speed (3rd)** | ✅ Hedge accel. | ✅ Asymmetric spread | ✅ Momentum sizing | ✅ Momentum direction | **สูง** |
| **Snap (4th)** | ✅ Tail-risk PnL | ⚠️ Marginal | ✅ Tail hedge sizing | ⚠️ >3σ only | **กลาง** |
| **Quartic Solver** | ✅ Precise BE | ✅ Precise BE | ✅ Entry/exit | ✅ Precise kill zone | **กลาง** |
| **PnL Attribution** | ✅ Core value | ✅ Core value | ✅ Core value | ✅ Core value | **สูง** |
| **Multiple Centers** | ⚠️ DGC only | ⚠️ ATM/DGC | ✅ All centers | ✅ DGC V-GTBR (แนะนำ) | **กลาง** |

### คำตอบ: เหมาะสมหรือไม่?

> **Rule of 16**: ✅ **เหมาะสมมาก** — ตรงกับ hedging frequency ของ Dealer/MM/Prop,
> เพิ่ม accuracy ~20% สำหรับ trading-day breakeven, implement ง่าย
>
> **Vol Surface Polynomial**: ✅ **เหมาะสมมาก** — ใช้ข้อมูลที่มีอยู่แล้ว (Vol Settle),
> ให้ asymmetric ranges ตาม Gold's Call Skew, ปรับปรุง DGC, Kill Zone, PnL accuracy
>
> **1σ–5σ with Multiple Centers**: ✅ **เหมาะสมมาก** — ครอบคลุมทุกผู้เล่น:
> - Dealer: safe/pressure/kill zones (1σ/2σ/3σ)
> - Prop Firm: entry/TP/SL framework (2σ/3σ/1σ)
> - HF: payoff mapping (2σ–5σ)
>
> **Fourth-Order Taylor (Speed/Snap)**: ✅ **เหมาะสม** แต่ต้อง phase —
> - **Phase 1**: เพิ่ม Speed (3rd order) ก่อน → ได้ asymmetric breakeven ที่ดีกว่า V-GTBR
> - **Phase 2**: เพิ่ม Snap (4th order) → capture tail PnL ที่ >2σ moves
> - **Trade-off**: ซับซ้อนขึ้น + quartic solver ไม่ guarantee 4 real roots → ต้อง fallback strategy

---

## 7. Validation Checklist (หลัง Update Formula)

### 7.1 Rule of 16
- [ ] `σ_daily_r16 ≈ 1.20 × σ_daily_calendar` (expected ~20% wider)
- [ ] `breakeven_r16 > breakeven_365` (always)
- [ ] Dealer PnL negative when `|realized_move| > F×IV/16`
- [ ] Consistent with VIX interpretation: IV=16 → expected 1% daily move

### 7.2 Speed (3rd Order)
- [ ] `Speed` เปลี่ยนเครื่องหมายที่ ATM (positive below, negative above)
- [ ] `net_speed_total` sign consistent with skew direction
- [ ] Cubic term shifts breakeven asymmetrically (downside wider if net_speed > 0)
- [ ] Magnitude: |Speed contribution| < 30% of |Gamma contribution| at 1σ

### 7.3 Snap (4th Order)
- [ ] `Snap > 0` at ATM (gamma convexity)
- [ ] Quartic solver returns 2 or 4 real roots (not 0)
- [ ] Fallback to quadratic when quartic gives no valid roots
- [ ] Breakeven difference vs quadratic: < 5% at 1σ, > 10% at 3σ

### 7.4 PnL Attribution
- [ ] `Dealer_PnL + MM_PnL + HF_PnL ≈ 0` (zero-sum at portfolio level)
- [ ] Dealer PnL negative in SHORT γ regime with >1σ move
- [ ] Theta income scales with 1/252 (Rule of 16) not 1/365
- [ ] Vanna PnL direction matches vol-spot correlation sign

### 7.5 Integration with Existing GEX Data
- [ ] `net_speed_total` aggregation: Σ Speed_K × (Call − Put) [directional]
- [ ] `net_snap_total` aggregation: Σ Snap_K × (Call − Put) [directional]
- [ ] New Greeks added to `GexResult` dataclass without breaking existing fields
- [ ] All existing tests pass (`python3 test_black76.py`)
- [ ] Compile check passes on all modified files

---

## 8. New Domain Models (Preview)

```python
# เพิ่มใน core/domain/models.py

@dataclass
class QuarticGtbrResult:
    """Fourth-order polynomial breakeven range."""
    lo_daily: float
    hi_daily: float
    lo_expiry: float
    hi_expiry: float
    shift_daily: float       # asymmetry from Speed + Vanna
    shift_expiry: float
    n_real_roots: int        # 2 or 4 (diagnostic)
    fallback_used: bool      # True if quartic failed → used quadratic

@dataclass
class ParticipantPnL:
    """PnL attribution by market participant."""
    # Dealer (short gamma default)
    dealer_gamma_pnl: float     # ½Γ(δF)² + higher-order
    dealer_theta_income: float  # |θ|/252
    dealer_vanna_cost: float    # Vanna·δF·Δσ
    dealer_volga_cost: float    # ½Volga·(Δσ)²
    dealer_net_pnl: float       # sum

    # Market Maker (spread + gamma)
    mm_spread_estimate: float   # estimated from bid-ask
    mm_net_pnl: float

    # Hedge Fund (strategic gamma, directional)
    hf_gamma_pnl: float
    hf_convexity_bonus: float   # 3rd + 4th order terms
    hf_net_pnl: float

    # Context
    regime: str                 # "LONG γ" / "SHORT γ"
    realized_move_sigma: float  # |δF| / (F·σ/16) — Rule of 16 basis
```

---

## 9. New Black-76 Functions (Preview)

```python
# เพิ่มใน core/domain/black76.py

def b76_speed(F: float, K: float, T: float, sigma: float) -> float:
    """Speed = dΓ/dF (3rd derivative of option price w.r.t. F).

    Speed = −Γ/F · [1 + d₁/(σ√T)]
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    sigma = normalize_iv(sigma)
    d1 = b76_d1(F, K, T, sigma)
    gamma = b76_gamma(F, K, T, sigma)
    sqrt_T = math.sqrt(T)
    return -gamma / F * (1.0 + d1 / (sigma * sqrt_T))


def b76_snap(F: float, K: float, T: float, sigma: float) -> float:
    """Snap = d(Speed)/dF (4th derivative of option price w.r.t. F).

    Snap = Γ/F² · [(d₁² − 1)/(σ²T) − 3·(1 + d₁/(σ√T))/F + 2/F]

    Simplified form for Black-76.
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    sigma = normalize_iv(sigma)
    d1 = b76_d1(F, K, T, sigma)
    gamma = b76_gamma(F, K, T, sigma)
    sqrt_T = math.sqrt(T)
    sig_sqrtT = sigma * sqrt_T

    term1 = (d1 * d1 - 1.0) / (sigma * sigma * T)
    term2 = 3.0 * d1 / (F * sig_sqrtT)
    term3 = 2.0 / (F * F)
    return gamma / (F * F) * (term1 + term2 + term3)
```

---

## 10. Vol Surface Polynomial (CME QuikVol Approach)

> ⚠️ **สำคัญ**: "Fourth-Order Polynomial" มี **สองความหมาย** ในเอกสารนี้:
> - **Section 3**: Taylor expansion ของ PnL (Speed, Snap) — higher-order Greeks
> - **Section 10**: Polynomial fit ของ Volatility Surface σ(δ) — CME QuikVol method
>
> ทั้งสองอย่าง **ทำงานร่วมกัน** แต่เป็นคนละเรื่อง

### 10.1 หลักการ — Volatility Smile Fitting

ปัจจุบัน Dashboard ใช้ **Flat ATM IV** (σ เดียวทุก Strike) → Greeks สมมาตร
CME Vol2Vol™ ใช้ **4th-order polynomial** fit บน Volatility Surface:

```
σ(δ) = D₀ + D₁·δ + D₂·δ² + D₃·δ³ + D₄·δ⁴
```

- `δ` = Raw Delta (0.0 ถึง 1.0), ATM = 0.50
- Fit ด้วย **least-squares regression** บน (Delta_i, VolSettle_i) pairs
- ช่วง Delta ที่ fit: **0.05 ถึง 0.95** (ประมาณ ±2 SD)
- ผลลัพธ์: **strike-specific IV** ที่สะท้อน Skew/Smile จริง

### 10.2 Data Input — ใช้ข้อมูลที่มีอยู่แล้ว

```
Step 1: ดึง (Strike_i, VolSettle_i) จาก CME data ← มีอยู่แล้วใน OI/Intraday CSV

Step 2: แปลง Strike → Delta ด้วย Black-76:
        Delta_Call_i = N(d1_i)
        d1_i = [ln(F/K_i) + ½σ_K²T] / (σ_K·√T)
        ใช้ σ_K = VolSettle ของแต่ละ Strike (ไม่ใช่ ATM IV)

Step 3: Fit polynomial σ(δ) = D₀ + D₁δ + D₂δ² + D₃δ³ + D₄δ⁴
        ด้วย numpy.polyfit(deltas, ivs, 4)
```

> ✅ **Feasibility**: CME ใช้ EOD settlement data (Vol Settle) เป็นแหล่งหลัก
> ในการสร้าง vol curves เหมือนกัน — ข้อมูลเดียวกับที่ Dashboard มีอยู่แล้ว

### 10.3 ประโยชน์เทียบ Flat IV

| Feature | Flat ATM IV (ปัจจุบัน) | + Polynomial Surface |
|---------|----------------------|---------------------|
| GTBR | สมมาตร ±เท่ากัน | **ไม่สมมาตร** ตาม Skew จริง |
| DGC | ขึ้นกับ ΔIV proxy | **แม่นยำ** — ใช้ Spot-Vol Correlation จาก curve |
| Vanna/Volga | คำนวณจาก σ เดียว | คำนวณจาก **slope/curvature** ของ polynomial |
| Kill Zone | ทั้งสองฝั่งเท่ากัน | **Gold**: ฝั่งขาขึ้นกว้างกว่า (Call Skew) |
| Risk estimate | Underestimate tail risk | **สะท้อน Wing IV** ที่แพงกว่า ATM |

### 10.4 Implementation

```python
# NEW: core/domain/vol_surface.py

import numpy as np
from scipy.stats import norm

def fit_vol_surface(
    strikes: np.ndarray,
    vol_settles: np.ndarray,
    F: float, T: float,
    degree: int = 4,
) -> np.ndarray:
    """Fit 4th-order polynomial on (delta, IV) pairs.

    Returns D₀…D₄ coefficients.
    """
    # Strike → Delta conversion (Black-76, strike-specific IV)
    sigmas = vol_settles / 100.0 if vol_settles.max() > 1.0 else vol_settles
    sqrt_T = np.sqrt(T)
    d1s = (np.log(F / strikes) + 0.5 * sigmas**2 * T) / (sigmas * sqrt_T)
    deltas = norm.cdf(d1s)  # Call deltas, raw 0.0–1.0

    # Filter valid delta range (0.05 to 0.95)
    mask = (deltas >= 0.05) & (deltas <= 0.95)
    return np.polyfit(deltas[mask], sigmas[mask], degree)


def eval_vol_at_delta(coeffs: np.ndarray, delta: float) -> float:
    """Evaluate polynomial σ(δ) at specific delta."""
    return float(np.polyval(coeffs, delta))
```

---

## 11. Critical Correction — Greek Aggregation for P&L

> ⚠️ **แก้ไขจาก NotebookLM (gex-gbtr-data)**: Section 1.3 ใช้ (Call−Put)
> สำหรับ Gamma/Theta ซึ่งถูกต้องสำหรับ **directional GEX analysis**
> แต่สำหรับ **P&L Attribution** ต้องแยกเป็นสองประเภท

### 11.1 สองระบบ Aggregation ที่ต่างกัน

```
┌────────────────────────────────────────────────────────────┐
│  SYSTEM 1: GEX / Directional Analysis (เดิม — คงไว้)      │
│  ─────────────────────────────────────────────────         │
│  Net GEX_K = Γ × (Call − Put) × F² × 0.01                │
│  → บอก DIRECTION ของ dealer hedging flow                  │
│  → ใช้หา: Flip, ±Walls, Regime                             │
│                                                            │
│  Net Vanna = Σ Vanna × (Call − Put)  [directional]        │
│  Net Volga = Σ Volga × (Call + Put)  [symmetric]          │
│  Net Gamma = Σ Γ     × (Call − Put)  [directional]        │
│  Net Theta = Σ θ     × (Call − Put)  [directional]        │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  SYSTEM 2: PnL Attribution (ใหม่)                          │
│  ─────────────────────────────────────────────────         │
│  Dealer = Short Options (ทั้ง Call และ Put)                 │
│  → Gamma/Theta/Volga = SYMMETRIC risk (Call+Put)           │
│  → Vanna = DIRECTIONAL risk (Call−Put)                     │
│                                                            │
│  PnL_Gamma_K = Γ_K × (Call_K + Put_K)  [symmetric]       │
│  PnL_Theta_K = θ_K × (Call_K + Put_K)  [symmetric]       │
│  PnL_Vanna_K = Vanna_K × (Call_K − Put_K) [directional]  │
│  PnL_Volga_K = Volga_K × (Call_K + Put_K) [symmetric]    │
└────────────────────────────────────────────────────────────┘
```

### 11.2 ทำไมต้องแยก?

**Gamma/Theta** = ความโค้ง (convexity) ของราคา Options
- Call Gamma = Put Gamma (เท่ากันที่ Strike เดียวกัน)
- Dealer ที่ Short ทั้ง Call และ Put มี Gamma exposure รวม = Γ × (Call + Put)
- ถ้าใช้ (Call − Put) จะ undercount risk เมื่อมีทั้ง Call/Put OI สูง

**Vanna** = Delta เปลี่ยนตาม IV (directional)
- Call OTM: Vanna > 0, Put OTM: Vanna < 0
- ต้องใช้ (Call − Put) เพื่อให้ได้ net directional shift

**Volga** = Vega เปลี่ยนตาม IV (symmetric)
- ทั้ง Call/Put มี Volga > 0 ที่ OTM wings
- ใช้ (Call + Put) เพราะทั้งคู่ขยาย risk เท่ากัน

### 11.3 Corrected PnL Formula (Carr & Wu 2020)

```
Portfolio_PnL(ΔF) = Σ_K [
    (θ_K/T_basis + ½Γ_K·(ΔF)² + ½Volga_K·(Δσ_K)²) × (Call_K + Put_K)   ← SYMMETRIC
  + (Vanna_K · ΔF · Δσ_K) × (Call_K − Put_K)                             ← DIRECTIONAL
]
```

> **Note**: คูณ −1 ถ้าคำนวณจากมุม Dealer (ผู้ขาย Options)

### 11.4 ผลกระทบต่อ V-GTBR ที่มีอยู่

V-GTBR ปัจจุบันใช้ (Call−Put) สำหรับ Gamma/Theta → **ถูกต้อง** สำหรับ
directional breakeven analysis (หาจุดที่ net directional flow = 0)

P&L Attribution ใหม่ใช้ (Call+Put) สำหรับ Gamma/Theta → **ถูกต้อง** สำหรับ
total risk assessment (ประเมิน total dollar P&L ของ dealer)

> ✅ **ทั้งสองระบบอยู่ร่วมกันได้** — ตอบคำถามคนละแบบ:
> - V-GTBR (Call−Put): "Dealer ถูกบีบไปทิศไหน?"
> - PnL (Call+Put): "Dealer ขาดทุนเท่าไหร่?"

---

## 12. Dynamic Δσ(ΔF) — Polynomial-Derived IV Shift

### 12.1 ปัจจุบัน vs ใหม่

| | ปัจจุบัน | ใหม่ (Polynomial) |
|---|---------|------------------|
| **Δσ** | Fixed: `IV_Intraday − IV_OI` | Dynamic: `σ(δ_new) − σ(δ_old)` |
| **ขึ้นกับ ΔF?** | ไม่ — ค่าเดียวทุก scenario | ใช่ — เปลี่ยนตาม price move |
| **สะท้อน Skew?** | ไม่ | ใช่ — ผ่าน polynomial shape |

### 12.2 Calculation Chain

```
สำหรับ hypothetical move ΔF จาก F ปัจจุบัน:

1. F' = F + ΔF                                     (ราคาใหม่)
2. δ_old = N(d1(F, K, σ_K, T))                    (delta เดิม ที่ ATM)
3. d1' = [ln(F'/K) + ½σ_K²T] / (σ_K·√T)          (d1 ใหม่ที่ราคา F')
4. δ_new = N(d1')                                   (delta ใหม่)
5. σ_new = D₀ + D₁·δ_new + ... + D₄·δ_new⁴        (IV ใหม่จาก polynomial)
6. Δσ(ΔF) = σ_new − σ_old                          (IV shift เฉพาะ scenario นี้)
```

### 12.3 ทำไม Dynamic Δσ ดีกว่า Fixed

**Gold ที่มี Positive Skew (Call Skew)**:
- ราคาขึ้น (ΔF > 0) → delta เลื่อนขวา → polynomial ให้ **IV สูงขึ้น**
- ราคาลง (ΔF < 0) → delta เลื่อนซ้าย → polynomial ให้ **IV ต่ำลง** (OTM Put side)

→ Δσ(+ΔF) > Δσ(−ΔF) → **P&L ไม่สมมาตร** ตาม Skew จริง
→ GTBR ฝั่งขาขึ้นจะแคบกว่าขาลง (Gamma Squeeze ง่ายกว่า)

```
Fixed Δσ:     Δσ = +0.02 ทุก ΔF        → PnL สมมาตร (ไม่ถูกต้อง)
Dynamic Δσ:   Δσ(+50) = +0.028          → PnL ฝั่งขาขึ้นแรงกว่า
              Δσ(−50) = +0.012          → PnL ฝั่งขาลงเบากว่า (Gold-specific)
```

---

## 13. Improved DGC with Vol Surface

### 13.1 DGC ปัจจุบัน vs Polynomial DGC

| | DGC ปัจจุบัน | DGC + Polynomial |
|---|-------------|-----------------|
| **สูตร** | `F − (Vanna·ΔIV) / Gamma` | `F − (Vanna·Δσ(ΔF*)) / Gamma` |
| **Δσ** | Fixed proxy | Dynamic จาก vol surface |
| **Accuracy** | ถูกต้องเมื่อ Skew flat | ถูกต้องเสมอ |

### 13.2 การหา DGC ด้วย Polynomial

```
DGC = ΔF* ที่ maximize Portfolio_PnL(ΔF)

จาก Section 11.3:
PnL(ΔF) = Σ_K [
    (θ_K/T + ½Γ_K·(ΔF)² + ½Volga_K·(Δσ_K(ΔF))²) × (Call+Put)
  + (Vanna_K · ΔF · Δσ_K(ΔF)) × (Call−Put)
]

dPnL/dΔF = 0  →  ΔF_vertex (= DGC − F)
```

เมื่อ Δσ_K เป็น function ของ ΔF (จาก polynomial) สมการนี้ไม่มี closed-form
→ ใช้ **numerical optimization** (scipy.optimize.minimize_scalar)

### 13.3 Gold-Specific Insight

ในตลาดทองคำ (Positive Spot-Vol Correlation):
```
ราคาขึ้น → IV พุ่ง → Vanna ดึง DGC ขึ้นตาม (Bullish Gravity)
```
Polynomial DGC จะจับ dynamic นี้ได้แม่นกว่า Fixed-Δσ DGC
เพราะ Δσ(ΔF) เปลี่ยนตาม position บน Vol Curve จริง

---

## 14. CME Vol2Vol™ SD Methodology

### 14.1 ATM = 50 Delta — ทำไม ±50?

"±50" หมายถึง **Delta** ไม่ใช่ Price Points:

| Delta | ความหมาย |
|-------|----------|
| **50Δ** (center) | ATM — 50% probability of finishing ITM |
| **0Δ** (−50 จาก center) | Deep OTM — extreme downside tail |
| **100Δ** (+50 จาก center) | Deep ITM — extreme upside tail |

→ ±50 delta ครอบคลุม **full probability spectrum** ของ options pricing

### 14.2 SD Value — สูตรคำนวณ

**Base SD** (de-annualized ATM sigma):
```
SD_daily  = F × σ_ATM / √252       (Rule of 16 basis — trading days)
SD_expiry = F × σ_ATM × √(DTE/252) (Rule of 16 basis)
```

> Note: CME Vol2Vol ใช้ **trading days** ไม่ใช่ calendar days

**SD Bounds** (+ polynomial adjustment):
```
1σ: Mean ± 1.0 × SD   → ~68.2% probability
2σ: Mean ± 2.0 × SD   → ~95.4% probability
3σ: Mean ± 3.0 × SD   → ~99.7% probability
```

แต่ที่แต่ละ σ marker **IV จะถูก evaluate จาก polynomial** ไม่ใช่ flat ATM IV
→ ทำให้ range **ไม่สมมาตร** เมื่อ Skew มีอยู่

### 14.3 เปรียบเทียบกับ Dashboard

| Feature | Dashboard σ-Range | CME Vol2Vol™ |
|---------|------------------|-------------|
| Base SD | `F×σ/√365` (calendar) | `F×σ/√252` (trading) |
| IV source | Flat ATM IV (symmetric) | 4th-order polynomial (asymmetric) |
| Skew | ไม่จับ | จับผ่าน polynomial coefficients |
| V-GTBR | Vanna/Volga quadratic → asymmetry | N/A (ใช้ polynomial แทน) |
| Result | V-GTBR ≈ asymmetric GTBR | Asymmetric SD cone |

> **ข้อสรุป**: V-GTBR (Carr & Wu quadratic) และ Vol2Vol™ (polynomial surface)
> ทั้งคู่ **เป้าหมายเดียวกัน** = asymmetric breakeven range
> แต่ใช้คนละวิธี:
> - V-GTBR: แก้สมการ PnL = 0 ด้วย Vanna/Volga terms
> - Vol2Vol: evaluate polynomial IV ที่แต่ละ SD marker

---

## 15. Updated Validation Checklist (เพิ่มจาก Section 7)

### 15.1 Vol Surface Polynomial
- [ ] `fit_vol_surface()` returns 5 coefficients (D₀…D₄)
- [ ] `eval_vol_at_delta(coeffs, 0.50) ≈ ATM IV` (polynomial ผ่าน ATM)
- [ ] Polynomial shape matches observed Vol Settle curve
- [ ] Delta conversion ใช้ strike-specific IV (ไม่ใช่ flat ATM)
- [ ] Filter: เฉพาะ delta 0.05–0.95 (exclude extreme wings)

### 15.2 Greek Aggregation (PnL System)
- [ ] Gamma/Theta/Volga ใช้ `(Call + Put)` OI [symmetric]
- [ ] Vanna ใช้ `(Call − Put)` OI [directional]
- [ ] PnL system แยกจาก GEX system (ไม่ break existing directional analysis)
- [ ] PnL(ΔF=0) = Σ θ_K × (Call+Put) / T_basis (pure theta income)

### 15.3 Dynamic Δσ(ΔF)
- [ ] Δσ(ΔF=0) = 0 (ไม่มี IV change เมื่อราคาไม่ขยับ)
- [ ] Δσ(+ΔF) ≠ Δσ(−ΔF) เมื่อ Skew ≠ 0 (asymmetric)
- [ ] Gold: Δσ(+ΔF) > Δσ(−ΔF) (Positive Skew / Call Skew)
- [ ] Cap: |Δσ| ≤ 0.10 (10% absolute — safety bound)

### 15.4 Polynomial DGC
- [ ] DGC = F เมื่อ Skew = 0 (flat vol surface)
- [ ] DGC ≠ Fixed-Δσ DGC เมื่อ Skew steep
- [ ] DGC อยู่ในช่วง [−Wall, +Wall] (sanity check)
- [ ] Numerical optimizer converges (scipy minimize_scalar)

---

## 16. Implementation Phases (Updated)

### Phase 1: Rule of 16 + Vol Surface Foundation
1. เพิ่ม `TRADING_DAYS_PER_YEAR = 252` ใน constants.py
2. เพิ่ม `calculate_gtbr_rule16()` ใน gtbr.py
3. สร้าง `core/domain/vol_surface.py` — polynomial fit + evaluation
4. เพิ่ม Theta/252 basis ใน PnL metrics

### Phase 2: PnL Attribution System
1. สร้าง `core/use_cases/dealer_pnl.py` — PnL(ΔF) calculation
2. เพิ่ม (Call+Put) aggregation สำหรับ symmetric Greeks
3. Implement dynamic Δσ(ΔF) ด้วย polynomial
4. เพิ่ม `ParticipantPnL` dataclass ใน models.py

### Phase 3: Higher-Order Greeks (Speed, Snap)
1. เพิ่ม `b76_speed()`, `b76_snap()` ใน black76.py
2. เพิ่ม Quartic PnL solver
3. Update PnL attribution ด้วย 3rd/4th order terms
4. เพิ่ม `QuarticGtbrResult` dataclass

### Phase 4: Visualization
1. PnL Heatmap (Plotly) — Safe/Pressure/Kill zones
2. Polynomial DGC on chart
3. Vol Surface visualization (optional)
4. Participant PnL cards in dashboard

---

*สร้างเมื่อ: 2026-03-18 | อัปเดต: 2026-03-18*
*อ้างอิง: GEX–GTBR data (NotebookLM) + core/use_cases/ + core/domain/*
*ใช้เป็น reference สำหรับ validate หลัง update formula*

### Changelog
- **v1**: Initial concept — Rule of 16 + Taylor expansion (Speed/Snap)
- **v2**: Added Vol Surface Polynomial (CME QuikVol), corrected Greek aggregation
  for PnL (Call+Put symmetric vs Call-Put directional), dynamic Δσ(ΔF),
  improved DGC, CME Vol2Vol methodology, updated implementation phases
- **v3**: Added Prop Firm Trader to Section 2.2 with σ-zone strategy,
  added 1σ–5σ SD calculation with 5 center options, asymmetric ranges via
  Vol Surface polynomial. Updated Section 3.5 (quartic per-player with σ-zones)
  and Section 4 (full PnL framework per player: Dealer/MM/HF/PropFirm with
  Vol Surface enhancement, entry/exit logic, aggregation rules, zero-sum check)
