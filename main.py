import streamlit as st
import json
import random

# CẤU HÌNH
st.set_page_config(page_title="AI BACCARAT VIP", page_icon="🎰", layout="centered")
st.markdown("""<style>.stApp {background-color: #000; color: #fff;} .box {border: 2px solid #d4af37; padding: 20px; border-radius: 10px; text-align: center; background: #222; margin-bottom: 20px;} .big {font-size: 40px; font-weight: bold;} .red {color: #ff4b4b;} .blue {color: #2e86de;}</style>""", unsafe_allow_html=True)

# LOGIC
if 'h' not in st.session_state: st.session_state.h = []
if 'd' not in st.session_state:
    st.session_state.d = {}
    pop = ['B']*46+['P']*45+['T']*9
    s = "".join(random.choices(pop, k=2000))
    cl = [x for x in s if x!='T']
    for i in range(len(cl)-5):
        p="".join(cl[i:i+5]); o=cl[i+5]
        if p not in st.session_state.d: st.session_state.d[p]={'B':0,'P':0}
        st.session_state.d[p][o]+=1

def get_pred():
    cl = [x for x in st.session_state.h if x!='T']
    if len(cl)<5: return "WAIT", "", "Đang soi..."
    s = "".join(cl); pat = "".join(cl[-5:])
    
    # Kèo Bệt
    if s.endswith("BBBB"): return "BANKER", "🔴", "Bệt Đỏ VIP"
    if s.endswith("PPPP"): return "PLAYER", "🔵", "Bệt Xanh VIP"
    if s.endswith("BPBP"): return "BANKER", "🔴", "Cầu 1-1"
    if s.endswith("PBPB"): return "PLAYER", "🔵", "Cầu 1-1"
    
    # Kèo AI
    d = st.session_state.d.get(pat)
    if d:
        tot = d['B']+d['P']
        if tot>0:
            r = d['B']/tot
            if r>=0.6: return "BANKER", "🔴", f"AI ({int(r*100)}%)"
            if r<=0.4: return "PLAYER", "🔵", f"AI ({int((1-r)*100)}%)"
    return cl[-1], "⚪", "Theo Đuôi"

# GIAO DIỆN
st.title("🎰 AI BACCARAT MOBILE")
p, i, r = get_pred()

if p!="WAIT":
    c = "red" if p=="BANKER" else "blue"
    st.markdown(f'<div class="box"><h3>AI CHỐT KÈO</h3><div class="big {c}">{p} {i}</div><div>💡 {r}</div></div>', unsafe_allow_html=True)
else: st.info("Nhập cầu để AI chạy...")

c1,c2,c3 = st.columns(3)
if c1.button("🔴 BANKER", use_container_width=True): st.session_state.h.append('B'); st.rerun()
if c2.button("🔵 PLAYER", use_container_width=True): st.session_state.h.append('P'); st.rerun()
if c3.button("🟢 TIE", use_container_width=True): st.session_state.h.append('T'); st.rerun()

st.text_area("Lịch sử:", value=" ".join(st.session_state.h[-10:]), disabled=True)
if st.button("🔄 Xóa Cầu"): st.session_state.h=[]; st.rerun()
