import streamlit as st


def render_guide_tab():
    """Render Tab 4 — Thai Guide, Beginner → Expert Financial Engineering.
    8 sections, structured by knowledge level with NotebookLM-sourced content.
    """

    st.markdown("## :material/menu_book: คู่มือ Gamma Bomb Trap")
    st.caption(
        "อ่านค่า Dashboard ตั้งแต่ระดับเริ่มต้นจนถึง Financial Engineering ขั้นสูง  ·  "
        "คลิกแต่ละหัวข้อเพื่อเปิดอ่าน  ·  "
        "ทุกสูตรใช้ Black-76 (r = 0, Options on Futures)"
    )

    # ─────────────────────────────────────────────
    # Section 1 — พื้นฐาน (Beginner)
    # ─────────────────────────────────────────────
    st.markdown("### :material/school: ส่วนที่ 1 — พื้นฐาน สำหรับผู้เริ่มต้น")
    st.caption(
        "📚 Hull, J.C. (2022) *Options, Futures, and Other Derivatives* 11th Ed.  ·  "
        "CME Group (2024) *Gold Futures & Options Contract Specifications*"
    )

    with st.expander("📌 ATM (At-The-Money) คืออะไร?"):
        st.markdown("""
**ระดับเริ่มต้น**

ATM = **ราคาซื้อขายปัจจุบันของ Gold Futures** ที่ดึงมาจาก Header ข้อมูล CME โดยตรง
ไม่ผ่านการคำนวณ — อ่านตรงจาก data feed

คือสภาวะที่ราคาใช้สิทธิ์ (Strike Price) ของออปชันอยู่ใกล้เคียงกับ
ราคาตลาดปัจจุบันของสัญญาฟิวเจอร์สทองคำมากที่สุด

**วิธีอ่าน**
- ราคาอยู่ **เหนือ ATM** → ตลาดมีแนวโน้ม Bullish
- ราคาอยู่ **ต่ำกว่า ATM** → ตลาดมีแนวโน้ม Bearish
- ATM คือจุดอ้างอิงกลางของ Greek ทุกตัวในแดชบอร์ด

**ระดับกลาง**

ATM เป็นจุดที่ออปชันมีค่า **Delta ≈ 0.50** สำหรับ Call และ **−0.50** สำหรับ Put
และเป็นบริเวณที่มีค่า **Gamma และ Vega สูงสุด** — ราคาออปชันจะมีความไวต่อ
การเปลี่ยนแปลงของราคาทองคำและความผันผวนมากที่สุด

ทุก Greek ถูกคำนวณจาก Black-76 โดยใช้ ATM เป็น **F (Futures Price)**
ดังนั้นเมื่อ ATM เปลี่ยน ค่าทุกตัวเปลี่ยนตามทันที

**ระดับสูง**

ในเชิงปริมาณ ค่า Gamma ของสถานะ Straddle จะมีค่าสูงสุดเมื่อ `d₁ = 0`
ซึ่งเกิดขึ้นเมื่อ `F = K` พอดี สำหรับการวิเคราะห์ระดับสถาบัน
มักใช้ ATM Forward Options ที่มีการ Interpolate เพื่อให้ได้ค่า Greeks
ที่แม่นยำที่สุดในการวัดแรงกดดันจากการ Hedge
""")

    with st.expander("📌 DTE (Days to Expiry) คืออะไร?"):
        st.markdown("""
**ระดับเริ่มต้น**

DTE = จำนวนวันที่เหลือก่อน Options หมดอายุและไร้ค่า
ยิ่ง DTE น้อย Options ยิ่งไวต่อราคา

**วิธีอ่าน**
| DTE | พฤติกรรมตลาด |
|-----|-------------|
| > 30 วัน | ตลาดเคลื่อนไหวช้า Theta กินทีละน้อย ช่วง BE กว้าง |
| 7–30 วัน | สมดุล — Gamma และ Theta แข่งกัน |
| < 7 วัน | ตลาดไวมาก Theta เร่งตัว Gamma "ระเบิด" ง่าย |
| 0DTE | Gamma Peak — แม้ราคาขยับเล็กน้อยทำให้เกิดการ Rebalancing รุนแรง |

**ระดับกลาง**

เมื่อ DTE ลดลง (ใกล้หมดอายุ):
- **Vega และ Rho ลดลง** — โอกาสที่ IV/ดอกเบี้ยจะส่งผลน้อยลง
- **Gamma และ Theta เพิ่มขึ้นอย่างรุนแรง** — ราคาออปชันลดเร็วมากตามเวลา (Time Decay)
  และ Delta จะเปลี่ยนทิศทางเร็วมากหากราคาขยับ

ในสูตร Black-76: `T = DTE / 365` (calendar days สำหรับ pricing)
แต่สำหรับ GTBR: `T_basis = 1/252` (trading days สำหรับ daily breakeven — Rule of 16)
เมื่อ T → 0 ค่า Gamma พุ่งสูงมากบริเวณ ATM → **Gamma Squeeze** (Hypersensitive Market)

**ระดับสูง**

สภาวะ **0DTE** จะนำไปสู่ปรากฏการณ์ **Gamma Peak / Gamma Compression**
ตลาดมีความอ่อนไหวสูงเป็นพิเศษ (Hypersensitive) และอาจเกิด
**Samuelson Effect** ที่ความผันผวนของสัญญาฟิวเจอร์สจะพุ่งสูงขึ้นเมื่อใกล้ส่งมอบสินค้าจริง

ผลลัพธ์: ในช่วง 0DTE แม้ราคาขยับเพียงเล็กน้อยผ่าน Kill Zone
→ MM Rebalancing รุนแรงมาก → Move Explosive (Binary Outcome)
""")

    with st.expander("📌 IV — Implied Volatility (Vol Settle) คืออะไร?"):
        st.markdown("""
**ระดับเริ่มต้น**

IV = **ความผันผวนที่ตลาดคาดการณ์** สำหรับราคา Gold Futures ในอนาคต หน่วย % ต่อปี

**วิธีอ่าน**
- **IV สูง** → ตลาดคาดราคาผันผวนมาก → Premium Options แพง → GTBR กว้าง
- **IV ต่ำ** → ตลาดคาดราคานิ่ง → Premium Options ถูก → GTBR แคบ

**ระดับกลาง**

ATM IV เป็นตัวตั้งต้นของ:
- Gamma-Theta Breakeven Range (GTBR): `ΔF = F × σ / √252` (Rule of 16)
- Vanna-Volga Adjusted GTBR
- ค่า `σ` ในทุกสูตร Black-76

**กฎเลข 16**: เทรดเดอร์ใช้ IV ÷ 16 เพื่อหาค่า Daily Expected Move โดยเร็ว
(เพราะ √252 ≈ 16 โดยประมาณ)

**Volatility Smile / Skew**: IV ไม่เท่ากันทุก Strike
- ตลาดทองคำมักพบ **Positive Skew (Call Skew)** เพราะทองเป็น Safe-Haven
- นักลงทุนยอมจ่ายแพงเพื่อซื้อ Call Options ในยามวิกฤต (ไล่ซื้อสินทรัพย์ปลอดภัย)
- ต่างจากตลาดหุ้นที่มี Put Skew (ซื้อประกันขาลง)

**ระดับสูง**

การสร้างเส้นโค้งความผันผวนใช้ **Fourth-order polynomial surface fitting**
เพื่อครอบคลุมทุก Strike

ดัชนี **CVOL ของ CME** คำนวณจาก Simple Variance (ผลรวม OTM Puts + Calls)
ต่างจาก VIX ที่ใช้ Log-variance — CVOL สะท้อน Tail Risk และ
Volatility Risk Premium (VRP) ได้ชัดเจนกว่า
""")

    with st.expander("📌 Call / Put Volume และ Open Interest คืออะไร?"):
        st.markdown("""
**ระดับเริ่มต้น**

| ค่า | ความหมาย | เปรียบกับ |
|-----|---------|---------|
| **Call Volume** | จำนวน Call Options ที่ซื้อขายระหว่างวัน | "พลังงานชั่วคราว" |
| **Put Volume** | จำนวน Put Options ที่ซื้อขายระหว่างวัน | "พลังงานชั่วคราว" |
| **Call OI** | จำนวน Call Options ที่ยังเปิดสถานะอยู่ | "ภาระผูกพันจริง" |
| **Put OI** | จำนวน Put Options ที่ยังเปิดสถานะอยู่ | "ภาระผูกพันจริง" |

**ความแตกต่างสำคัญ**
- **Intraday Volume** = *กิจกรรม* — Reset ทุกวัน ไม่สะสม
- **Open Interest** = *ตำแหน่งที่สะสม* — แสดง Capital Commitment ที่แท้จริง

**ระดับกลาง**

OI ≈ "เชื้อเพลิงสำรอง" (Capital Commitment)
Volume ≈ "พลังงานชั่วคราว" (Market Energy)

Dashboard ใช้ทั้งสองมุมควบคู่:
- Volume → **γ-Flow** (แรงไหลของ Gamma วันนี้)
- OI → **GEX** (Gamma Exposure ของ Dealer ที่สะสม)

การคำนวณ GEX ใช้สูตร `Γ × OI × 100` เพื่อวัดปริมาณสัญญา
ที่ MM ต้องซื้อหรือขายเพื่อรักษาสถานะ Delta Neutral

**ระดับสูง**

การวิเคราะห์แบบ **Composite GEX** ผสมผสาน OI และ Intraday Volume
เพื่อตรวจจับการเปลี่ยนแปลงสถานะระหว่างวัน:
- **Long Buildup**: ราคาขึ้น + Volume สูง + OI เพิ่ม (เงินทุนใหม่ไหลเข้าจริง)
- **Short Covering**: ราคาขึ้น + Volume สูง + OI ลด (คนขายเดิมยอมแพ้ — ขาขึ้นอ่อนแอ)

ในกรณี **0DTE** แรงซื้อขายมหาศาล (Volume) จะสร้างแรงบีบให้เกิด
Gamma Squeeze ได้แม้ OI เมื่อวานจะต่ำ เนื่องจาก MM ต้องปรับพอร์ตทันที
ตามกระแสคำสั่งซื้อขายที่เข้ามาอย่างรวดเร็ว
""")

    # ─────────────────────────────────────────────
    # Section 2 — Gamma & GEX
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### :material/ssid_chart: ส่วนที่ 2 — Gamma & GEX: ระบอบตลาด")
    st.caption(
        "📚 Black, F. (1976) *The Pricing of Commodity Contracts*, J. Financial Economics  ·  "
        "Barbon & Buraschi (2021) *Gamma Fragility*, J. Financial Economics  ·  "
        "Bollen & Whaley (2004) *Does Net Buying Pressure Affect Implied Volatility?*, J. Finance"
    )

    with st.expander("🏦 GEX คืออะไร? — อุปมา Market Maker เป็นบริษัทประกัน"):
        st.markdown("""
**ระดับเริ่มต้น — อุปมา**

Market Maker (MM) เปรียบเสมือน **บริษัทประกันภัย**:
- นักลงทุนซื้อ Options (ซื้อประกัน) → MM เป็นผู้ขายประกัน
- MM ต้องรีบ **ซื้อหรือขาย Futures** เพื่อป้องกันความเสี่ยงที่เปลี่ยนไปตลอดเวลา

**ทำไมต้อง Hedge Gamma?**

Options มีความโค้ง (Convexity) — ค่า Delta เปลี่ยนไปตามราคา (นี่คือ Gamma)
MM จึงต้อง **Rebalance พอร์ตตลอดเวลา** เพื่อให้ Portfolio คงความเป็น Delta Neutral

**ระดับกลาง — สูตร GEX**
```
Net GEX_K = Γ_B76(F,K,T,σ) × (Call_OI − Put_OI) × F² × 0.01
```
- `F² × 0.01` = ปรับเป็น **Dollar Impact** ต่อการเปลี่ยนราคา 1%
  (แปลง Gamma ปกติให้เป็นมูลค่าเงินดอลลาร์ที่ต้อง Hedging)
- เครื่องหมาย + = Dealer Long Gamma (ซื้อเมื่อลง/ขายเมื่อขึ้น → **สะกดความผันผวน**)
- เครื่องหมาย − = Dealer Short Gamma (ขายเมื่อลง/ซื้อเมื่อขึ้น → **เร่งความผันผวน**)

**ระดับสูง — Black-76 (r = 0)**
```
Γ = N′(d1) / (F × σ × √T)
d1 = [ln(F/K) + ½σ²T] / (σ√T)
```
ใช้ r = 0 เพราะ Futures Price F รวม cost-of-carry ไว้แล้ว

ในเชิงสถิติ ความผันผวนจะเพิ่มขึ้นแบบ **ทวีคูณ (Exponentially)** เมื่อค่า GEX
ติดลบมากขึ้น เนื่องจากสภาพคล่องใน Order Book ถูกดูดซับไปจนหมด
กลไก Hedging ของ MM ในโซน Negative GEX จะกลายเป็น **Momentum Trader** โดยปริยาย
""")

    with st.expander("🟣 GEX Flip — จุดเปลี่ยนระบอบตลาด"):
        st.markdown("""
**ระดับเริ่มต้น**

GEX Flip คือ **ราคาที่ตลาดเปลี่ยนพฤติกรรม** ระหว่าง "ดีดกลับ" กับ "วิ่งต่อเนื่อง"
เปรียบเหมือน "จุดเปลี่ยนนิสัย" ของตลาด — หากราคาอยู่เหนือจุดนี้ตลาดจะสงบ
แต่ถ้าต่ำกว่าจุดนี้ตลาดจะเริ่มผันผวนรุนแรง

| ตำแหน่งราคา | สถานะ Dealer | พฤติกรรมตลาด |
|------------|-------------|-------------|
| เหนือ GEX Flip | Long Gamma | **Mean-Revert** — ดีดกลับเข้าหา Flip |
| ต่ำกว่า GEX Flip | Short Gamma | **Trending** — วิ่งรุนแรงในทิศเดิม |

**ระดับกลาง — วิธีคำนวณ**

1. คำนวณ Net GEX ทุก Strike (เฉพาะที่มี OI/Volume > 0)
2. เรียง Strike จากต่ำไปสูง แล้วทำ Cumulative Sum
3. หาจุดที่ Cumulative GEX **ข้ามศูนย์** (เปลี่ยนเครื่องหมาย)
4. ถ้ามีหลายจุด → เลือกจุดที่ **ใกล้ ATM ที่สุด**

Flip Point คือจุดที่สถานะรวมของ Dealer เปลี่ยนจาก Positive GEX
(สะกดความผันผวน / Mean-reverting) เป็น Negative GEX
(เร่งความผันผวน / Trend-following)

**ระดับสูง — กลไก Feedback Loop**

- **Positive GEX Zone**: MM ซื้อเมื่อลง / ขายเมื่อขึ้น → กดความผันผวน (Vol Suppression)
- **Negative GEX Zone**: MM ขายเมื่อลง / ซื้อเมื่อขึ้น → เร่งความผันผวน (Vol Amplification) → Trend รุนแรง

ธรรมเนียมปฏิบัติของสถาบันจะยึดจุดที่ **ใกล้ราคา ATM ที่สุด** เป็นหลัก
เนื่องจากเป็นจุดที่มีความไวสูงสุด (Gamma Peak)
""")

    with st.expander("🟢 +GEX Wall — แนวต้านจาก Gamma (Call Wall)"):
        st.markdown("""
**ระดับเริ่มต้น**

Strike ที่มี **Positive Net GEX สูงสุด** — มักเกิดจาก Call OI/Volume หนาแน่น
เปรียบเสมือน **"เพดาน"** หรือแนวต้านที่สำคัญ เนื่องจากมีคนถือครอง
Call Options จำนวนมากที่ระดับนี้ ทำให้ราคาผ่านไปได้ยาก

**กลไก**
- ราคาเข้าใกล้ +Wall → MM ต้องขาย Futures เพิ่ม → แรงขายสกัดราคา
- ทำหน้าที่เป็น **Gamma Resistance** (แนวต้านจากโครงสร้าง Dealer)

**ระดับกลาง — Gamma Squeeze**

ถ้าราคา **ทะลุ +Wall ขึ้นไป** → MM ที่ Short Call ต้อง **"Panic Buy"** Futures เพื่อ Hedge
→ เกิด **Gamma Squeeze** (ซื้อตาม Momentum รุนแรง) → ราคาพุ่งเป็นเส้นตรง
→ Dealer ที่มีสถานะ Short Call จะต้องรีบไล่ซื้อ Futures คืนอย่างรุนแรง
เพื่อแก้พอร์ตตามค่า Delta ที่พุ่งสูงขึ้นอย่างรวดเร็ว

**+Wall Convergence**: ถ้า OI Wall ≈ Volume Wall (ห่างกัน ≤ 25 จุด) → **high-conviction resistance**

**ระดับสูง**

ที่ระดับ Call Wall มีค่า Call OI หนาแน่นที่สุด เมื่อราคาทะลุ **Up Trigger**
(มักเป็นบริเวณ Delta 25) MM จะเผชิญกับ **Inelastic Demand** —
ความต้องการซื้อที่ไม่อ่อนไหวต่อราคา เนื่องจาก P&L รายวันเริ่มติดลบเกินขอบเขต GTBR
""")

    with st.expander("🔴 −GEX Wall — แนวรับจาก Gamma (Put Wall)"):
        st.markdown("""
**ระดับเริ่มต้น**

Strike ที่มี **Negative Net GEX สูงสุด** — มักเกิดจาก Put OI/Volume หนาแน่น
เปรียบเสมือน **"พื้น"** หรือแนวรับที่เกิดจากปริมาณ Put Options มหาศาล
หากพื้นนี้แตก ราคาจะร่วงลงอย่างรวดเร็วเหมือนตกเหว

**กลไก**
- ราคาเข้าใกล้ −Wall → MM ต้องซื้อ Futures กลับ → แรงซื้อรองรับราคา
- ทำหน้าที่เป็น **Gamma Support** (แนวรับจากโครงสร้าง Dealer)

**ระดับกลาง — Cascading Sell-off**

ถ้าราคา **หลุด −Wall ลงไป** → MM ที่ Short Put ต้อง Short Futures เพิ่มเรื่อย ๆ
→ เกิด **Gamma Cascade** (ขายตาม Momentum) → Sell-off รุนแรงแบบวงจรป้อนกลับ
ยิ่งขาย ราคายิ่งลง → ยิ่งลง MM ก็ยิ่งต้องขายเพิ่ม → วงจรป้อนกลับทางลบ

⚠ **สัญญาณอันตราย**: หลุด −Wall พร้อม IV spike = Vanna จะเร่งแรงขายอีกชั้น

**ระดับสูง**

ในโซน Negative GEX กลไก Hedging ของ MM จะกลายเป็น **Momentum Trader** โดยปริยาย
ความผันผวนจะเพิ่มขึ้นแบบ **ทวีคูณ (Exponentially)** เมื่อค่า GEX ติดลบมากขึ้น
เนื่องจากสภาพคล่องใน Order Book ถูกดูดซับไปจนหมด
""")

    with st.expander("🟣 GEX Peak — จุดโครงสร้างหลัก (เมื่อไม่มี Flip)"):
        st.markdown("""
**ระดับเริ่มต้น**

เมื่อ Cumulative GEX **ไม่ข้ามศูนย์เลย** (ไม่มี Flip) → Dashboard แสดง Peak แทน

- Peak = Strike ที่มี |Net GEX| สูงสุด
- ใช้เป็น **จุดโครงสร้างหลัก** เมื่อตลาดอยู่ในระบอบเดียวกันทั้งหมด

**ระดับกลาง**

หากไม่มี Flip Point ให้ความสำคัญกับ GEX Peak แทน — ระดับนี้จะทำหน้าที่เป็น
**"แม่เหล็ก"** ดึงดูดราคา (Pinning Effect) ในช่วงใกล้หมดอายุสัญญา

| Peak เครื่องหมาย | ความหมาย |
|----------------|---------|
| Peak บวก | ตลาดล้วน Long Gamma → Mean-Revert แรง |
| Peak ลบ | ตลาดล้วน Short Gamma → Trending แรง ระวัง Breakout |

**ระดับสูง**

ในสภาวะ Pure Positive GEX ระดับ GEX Peak คือจุดที่ความผันผวนถูกสะกดไว้ได้ดีที่สุด
และเป็นจุดที่ MM มีกำไรจากค่าเสื่อมเวลา (Theta) สูงสุดเทียบกับความเสี่ยง
ซึ่งมักจะตรงกับระดับ **Max Pain** ที่ทำให้ผู้ซื้อออปชันในตลาดโดยรวมขาดทุนมากที่สุด
→ กลายเป็นศูนย์กลางแรงโน้มถ่วงของราคา (Dealer Gravity Center)
""")

    # ─────────────────────────────────────────────
    # Section 3 — GTBR
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### :material/balance: ส่วนที่ 3 — Gamma-Theta Breakeven Range (GTBR)")
    st.caption(
        "📚 Silic & Poulsen (2021) *Gamma Exposure and the Dynamics of Delta Hedging* — eq.27-28  ·  "
        "Bossu et al. (2005) *Variance Swaps and Gamma Exposure*  ·  "
        "Park & Zhao (2020) *Gamma Scalping Breakeven* — eq.1"
    )

    with st.expander("🟠 GTBR คืออะไร? — เส้นตายของ Dealer"):
        st.markdown("""
**ระดับเริ่มต้น**

GTBR = ช่วงราคาที่ **กำไรจาก Gamma = ต้นทุน Theta** พอดี
เมื่อราคาหลุดออกนอกช่วงนี้ → Market Maker ขาดทุนสุทธิ → เกิด **Inelastic Demand**
(MM ถูกบีบให้ต้องไล่ซื้อ/ขายตาม Momentum ทันที ไม่สามารถรอได้)

**ระดับกลาง — ที่มาสูตร**

GTBR มีรากฐานมาจากสมการ PDE ของ Black-76:
เมื่อทำ Delta-neutral จะเหลือความสัมพันธ์หลัก:
```
Daily P&L = ½Γ(ΔF)² + Θ·Δt
```
ตั้ง P&L = 0 แก้สมการ:
```
ΔF_daily  = F × σ / √252       (Breakeven รายวัน — Rule of 16)
ΔF_expiry = F × σ × √(DTE/252)  (Breakeven ตลอด DTE)
```

**ระดับสูง — สูตรเต็มจาก Dollar Gamma**
```
GTBR = ± √( −θ/252 / (50 × Γ_Dollar) )
โดยที่ Γ_Dollar = 100 × Γ × F²
```
สูตร `F×σ/√252` (Rule of 16) คือ simplified form ที่ได้จากการแทนค่า ATM Black-76 ลงไปจนถึง closed-form
ใช้ **252 วันทำการ** (ไม่ใช่ 365 วันปฏิทิน) เพราะตรงกับ hedging frequency จริงของ Dealer/MM
""")

    with st.expander("🟡 γ/θ Daily Range — Breakeven รายวัน"):
        st.markdown("""
**ระดับเริ่มต้น**

ช่วงราคาที่ **กำไร Gamma ต่อวัน = ต้นทุน Theta รายวัน**

**วิธีอ่าน**
- Realized Move วันนี้ **> Daily BE** → Long Gamma ได้กำไรสุทธิ
- Realized Move **< Daily BE** → Long Gamma ขาดทุนสุทธิ
- ใช้เป็น **เป้าหมายรายวัน** สำหรับ Gamma Scalping

**สูตร**
```
ΔF_daily = F × σ / √252  (Rule of 16)
```

**ระดับกลาง — เปรียบ Daily vs Expiry**

| ค่า | Δt | ใช้เมื่อ |
|-----|-----|--------|
| Daily Range | 1/252 | ตัดสินใจเทรดวันต่อวัน (Rule of 16) |
| Expiry Range | DTE/252 | ประเมินภาพรวม DTE ทั้งหมด |

ยิ่ง DTE ต่ำ → Daily Range แคบลง (เพราะ Theta เร่งตัว แต่ผ่านไปแล้วมาก)

**ระดับสูง**

ราคาเริ่มทะลุ Daily BE → MM เริ่มขาดทุนจาก Gamma (P&L รายวันติดลบ)
→ เข้าสู่ **2σ Hedging Pressure Zone** — MM ต้องเริ่ม Rebalance เชิงรุก
→ ถ้าทะลุต่อไปถึง 3σ → **Inelastic Demand / Panic Hedge** เริ่มต้น
""")

    with st.expander("🟠 γ/θ Expiry Range — Breakeven ตลอด DTE ที่เหลือ"):
        st.markdown("""
**ระดับเริ่มต้น**

ช่วงราคาที่ **กำไร Gamma ตลอดอายุ Options = ต้นทุน Theta ทั้งหมด**

**วิธีอ่าน**
- ราคาอยู่ **ภายใน** Expiry Range → Long Gamma ขาดทุนสะสม (Theta กิน)
- ราคา **หลุดออกนอก** Expiry Range → Long Gamma กำไร

**สูตร**
```
ΔF_expiry = F × σ × √(DTE/252)
```

**ระดับสูง — การใช้งานระดับสถาบัน**

ใช้ประเมินว่า Options จะ Expire ITM หรือไม่ จากมุมมอง Gamma-Theta balance
ผู้ที่ Short Gamma จะ Hedge รุนแรงขึ้นเมื่อราคาเข้าใกล้ขอบ Expiry Range
""")

    # ─────────────────────────────────────────────
    # Section 4 — Vanna & Volga
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### :material/auto_graph: ส่วนที่ 4 — Vanna & Volga: Second-Order Greeks")
    st.caption(
        "📚 Carr & Wu (2020) *Static Hedging of Standard Options*, J. Financial Econometrics — Appendix A1  ·  "
        "Castagna & Mercurio (2007) *The Vanna-Volga Method for Implied Volatilities*, Risk Magazine  ·  "
        "Taleb, N.N. (1997) *Dynamic Hedging* Ch.9-10, Wiley"
    )

    with st.expander("🔵 Net Vanna — Shadow Delta: ผลกระทบที่ซ่อนอยู่เมื่อ IV เปลี่ยน"):
        st.markdown("""
**ระดับเริ่มต้น**

Vanna = **Delta เปลี่ยนแค่ไหนเมื่อ IV เปลี่ยน**
หรืออีกมุม: **Vega เปลี่ยนแค่ไหนเมื่อราคา Futures เปลี่ยน**

เปรียบเหมือน "เงา" ที่ซ่อนอยู่ใต้ Delta — ในวันปกติไม่เห็น แต่เมื่อ IV พุ่ง มันปรากฏขึ้นมา
Vanna ทำให้กรอบจุดคุ้มทุน (Breakeven) ขยับแบบ **Asymmetric (ไม่สมมาตร)**

**วิธีอ่าน**
| Net Vanna | IV เพิ่มขึ้น | ผลต่อ GTBR |
|-----------|------------|----------|
| > 0 (Bullish Shift) | Dealers ต้อง Short Futures เพิ่ม | BE เลื่อนลง |
| < 0 (Bearish Shift) | Dealers ต้อง Buy Futures กลับ | BE เลื่อนขึ้น |

**ระดับกลาง — การคำนวณ**
```
Net Vanna = Σ [ Vanna(F,K,T,σ) × (Call_qty − Put_qty) ]
```
ใช้ (Call − Put) เพราะ Vanna มี **ทิศทาง** — Call OTM มี Vanna > 0, Put OTM มี Vanna < 0

**Gold-Specific**: ทองคำมีลักษณะ **Positive Spot-Vol Correlation**
(ราคาขึ้น = IV พุ่ง เพราะคนแห่ซื้อสินทรัพย์ปลอดภัย)
→ Vanna ในทองคำทำงานสลับด้านกับหุ้น โดยจะบีบให้ Dealer ต้องไล่ซื้อ Futures ตาม
เมื่อราคาทองเป็นขาขึ้นรุนแรง (**Upside Gamma Squeeze**)

**ระดับสูง — สูตร Black-76**
```
Vanna = −N′(d1) × d2 / σ
d2 = d1 − σ√T
```

**PnL Attribution (Carr & Wu 2020)**
```
Vanna PnL = Vanna × ΔF × ΔIV
```
⚠ ไม่มีสัมประสิทธิ์ ½ — เป็น cross-derivative (สำคัญ: อย่าหารด้วย 2)

**ตัวอย่างสถานการณ์ Gold Crisis**

🔻 *ราคาทองร่วง + IV พุ่ง + Net Vanna สูง*:
```
Vanna × (−ΔF) × (+ΔIV) = ขาดทุนเพิ่มจาก Vanna
```
→ Dealer ต้อง Short Futures เพิ่มกว่าที่ Gamma บอก → **Crash รุนแรงขึ้น**
นี่คือ "Shadow Delta" — ความเสี่ยงที่ซ่อนอยู่ใต้ผิวน้ำ

ในตลาดทองคำ ความสัมพันธ์เชิงบวกนี้ส่งผลให้ Vanna ผลักให้ DGC ขยับขึ้นตามราคาที่เพิ่มขึ้น
ทำให้จุด Peak Profit ของ Dealer ขยับไปในทิศทาง Bullish มากกว่าปกติ
ต่างจากหุ้นที่ Vanna จะกดจุด Breakeven ลงด้านล่างตาม Panic
""")

    with st.expander("🟡 Net Volga (Vomma) — Shadow Vega: ตัวขยายความเสี่ยง"):
        st.markdown("""
**ระดับเริ่มต้น**

Volga = **Vega เปลี่ยนแค่ไหนเมื่อ IV เปลี่ยน** = "Vol of Vol" sensitivity

คือ "ความผันผวนของความผันผวน" — มันบอกว่า **ความกลัวไม่ได้เพิ่มขึ้นเป็นเส้นตรง
แต่ระเบิดได้เหมือนดอกไม้ไฟ** หาก Volga สูง ความเสียหายจากการขายออปชัน
จะเพิ่มขึ้นแบบทวีคูณเมื่อตลาดเริ่มตกใจ

**วิธีอ่าน**
| Net Volga | ผลต่อ GTBR |
|-----------|-----------|
| > 0 | ช่วง BE **กว้างขึ้น** ทั้งสองด้านสมมาตร |
| < 0 | ช่วง BE **แคบลง** |

Volga > 0 สำหรับ OTM Options (d1·d2 > 0)  ·  Volga ≈ 0 ที่ ATM (Vega อยู่ที่ Peak แล้ว ความชันเกือบศูนย์)  ·  ผลรวม Net Volga ของพอร์ตมักเป็นบวกเพราะ OTM Wings ครอบงำ

**ระดับกลาง — การคำนวณ**
```
Net Volga = Σ [ Volga(F,K,T,σ) × (Call_qty + Put_qty) ]
```
ใช้ (Call + Put) เพราะ Volga เป็น **symmetric** — ทั้ง Call และ Put ขยาย BE เท่ากัน
ไม่ว่าจะเป็น Call หรือ Put ต่างก็มีค่า Vega เป็นบวก (ราคาแพงขึ้นทั้งคู่เมื่อ IV พุ่ง)

**ระดับสูง — สูตร Black-76**
```
Volga = Vega × (d1 × d2) / σ
Vega  = F × N′(d1) × √T
```

**PnL Attribution (Carr & Wu 2020)**
```
Volga PnL = ½ × Volga × (ΔIV)²
```
สัมประสิทธิ์ ½ เพราะเป็น pure second-order term ของตัวแปรเดียว (IV)  ·  (ΔIV)² เสมอบวก

Volga จะต่ำที่สุดที่จุด ATM และจะพุ่งสูงขึ้นอย่างมากใน OTM
ซึ่งเป็นจุดที่อันตรายที่สุดสำหรับ MM ที่มีสถานะ Short Gamma / Short Vega

**Shadow Vega — สถานการณ์อันตรายสูงสุด**

🔻 *Short Vega + High Volga + IV Spike*:
```
Volga PnL = ½ × (+Volga) × (+ΔIV)² = ขาดทุนเพิ่มแบบทวีคูณ
```
Volga ทำให้ Loss เร่งตัวแบบ non-linear ซึ่งไม่เห็นจาก Vega อย่างเดียว
นี่คือสาเหตุที่ Hedge Fund ใหญ่ล้มแบบฉับพลัน (ดูตัวอย่าง 2018 Vol Spike)

**Regime Change Signal**

การพุ่งขึ้นของ Volga คือสัญญาณเตือนว่าตลาดกำลังเข้าสู่ **สภาวะวิกฤต**
เมื่อ Volga สูง Correlation ของสินทรัพย์ทุกชนิดจะวิ่งเข้าหา 1 (Diversification หายไป)
""")

    with st.expander("🔷 ΔIV Proxy — ค่าประมาณการเปลี่ยนแปลง IV (พร้อม Cap)"):
        st.markdown("""
**ระดับเริ่มต้น**

ΔIV Proxy = **ประมาณว่า IV จะเปลี่ยนเท่าไหร่** ใช้เป็น input สำหรับ Vanna-Volga GTBR
หรือพูดง่าย ๆ คือ "ตอนนี้คนในตลาดกลัวมากกว่าเมื่อเช้าแค่ไหน"
โดยเทียบค่า IV ปัจจุบันกับค่า IV ตอนปิดตลาดวันก่อน

**วิธีคำนวณ**
```
ΔIV = IV_Intraday − IV_OI
```
- IV Intraday = ATM IV จากข้อมูล Volume ล่าสุด (ราคาที่เทรดอยู่ตอนนี้)
- IV OI = ATM IV จากข้อมูล OI (ปิดวันก่อน)

**วิธีอ่าน**
| ΔIV | ความหมาย |
|-----|---------|
| > 0 | IV กำลังเพิ่ม (ตลาดกังวลมากขึ้น) |
| < 0 | IV กำลังลด (ตลาดสงบลง) |
| ≈ 0 | IV คงที่ → Vanna/Volga ไม่มีผลต่อ BE |

**ระดับกลาง — Cap ที่ ±5%**

Dashboard จะ **จำกัด ΔIV ไม่เกิน ±5% (absolute)** เพื่อป้องกัน
ข้อมูลที่ผิดปกติ (Noise) หรือการกระชากของราคาที่ไม่มีนัยสำคัญทางสถิติ
ในช่วง Vol Regime Jump (เช่น ข่าว Geopolitical กะทันหัน) ΔIV อาจพุ่งสูงมากชั่วคราว
หากถึง Cap จะเห็น **(capped)** ต่อท้ายค่าในแดชบอร์ด

**ระดับสูง — ข้อจำกัด**

ΔIV Proxy เป็นค่า **Static (Point-to-Point)** — คำนวณจากจุดเดียว

สถาบันใช้เครื่องมือที่แม่นยำกว่า:
- **GARCH / EGARCH**: พยากรณ์ Realized Volatility วันถัดไป → ใช้แทน ΔIV ใน V-GTBR
- **CME CVOL**: ใช้ข้อมูลจากทั้ง Volatility Surface (OTM Puts + Calls ทุกตัว)
  สะท้อนภาพรวมความเสี่ยง (Expected Move) ได้แม่นยำกว่า Proxy เพียงอย่างเดียว
""")

    # ─────────────────────────────────────────────
    # Section 5 — Vanna-Volga Adjusted GTBR
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### :material/science: ส่วนที่ 5 — Vanna-Volga Adjusted GTBR (สูตรเต็ม Carr & Wu)")
    st.caption(
        "📚 Carr & Wu (2020) *Static Hedging of Standard Options* — Appendix A1, full Taylor expansion  ·  "
        "Castagna & Mercurio (2007) *The Vanna-Volga Method* — quadratic adjustment  ·  "
        "Alexander (2008) *Market Risk Analysis Vol.III* Ch.6, Wiley"
    )

    with st.expander("🔹 V-GTBR — ช่วง BE ที่ปรับด้วย Vanna + Volga"):
        st.markdown("""
**ระดับเริ่มต้น**

V-GTBR = Gamma-Theta Breakeven Range ที่ **รวมผลกระทบจาก IV เปลี่ยนแปลงด้วย**
สมจริงกว่า GTBR มาตรฐานที่สมมติว่า IV คงที่

โมเดลของ Carr & Wu (2020) ระบุว่าในสภาวะวิกฤต ค่า IV จะไม่คงที่
ทำให้เกิดความเสี่ยงจาก **Greeks เงา (Shadow Greeks)**

**วิธีอ่าน**
| ค่า | ความหมาย |
|-----|---------|
| **Shift ≠ 0** | ช่วง BE เลื่อนไม่สมมาตร → ผลจาก Vanna |
| V-GTBR **กว้างกว่า** GTBR | Volga ขยาย BE → ความเสี่ยงสูงกว่าที่ Gamma-Theta บอก |
| V-GTBR **แคบกว่า** GTBR | Volga หด BE |
| Shift **ลง** | Vanna ดัน Dealer ต้อง Hedge ฝั่งขาลงเพิ่ม |

**ระดับกลาง — ผลแต่ละ Term**

- **Vanna (Directional Shift)**: ในตลาดทองคำที่มี Positive Spot-Vol Correlation
  (ราคาขึ้น IV พุ่ง) Vanna จะดึงให้กรอบ GTBR ฝั่งขาขึ้นบีบแคบลงอย่าง **ไม่สมมาตร**
  ทำให้เกิด Gamma Squeeze ได้ง่ายขึ้นแม้ราคาขยับเพียงนิดเดียว
- **Volga (Symmetric Width)**: หาก Volga สูง จะทำให้กรอบ GTBR
  ขยายกว้างขึ้นหรือแคบลง **พร้อมกันทั้งสองข้าง** อย่างสมมาตร
  เพื่อชดเชยต้นทุนของความกลัวที่เพิ่มขึ้นแบบทวีคูณ

**ระดับสูง — Full PnL Attribution (Carr & Wu 2020)**

สมการ PnL ของ delta-hedged portfolio:
```
dPnL = θ·dt + ½Γ(ΔF)² + Vanna·(ΔF)(Δσ) + ½Volga·(Δσ)²
```

ตั้ง PnL = 0 จัดรูปเป็น Quadratic ใน ΔF:
```
a·(ΔF)² + b·(ΔF) + c = 0

a = ½ × Γ_ATM                        (Gamma Risk — ความนูนของราคา)
b = Net_Vanna × Δσ                   (Shadow Delta — ไม่มี ½)
c = θ/365 + ½ × Net_Volga × (Δσ)²   (Time Decay + Vol-of-Vol)
```

แก้ด้วยสูตร Quadratic:
```
ΔF = [−b ± √(b² − 4ac)] / 2a
```

**กรณีพิเศษ**
- Δσ = 0 → b = 0, Volga term = 0 → ลดรูปเป็น GTBR มาตรฐานพอดี
- discriminant < 0 → ไม่มีจุดคุ้มทุน → Dashboard ใช้ GTBR มาตรฐานแทน

**Aggregate Greeks Design (Carr & Wu Consistency)**

Dashboard ใช้ `Net_Gamma` และ `Net_Theta` สะสมทุก Strike (× (Call−Put)) แทน ATM-only
เพื่อให้ทุก Coefficient (a, b, c) อยู่ใน "Portfolio Level" เดียวกัน ตามหลัก Carr & Wu (2020)
→ สมการ Quadratic ภายในสอดคล้องกันทุกพจน์ ไม่ผสม Portfolio-level กับ Point-level

การใช้ Aggregate Greeks ทั้งหมดช่วยให้หา **Dealer Gravity Center (DGC)** หรือจุดที่
พอร์ตสถาบันมีกำไรสูงสุด (Vertex of the parabola) ได้แม่นยำกว่าการดูแค่ราคา ATM ปกติ
""")

    # ─────────────────────────────────────────────
    # Section 5b — Dealer Gravity Center (DGC)
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### :material/hub: ส่วนที่ 5b — Dealer Gravity Center (DGC): จุดศูนย์ถ่วงเชิงพฤติกรรม")
    st.caption(
        "📚 Carr & Wu (2020) *Static Hedging of Standard Options* — quadratic vertex  ·  "
        "GEX Pinning Theory: Bollen & Whaley (2004) · Barbon & Buraschi (2021)  ·  "
        "Max Pain Theory: Augen, J. (2009) *The Volatility Edge in Options Trading*"
    )

    with st.expander("📌 DGC คืออะไร? — จุดที่ Dealer มีแรงจูงใจ Pin ราคาสูงสุด"):
        st.markdown("""
**ระดับเริ่มต้น**

DGC (Dealer Gravity Center) = ราคาที่ Market Maker มีแรงจูงใจ **ตรึงราคาไว้** มากที่สุด
เพื่อให้ Portfolio ของพวกเขาทำกำไรสูงสุดจาก Theta โดยขาดทุน Gamma น้อยที่สุด

เปรียบเหมือน **"โซนที่เจ้ามือแฮปปี้ที่สุด"** — จุดที่เขาเก็บค่าเช่า (Theta)
ได้เต็มเม็ดเต็มหน่วยโดยไม่ต้องเหนื่อยวิ่งไล่ Hedging ตามราคา

**ความแตกต่างจาก Max Pain**

| ค่า | วิธีคำนวณ | ความแม่นยำ |
|-----|---------|----------|
| **Max Pain** | คงที่ — คิดจากมูลค่าพรีเมียมที่ถูกทำลาย (Static OI) | Static (ไม่อัปเดตตาม IV) |
| **DGC** | Dynamic — คำนวณจาก Vanna × ΔIV / Gamma (Vertex ของ P&L) | Real-time (รวม Shadow Greeks) |

DGC ปรับตัวตาม **ความกลัวของตลาด (IV)** แบบ Real-time ในขณะที่ Max Pain ไม่ทำ

**วิธีอ่าน**
- ราคาใกล้ DGC → ตลาดมักนิ่ง / Sideways (Dealer Pinning Effect ทำงาน)
- ราคาทิ้งห่างจาก DGC → Dealer เริ่มล้า → โอกาส Breakout สูงขึ้น
- DGC อยู่เหนือ ATM → Dealer ดึงตลาดขึ้น (Bullish Gravity)
- DGC อยู่ต่ำกว่า ATM → Dealer ดึงตลาดลง (Bearish Gravity)
""")

    with st.expander("🔢 DGC — สูตรและที่มา (Carr & Wu 2020 Quadratic Vertex)"):
        st.markdown("""
**ระดับกลาง — ที่มาสูตร**

จากสมการ Vanna-Volga Adjusted GTBR (Carr & Wu 2020):
```
a·(ΔF)² + b·(ΔF) + c = 0
```

DGC คือจุดยอด (Vertex) ของพาราโบลา P&L — จุดที่แรงบีบจาก Gamma
และ Vanna หักล้างกันจนเหลือความเสี่ยงต่ำที่สุด:
```
ΔF_vertex = −b / (2a) = −(Net_Vanna × ΔIV) / Net_Gamma
```

ดังนั้น:
```
DGC = F + ΔF_vertex = F − (Net_Vanna × ΔIV) / Net_Gamma
```

**DGC Wall Midpoint — จุดสมดุลเชิงโครงสร้าง**

อีกวิธีหนึ่ง:
```
DGC_Wall = (+Wall + −Wall) / 2
```
ระดับนี้แสดงถึง **Structural Equilibrium** — จุดที่แรงซื้อจากการ Hedge Call
และแรงขายจากการ Hedge Put อยู่ในสภาวะสมดุล
หาก DGC ขยับเข้าหา Wall Midpoint → ตลาดมักเข้าสู่ Mean Reversion อย่างรุนแรง

**ระดับสูง — ทำไม Vertex = จุด Pin ที่ดีที่สุด**

พาราโบลา P&L ของ Short-Gamma Dealer มีรูปเป็น **Concave (คว่ำหัว)**
→ Vertex คือจุดสูงสุดของกำไร = จุดที่ Dealer มี **ต้นทุนการ Hedge ต่ำที่สุด**
→ Dealer จึงมีแรงจูงใจสูงสุดที่จะรักษาราคาให้อยู่ที่ Vertex นี้

**ข้อสังเกตสำคัญ**
- ถ้า ΔIV = 0 → DGC = F (ไม่มี Shadow Greek → ตรึงที่ ATM)
- ถ้า Net_Vanna > 0 + ΔIV > 0 (gold: ราคาขึ้น+IV ขึ้น) → DGC < F (Dealer ดึงลงเล็กน้อย)
- ถ้า Net_Vanna < 0 + ΔIV > 0 (equities: ราคาลง+IV ขึ้น) → DGC > F (Dealer ดึงขึ้น)
""")

    with st.expander("📐 SD Center & SD Range — ตัวเลือกบนกราฟ"):
        st.markdown("""
**ระดับเริ่มต้น**

Dashboard มี Dropdown 2 ตัวให้เลือก **จุดศูนย์กลาง** และ **ขนาด σ** ของแถบสีบนกราฟ:

**📐 SD Center — จุดศูนย์กลาง**

| ตัวเลือก | ค่า | คำถามที่ตอบ | เหมาะกับ |
|---------|-----|-----------|---------|
| **Nearest Flip / ATM** | Composite Flip ที่ใกล้ ATM สุด | ตลาดเปลี่ยน Regime ที่ไหน? | Regime Detection |
| **DGC Wall** | (+Wall + −Wall) / 2 | จุดสมดุลโครงสร้าง Hedging | Structural Analysis |
| **DGC V-GTBR** | V-GTBR Midpoint | Dealer มี Profit สูงสุดที่ไหน? | **PropFirm (แนะนำ)** |
| **DGC Polynomial** | Numerical vertex จาก PnL(ΔF) | จุด Pin ที่แท้จริง (รวม Skew) | Expert / Quant |

**📏 SD Range — ขนาด 1σ**

| ตัวเลือก | สูตร | ใช้เมื่อ |
|---------|------|--------|
| **R16 Daily** | F × σ / √252 | ดู Breakeven รายวัน (Rule of 16) |
| **R16 Expiry** | F × σ × √(DTE/252) | ดู Breakeven ตลอด DTE ที่เหลือ |
| **V-GTBR Daily/Expiry** | ครึ่งของ Kill Zone | สะท้อนขีดจำกัดของ Dealer จริง |

**ระดับกลาง — σ-Zone สี (PropFirm Strategy)**

แถบสีบนกราฟแบ่งตาม **ระดับความเจ็บปวดของ Dealer**:

| σ Level | สี | ความหมาย | กลยุทธ์ PropFirm |
|---------|-----|---------|----------------|
| **1σ** (~68%) | 🟢 เขียว | **Safe Zone** — Theta > Gamma Loss | SL / Position Sizing |
| **2σ** (~95%) | 🟡 เหลือง | **Pressure Zone** — Dealer เริ่มเจ็บ | **Entry** (จุดเข้าเทรด) |
| **3σ** (~99.7%) | 🔴 แดง | **Kill Zone** — Inelastic Demand | **TP** (จุดปิดกำไร) |

**ระดับสูง — Gold Asymmetric σ-Zone**

ทองคำมี **Positive Skew** (Call Skew) จาก Vol Surface Polynomial ทำให้:
- σ-Zone ฝั่งบนกว้างกว่าฝั่งล่าง
- Gamma Squeeze ฝั่งขาขึ้นเกิดได้ง่ายกว่า → Kill Zone ฝั่งบนอยู่ไกลกว่า
- PropFirm Long entry มี R:R ดีกว่า Short entry

**การอ่านร่วมกัน**

```
DGC อยู่ใน 1σ ของ Probability Range → ตลาดนิ่ง, Dealer ไม่ต้องทำงานหนัก
DGC ออกนอก 1σ ของ Probability Range → แรงตึงสูง → โอกาส Squeeze / Cascade
```
""")

    # ─────────────────────────────────────────────
    # Section 6 — Composite OI + Volume Analysis
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### :material/compare_arrows: ส่วนที่ 6 — Composite OI + Volume: อ่านสัญญาณสถาบัน")
    st.caption(
        "📚 Barbon & Buraschi (2021) *Gamma Fragility* — OI + Volume composite  ·  "
        "Kolanovic & Krishnamachari (2017) *Big Data and AI Strategies*, J.P. Morgan  ·  "
        "CME Group (2023) *Open Interest as Market Intelligence*"
    )

    with st.expander("📊 Quadrant Analysis — อ่าน OI + Volume แบบมืออาชีพ"):
        st.markdown("""
**ระดับเริ่มต้น**

การอ่านสัญญาณสถาบันต้องแยกแยะ "พลังงานชั่วคราว" (Volume) ออกจาก "ภาระผูกพันจริง" (OI)

**ตาราง Quadrant Analysis**

| สถานการณ์ | ราคา | Volume | OI | ความหมาย |
|----------|------|--------|-----|---------|
| **Long Buildup** | ↑ ขึ้น | สูง | ↑ เพิ่ม | 🟢 กระทิงแข็งแกร่ง: เงินใหม่ไหลเข้าจริง |
| **Short Covering** | ↑ ขึ้น | สูง | ↓ ลด | ⚠ กระทิงอ่อนแอ: แค่ Short ปิดสถานะ (กับดัก) |
| **Short Buildup** | ↓ ลง | สูง | ↑ เพิ่ม | 🔴 หมีแข็งแกร่ง: แรงขายจริงจากสถาบัน |
| **Long Liquidation** | ↓ ลง | สูง | ↓ ลด | ⚠ หมีอ่อนแรง: แค่ Long ทำกำไร (คนซื้อเดิมยอมแพ้) |

**ระดับกลาง — Confluence Signal (High-Confidence)**

สัญญาณที่น่าเชื่อถือที่สุด: **Breakout + Volume Surge + OI เพิ่ม พร้อมกัน**
→ Institutional Smart Money กำลัง Drive Move นั้น

**ระดับสูง — สูตร Composite Score**

Dashboard รวม GEX (OI) และ γ-Flow (Volume) ด้วยสัดส่วน α:
```
Composite_K = (1 − α) × GEX_OI_K + α × γFlow_Vol_K
```
- α = 0 → ดูเฉพาะ OI (ตำแหน่งสะสม)
- α = 0.4 → **แนะนำสำหรับทองคำ** (60% OI + 40% Volume)
- α = 1 → ดูเฉพาะ Volume (กิจกรรมวันนี้)
""")

    with st.expander("🟣 Block Trade Detection + TP/SL — จับสัญญาณสถาบัน"):
        st.markdown("""
**ระดับเริ่มต้น**

Block Trade = การซื้อขาย Options ปริมาณมากในคราวเดียว ที่ **ไม่สมดุลกับ OI ที่มีอยู่**
สัญญาณว่า Institutional Player กำลัง Build หรือ Unwind Position ขนาดใหญ่
เปรียบเหมือนการดักจับ **"รอยเท้าช้าง"** หรือรายการใหญ่ที่แอบซ่อนอยู่

**เกณฑ์ Dashboard**
```
Ratio = |γ-Flow (Vol)| / |GEX (OI)| ≥ 1.0x
```
เมื่อ Intraday GEX Flow ≥ Structural OI GEX ที่ Strike เดียวกัน → แสดงว่ามีการซื้อขายใหม่
ในสัดส่วน 1:1 กับ OI ที่มีอยู่ → สัญญาณ **Opening Block Trade** (Smart Money สร้างฐานใหม่)

**วิธีอ่านคอลัมน์ในตาราง**

| คอลัมน์ | ความหมาย |
|---------|---------|
| **Strike** | ระดับราคาที่ตรวจพบ Block Trade |
| **Call/Put Vol** | ปริมาณ Call/Put ที่ซื้อขายระหว่างวัน |
| **γ-Flow** | Gamma Exposure จาก Volume (พลังงานชั่วคราว) |
| **GEX (OI)** | Gamma Exposure จาก OI (ภาระผูกพันจริง) |
| **Ratio** | สัดส่วน γ-Flow / GEX_OI — ≥ 1.0 = Block Trade |
| **TP Long** | จุดปิดกำไร (Take Profit) สำหรับ Long position |
| **TP Short** | จุดปิดกำไร (Take Profit) สำหรับ Short position |
| **SL** | จุดตัดขาดทุน (Stop Loss) |

**ระดับกลาง — TP/SL ตาม Regime**

Dashboard คำนวณ TP/SL อัตโนมัติตาม GEX Regime:

| Regime | กลยุทธ์ | TP Long | TP Short | SL |
|--------|---------|---------|----------|-----|
| **LONG γ** | Mean-Reversion | +Wall | −Wall | Composite Flip |
| **SHORT γ** | Trend-Following | Upper 3σ | Lower 3σ | Composite Flip / Center |

**LONG γ — Mean-Reversion** (Dealer กดราคากลับ):
- TP = ±Wall เพราะเป็นจุดสมดุลของ Dealer Hedging
- SL = Composite Flip เพราะเป็น Regime boundary — ถ้าหลุด = thesis ผิด
- Entry: Block Trade ปรากฏ → fade direction (สวนทาง)

**SHORT γ — Trend-Following** (Dealer ถูกบีบตาม):
- TP = 3σ boundary เพราะเป็นจุดที่ Dealer forced hedge ถึง climax
- SL = Flip / Center เพราะกลับเข้า safe zone = thesis invalidation
- Entry: ราคาแตะ 2σ + SHORT γ + Block Trade ที่ Kill Zone

**ระดับสูง**

หาก Ratio พุ่งสูงมาก แสดงว่ามี **Opening Block Trade** ปริมาณมหาศาล
ระดับนี้จะกลายเป็น Kill Zone ทันที เพราะเจ้ามือต้องป้องกันราคานี้อย่างถวายหัว

**Position Sizing (Rule of 16)**:
```
Risk_Per_Trade = Account × 1%
Stop_Distance = |Entry − SL|
Lot_Size = Risk_Per_Trade / Stop_Distance
```
""")

    with st.expander("✅ Convergence Analysis — ยืนยันแนวรับ/ต้าน"):
        st.markdown("""
**ระดับเริ่มต้น**

Convergence ตรวจว่า **Wall จาก OI และ Wall จาก Volume อยู่ใกล้กันหรือไม่**

| สถานะ | เกณฑ์ | ความหมาย |
|-------|-------|---------|
| ✅ **Converged** | ห่างกัน ≤ 25 จุด | แนวรับ/ต้านน่าเชื่อถือสูง (High Conviction) |
| ⚠ **Diverged** | ห่างกัน > 25 จุด | แนวรับ/ต้านไม่แน่นอน ตลาดยังไม่ตกลงกัน |

**ระดับกลาง — ตรรกะเบื้องหลัง**

- OI = ตำแหน่งเก่า (สะสมหลายวัน) = ความเห็นระยะยาว
- Volume = กิจกรรมวันนี้ = ความเห็นระยะสั้น

**Converged**: ทั้งตำแหน่งเก่าและกิจกรรมใหม่ชี้ที่เดียวกัน → **สัญญาณที่ตลาดทั้ง Long-term และ Short-term เห็นตรงกัน**

ความหมายเชิงกลยุทธ์:
- หากเกิดที่ **Call Wall**: จะเป็นแนวต้านที่ผ่านยากที่สุด แต่ถ้าผ่านได้จะเกิด Gamma Squeeze ที่รุนแรงที่สุด
- หากเกิดที่ **Put Wall**: จะเป็นแนวรับที่หนาแน่นที่สุด แต่ถ้าหลุดจะเกิดความเสียหายที่รุนแรงมาก

**ระดับสูง — Regime Dashboard**
| Composite Net | ระบอบ | กลยุทธ์ |
|---------------|-------|--------|
| > 0 | **LONG γ — Mean-Revert** | ขายที่ +Wall, ซื้อที่ −Wall หรือ Flip |
| < 0 | **SHORT γ — Trend-Follow** | ตามเทรนด์, หลีกเลี่ยง Counter-trend |
""")

    # ─────────────────────────────────────────────
    # Section 7 — Shadow Greeks & Regime Change
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### :material/emergency: ส่วนที่ 7 — Shadow Greeks & Regime Change (ระดับผู้เชี่ยวชาญ)")
    st.caption(
        "📚 Carr & Wu (2020) *Static Hedging of Standard Options* — Shadow Greeks framework  ·  "
        "Gatheral, J. (2006) *The Volatility Surface* Ch.4, Wiley  ·  "
        "CME Group (2023) *SPAN 2 Margin Methodology* — HVaR dynamic adjustment"
    )

    with st.expander("👁 Shadow Greeks — ความเสี่ยงที่ซ่อนอยู่ใต้ผิวน้ำ"):
        st.markdown("""
**ระดับเริ่มต้น**

Shadow Greeks เปรียบเหมือน **"แรงลับ"** ที่บิดเบือนตำแหน่งของคุณ
เมื่อตลาดตกใจ (IV พุ่ง) แม้ราคาจะอยู่ที่เดิม แต่ความเสี่ยงของคุณ
อาจ "วาร์ป" ไปอยู่ในจุดที่อันตรายกว่าเดิม

**ระดับกลาง — แนวคิด**

Shadow Greeks คือ Greeks ที่ปรับแล้วด้วยผลกระทบของ IV:
```
Adjusted Delta = Normal Delta + [Vanna × ΔIV]
Adjusted Gamma = Normal Gamma + [Volga-related term × ΔIV]
```

ในสภาวะปกติ Adjusted ≈ Normal
แต่เมื่อ IV พุ่ง → Shadow Greeks ปรากฏขึ้นมาและอาจ **ใหญ่กว่า Normal Greeks** หลายเท่า

ใช้สูตร Adjusted Delta เพื่อคำนวณว่า MM ต้อง Re-hedge Futures เพิ่มขึ้นเท่าไหร่
เมื่อความกลัว (IV) เปลี่ยนไป

**ระดับสูง — ทำไมสำคัญ**

Risk System ส่วนใหญ่รายงาน Normal Greeks เท่านั้น
ทำให้ผู้จัดการพอร์ตคิดว่าตัวเองมีความเสี่ยงน้อย แต่ที่จริงแล้ว Shadow Greeks ซ่อนอยู่

ในสภาวะที่ **Spot-Vol Correlation** รุนแรง เช่น ทองคำ
ค่า Vanna จะดึงให้ Delta ขยับแบบ **Bullish อย่างไม่สมมาตร**

**สัญญาณเตือน**
- Net Vanna สูง + ΔIV สูง → **Shadow Delta** กำลังทำงาน
- Net Volga สูง + ΔIV สูง → **Shadow Vega** กำลังขยายการขาดทุน
- ทั้งสองพร้อมกัน + Negative GEX Zone = **ภาวะ Gamma Cascade ขั้นรุนแรง**
""")

    with st.expander("🎯 Kill Zones — จุดที่มีโอกาสสูงสุดเกิด Regime Change"):
        st.markdown("""
**ระดับเริ่มต้น**

Kill Zone คือ **"จุดระเบิด"** ที่เจ้ามือทนไม่ไหว ต้องรีบไล่ซื้อหรือขาย
ตามตลาดเพื่อรักษาชีวิตรอด ทำให้ราคาพุ่งเป็นเส้นตรง

**ระดับกลาง**

Kill Zone เกิดจากจุดราคาที่หลายสัญญาณมา **Confluence พร้อมกัน**:
1. ราคาอยู่ใกล้ GTBR Boundary (ขอบ Breakeven — P&L ของ MM เริ่มติดลบ)
2. Call/Put Wall Converged (OI Wall ≈ Volume Wall ≤ 25 จุด)
3. มี Volume Surge พร้อม OI เพิ่มขึ้น (Long Buildup หรือ Short Buildup)
4. Block Trade ที่ Strike บริเวณนั้น (|γ-Flow / GEX_OI| ≥ 1.0)

**เมื่อเกิด Kill Zone → สองสถานการณ์ที่เป็นไปได้**

| สถานการณ์ | ผลลัพธ์ |
|----------|--------|
| ราคาสะท้อนกลับจาก Kill Zone | **Regime คงเดิม** — Mean-Revert แรง |
| ราคาทะลุผ่าน Kill Zone | **Regime Breakout** — Trend ใหม่เริ่มต้น + MM Forced Hedge |

**ระดับสูง — Hidden Markov Model (HMM)**

Framework สถาบันใช้ HMM เพื่อตรวจจับ Regime Change:
- สังเกต: ราคา, Volume, OI, IV (observable)
- ทำนาย: Market State — Sideways / Breakout / Trend (hidden)
- ใช้ **Viterbi Algorithm** ในการหาลำดับสภาวะที่น่าจะเกิดขึ้นมากที่สุด
  โดยป้อน Log Returns และ Rolling Std Dev เป็น Features
  เพื่อระบุ **Transition Probability** (ความน่าจะเป็นในการเปลี่ยนสถานะ)
- เมื่อ HMM สัญญาณเปลี่ยน State + Kill Zone ตรงกัน = **Highest Confidence Entry**

**0DTE — Hypersensitive Kill Zone**

เมื่อ DTE < 1 วัน Gamma Peak รุนแรงสุด — ปรากฏการณ์ **Gamma Compression**
ทำให้ราคาเคลื่อนไหวแบบ **Binary** (ถ้านิ่งคือนิ่งสนิท ถ้าขยับคือระเบิดรุนแรง)
แม้ราคาขยับเล็กน้อยผ่าน Kill Zone → MM Rebalancing รุนแรงมาก → Move Explosive
""")

    with st.expander("📈 GARCH / CVOL — การพยากรณ์ IV ระดับสถาบัน"):
        st.markdown("""
**ระดับเริ่มต้น**

Dashboard ใช้ ΔIV Proxy แบบ simplified แต่สถาบันใช้เครื่องมือที่ซับซ้อนกว่า:
เป็นโมเดลที่ **"จดจำ" ความบ้าคลั่งในอดีตมาคาดการณ์ความเสี่ยงในอนาคต**

**ระดับกลาง**

**GARCH / EGARCH**
```
σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}
```
- α = ความไวต่อเหตุการณ์ใหม่ (Innovation Response)
- β = ความคงอยู่ของความเสี่ยงเดิม (Volatility Persistence)
- พยากรณ์ Realized Volatility วันถัดไป → ใช้แทน ΔIV ใน V-GTBR

**CME CVOL (CME Group Volatility Index)**
- เหมือน VIX แต่ครอบคลุมหลายสินทรัพย์ (ทองคำ, น้ำมัน, FX)
- แยก Up Vol / Down Vol → เห็น Skew ได้ชัดเจน
- ใช้ติดตาม IV Regime แบบ Real-time

**ระดับสูง**

**EGARCH**: พัฒนาเพื่อแก้ปัญหา **Leverage Effect** — เหตุการณ์ด้านลบ
ส่งผลให้ความผันผวนพุ่งสูงกว่าเหตุการณ์ด้านบวกในขนาดที่เท่ากัน
ใช้ในการตั้งค่า Position Sizing แบบ **Volatility-Adjusted** เพื่อคุม VaR ของพอร์ตให้คงที่

**CVOL vs VIX Methodology**
- CVOL ใช้ **Simple Variance** ถ่วงน้ำหนักด้วย Dollar Vega OI
  เพื่อสะท้อนความเสี่ยงจริงของสถาบัน
- VIX ใช้ **Log-variance** — สะท้อน Tail Risk ต่างกัน

**SPAN 2 Margin (HVaR)**
- CME ใช้ **Filtered Historical Simulation (FHS)** เพื่อ Normalize
  ข้อมูลย้อนหลังให้สอดคล้องกับสภาพตลาดปัจจุบัน (Volatility/Correlation Scaling)
- มีการคิดค่า Add-on สำหรับความไม่แน่นอน (VUM)
  และความเข้มข้นของพอร์ต (Concentration Charge)
- เมื่อ SPAN 2 Margin พุ่ง → MM บางรายถูก Margin Call → **Forced Liquidation**
- นี่คืออีกหนึ่งสาเหตุของ Gamma Cascade ที่ไม่ใช่จาก Hedging ปกติ
""")

    # ─────────────────────────────────────────────
    # Section 8 — Trading Scenarios
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### :material/strategy: ส่วนที่ 8 — สถานการณ์จริง: อ่านสัญญาณแล้วทำอะไร?")
    st.caption(
        "📚 Sinclair, E. (2013) *Volatility Trading* 2nd Ed. Wiley — Ch.7 Gamma Scalping  ·  "
        "Bennett, C. (2014) *Trading Volatility*, Santander — practical scenario analysis  ·  "
        "Hedged Capital (2023) *GEX Dealer Hedging Playbook*"
    )

    with st.expander("📖 สถานการณ์ที่ 1: Long Gamma Regime + Mean-Revert"):
        st.markdown("""
**สภาพตลาด**
- ราคา > GEX Flip
- Composite Net > 0 (LONG γ)
- +Wall และ −Wall Converged
- ΔIV ≈ 0

**การตีความ**

Dealers เป็น Long Gamma → ทุกครั้งที่ราคาขึ้น Dealers ขาย / ราคาลง Dealers ซื้อ
MM จะช่วย **"ซื้อเมื่อราคาลง และขายเมื่อราคาขึ้น"** ทำให้ตลาดนิ่งและอยู่ในกรอบ
ตลาด "ติด" อยู่ในกรอบระหว่าง +Wall และ GEX Flip

**กลยุทธ์ที่เหมาะ**
- ขายที่ +Wall / ซื้อที่ GEX Flip → **Mean-Revert Trade**
- Short Straddle / Iron Condor ถ้า DTE ต่ำ + Walls Converged
- หยุดขาดทุน: ถ้าราคาทะลุ +Wall ขึ้นไป → ออก (อาจเกิด Gamma Squeeze)

**สิ่งที่ต้องระวัง**

ถ้าราคาพุ่งทะลุ +Wall → อาจเกิด Gamma Squeeze → ราคาพุ่งหา Target ถัดไปอย่างรวดเร็ว
""")

    with st.expander("📖 สถานการณ์ที่ 2: Gamma Cascade — Short Gamma + IV Spike"):
        st.markdown("""
**สภาพตลาด**
- ราคา < −Wall (หลุด Put Wall ลงไป)
- Composite Net < 0 (SHORT γ)
- ΔIV พุ่งสูง (> 0)
- Net Vanna สูง

**การตีความ**

Dealers เป็น Short Gamma → ต้อง **"ขายเมื่อราคาลง"** → เร่ง Sell-off
IV พุ่ง → Vanna ทำให้ Delta เปลี่ยน → Dealers ต้อง Hedge เพิ่มอีกชั้น
เกิดเป็นวงจร **Feedback Loop** ที่ทำให้ตลาดถล่มรุนแรง
V-GTBR จะ **Shift ลง + กว้างขึ้น** → ราคามีโอกาสลงไปอีกไกลกว่า GTBR ปกติ

**สิ่งที่ต้องระวัง**
- **Gamma Cascade** = วงจรป้อนกลับเชิงลบ — ขายแล้วทำให้ต้องขายต่อ
- Shadow Vega (Volga) จะเร่งการขาดทุน exponential
- ⚠ **ไม่ควร Catch Bottom** จนกว่า IV เริ่มลด + ราคากลับเหนือ −Wall

**สัญญาณที่ Cascade จะจบ**

IV เริ่มลดลง (ΔIV < 0) + ราคากลับเหนือ −Wall + Block Trade ฝั่ง Call ปรากฏ
""")

    with st.expander("📖 สถานการณ์ที่ 3: Kill Zone + DTE ต่ำ"):
        st.markdown("""
**สภาพตลาด**
- +Wall OI ≈ +Wall Volume (Converged)
- −Wall OI ≈ −Wall Volume (Converged)
- DTE < 7 วัน
- Block Trade ปรากฏที่ Strike ใกล้ Wall

**การตีความ**

Walls ยืนยันแล้ว → แนวรับ/ต้านแข็งแกร่ง
DTE ต่ำ → Gamma สูงมาก → ราคา "ติด" อยู่ในกรอบ Walls แน่น
Block Trade ที่ Wall = สถาบันเชื่อว่า Wall นั้นจะ Hold

**กลยุทธ์ที่เหมาะ**
- **Range Trade**: ซื้อที่ −Wall, ขายที่ +Wall
- **Short Straddle/Strangle** ถ้ามั่นใจ Wall ไม่แตก
- Daily BE แคบมาก → เคลื่อนไหวเล็กน้อยก็ Breakeven ได้

**⚠ ระวังสูงสุด**: ถ้า Wall แตก + DTE ต่ำ → **0DTE Gamma Explosion**
ปรากฏการณ์ Gamma Compression ทำให้ราคาเคลื่อนไหวแบบ **Binary**
(ถ้านิ่งคือนิ่งสนิท ถ้าขยับคือระเบิดรุนแรง) — การเคลื่อนไหวจะรุนแรงมากจนหยุดไม่ได้
""")

    with st.expander("📖 สถานการณ์ที่ 4: Shadow Greek Warning — ΔIV Capped"):
        st.markdown("""
**สภาพตลาด**
- ΔIV Proxy แสดง **(capped)** ในแดชบอร์ด
- Net Vanna สูง (> 0 หรือ < 0 อย่างชัดเจน)
- V-GTBR Shift ≠ 0

**การตีความ**

ΔIV ถูก Cap ที่ ±5% เพราะ IV ระหว่าง Intraday กับ OI ต่างกันมากผิดปกติ
แสดงว่า **IV กำลังเปลี่ยน Regime** (อาจเกิดจากข่าว Geopolitical หรือ Risk-off Event)

Shadow Greeks กำลังทำงาน — เปรียบเหมือน "แรงลับ" ที่บิดเบือนตำแหน่ง:
```
Adjusted Delta ≠ Normal Delta (Vanna × ΔIV ทำงาน)
Adjusted Vega ≠ Normal Vega (Volga × (ΔIV)² ทำงาน)
```

**สิ่งที่ต้องทำ**

1. ดู V-GTBR Shift: เลื่อนไปทางไหน? → นั่นคือทิศที่ Dealer ถูกบีบ
2. ดู Net Vanna เครื่องหมาย: + = Bearish Pressure, − = Bullish Pressure
3. ลดขนาด Position ลง เพราะ Risk ที่แท้จริงสูงกว่าที่โมเดลบอก
4. รอให้ ΔIV กลับมา < 5% ก่อนเพิ่ม Position ใหม่

**ระดับสูง — Position Sizing**

ใน High Vanna + High ΔIV Regime ควรใช้ **Adjusted Greeks** ในการคำนวณ Position Size:
```
Position Size = Target Risk / |Adjusted Delta × F|
```
ไม่ใช่ Normal Delta เพราะจะ Underestimate ความเสี่ยงจริง

ใช้ **Volatility-Adjusted Position Sizing** เพื่อคุม VaR ของพอร์ตให้คงที่
ตามหลัก EGARCH Leverage Effect
""")

    with st.expander("📖 สถานการณ์ที่ 5: DGC ไกลจาก ATM — Dealer Gravity Pull"):
        st.markdown("""
**สภาพตลาด**
- DGC อยู่ห่างจาก ATM มากกว่า 1σ Daily
- ราคาปัจจุบันอยู่ระหว่าง ATM กับ DGC (กำลังเดินไปหา DGC)
- Positive GEX Regime (Composite Net > 0)
- ΔIV ≠ 0 (มี Shadow Greek ทำงาน)

**การตีความ**

Dealer กำลัง "ดึง" ราคาไปทิศทาง DGC เพื่อลด Hedging Cost ของตัวเอง
ราคาถูก **"ดูด"** เข้าหาจุดศูนย์ถ่วง (Vertex of P&L) ทำให้เกิดการ Pinning ที่ Strike นั้น
ราคามักวิ่งช้า ๆ ไปหา DGC ในสภาวะ Positive GEX (Pinning Effect + Gravity Pull)

**วิธีอ่าน DGC vs ATM**
```
DGC > ATM → Dealer มีแรงจูงใจดันตลาดขึ้น → Bullish Bias
DGC < ATM → Dealer มีแรงจูงใจดึงตลาดลง → Bearish Bias
DGC ≈ ATM → ไม่มี Shadow Greek → ตลาดเป็น Pure Gamma ล้วน
```

**กลยุทธ์ที่เหมาะ**
- เทรด **ตามทิศ DGC** เมื่อราคาอยู่ใน 1σ DGC-Range และ GEX Positive
- **Take Profit ที่ DGC** เพราะเมื่อราคาถึง DGC แล้ว Dealer จะหยุด "ดึง"
- ถ้าราคาเด้งออกจาก DGC ให้เตรียมรับ Reversal กลับมาหา Flip / Walls

**สิ่งที่ต้องระวัง**
- DGC เปลี่ยนได้ตลอดเมื่อ ΔIV เปลี่ยน → ติดตาม Real-time เสมอ
- ถ้า DGC ออกนอก 2σ Probability Range → ความตึงเครียดสูงมาก → พร้อม Volatility Spike

**Gold-Specific**

ในตลาดทองคำ Vanna จะผลักให้ DGC ขยับขึ้นตามราคาที่เพิ่มขึ้น
(Positive Spot-Vol Correlation) ทำให้จุด Peak Profit ของ Dealer
ขยับไปในทิศทาง Bullish มากกว่าปกติ ต่างจากหุ้นที่ Vanna จะกด Breakeven ลง
""")

    # Footer
    st.markdown("---")
    st.caption(
        "📐 ข้อมูลทุกค่าคำนวณด้วย **Black-76 Model** (Options on Futures, r = 0)  ·  "
        "GTBR ใช้ **Rule of 16** (√252 trading days)  ·  "
        "แหล่งข้อมูล: CME Group  ·  "
        "อ้างอิงหลัก: Carr & Wu (2020) · Bossu et al. (2005) · Silic & Poulsen (2021) · "
        "Barbon & Buraschi (2021) · CME SPAN 2 Methodology"
    )
