import streamlit as st
import json
import random

# ==============================================================================
# 🎨 CẤU HÌNH VÀ GIAO DIỆN
# ==============================================================================
st.set_page_config(page_title="AI BACCARAT VIP", page_icon="🎰", layout="centered")
st.markdown("""
<style>
    .stApp {background-color: #000000; color: #fff;}
    .box {border: 2px solid #d4af37; padding: 20px; border-radius: 10px; text-align: center; background: #1a1a1a; margin-bottom: 20px;}
    .big {font-size: 40px; font-weight: bold;}
    .red {color: #ff4b4b;} .blue {color: #2e86de;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🧠 LOGIC AI VVIP (FUZZY & BẺ CẦU)
# ==============================================================================
PATTERN_LENGTH = 5

# Khởi tạo bộ nhớ (Chỉ chạy 1 lần)
if 'h' not in st.session_state: st.session_state.h = []
if 'd' not in st.session_state:
    st.session_state.d = {}
    # Giả lập 2000 ván để học mẫu cầu ngay từ đầu
    pop = ['B']*46 + ['P']*45 + ['T']*9
    sim = "".join(random.choices(pop, k=2000))
    cl = [x for x in sim if x != 'T']
    for i in range(len(cl)-PATTERN_LENGTH):
        p="".join(cl[i:i+PATTERN_LENGTH]); o=cl[i+PATTERN_LENGTH]
        if p not in st.session_state.d: st.session_state.d[p]={'B':0,'P':0}
        st.session_state.d[p][o]+=1

def calculate_hamming_distance(s1, s2):
    if len(s1) != len(s2): return float('inf')
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def predict_ai():
    clean = [x for x in st.session_state.h if x != 'T']
    s = "".join(clean)
    
    # 1. KIỂM TRA GÃY CẦU CỨNG (Hard Break Rules)
    if s.endswith("BBBBBB"): return "PLAYER", "🔵", "Bẻ Bệt Đỏ (6)", 85
    if s.endswith("PPPPPP"): return "BANKER", "🔴", "Bẻ Bệt Xanh (6)", 85
    
    if len(clean) < PATTERN_LENGTH: return "WAIT", "", "Đang chờ cầu...", 0
    current_pattern = "".join(clean[-PATTERN_LENGTH:])
    
    learned = st.session_state.d
    best_pred = ""; conf = 0; method = ""

    # 2. TRA CỨU CHÍNH XÁC & MẪU TƯƠNG TỰ (AI Logic)
    if current_pattern in learned:
        data = learned[current_pattern]; total = data['B']+data['P']
        if total > 0:
            pb = data['B']/total
            if pb >= 0.6: best_pred="BANKER"; conf=int(pb*100); method="AI Kinh Nghiệm"
            elif pb <= 0.4: best_pred="PLAYER"; conf=int((1-pb)*100); method="AI Kinh Nghiệm"

    if not best_pred:
        fuzzy_B = 0; fuzzy_P = 0; total_fuzzy = 0
        for pat, data in learned.items():
            if pat and len(pat) == PATTERN_LENGTH and calculate_hamming_distance(current_pattern, pat) <= 1: 
                fuzzy_B += data['B']; fuzzy_P += data['P']
        total_fuzzy = fuzzy_B + fuzzy_P
        if total_fuzzy > 5:
            pb = fuzzy_B / total_fuzzy
            if pb >= 0.55: best_pred="BANKER"; conf=int(pb*100); method="Mẫu Tương Tự"
            elif pb <= 0.45: best_pred="PLAYER"; conf=int((1-pb)*100); method="Mẫu Tương Tự"

    # 3. LUẬT CẦU CƠ BẢN (Fallback)
    if not best_pred:
        if s.endswith("BB"): best_pred="BANKER"; method="Theo Bệt"; conf=60
        elif s.endswith("PP"): best_pred="PLAYER"; method="Theo Bệt"; conf=60
        else: best_pred=clean[-1]; method="Theo Đuôi"; conf=50

    icon = "🔴" if best_pred == "BANKER" else "🔵"
    return best_pred, icon, method, conf

# ==============================================================================
# 🖥️ GIAO DIỆN
# ==============================================================================
st.title("🎰 AI BACCARAT MOBILE")
p, i, r, c = predict_ai() # Gọi hàm AI VVIP

if p!="WAIT":
    color = "red" if p=="BANKER" else "blue"
    st.markdown(f'<div class="box"><h3>AI CHỐT KÈO</h3><div class="big {color}">{p} {i}</div><div>📊 Tỉ lệ: {c}%</div><div>💡 {r}</div></div>', unsafe_allow_html=True)
else: st.info("Nhập cầu để AI chạy...")

# NÚT BẤM VÀ CẬP NHẬT LỊCH SỬ
def learn_new_result(winner):
    st.session_state.h.append(winner)
    # Học tập (Tự động cập nhật session state)
    clean = [x for x in st.session_state.h if x != 'T']
    if len(clean) >= PATTERN_LENGTH + 1:
        pattern = "".join(clean[-(PATTERN_LENGTH + 1):-1])
        outcome = clean[-1]
        if pattern not in st.session_state.d: 
            st.session_state.d[pattern] = {'B': 0, 'P': 0}
        st.session_state.d[pattern][outcome] += 1
    st.rerun()

c1,c2,c3 = st.columns(3)
if c1.button("🔴 BANKER", use_container_width=True): learn_new_result('B')
if c2.button("🔵 PLAYER", use_container_width=True): learn_new_result('P')
if c3.button("🟢 TIE", use_container_width=True): learn_new_result('T')

st.text_area("Lịch sử:", value=" ".join(st.session_state.h[-10:]), disabled=True)
if st.button("🔄 Xóa Cầu"): st.session_state.h=[]; st.rerun()
