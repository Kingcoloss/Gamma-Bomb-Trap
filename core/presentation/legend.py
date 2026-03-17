"""
Thai Hover-Tooltip Legend
=========================
Hoverable badge legend with Thai explanations for chart lines.
"""
import streamlit as st


# ── Legend data ──
THAI_LINE_INFO = {
    "ATM": {
        "color": "#888888",
        "title": "เส้น ATM (At-The-Money)",
        "desc": (
            "ATM คือ <b>ราคาซื้อขายปัจจุบันของ Gold Futures</b> (ดึงจาก Header ข้อมูล CME) "
            "ทุก Greek ถูกคำนวณโดยอิงกับราคานี้<br><br>"
            "• ราคาอยู่ <b>เหนือ ATM</b> → ตลาดอยู่ฝั่ง Bullish<br>"
            "• ราคาอยู่ <b>ต่ำกว่า ATM</b> → ตลาดอยู่ฝั่ง Bearish<br><br>"
            "<i>เส้นนี้ไม่ได้มาจากการคำนวณ — อ่านตรงจาก CME data feed</i>"
        ),
    },
    "GEX Flip": {
        "color": "#A855F7",
        "title": "จุด GEX Flip — เปลี่ยนระบอบตลาด",
        "desc": (
            "<b>Gamma Exposure (GEX)</b> คือผลรวม Gamma ของ Dealers คูณ Open Interest ในแต่ละ Strike "
            "คำนวณด้วย <b>Black-76 Model</b> (เหมาะกับ Options on Futures)<br><br>"
            "GEX Flip คือ <b>จุดที่ Cumulative Net GEX เปลี่ยนจากบวกเป็นลบ</b><br><br>"
            "• เหนือ GEX Flip → Dealers <b>Long Gamma</b> → ตลาดมักดีดกลับ (Mean-Revert)<br>"
            "• ต่ำกว่า GEX Flip → Dealers <b>Short Gamma</b> → ตลาดอาจเคลื่อนรุนแรง (Trending)<br><br>"
            "<i>สูตร: Net GEX_K = Γ_B76(F,K,T,σ) × (Call_OI − Put_OI) × F² × 0.01</i>"
        ),
    },
    "+GEX Wall": {
        "color": "#22C55E",
        "title": "กำแพง Gamma บวก (+GEX Wall) — แนวต้านตาม Gamma",
        "desc": (
            "Strike ที่มีค่า <b>Positive Net GEX สูงสุด</b> — เกิดจาก Call Open Interest ที่หนาแน่น<br><br>"
            "เมื่อ Futures เข้าใกล้ระดับนี้ Dealers ต้อง <b>ซื้อ Futures กลับ (Buy to Hedge)</b> "
            "เพื่อ Delta Hedge Call ที่ขายออกไป → แรงซื้อนี้ทำให้ราคามักชะลอหรือดีดกลับ<br><br>"
            "• ใช้เป็น <b>แนวต้านที่อิงจาก Gamma</b> (Gamma Resistance Zone)<br>"
            "• ยิ่ง OI หนามาก แรงต้านยิ่งแกร่ง"
        ),
    },
    "-GEX Wall": {
        "color": "#F43F5E",
        "title": "กำแพง Gamma ลบ (−GEX Wall) — แนวรับตาม Gamma",
        "desc": (
            "Strike ที่มีค่า <b>Negative Net GEX สูงสุด</b> — เกิดจาก Put Open Interest ที่หนาแน่น<br><br>"
            "เมื่อ Futures เข้าใกล้ระดับนี้ Dealers ต้อง <b>ขาย Futures (Sell to Hedge)</b> "
            "เพื่อ Delta Hedge Put ที่ขายออกไป → แรงขายนี้ทำให้ราคามักชะลอหรือดีดขึ้น<br><br>"
            "• ใช้เป็น <b>แนวรับที่อิงจาก Gamma</b> (Gamma Support Zone)<br>"
            "• ถ้าราคาหลุด −GEX Wall แรงขาย Dealer จะเพิ่มขึ้น → Sell-off รุนแรงได้"
        ),
    },
    "γ/θ Expiry": {
        "color": "#FB923C",
        "title": "ช่วง γ/θ Breakeven — ตลอดอายุ DTE ที่เหลือ",
        "desc": (
            "ช่วงราคาที่ <b>กำไรจาก Gamma ตลอด DTE ที่เหลือ = ต้นทุน Theta ทั้งหมด</b><br><br>"
            "คำนวณจาก Black-76 ที่ ATM (r=0):<br>"
            "<b>ΔF = F × σ × √(DTE / 365)</b><br><br>"
            "• ราคาอยู่ <b>ภายในช่วงนี้</b> → Theta กินกำไร Gamma → Long Gamma ขาดทุน<br>"
            "• ราคา <b>หลุดออกนอกช่วง</b> → Gamma ทำกำไรได้คุ้มกว่า Theta → Long Gamma กำไร<br><br>"
            "<i>ยิ่ง DTE น้อย ช่วงนี้ยิ่งแคบ — เพราะ Theta สูงขึ้นมาก ใกล้ Expire</i>"
        ),
    },
    "γ/θ Daily": {
        "color": "#FCD34D",
        "title": "ช่วง γ/θ Breakeven — รายวัน (1 Calendar Day)",
        "desc": (
            "ช่วงราคาที่ <b>กำไรจาก Gamma ต่อวัน = ต้นทุน Theta รายวัน</b><br><br>"
            "คำนวณจาก Black-76 ที่ ATM:<br>"
            "<b>ΔF = F × σ / √365</b><br><br>"
            "• ใช้ประเมินว่า Futures ต้องเคลื่อนไหวขนาดไหน<b>ต่อวัน</b>เพื่อให้ Long Gamma มีกำไร<br>"
            "• ถ้า Realized Move > Daily BE → Long Gamma ได้กำไรสุทธิในวันนั้น<br><br>"
            "<i>ช่วง Daily BE ใหญ่กว่า Expiry BE เสมอ เมื่อ DTE &lt; 1 วัน</i>"
        ),
    },
    "Vanna": {
        "color": "#38BDF8",
        "title": "Vanna — ความสัมพันธ์ระหว่าง Delta กับ IV",
        "desc": (
            "<b>Vanna = ∂Delta / ∂σ = ∂Vega / ∂S</b><br>"
            "วัดว่า <b>Delta เปลี่ยนแค่ไหนเมื่อ IV เปลี่ยน</b> (หรือ Vega เปลี่ยนแค่ไหนเมื่อราคาเปลี่ยน)<br><br>"
            "• <b>Vanna &gt; 0</b> (Call OTM / Put ITM) → IV พุ่ง ทำให้ Delta เพิ่ม → Dealer ต้อง Short Futures เพิ่ม<br>"
            "• <b>Vanna &lt; 0</b> (Call ITM / Put OTM) → IV พุ่ง ทำให้ Delta ลด → Dealer ต้อง Buy Futures กลับ<br><br>"
            "ผลกระทบต่อ Breakeven:<br>"
            "• Net Vanna สูง → ช่วง γ/θ BE <b>เลื่อนไม่สมมาตร</b> (Shift) ตามทิศทาง IV<br>"
            "• ใน PnL Attribution: <b>½ × Vanna × ΔS × ΔI</b><br><br>"
            "<i>สูตร B76: Vanna = −Vega × d2 / (F × σ × √T)  โดยที่ d2 = d1 − σ√T</i>"
        ),
    },
    "Volga": {
        "color": "#E879F9",
        "title": "Volga (Vomma) — ความโค้งของ Vega ต่อ IV",
        "desc": (
            "<b>Volga = ∂²V / ∂σ² = ∂Vega / ∂σ</b><br>"
            "วัดว่า <b>Vega เปลี่ยนแค่ไหนเมื่อ IV เปลี่ยน</b> — เป็น \"Vol of Vol\" sensitivity<br><br>"
            "• <b>Volga &gt; 0 เสมอ</b> สำหรับทุก Options (Convex in Vol)<br>"
            "• ค่า Volga สูงสุดบริเวณ ATM → ยิ่ง IV พุ่ง ค่า Vega ยิ่งขยายตัว<br><br>"
            "ผลกระทบต่อ Breakeven:<br>"
            "• <b>Short Volga + IV Spike</b> → ขาดทุนเพิ่มแบบทวีคูณ (Shadow Vega)<br>"
            "• <b>Long Volga + IV Spike</b> → กำไรจาก Convexity ของ Vega<br>"
            "• Volga <b>ขยาย/หด</b>ช่วง BE แบบสมมาตร ทั้งสองด้าน<br><br>"
            "ใน PnL Attribution: <b>½ × Volga × (ΔI)²</b><br><br>"
            "<i>สูตร B76: Volga = Vega × (d1 × d2) / σ</i>"
        ),
    },
}


# ── Legend CSS ──
_LEGEND_CSS = """
<style>
.vl-legend { display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 14px 0; }
.vl-item {
    position:relative; display:inline-flex; align-items:center; gap:7px;
    padding:5px 11px 5px 9px; border-radius:7px; cursor:help;
    font-size:12px; font-weight:500; white-space:nowrap;
    background:rgba(255,255,255,0.04); border:1.5px solid;
    transition:background 0.15s;
}
.vl-item:hover { background:rgba(255,255,255,0.10); }
.vl-dot  { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.vl-tip  {
    display:none; position:absolute; bottom:118%; left:0;
    width:310px; background:#12122a; color:#dde4ff;
    padding:13px 15px; border-radius:10px; font-size:12px; line-height:1.65;
    border:1px solid rgba(180,180,255,0.18);
    box-shadow:0 8px 28px rgba(0,0,0,0.65); z-index:9999; pointer-events:none;
    white-space:normal;
}
.vl-tip b { color:#ffffffcc; }
.vl-tip i { color:#aaa; font-size:11px; }
.vl-item:hover .vl-tip { display:block; }
</style>
"""


def render_line_legend():
    """Render a compact hoverable legend row with Thai explanations."""
    badges = ""
    for key, info in THAI_LINE_INFO.items():
        c = info["color"]
        badges += (
            f'<div class="vl-item" style="border-color:{c}">'
            f'  <span class="vl-dot" style="background:{c}"></span>'
            f'  <span style="color:{c}">{key}</span>'
            f'  <div class="vl-tip">'
            f'    <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:6px">'
            f'      {info["title"]}'
            f'    </div>'
            f'    {info["desc"]}'
            f'  </div>'
            f'</div>'
        )
    st.markdown(
        f'{_LEGEND_CSS}<div class="vl-legend">{badges}</div>',
        unsafe_allow_html=True,
    )
