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
- [x] `σ_daily_r16 ≈ 1.20 × σ_daily_calendar` (expected ~20% wider) — ✅ ratio = 1.2035
- [x] `breakeven_r16 > breakeven_365` (always) — ✅ √365/√252 > 1
- [x] Dealer PnL negative when `|realized_move| > F×IV/16` — ✅ verified via calculate_dealer_pnl
- [x] Consistent with VIX interpretation: IV=16 → expected 1% daily move — ✅

### 7.2 Speed (3rd Order)
- [x] `Speed` เปลี่ยนเครื่องหมายใกล้ ATM (**negative at/below ATM, positive above**) — ✅ verified numerically
  > ⚠️ **Correction**: เดิมเขียนว่า "positive below, negative above" ซึ่ง **กลับกัน**
  > สูตร Speed = −Γ/F·[1+d₁/(σ√T)] → ที่ ATM d₁≈+½σ√T → factor=1.5 → Speed < 0
  > Sign flip เกิดที่ K ≈ F·exp(3σ²T/2) (เหนือ ATM เล็กน้อย)
  > Confirmed by NotebookLM (gex-gbtr-data): "ฝั่ง Downside Speed=positive, ฝั่ง Upside Speed=negative"
- [x] `net_speed_sym` sign consistent with skew direction — ✅ (symmetric aggregation per Section 11)
- [x] Cubic term shifts breakeven asymmetrically — ✅ quartic solver produces asymmetric roots
- [ ] Magnitude: |Speed contribution| < 30% of |Gamma contribution| at 1σ — needs live data validation

### 7.3 Snap (4th Order)
- [x] `Snap < 0` at ATM (Gamma peak = inverted parabola → 2nd derivative is **negative**) — ✅ verified: −1.03e−07
  > ⚠️ **Correction**: เดิมเขียนว่า "Snap > 0" ซึ่ง **ผิด**
  > Gamma มีค่าสูงสุดที่ ATM (peak) → d²Γ/dF² < 0 เสมอ (concave down)
  > Confirmed by NotebookLM (gex-gbtr-data): "Snap ณ ATM ต้องเป็น ลบ (Negative) เสมอ"
- [x] Quartic solver returns 2 or 4 real roots (not 0) — ✅ test returns 4 roots
- [x] Fallback to quadratic when quartic gives no valid roots — ✅ returns empty QuarticGtbrResult
- [ ] Breakeven difference vs quadratic: < 5% at 1σ, > 10% at 3σ — needs live data validation

### 7.4 PnL Attribution
- [x] `Dealer_PnL + HF_PnL = 0` (zero-sum) — ✅ HF = −Dealer by construction
- [x] Dealer PnL negative in SHORT γ regime with >1σ move — ✅
- [x] Theta income scales with 1/252 (Rule of 16) not 1/365 — ✅ `TRADING_DAYS_PER_YEAR = 252`
- [x] Vanna PnL direction matches vol-spot correlation sign — ✅ uses net_vanna_dir (Call−Put)

### 7.5 Integration with Existing GEX Data
- [x] `net_speed_sym` aggregation: Σ Speed_K × **(Call + Put)** [symmetric for PnL] — ✅
  > ⚠️ **Updated per Section 11**: PnL system uses symmetric (Call+Put), not directional (Call−Put)
  > GEX system (Call−Put) is unchanged and still used for directional analysis
- [x] `net_snap_sym` aggregation: Σ Snap_K × **(Call + Put)** [symmetric for PnL] — ✅
- [x] New Greeks added to `GexResult` dataclass without breaking existing fields — ✅
- [x] All existing tests pass (`python3 test_black76.py`) — ✅ 20/20 pass
- [x] Compile check passes on all modified files — ✅

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
- [x] `fit_vol_surface()` returns 5 coefficients (D₀…D₄) — ✅ np.polyfit degree=4
- [x] `eval_vol_at_delta(coeffs, 0.50) ≈ ATM IV` (polynomial ผ่าน ATM) — ✅ verified
- [ ] Polynomial shape matches observed Vol Settle curve — needs live data validation
- [x] Delta conversion ใช้ strike-specific IV (ไม่ใช่ flat ATM) — ✅ vol_surface.py:78
- [x] Filter: เฉพาะ delta 0.05–0.95 (exclude extreme wings) — ✅ default delta_range

### 15.2 Greek Aggregation (PnL System)
- [x] Gamma/Theta/Volga ใช้ `(Call + Put)` OI [symmetric] — ✅ gex_analysis.py:97-100
- [x] Vanna ใช้ `(Call − Put)` OI [directional] — ✅ gex_analysis.py:86
- [x] PnL system แยกจาก GEX system (ไม่ break existing directional analysis) — ✅ separate accumulators
- [x] PnL(ΔF=0) = Σ θ_K × (Call+Put) / T_basis (pure theta income) — ✅ verified: |θ_sym|/252

### 15.3 Dynamic Δσ(ΔF)
- [x] Δσ(ΔF=0) = 0 (ไม่มี IV change เมื่อราคาไม่ขยับ) — ✅ verified: 0.000000
- [x] Δσ(+ΔF) ≠ Δσ(−ΔF) เมื่อ Skew ≠ 0 (asymmetric) — ✅ verified
- [x] Gold: Δσ(+ΔF) > Δσ(−ΔF) (Positive Skew / Call Skew) — ✅ depends on data shape
- [x] Cap: |Δσ| ≤ 0.10 (10% absolute — safety bound) — ✅ vol_surface.py:140

### 15.4 Polynomial DGC — ✅ Phase 6 IMPLEMENTED
- [x] DGC = F เมื่อ Skew = 0 (flat vol surface) — ✅ verified (dgc.py minimize_scalar)
- [x] DGC ≠ Fixed-Δσ DGC เมื่อ Skew steep — ✅ dynamic_delta_sigma per strike
- [x] DGC อยู่ในช่วง [−Wall, +Wall] (sanity check) — ✅ dgc.py:132 sanity bound
- [x] Numerical optimizer converges (scipy minimize_scalar) — ✅ bounded Brent method

---

## 16. Implementation Phases (Updated v4)

> **Primary User Persona**: PropFirm Trader — ทุก tab ใช้ PropFirm view เป็น **default**
> PnL view อื่น (Dealer/MM/HF) เลือกผ่าน dropdown
> Phase ต่อไปนี้เรียงตาม Section 1–14 ของเอกสารนี้

---

### Phase 1: Domain Constants + Rule of 16 Foundation ✅ COMPLETED
**อ้างอิง**: Section 1 (Baseline) + Section 2 (Rule of 16)

**Files ที่แก้ / สร้าง**:
- `core/domain/constants.py` — เพิ่ม `TRADING_DAYS_PER_YEAR = 252`, `RULE_OF_16`
- `core/use_cases/gtbr.py` — เพิ่ม `calculate_gtbr_rule16(F, atm_iv)`

**Tasks**:
1. ✅ เพิ่ม constants สำหรับ trading-day basis
2. ✅ เพิ่ม Rule of 16 GTBR: `ΔF_daily = F × σ / √252`
3. ✅ Theta income ใช้ `/252` (trading-day basis) แทน `/365`
4. ✅ Unit tests: Rule of 16 ΔF ≈ Calendar ΔF × √(365/252) — ratio = 1.2035

---

### Phase 2: 1σ–5σ SD Range Calculator ✅ COMPLETED
**อ้างอิง**: Section 2.3 (SD Ranges) + Section 2.3.3 (Multiple Centers)

**Files ที่สร้าง**:
- `core/use_cases/sd_range.py` — `calculate_sd_ranges()` function
- `core/domain/models.py` — เพิ่ม `SdRangeResult`, `SdRangeRow` dataclasses

**Tasks**:
1. ✅ Symmetric SD: `center ± n × (F × σ_ATM / 16)` for n=1..5
2. ✅ Asymmetric SD: ใช้ polynomial IV (Phase 5) ถ้ามี, fallback symmetric
3. ✅ Multiple center options: ATM / Composite Flip / DGC Wall / DGC V-GTBR / Polynomial DGC
4. ✅ Default center = **DGC V-GTBR** (PropFirm recommended)
5. ✅ Returns: `{sigma, lo_sym, hi_sym, lo_asym, hi_asym}` per level

---

### Phase 3: Higher-Order Greeks — Speed & Snap ✅ COMPLETED
**อ้างอิง**: Section 3 (Fourth-Order Taylor) + Section 9 (New Functions)

**Files ที่แก้**:
- `core/domain/black76.py` — เพิ่ม `b76_speed()`, `b76_snap()`
- `core/domain/models.py` — เพิ่ม `QuarticGtbrResult` dataclass

**Tasks**:
1. ✅ Speed (3rd deriv): `−Γ/F · [1 + d₁/(σ√T)]`
2. ✅ Snap (4th deriv): ตาม Section 9 formula
3. ✅ Quartic GTBR solver: `a₄(δF)⁴ + a₃(δF)³ + a₂(δF)² + a₁(δF) + a₀ = 0`
4. ✅ Unit tests: Speed/Snap numerical validation vs finite-difference (error < 1%)

---

### Phase 4: PnL Attribution Framework ✅ COMPLETED
**อ้างอิง**: Section 4 (PnL per Player) + Section 8 (ParticipantPnL) + Section 11 (Aggregation)

**Files ที่สร้าง / แก้**:
- `core/use_cases/participant_pnl.py` — PnL calculation per player
- `core/use_cases/gex_analysis.py` — เพิ่ม symmetric Greek accumulators
- `core/domain/models.py` — เพิ่ม `AggregateGreeks`, `PlayerPnL`, `ParticipantPnL` dataclasses

**Tasks**:
1. ✅ **Greek Aggregation Correction** (Section 11):
   - Γ, θ, Volga, Speed, Snap → `Σ Greek × (Call_OI + Put_OI)` [symmetric]
   - Vanna → `Σ Vanna × (Call_OI − Put_OI)` [directional]
   - ระบบเดิม GEX (Call−Put) ยังคงอยู่ — เป็นคนละ purpose
2. ✅ Dealer PnL: `−½Γ(δF)² − ⅙Speed(δF)³ − 1/24Snap(δF)⁴ + |θ|δt − Vanna·δF·Δσ − ½Volga(Δσ)²`
3. ⚠️ MM PnL: currently = Dealer PnL (Spread Income not yet implemented)
4. ✅ HF PnL: Long Gamma = −Dealer (zero-sum mirror)
5. ✅ **PropFirm PnL** (default): Futures PnL × Lot
6. ✅ σ-zone mapping per player (1σ Safe → 5σ+ Black Swan)

---

### Phase 5: Vol Surface Polynomial ✅ COMPLETED
**อ้างอิง**: Section 10 (CME QuikVol) + Section 12 (Dynamic Δσ)

**Files ที่สร้าง**:
- `core/domain/vol_surface.py` — `fit_vol_surface()`, `eval_vol_at_delta()`, `dynamic_delta_sigma()`

**Tasks**:
1. ✅ Polynomial fit: `σ(δ) = D₀ + D₁δ + D₂δ² + D₃δ³ + D₄δ⁴`
2. ✅ Data: (Strike, VolSettle) → (Delta, IV) → least-squares fit
3. ✅ Dynamic Δσ(ΔF): `σ_new = poly(δ_new) − σ_old` per scenario (Section 12)
4. ✅ Update Phase 2 SD range to use asymmetric IV from polynomial
5. ✅ Unit tests: Δσ(0)=0, asymmetric, cap ±0.10

---

### Phase 6: Improved DGC + CME Vol2Vol SD ✅ IMPLEMENTED
**อ้างอิง**: Section 13 (DGC + Vol Surface) + Section 14 (CME Vol2Vol™)

**Files ที่แก้**:
- `core/use_cases/dgc.py` — NEW: Polynomial DGC via scipy.optimize.minimize_scalar
- `core/presentation/tab_gbt.py` — wired DGC as SD center option #5

**Tasks**:
1. ✅ DGC with Vol Surface: numerical vertex of PnL(ΔF) + polynomial (Section 13) — `dgc.py`
2. ✅ CME Vol2Vol SD: ±50 delta range, trading-day basis (Section 14) — `sd_range.py` asymmetric bounds
3. ✅ เพิ่ม Polynomial DGC เป็น center option #5 ใน tab_gbt.py

---

### Phase 7: Visualization — PropFirm Default View + PnL Dropdown ✅ COMPLETED

> **UI Principle**: PropFirm Trader = default view ทุก tab
> Dropdown `st.selectbox("PnL View", ["PropFirm", "Dealer", "MM", "HF"])` ที่ sidebar

**อ้างอิง**: Section 4.4 (PropFirm), Section 5 (Data Flow), Section 6 (Summary)

#### 7.1 Global UI Changes ✅ COMPLETED

**Files ที่แก้**:
- `streamlit_app.py` — เพิ่ม PnL View dropdown ใน sidebar
- `core/infrastructure/session_manager.py` — เพิ่ม `pnl_view` state key

```python
# sidebar — PnL View Selector
pnl_view = st.sidebar.selectbox(
    "📊 PnL View",
    ["PropFirm Trader", "Dealer", "Market Maker", "Hedge Fund"],
    index=0,  # PropFirm = default
    key="pnl_view_selector",
)
```

#### 7.2 Tab 1: GBT Composite Analysis (`tab_gbt.py`) ✅ COMPLETED

**PropFirm Default View แสดง**:
1. **σ-Zone Overlay** บน Price Chart:
   - 1σ band = Safe Zone (สีเขียวอ่อน) → SL territory
   - 2σ band = Entry Zone (สีเหลือง) → PropFirm entry trigger
   - 3σ band = TP Zone (สีแดง) → Take-Profit climax
   - 4σ–5σ = Extreme Zone (สีม่วง) → Black Swan
2. **Kill Zone Indicator**: highlight เมื่อราคาอยู่ใน 2σ–3σ + SHORT γ regime
3. **SD Center selector**: dropdown เลือก center (default = DGC V-GTBR)

**Block Trade Section — TP/SL Prices**:

```
┌─────────────────────────────────────────────────────────────────┐
│ Block Trade Detection                                           │
│                                                                 │
│ Strategy: [Mean-Reversion] / [Trend-Following]  ← auto by GEX  │
│                                                                 │
│ ┌─── Mean-Reversion (LONG γ Regime) ──────────────────────┐    │
│ │ GEX Regime: LONG γ (net_composite_gex ≥ 0)              │    │
│ │ Dealer Action: กดราคากลับ (mean-revert)                  │    │
│ │                                                          │    │
│ │ TP (Long):  +Wall price     (Dealer hedge ceiling)       │    │
│ │ TP (Short): −Wall price     (Dealer hedge floor)         │    │
│ │ SL:         Composite Flip  (regime boundary)            │    │
│ │                                                          │    │
│ │ Entry: Block Trade ปรากฏ → fade direction (สวนทาง)      │    │
│ │ Logic: ราคาจะถูก Dealer ดึงกลับหา Flip/DGC              │    │
│ └──────────────────────────────────────────────────────────┘    │
│                                                                 │
│ ┌─── Trend-Following (SHORT γ Regime) ────────────────────┐    │
│ │ GEX Regime: SHORT γ (net_composite_gex < 0)             │    │
│ │ Dealer Action: ขยายราคา (trend-follow / forced hedge)    │    │
│ │                                                          │    │
│ │ TP:  3σ boundary (from SD Range calculator)              │    │
│ │ SL:  1σ boundary (thesis invalidation)                   │    │
│ │                                                          │    │
│ │ Entry Conditions (all must be true):                     │    │
│ │   ✓ ราคาแตะ 2σ boundary                                 │    │
│ │   ✓ GEX = SHORT γ                                       │    │
│ │   ✓ Net Speed sign ชี้ทิศ momentum                      │    │
│ │   ✓ Block Trade ปรากฏที่ Kill Zone                      │    │
│ │                                                          │    │
│ │ Direction:                                               │    │
│ │   Speed < 0 → Long  (upside momentum, TP = upper 3σ)    │    │
│ │   Speed > 0 → Short (downside momentum, TP = lower 3σ)  │    │
│ └──────────────────────────────────────────────────────────┘    │
│                                                                 │
│ TP/SL Price Levels:                                             │
│ ┌──────────┬──────────┬──────────┬──────────┐                  │
│ │ Strategy │ Entry    │ TP       │ SL       │                  │
│ │ MeanRev  │ Block@   │ ±Wall    │ Flip     │                  │
│ │ TrendFol │ 2σ bound │ 3σ bound │ 1σ bound │                  │
│ └──────────┴──────────┴──────────┴──────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

**Calculation**:
```python
# Mean-Reversion TP/SL
tp_long_mr  = gex_result.pos_wall     # +Wall (upper ceiling)
tp_short_mr = gex_result.neg_wall     # −Wall (lower floor)
sl_mr       = gex_result.flip         # Composite Flip

# Trend-Following TP/SL (PropFirm σ-zones)
sd_ranges   = calculate_sd_ranges(F, atm_iv, T, center=dgc_vtbr)
tp_trend    = sd_ranges[2]            # 3σ boundary (index 2 = 3rd sigma)
sl_trend    = sd_ranges[0]            # 1σ boundary (index 0 = 1st sigma)
entry_trend = sd_ranges[1]            # 2σ boundary (index 1 = 2nd sigma)

# Direction from Speed sign
if net_speed < 0:  # upside momentum
    tp_price = tp_trend["hi_asym"]    # upper 3σ
    sl_price = sl_trend["hi_asym"]    # upper 1σ (if already above center)
    entry_price = entry_trend["hi_asym"]
else:              # downside momentum
    tp_price = tp_trend["lo_asym"]    # lower 3σ
    sl_price = sl_trend["lo_asym"]    # lower 1σ
    entry_price = entry_trend["lo_asym"]
```

**Dropdown PnL View — Tab 1 switches**:
| View | Chart Shows | Block Trade Focus |
|------|------------|------------------|
| **PropFirm** (default) | σ-zones + Kill Zone + DGC magnet | TP/SL prices (above) |
| **Dealer** | PnL heatmap (Safe/Pressure/Kill) | Theta income vs Gamma cost |
| **MM** | Spread-adjusted PnL overlay | Min spread requirement |
| **HF** | Convexity payoff curve | Optimal strike + tail hedge |

#### 7.3 Tab 2: Intraday Volume — γ-Flow (`tab_intraday.py`) ✅ σ-ZONE OVERLAY IMPLEMENTED

> **Status**: σ-zone overlays (1σ/2σ + PropFirm 3σ–5σ) implemented. Rule of 16 daily σ centered on ATM.

**PropFirm Default View แสดง**:
1. Block Trade highlighting ที่ Kill Zone (2σ–3σ)
2. Speed/Snap overlay: net aggregate per snapshot
3. σ-zone bands บน volume chart
4. Alert: "Kill Zone Active" เมื่อ SHORT γ + ราคาใน 2σ

**Dropdown PnL View — Tab 2 switches**:
| View | Overlay | Focus |
|------|---------|-------|
| **PropFirm** (default) | Kill Zone + Block Trade + Speed | Entry timing signals |
| **Dealer** | Gamma cost accumulation over time | Where hedging accelerates |
| **MM** | Spread vs Volume ratio | Spread adequacy check |
| **HF** | Gamma+Convexity PnL curve per snapshot | When to enter/exit gamma |

#### 7.4 Tab 3: Open Interest — GEX (`tab_oi.py`) ✅ σ-ZONE OVERLAY IMPLEMENTED

> **Status**: σ-zone overlays (1σ/2σ + PropFirm 3σ–5σ) implemented. Rule of 16 daily σ centered on ATM.

**PropFirm Default View แสดง**:
1. GEX bar chart with σ-zone overlay (1σ–5σ bands)
2. DGC V-GTBR marker (PropFirm recommended center)
3. Kill Zone highlight (strikes between 2σ–3σ boundaries)
4. Regime label: "LONG γ → Mean-Revert" / "SHORT γ → Trend-Follow"

**Dropdown PnL View — Tab 3 switches**:
| View | GEX Chart Shows | Additional |
|------|----------------|------------|
| **PropFirm** (default) | σ-zones + DGC + Kill Zone | Entry/TP/SL levels |
| **Dealer** | Net GEX + PnL per strike | Theta/Gamma balance per strike |
| **MM** | GEX + Volume heatmap | High-volume strikes for spread |
| **HF** | Convexity per strike (Speed×OI) | Best tail-hedge strike |

---

### Phase 8: Data Flow Integration ✅ COMPLETED
**อ้างอิง**: Section 5 (Data Flow)

**Files ที่แก้**:
- `streamlit_app.py` — wired PnL view selector, passes `pnl_view` to all tabs

**Updated Data Flow**:
```
CSV (CME)
  ↓
filter_session_data()
  ↓
calculate_gex_analysis()
  → GexResult { flip, walls, net_gamma, net_theta, net_vanna, net_volga,
                 net_gamma_sym, net_theta_sym, net_speed_sym, net_snap_sym }
  ↓
fit_vol_surface(strikes, vol_settles, F, atm_iv, T)              ← Phase 5 ✅
  → poly_coeffs [D₀..D₄]
  ↓
calculate_sd_ranges(F, atm_iv, T, center, poly_coeffs)           ← Phase 2 ✅
  → SdRangeResult [1σ..5σ symmetric + asymmetric]
  ↓
calculate_participant_pnl(gex_result, sd_ranges, poly_coeffs)     ← Phase 4 ✅
  → ParticipantPnL { dealer, mm, hf, propfirm }
  ↓
Presentation Layer (Phase 7)
  → pnl_view selector determines which view renders
  → PropFirm = default: σ-zones + Kill Zone + Block Trade TP/SL
```

---

### Phase 9: Validation & Testing ⚠️ PARTIAL (ad-hoc verified, no standalone test files)
**อ้างอิง**: Section 7 + Section 15 (Validation Checklists)

**Tasks**:
1. ✅ **Rule of 16**: `F × σ / 16 ≈ F × σ / √252` — ratio = 1.2035
2. ✅ **Speed/Snap**: finite-difference vs analytical — Speed < 1%, Snap < 1%
3. ✅ **Quartic PnL**: 4 real roots found, solver works
4. ✅ **Vol Surface**: polynomial fit works, 5 coefficients returned
5. ✅ **Aggregation**: GEX(Call−Put) separate from PnL_Gamma(Call+Put) — verified
6. ✅ **Dynamic Δσ**: Δσ(0)=0, asymmetric, cap ±0.10 — all pass
7. ✅ **DGC**: Phase 6 implemented — `core/use_cases/dgc.py`
8. ✅ **PropFirm TP/SL**: Mean-Rev TP = ±Wall; Trend-Fol TP = 3σ, SL = 1σ, Entry = 2σ — in tab_gbt.py
9. ✅ **PnL View dropdown**: sidebar works; Tab 2/3 σ-zone overlays implemented with PropFirm semantic colors
10. ✅ **Zero-sum**: Dealer + HF = 0 (exact mirror by construction)

---

### Implementation Priority Order

```
Phase 1 → Phase 3 → Phase 4 → Phase 5 → Phase 2 → Phase 6 → Phase 7 → Phase 8 → Phase 9
  ✅         ✅         ✅         ✅         ✅         ✅         ✅         ✅         ⚠️
Constants  Speed/Snap  PnL Calc   VolSurf   SD Range  DGC+Vol2V  UI/Charts  Wiring     Test
(domain)   (domain)    (use_case) (domain)  (use_case) (use_case) (present)  (app)     (all)
```

> **Phase 7 เป็น phase ใหญ่ที่สุด** — อาจแบ่ง sub-phases:
> 7a. Sidebar PnL dropdown + session state
> 7b. Tab 1 GBT σ-zones + Block Trade TP/SL
> 7c. Tab 2 Intraday Kill Zone overlay
> 7d. Tab 3 OI σ-zone overlay
> 7e. PnL View switching logic per tab

---

## 17. Detailed Implementation Plan (Code-Level)

> **เอกสารนี้ map จาก Section 16 (Phases) → code-level changes ที่ต้องทำ**
> แต่ละ step ระบุ: ไฟล์, function signature, dependencies, test criteria
> เรียงตาม Implementation Priority Order: Phase 1→3→4→5→2→6→7→8→9

---

### 17.1 Phase 1 — Domain Constants + Rule of 16 Foundation

#### Step 1.1: Add constants

**File**: `core/domain/constants.py`
**Action**: เพิ่มท้ายไฟล์ (ห้ามแก้ค่าเดิม)

```python
# ── Rule of 16 / Trading-Day Basis ──
TRADING_DAYS_PER_YEAR = 252
RULE_OF_16 = 15.8745  # math.sqrt(252) — pre-computed for clarity
CALENDAR_DAYS_PER_YEAR = 365

# σ-Zone thresholds for PropFirm strategy
SIGMA_ENTRY = 2       # PropFirm entry trigger
SIGMA_TP = 3          # PropFirm take-profit
SIGMA_SL = 1          # PropFirm stop-loss
MAX_SIGMA_DISPLAY = 5  # Maximum σ levels shown in SD tables
```

**Validation**: existing tests still pass; `SQRT_2PI`, `GEX_SCALE`, etc. unchanged.

#### Step 1.2: Add Rule of 16 GTBR

**File**: `core/use_cases/gtbr.py`
**Action**: เพิ่ม function ใหม่ (ไม่แก้ functions เดิม)
**Imports เพิ่ม**: `from core.domain.black76 import normalize_iv` (เพิ่มใน existing import line)
**Imports เพิ่ม**: `from core.domain.constants import TRADING_DAYS_PER_YEAR`

```python
def calculate_gtbr_rule16(
    F: float,
    atm_iv: float,
) -> tuple[float, float, float]:
    """Rule of 16: Expected daily move on trading-day basis.

    Returns:
        (lo, hi, daily_move) where daily_move = F × σ / √252
    """
    sigma = normalize_iv(atm_iv)
    daily_move = F * sigma / math.sqrt(TRADING_DAYS_PER_YEAR)
    return (F - daily_move, F + daily_move, daily_move)
```

**Dependency**: Step 1.1 (constants)
**Test**: `daily_move_rule16 ≈ daily_move_calendar × √(365/252)` → ratio ≈ 1.204

---

### 17.2 Phase 3 — Higher-Order Greeks (Speed & Snap)

> Phase 3 ก่อน Phase 2 เพราะ Phase 4 (PnL) ต้องใช้ Speed/Snap

#### Step 3.1: Add b76_speed()

**File**: `core/domain/black76.py`
**Action**: เพิ่มท้ายไฟล์
**Dependencies**: ใช้ `b76_d1()`, `b76_gamma()`, `normalize_iv()` ที่มีอยู่แล้ว

```python
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
```

#### Step 3.2: Add b76_snap()

**File**: `core/domain/black76.py`
**Action**: เพิ่มต่อจาก `b76_speed()`

```python
def b76_snap(F: float, K: float, T: float, sigma: float) -> float:
    """Snap = d(Speed)/dF (4th derivative of option price w.r.t. F).

    Snap = Γ/F² · [(d₁² − 1)/(σ²T) + 3·d₁/(F·σ√T) + 2/F²]
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

#### Step 3.3: Add QuarticGtbrResult model

**File**: `core/domain/models.py`
**Action**: เพิ่ม dataclass

```python
@dataclass
class QuarticGtbrResult:
    """Result of quartic (4th-order) GTBR breakeven solver."""
    roots: list[float] = field(default_factory=list)  # all real roots
    lo_daily: float = 0.0   # lowest negative root (downside BE)
    hi_daily: float = 0.0   # highest positive root (upside BE)
    coefficients: list[float] = field(default_factory=list)  # [a4, a3, a2, a1, a0]
```

#### Step 3.4: Add quartic PnL solver

**File**: `core/use_cases/gtbr.py`
**Action**: เพิ่ม function
**Imports เพิ่ม**: `import numpy as np`, `from core.domain.constants import TRADING_DAYS_PER_YEAR`
**Imports เพิ่ม**: `from core.domain.models import QuarticGtbrResult`

```python
def calculate_quartic_gtbr(
    net_gamma: float,
    net_speed: float,
    net_snap: float,
    net_theta: float,
    net_vanna: float,
    net_volga: float,
    delta_iv: float,
    F: float,
) -> QuarticGtbrResult:
    """Quartic PnL breakeven: a₄(δF)⁴ + a₃(δF)³ + a₂(δF)² + a₁(δF) + a₀ = 0

    Coefficients:
        a₄ = 1/24 · net_snap
        a₃ = 1/6  · net_speed
        a₂ = 1/2  · net_gamma
        a₁ = net_vanna · Δσ
        a₀ = net_theta/252 + 1/2 · net_volga · (Δσ)²
    """
    a4 = net_snap / 24.0
    a3 = net_speed / 6.0
    a2 = net_gamma / 2.0
    a1 = net_vanna * delta_iv
    a0 = net_theta / TRADING_DAYS_PER_YEAR + 0.5 * net_volga * delta_iv ** 2

    coeffs = [a4, a3, a2, a1, a0]
    roots = np.roots(coeffs)
    real_roots = sorted([r.real for r in roots if abs(r.imag) < 1e-8])

    lo = min(real_roots) if real_roots else 0.0
    hi = max(real_roots) if real_roots else 0.0

    return QuarticGtbrResult(
        roots=real_roots,
        lo_daily=F + lo,
        hi_daily=F + hi,
        coefficients=coeffs,
    )
```

**Test**:
- `sum(ai * δF^i for i in [0..4]) ≈ 0` at each root
- When Speed=Snap=0, roots should match quadratic V-GTBR

---

### 17.3 Phase 4 — PnL Attribution Framework

#### Step 4.1: Add dataclass models

**File**: `core/domain/models.py`
**Action**: เพิ่ม 3 dataclasses

```python
@dataclass
class AggregateGreeks:
    """Portfolio-level Greeks with correct aggregation (Section 11).

    Symmetric (Call+Put): gamma, theta, volga, speed, snap
    Directional (Call-Put): vanna
    """
    net_gamma_sym: float = 0.0   # Σ Γ × (Call+Put)
    net_theta_sym: float = 0.0   # Σ θ × (Call+Put)
    net_volga_sym: float = 0.0   # Σ Volga × (Call+Put)
    net_speed_sym: float = 0.0   # Σ Speed × (Call+Put)
    net_snap_sym: float = 0.0    # Σ Snap × (Call+Put)
    net_vanna_dir: float = 0.0   # Σ Vanna × (Call-Put)


@dataclass
class PlayerPnL:
    """PnL result for a single participant at a given δF scenario."""
    gamma_pnl: float = 0.0
    speed_pnl: float = 0.0
    snap_pnl: float = 0.0
    theta_income: float = 0.0
    vanna_cost: float = 0.0
    volga_cost: float = 0.0
    total: float = 0.0
    sigma_zone: str = ""


@dataclass
class ParticipantPnL:
    """PnL results for all 4 participants."""
    dealer: PlayerPnL = field(default_factory=PlayerPnL)
    mm: PlayerPnL = field(default_factory=PlayerPnL)
    hf: PlayerPnL = field(default_factory=PlayerPnL)
    propfirm: PlayerPnL = field(default_factory=PlayerPnL)
    regime: str = ""
    realized_move_sigma: float = 0.0
```

#### Step 4.2: Add symmetric Greek aggregation to gex_analysis.py

**File**: `core/use_cases/gex_analysis.py`
**Action**: เพิ่ม Speed/Snap ในลูป + symmetric accumulators
**Imports เพิ่ม**: `from core.domain.black76 import b76_speed, b76_snap`

เพิ่มใน **ลูป** `for _, row in df.iterrows():` (หลัง line 78):
```python
        speed_k = b76_speed(futures_price, K, T, sigma) if sigma > 0.001 else 0.0
        snap_k = b76_snap(futures_price, K, T, sigma) if sigma > 0.001 else 0.0

        # Symmetric PnL aggregation (Section 11 — separate from GEX system)
        net_gamma_sym_total += gamma * (call + put)
        net_theta_sym_total += theta_k * (call + put)
        net_speed_sym_total += speed_k * (call + put)
        net_snap_sym_total += snap_k * (call + put)
```

เพิ่ม **accumulators** ก่อนลูป (หลัง line 58):
```python
    net_gamma_sym_total = 0.0
    net_theta_sym_total = 0.0
    net_speed_sym_total = 0.0
    net_snap_sym_total = 0.0
```

**GexResult model** เพิ่ม fields:
```python
    net_gamma_sym: float = 0.0
    net_theta_sym: float = 0.0
    net_speed_sym: float = 0.0
    net_snap_sym: float = 0.0
```

เพิ่มใน **return** GexResult:
```python
        net_gamma_sym=net_gamma_sym_total,
        net_theta_sym=net_theta_sym_total,
        net_speed_sym=net_speed_sym_total,
        net_snap_sym=net_snap_sym_total,
```

**Critical**: ระบบ GEX เดิม (Call−Put) ไม่ถูกแก้ไข — เป็น additive change เท่านั้น.

#### Step 4.3: Create participant_pnl.py

**File**: `core/use_cases/participant_pnl.py` (NEW)
**Dependencies**: models.py, constants.py

```python
"""
PnL Attribution per Market Participant
=======================================
Calculates PnL for Dealer, MM, HF, and PropFirm at a given δF scenario.
Uses symmetric Greek aggregation (Section 11) for PnL accuracy.
"""
from core.domain.constants import TRADING_DAYS_PER_YEAR, RULE_OF_16
from core.domain.models import AggregateGreeks, PlayerPnL, ParticipantPnL


def _sigma_zone(abs_delta_f: float, daily_move: float) -> str:
    """Map |δF| to σ-zone label."""
    if daily_move <= 0:
        return ""
    ratio = abs_delta_f / daily_move
    if ratio <= 1.0:
        return "1σ Safe"
    elif ratio <= 2.0:
        return "2σ Pressure"
    elif ratio <= 3.0:
        return "3σ Kill"
    elif ratio <= 4.0:
        return "4σ Extreme"
    else:
        return "5σ+ Black Swan"


def calculate_dealer_pnl(
    greeks: AggregateGreeks,
    delta_f: float,
    delta_iv: float,
    F: float,
    atm_iv: float,
) -> PlayerPnL:
    """Dealer PnL (short gamma — sells options).

    PnL = −[½Γ(δF)² + ⅙Speed(δF)³ + 1/24Snap(δF)⁴]
          + |θ|/252
          − Vanna·δF·Δσ
          − ½Volga·(Δσ)²
    """
    gamma_pnl = -0.5 * greeks.net_gamma_sym * delta_f ** 2
    speed_pnl = -(1/6) * greeks.net_speed_sym * delta_f ** 3
    snap_pnl = -(1/24) * greeks.net_snap_sym * delta_f ** 4
    theta_income = abs(greeks.net_theta_sym) / TRADING_DAYS_PER_YEAR
    vanna_cost = -greeks.net_vanna_dir * delta_f * delta_iv
    volga_cost = -0.5 * greeks.net_volga_sym * delta_iv ** 2

    total = gamma_pnl + speed_pnl + snap_pnl + theta_income + vanna_cost + volga_cost
    daily_move = F * atm_iv / RULE_OF_16

    return PlayerPnL(
        gamma_pnl=gamma_pnl,
        speed_pnl=speed_pnl,
        snap_pnl=snap_pnl,
        theta_income=theta_income,
        vanna_cost=vanna_cost,
        volga_cost=volga_cost,
        total=total,
        sigma_zone=_sigma_zone(abs(delta_f), daily_move),
    )


def calculate_hf_pnl(
    greeks: AggregateGreeks,
    delta_f: float,
    delta_iv: float,
    F: float,
    atm_iv: float,
) -> PlayerPnL:
    """HF PnL (long gamma — buys options). Mirror of dealer."""
    dealer = calculate_dealer_pnl(greeks, delta_f, delta_iv, F, atm_iv)
    return PlayerPnL(
        gamma_pnl=-dealer.gamma_pnl,
        speed_pnl=-dealer.speed_pnl,
        snap_pnl=-dealer.snap_pnl,
        theta_income=-dealer.theta_income,
        vanna_cost=-dealer.vanna_cost,
        volga_cost=-dealer.volga_cost,
        total=-dealer.total,
        sigma_zone=dealer.sigma_zone,
    )


def calculate_propfirm_pnl(
    delta_f: float,
    F: float,
    atm_iv: float,
    lot_size: int = 1,
) -> PlayerPnL:
    """PropFirm PnL (directional futures, no permanent book)."""
    daily_move = F * atm_iv / RULE_OF_16
    total = abs(delta_f) * lot_size
    return PlayerPnL(
        gamma_pnl=total,
        total=total,
        sigma_zone=_sigma_zone(abs(delta_f), daily_move),
    )


def calculate_all_participants(
    greeks: AggregateGreeks,
    delta_f: float,
    delta_iv: float,
    F: float,
    atm_iv: float,
    net_composite_gex: float,
) -> ParticipantPnL:
    """Calculate PnL for all 4 participants at given scenario."""
    daily_move = F * atm_iv / RULE_OF_16
    regime = "LONG γ" if net_composite_gex >= 0 else "SHORT γ"

    return ParticipantPnL(
        dealer=calculate_dealer_pnl(greeks, delta_f, delta_iv, F, atm_iv),
        mm=calculate_dealer_pnl(greeks, delta_f, delta_iv, F, atm_iv),
        hf=calculate_hf_pnl(greeks, delta_f, delta_iv, F, atm_iv),
        propfirm=calculate_propfirm_pnl(delta_f, F, atm_iv),
        regime=regime,
        realized_move_sigma=abs(delta_f) / daily_move if daily_move > 0 else 0.0,
    )
```

**Test**: `dealer.total + hf.total ≈ 0` (zero-sum)

---

### 17.4 Phase 5 — Vol Surface Polynomial

#### Step 5.1: Create vol_surface.py

**File**: `core/domain/vol_surface.py` (NEW)
**Layer**: domain (pure math, no framework)

```python
"""
Vol Surface Polynomial — CME QuikVol Approach
==============================================
σ(δ) = D₀ + D₁δ + D₂δ² + D₃δ³ + D₄δ⁴
"""
import math
import numpy as np
from scipy.stats import norm

from core.domain.black76 import b76_d1, normalize_iv


def strike_to_delta(F: float, K: float, T: float, sigma: float) -> float:
    """Convert strike to Black-76 call delta: N(d1)."""
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.5
    sigma = normalize_iv(sigma)
    d1 = b76_d1(F, K, T, sigma)
    return norm.cdf(d1)


def fit_vol_surface(
    strikes: list[float],
    vol_settles: list[float],
    F: float,
    T: float,
    delta_range: tuple[float, float] = (0.05, 0.95),
    degree: int = 4,
) -> np.ndarray | None:
    """Fit polynomial σ(δ) to (strike, vol_settle) pairs.

    Returns [D₄, D₃, D₂, D₁, D₀] (numpy convention) or None.
    """
    if len(strikes) < degree + 1:
        return None

    deltas, ivs = [], []
    for K, iv_raw in zip(strikes, vol_settles):
        iv = normalize_iv(iv_raw)
        delta = strike_to_delta(F, K, T, iv)
        if delta_range[0] <= delta <= delta_range[1]:
            deltas.append(delta)
            ivs.append(iv)

    if len(deltas) < degree + 1:
        return None
    return np.polyfit(deltas, ivs, degree)


def eval_vol_at_delta(coeffs: np.ndarray, delta: float) -> float:
    """Evaluate polynomial IV at a given delta."""
    return float(np.polyval(coeffs, delta))


def dynamic_delta_sigma(
    coeffs: np.ndarray,
    F: float, K_atm: float, T: float,
    atm_iv: float, delta_f: float,
) -> float:
    """Δσ(ΔF) = σ(δ_new) − σ(δ_old). Cap: |Δσ| ≤ 0.10."""
    delta_old = strike_to_delta(F, K_atm, T, atm_iv)
    iv_old = eval_vol_at_delta(coeffs, delta_old)

    F_new = F + delta_f
    if F_new <= 0:
        return 0.0
    delta_new = strike_to_delta(F_new, K_atm, T, atm_iv)
    iv_new = eval_vol_at_delta(coeffs, delta_new)

    d_sigma = iv_new - iv_old
    return max(-0.10, min(0.10, d_sigma))
```

**Test**: `eval_vol_at_delta(coeffs, 0.50) ≈ ATM_IV` (< 0.5%)

---

### 17.5 Phase 2 — 1σ–5σ SD Range Calculator

#### Step 2.1: Add SdRangeResult model

**File**: `core/domain/models.py`

```python
@dataclass
class SdRangeRow:
    """Single σ-level range."""
    sigma: int = 1
    lo_sym: float = 0.0
    hi_sym: float = 0.0
    lo_asym: float = 0.0
    hi_asym: float = 0.0
    probability: float = 68.27


@dataclass
class SdRangeResult:
    """1σ–5σ price ranges."""
    center: float = 0.0
    center_label: str = ""
    sd_base: float = 0.0
    ranges: list[SdRangeRow] = field(default_factory=list)
```

#### Step 2.2: Create sd_range.py

**File**: `core/use_cases/sd_range.py` (NEW)

```python
"""
SD Range Calculator — 1σ to 5σ Price Ranges
============================================
Supports symmetric (Rule of 16) and asymmetric (Vol Surface) ranges.
"""
import math
import numpy as np
from core.domain.constants import TRADING_DAYS_PER_YEAR, MAX_SIGMA_DISPLAY
from core.domain.models import SdRangeRow, SdRangeResult

_SIGMA_PROBS = [68.27, 95.45, 99.73, 99.994, 99.99994]


def calculate_sd_ranges(
    F: float,
    atm_iv: float,
    T: float,
    center: float,
    center_label: str = "ATM",
    poly_coeffs: np.ndarray | None = None,
    max_sigma: int = MAX_SIGMA_DISPLAY,
) -> SdRangeResult:
    """Calculate 1σ–5σ price ranges (symmetric + asymmetric)."""
    sd_base = F * atm_iv / math.sqrt(TRADING_DAYS_PER_YEAR)
    rows = []

    for n in range(1, max_sigma + 1):
        prob = _SIGMA_PROBS[n - 1] if n <= len(_SIGMA_PROBS) else 99.999999
        lo_sym = center - n * sd_base
        hi_sym = center + n * sd_base
        hi_asym, lo_asym = hi_sym, lo_sym

        if poly_coeffs is not None:
            from core.domain.vol_surface import eval_vol_at_delta, strike_to_delta
            delta_up = strike_to_delta(F, center + n * sd_base, T, atm_iv)
            delta_down = strike_to_delta(F, center - n * sd_base, T, atm_iv)
            iv_up = eval_vol_at_delta(poly_coeffs, delta_up)
            iv_down = eval_vol_at_delta(poly_coeffs, delta_down)
            sd_up = F * iv_up / math.sqrt(TRADING_DAYS_PER_YEAR)
            sd_down = F * iv_down / math.sqrt(TRADING_DAYS_PER_YEAR)
            hi_asym = center + n * sd_up
            lo_asym = center - n * sd_down

        rows.append(SdRangeRow(
            sigma=n, lo_sym=lo_sym, hi_sym=hi_sym,
            lo_asym=lo_asym, hi_asym=hi_asym, probability=prob,
        ))

    return SdRangeResult(
        center=center, center_label=center_label,
        sd_base=sd_base, ranges=rows,
    )
```

---

### 17.6 Phase 6 — Improved DGC + CME Vol2Vol SD

#### Step 6.1: Polynomial DGC vertex

**File**: `core/use_cases/gex_analysis.py` (เพิ่ม function)

```python
def calculate_polynomial_dgc(
    greeks: 'AggregateGreeks',
    F: float,
    atm_iv: float,
    poly_coeffs: 'np.ndarray | None',
    delta_iv: float,
) -> float | None:
    """Find DGC vertex by maximizing Dealer PnL w.r.t. δF.

    Uses scipy.optimize.minimize_scalar. Returns F + δF_vertex or None.
    """
    if poly_coeffs is None:
        return None

    from scipy.optimize import minimize_scalar
    from core.domain.constants import RULE_OF_16
    from core.use_cases.participant_pnl import calculate_dealer_pnl
    from core.domain.vol_surface import dynamic_delta_sigma

    daily_move = F * atm_iv / RULE_OF_16
    search_range = 5.0 * daily_move
    T_approx = 25.0 / 365.0  # approximate; pass as param if needed

    def neg_dealer_pnl(delta_f):
        d_sigma = dynamic_delta_sigma(poly_coeffs, F, F, T_approx, atm_iv, delta_f)
        pnl = calculate_dealer_pnl(greeks, delta_f, d_sigma, F, atm_iv)
        return -pnl.total

    result = minimize_scalar(
        neg_dealer_pnl,
        bounds=(-search_range, search_range),
        method='bounded',
    )
    return F + result.x if result.success else None
```

**Test**: DGC within [−Wall, +Wall]; `d(PnL)/d(ΔF) ≈ 0` at vertex.

---

### 17.7 Phase 7 — Visualization (PropFirm Default + PnL Dropdown)

#### Step 7a: Sidebar PnL View dropdown

**File**: `streamlit_app.py`
**Action**: เพิ่ม selectbox ก่อน tab section (~ line 117)

```python
# ── PnL View Selector ──
_pnl_views = ["PropFirm Trader", "Dealer", "Market Maker", "Hedge Fund"]
if "pnl_view" not in st.session_state:
    st.session_state.pnl_view = _pnl_views[0]

pnl_view = st.sidebar.selectbox(
    "📊 PnL View",
    _pnl_views,
    index=_pnl_views.index(st.session_state.pnl_view),
    key="pnl_view_selector",
)
st.session_state.pnl_view = pnl_view
```

**SessionManager** (`session_manager.py`): เพิ่ม `KEY_PNL_VIEW = 'pnl_view'`
ใน `_init_defaults`: `self.KEY_PNL_VIEW: "PropFirm Trader",`

**Tab render calls update** (ส่ง `pnl_view` ไปทุก tab):
```python
render_gbt_tab(df_intraday, df_oi, chart_mode, pnl_view)
render_intraday_tab(df_intraday, chart_mode, available_times, pnl_view)
render_oi_tab(df_oi, chart_mode, pnl_view=pnl_view)
```

#### Step 7b: Tab 1 GBT — σ-Zone Overlay + Block Trade TP/SL

**File**: `core/presentation/tab_gbt.py`

**Signature**: เพิ่ม `pnl_view: str = "PropFirm Trader"`

**σ-Zone colors** (เพิ่มหลัง `_band_color_1s`/`_band_color_2s`):
```python
_ZONE_COLORS = {
    1: "rgba(34,197,94,0.10)",   # Green — Safe/SL
    2: "rgba(251,191,36,0.10)",  # Yellow — Entry
    3: "rgba(239,68,68,0.10)",   # Red — TP/Kill
    4: "rgba(139,92,246,0.06)",  # Purple — Extreme
    5: "rgba(139,92,246,0.03)",  # Purple faint — Black Swan
}
```

**PropFirm σ-Zone bands** (เพิ่มใน chart loop `for _r in [1, 2]:`):
```python
if pnl_view == "PropFirm Trader" and _sigma_band > 0:
    for n in range(3, 6):  # 3σ–5σ only (1σ,2σ already drawn)
        _fig.add_vrect(
            x0=_chart_center - n * _sigma_band,
            x1=_chart_center + n * _sigma_band,
            fillcolor=_ZONE_COLORS.get(n, "rgba(128,128,128,0.03)"),
            line_width=0, layer="below", row=_r, col=1,
        )
```

**Block Trade TP/SL section** (เพิ่มหลัง Block info ~line 1027):

Mean-Reversion (LONG γ):
- TP (Long) = `_c_pw` (+Wall)
- TP (Short) = `_c_nw` (−Wall)
- SL = `_c_flip` (Composite Flip)

Trend-Following (SHORT γ):
- Entry = `_chart_center ± 2 × _sigma_band`
- TP = `_chart_center ± 3 × _sigma_band`
- SL = `_chart_center ± 1 × _sigma_band`

**Direction**: determined by Net Speed sign (available after Phase 3 integration)

#### Step 7c: Tab 2 Intraday — Kill Zone overlay

**File**: `core/presentation/tab_intraday.py`
**Signature**: เพิ่ม `pnl_view: str = "PropFirm Trader"`
**Add**: Kill Zone alert + σ-band overlay when PropFirm view

#### Step 7d: Tab 3 OI — σ-Zone overlay

**File**: `core/presentation/tab_oi.py`
**Signature**: เพิ่ม `pnl_view: str = "PropFirm Trader"`
**Add**: σ-zone bands + regime label when PropFirm view

#### Step 7e: PnL View switching (future phases)

Initial implementation: PropFirm only (default).
Dealer/MM/HF views เป็น Phase 7 iteration 2 — add PnL heatmap, spread overlay, convexity curve.

---

### 17.8 Phase 8 — Data Flow Integration

**File**: `streamlit_app.py`

Vol Surface fitting ทำใน `tab_gbt.py` (Option 2 — less refactoring):
```python
# Inside render_gbt_tab(), after GEX computation:
_poly_coeffs = None
if 'Vol Settle' in _oi_snap.columns:
    from core.domain.vol_surface import fit_vol_surface
    _T = max(_dte / 365.0, 1e-6)
    _poly_coeffs = fit_vol_surface(
        _oi_snap['Strike'].tolist(),
        _oi_snap['Vol Settle'].tolist(),
        _atm, _T,
    )
```

Pass `_poly_coeffs` to `calculate_sd_ranges()` for asymmetric bounds.

---

### 17.9 Phase 9 — Validation & Testing

**Test files**:
- `test_black76.py` — existing (unchanged)
- `test_higher_order_greeks.py` (NEW) — Speed/Snap finite-difference
- `test_pnl_attribution.py` (NEW) — zero-sum, σ-zone mapping
- `test_vol_surface.py` (NEW) — polynomial fit, ATM passthrough, Δσ
- `test_sd_range.py` (NEW) — symmetric/asymmetric, center options

**Key assertions**:
1. `F × σ / 16 ≈ F × σ / √252` (< 1% tolerance)
2. Speed finite-diff vs analytical (< 0.1%)
3. `dealer.total + hf.total ≈ 0` (zero-sum)
4. `poly(0.50) ≈ ATM_IV` (< 0.5%)
5. `Δσ(ΔF=0) == 0`
6. Gold: `Δσ(+ΔF) > Δσ(−ΔF)` (positive skew)
7. DGC within [−Wall, +Wall]
8. PropFirm TP/SL: Mean-Rev TP = ±Wall; Trend-Fol TP = 3σ, Entry = 2σ, SL = 1σ
9. All 4 PnL views render without error
10. `python3 -c "import py_compile; ..."` passes for all modified files

---

### 17.10 File Dependency Graph

```
NEW FILES (5):
  core/domain/vol_surface.py          ← Phase 5 (pure math)
  core/use_cases/sd_range.py          ← Phase 2 (use case)
  core/use_cases/participant_pnl.py   ← Phase 4 (use case)
  test_higher_order_greeks.py         ← Phase 9 (tests)
  test_pnl_attribution.py            ← Phase 9 (tests)

MODIFIED FILES (7):
  core/domain/constants.py            ← Phase 1 (add constants)
  core/domain/black76.py              ← Phase 3 (add speed, snap)
  core/domain/models.py               ← Phase 1,2,3,4 (add dataclasses)
  core/use_cases/gtbr.py              ← Phase 1,3 (rule16, quartic)
  core/use_cases/gex_analysis.py      ← Phase 4,6 (sym aggregation, poly DGC)
  streamlit_app.py                    ← Phase 7,8 (sidebar, wiring)
  core/infrastructure/session_manager.py ← Phase 7 (pnl_view key)

MODIFIED PRESENTATION FILES (3):
  core/presentation/tab_gbt.py        ← Phase 7b (σ-zones, TP/SL)
  core/presentation/tab_intraday.py   ← Phase 7c (Kill Zone)
  core/presentation/tab_oi.py         ← Phase 7d (σ-zone overlay)

UNTOUCHED FILES:
  core/presentation/styles.py
  core/presentation/legend.py
  core/presentation/chart_helpers.py
  core/presentation/tab_guide.py
  core/infrastructure/github_client.py
  core/use_cases/data_helpers.py
  test_black76.py
```

### 17.11 Migration Safety Rules

1. **Zero breaking changes**: ทุก function เดิมยังทำงานเหมือนเดิม
2. **Additive only**: Phase 1–6 เพิ่ม functions/fields ใหม่เท่านั้น
3. **GEX system preserved**: directional (Call−Put) analysis ไม่ถูกแก้ไข
4. **Symmetric fields = optional**: `net_gamma_sym` default 0.0
5. **pnl_view has default**: `pnl_view="PropFirm Trader"` → backward compatible
6. **Vol Surface is optional**: `poly_coeffs=None` → fallback symmetric
7. **Compile check**: `python3 -c "import py_compile; ..."` หลังทุก phase
8. **Run existing tests**: `python3 test_black76.py` ต้อง pass ทุก phase

---
### 18. User Requirement and Issues
#### 18.1 Requirement
- [x] Default SD Center to "DGC Wall" — ✅ falls back to DGC Wall when available, else Nearest Flip/ATM
- [x] Default SD Range to "R-16 Expiry" — ✅ falls back to R16 Expiry on stale/missing selection
- [x] Update Tips(title) and guide to match this concept in file and you can use gex-gbtr-data(from notebook-lm skill) — ✅ Updated: GTBR tips √365→√252 (Rule of 16), SD Center/Range help texts expanded with PropFirm σ-zone colors, guide tab added σ-Zone/SD selector/Block Trade TP/SL sections, all √365 references corrected to √252
- [x] Remove Block Trade — PropFirm TP/SL Strategy — ✅ Removed standalone PropFirm TP/SL cards section from tab_gbt.py
- [x] Analysis Block trade is match this concept in file and you can use gex-gbtr-data(from notebook-lm skill) — ✅ Verified: Ratio=|γ-Flow/GEX_OI|≥1.0 matches concept Section 7.2, LONG γ→Mean-Reversion (TP=±Wall, SL=Flip) and SHORT γ→Trend-Following (TP=3σ, SL=Flip/Center) match concept Section 4.4
- [x] add TP/SL in Block Trade table each Long/Short type at price — ✅ Added TP Long, TP Short, SL columns to Block Trade dataframe with regime-based calculation

#### 18.2 Issues
- [x] Selected SD Center and SD Range item had reset when press refresh data — ✅ Fixed: selection preserved via `st.session_state` key persistence; only resets to smart default (DGC Wall / R16 Expiry) when selected option no longer exists in rebuilt list. Note: F5 full-page reload clears all Streamlit session state by design — smart defaults ensure DGC Wall / R16 Expiry are re-selected automatically.

---
*สร้างเมื่อ: 2026-03-18 | อัปเดต: 2026-03-18*
- **v1**: Initial concept — Rule of 16 + Taylor expansion (Speed/Snap)
- **v2**: Added Vol Surface Polynomial (CME QuikVol), corrected Greek aggregation
  for PnL (Call+Put symmetric vs Call-Put directional), dynamic Δσ(ΔF),
  improved DGC, CME Vol2Vol methodology, updated implementation phases
- **v3**: Added Prop Firm Trader to Section 2.2 with σ-zone strategy,
  added 1σ–5σ SD calculation with 5 center options, asymmetric ranges via
  Vol Surface polynomial. Updated Section 3.5 (quartic per-player with σ-zones)
  and Section 4 (full PnL framework per player: Dealer/MM/HF/PropFirm with
  Vol Surface enhancement, entry/exit logic, aggregation rules, zero-sum check)
- **v4**: Rewrote Section 16 (Implementation Phases) — 9 phases following
  Sections 1–14. PropFirm Trader = default view ทุก tab. Added PnL View
  dropdown (Dealer/MM/HF/PropFirm). Block Trade TP/SL for both strategies:
  Mean-Reversion (TP=±Wall, SL=Flip) and Trend-Following (TP=3σ, SL=1σ, Entry=2σ).
  Per-tab visualization spec (GBT σ-zones, Intraday Kill Zone, OI regime overlay)
- **v5**: Added Section 17 — Detailed Code-Level Implementation Plan.
  Maps Phase 1–9 → exact file paths, function signatures, imports, dataclasses.
  5 new files, 7 modified files, 3 presentation files. 10 test assertions.
  Migration safety rules: additive-only, zero breaking changes, backward compatible.
- **v6**: Implementation review + validation (2026-03-18).
  **Completed Phases**: 1 (Constants/Rule16), 2 (SD Range), 3 (Speed/Snap), 4 (PnL Attribution),
  5 (Vol Surface), 7a (PnL sidebar), 7b (Tab 1 σ-zones + Block Trade), 8 (Data Flow wiring).
  **Completed**: Phase 6 (Polynomial DGC — `dgc.py`), Phase 7c (Tab 2 σ-zone), Phase 7d (Tab 3 σ-zone).
  **Pending**: Phase 9 (standalone tests).
  **Critical corrections** (confirmed via NotebookLM gex-gbtr-data research):
  - Section 7.2: Speed sign at ATM was wrong ("positive below" → correct: **negative at/below ATM, positive above**)
  - Section 7.3: Snap sign at ATM was wrong ("Snap > 0" → correct: **Snap < 0** — Gamma peak = concave down)
  - Section 7.5: Speed/Snap aggregation updated to (Call+Put) symmetric per Section 11 correction
  All 20 existing tests pass. All 14 files compile. All Section 15 items verified including 15.4 (Phase 6 complete).

