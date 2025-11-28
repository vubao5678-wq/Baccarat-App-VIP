import pyautogui
import time
import os
import cv2        
import numpy as np 
import pytesseract 
import json 
import random
import telebot
import threading

# ==============================================================================
# 🔧 CẤU HÌNH
# ==============================================================================
API_TOKEN = '8313900005:AAE0ZHanHf5MEbQOBeD5QUga9Y6muzEQaLw'
MY_CHAT_ID = '7238866867'
LEARNING_FILE = 'learned_patterns.json' 
PATTERN_LENGTH = 5 

# Ngưỡng màu
NGUONG_DIEM_MAU = 40        
DO_KIEN_NHAN = 5            
NGUONG_TIMER_XANH_LA = 30 
TIMER_STABILITY_THRESHOLD = 2 

try:
    bot = telebot.TeleBot(API_TOKEN)
    bot.send_message(MY_CHAT_ID, "🛠️ ĐÃ FIX LỖI CRASH!\nBot đang khởi động lại...")
    print("✅ Telegram OK.")
except: pass

def gui_telegram(msg):
    try: bot.send_message(MY_CHAT_ID, msg, parse_mode='HTML')
    except: pass

t = threading.Thread(target=bot.infinity_polling); t.daemon = True; t.start()

# ==============================================================================
# 🧠 AI LOGIC
# ==============================================================================
def load_patterns():
    if os.path.exists(LEARNING_FILE):
        try: return json.load(open(LEARNING_FILE))
        except: return {}
    return {}

def save_patterns(patterns):
    with open(LEARNING_FILE, 'w') as f: json.dump(patterns, f, indent=4)

def learn_from_history(history, learned_patterns):
    clean = [r for r in history if r != 'T']
    if len(clean) < PATTERN_LENGTH + 1: return 
    pattern = "".join(clean[-(PATTERN_LENGTH + 1):-1])
    outcome = clean[-1]
    if pattern not in learned_patterns: learned_patterns[pattern] = {'B': 0, 'P': 0}
    if outcome in learned_patterns[pattern]: learned_patterns[pattern][outcome] += 1
    save_patterns(learned_patterns)

def simulate_1000_hands(learned_patterns):
    print("\n🔄 ĐANG GIẢ LẬP DỮ LIỆU...")
    population = ['B'] * 46 + ['P'] * 45 + ['T'] * 9
    simulated_history = "".join(random.choices(population, k=1000))
    clean_history = [r for r in simulated_history if r != 'T']
    
    if len(clean_history) >= PATTERN_LENGTH + 1:
        for i in range(len(clean_history) - PATTERN_LENGTH):
            pattern = "".join(clean_history[i : i + PATTERN_LENGTH])
            outcome = clean_history[i + PATTERN_LENGTH]
            if pattern not in learned_patterns: learned_patterns[pattern] = {'B': 0, 'P': 0}
            if outcome in learned_patterns[pattern]: learned_patterns[pattern][outcome] += 1
    save_patterns(learned_patterns)
    print(f"✅ Đã nạp dữ liệu AI.")
    return learned_patterns

def calculate_hamming_distance(s1, s2):
    if len(s1) != len(s2): return float('inf')
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def predict_ai(history, learned_patterns):
    clean = [r for r in history if r != 'T']
    s = "".join(clean)
    
    if s.endswith("BBBBBB"): return "PLAYER", "🔵", "Bẻ Bệt Đỏ (6)", 80
    if s.endswith("PPPPPP"): return "BANKER", "🔴", "Bẻ Bệt Xanh (6)", 80
    
    if len(clean) < PATTERN_LENGTH: return "WAIT", "", "Đang soi...", 0
    current_pattern = "".join(clean[-PATTERN_LENGTH:])
    
    best_prediction = ""
    confidence = 0
    method = ""

    if current_pattern in learned_patterns:
        data = learned_patterns[current_pattern]
        total = data['B'] + data['P']
        if total > 0:
            prob_B = data['B'] / total
            if prob_B >= 0.6: 
                best_prediction="BANKER"; confidence=int(prob_B*100); method="AI (Kinh nghiệm)"
            elif prob_B <= 0.4:
                best_prediction="PLAYER"; confidence=int((1-prob_B)*100); method="AI (Kinh nghiệm)"

    if not best_prediction:
        fuzzy_B = 0; fuzzy_P = 0; fuzzy_total = 0
        for pat, data in learned_patterns.items():
            if len(pat) == PATTERN_LENGTH and calculate_hamming_distance(current_pattern, pat) <= 1:
                fuzzy_B += data['B']; fuzzy_P += data['P']
        
        fuzzy_total = fuzzy_B + fuzzy_P
        if fuzzy_total > 5:
            prob_B = fuzzy_B / fuzzy_total
            if prob_B >= 0.55:
                best_prediction="BANKER"; confidence=int(prob_B*100); method="AI (Mẫu tương tự)"
            elif prob_B <= 0.45:
                best_prediction="PLAYER"; confidence=int((1-prob_B)*100); method="AI (Mẫu tương tự)"

    if not best_prediction:
        if s.endswith("BB"): best_prediction="BANKER"; method="Theo Bệt"; confidence=60
        elif s.endswith("PP"): best_prediction="PLAYER"; method="Theo Bệt"; confidence=60
        elif s.endswith("BPB"): best_prediction="PLAYER"; method="Cầu 1-1"; confidence=60
        elif s.endswith("PBP"): best_prediction="BANKER"; method="Cầu 1-1"; confidence=60
        else: best_prediction=clean[-1]; method="Theo Đuôi"; confidence=50

    if best_prediction == "BANKER": icon = "🔴"
    elif best_prediction == "PLAYER": icon = "🔵"
    else: icon = ""

    return best_prediction, icon, method, confidence

# ==============================================================================
# 📸 HÀM ĐỌC & SETUP
# ==============================================================================
def doc_so_dong_ho(region):
    try:
        img = cv2.cvtColor(np.array(pyautogui.screenshot(region=region)), cv2.COLOR_RGB2GRAY)
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(img, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        if text.strip().isdigit(): return int(text.strip())
    except: return None
    return None

def kiem_tra_mau_thang(pos_b, pos_p, pos_time):
    rgb_b = pyautogui.screenshot().getpixel(pos_b)
    rgb_p = pyautogui.screenshot().getpixel(pos_p)
    rgb_t = pyautogui.screenshot().getpixel(pos_time)
    
    score_red = rgb_b[0] - rgb_b[1]
    score_blue = rgb_p[2] - rgb_p[0]
    score_timer = rgb_t[1] - rgb_t[0]
    is_timer = (score_timer > NGUONG_TIMER_XANH_LA)

    if score_red > NGUONG_DIEM_MAU: return 'B', is_timer
    if score_blue > NGUONG_DIEM_MAU: return 'P', is_timer
    return 'WAIT', is_timer

def hien_thi_lich_su(history): return " ".join(history[-10:])

def setup():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("🔵 SETUP NHANH")
    input("1. BANKER (Đỏ) -> Enter"); pos_b = pyautogui.position()
    input("2. PLAYER (Xanh) -> Enter"); pos_p = pyautogui.position()
    input("3. ĐỒNG HỒ -> Enter"); pos_time = pyautogui.position()
    input("4. SỐ GIÂY -> Enter"); tx, ty = pyautogui.position(); pos_timer_reg = (tx - 25, ty - 25, 50, 50)
    
    print("-" * 50)
    print("📜 BƯỚC 5: NHẬP CẦU (VD: B B P T)")
    raw = input("👉 Nhập: ").upper()
    init_hist = [c for c in raw if c in ['B', 'P', 'T']]
    
    return pos_b, pos_p, pos_time, pos_timer_reg, init_hist

# ==============================================================================
# 🚀 MAIN LOOP
# ==============================================================================
try:
    learned_patterns = load_patterns()
    learned_patterns = simulate_1000_hands(learned_patterns)
    pos_b, pos_p, pos_time, pos_timer_reg, history = setup()
    
    last_winner = "WAIT"
    count_stable = 0; count_timer = 0 
    da_chot = False; dang_cuoc = False; last_sent = "" 
    
    # ⚠️ FIX LỖI CRASH: Khởi tạo giá trị mặc định là WAIT
    du_doan_hien_tai = "WAIT" 

    gui_telegram(f"🚀 AI ĐÃ VÀO BÀN!\nCầu: {hien_thi_lich_su(history)}")

    while True:
        winner, is_betting = kiem_tra_mau_thang(pos_b, pos_p, pos_time)
        timer_val = doc_so_dong_ho(pos_timer_reg)
        timer_str = str(timer_val) if timer_val else "??"
        
        du_doan, icon, ly_do, percent = predict_ai(history, learned_patterns)
        
        if du_doan != "WAIT":
            msg_dep = (
                f"➖➖➖➖➖➖➖➖\n"
                f"🧠 <b>AI DỰ ĐOÁN ({percent}%)</b>\n"
                f"➖➖➖➖➖➖➖➖\n"
                f"📜 Cầu: {hien_thi_lich_su(history)}\n"
                f"🔎 Lý do: {ly_do}\n"
                f"👉 CHỐT:  <b>{du_doan} {icon}</b>\n"
                f"➖➖➖➖➖➖➖➖"
            )
        else: msg_dep = ""
        
        if is_betting: count_timer += 1
        else: count_timer = 0

        # KHI ĐẾN GIỜ ĐẶT CƯỢC
        if count_timer >= TIMER_STABILITY_THRESHOLD:
            if not dang_cuoc:
                dang_cuoc = True; da_chot = False; count_stable = 0
                du_doan_hien_tai = du_doan # Lưu dự đoán
                
                if msg_dep and du_doan != "WAIT" and du_doan != last_sent:
                    gui_telegram(msg_dep)
                    last_sent = du_doan
                
                print(f"\n[AI CHỐT] {du_doan} ({percent}%)")

        elif not is_betting: dang_cuoc = False

        # KHI CÓ KẾT QUẢ
        if not dang_cuoc and not da_chot:
            if winner == last_winner: count_stable += 1
            else: count_stable = 0
            last_winner = winner

            if count_stable >= DO_KIEN_NHAN and winner != 'WAIT':
                da_chot = True
                history.append(winner)
                learn_from_history(history, learned_patterns)

                # ⚠️ FIX LỖI CRASH: Kiểm tra nếu chưa cược thì không so sánh
                if du_doan_hien_tai == "WAIT":
                    kq_txt = "⚠️ BỎ QUA (Không kịp cược)"
                elif winner == 'T': 
                    kq_txt = "🟢 HÒA"
                else:
                    # So sánh an toàn
                    first_char_dudoan = du_doan_hien_tai[0] if len(du_doan_hien_tai) > 0 else "X"
                    kq_txt = "✅ HÚP!" if winner == first_char_dudoan else "❌ GÃY"
                
                gui_telegram(f"{kq_txt} Về {winner} (Cầu: {hien_thi_lich_su(history)})")
                print(f"--> KQ: {winner}")

        print(f"\rAI: {du_doan} ({percent}%) | Timer: {timer_str} | KQ: {winner}", end="")
        time.sleep(0.2)

except KeyboardInterrupt: print("\nSTOP.")
except Exception as e: print(f"Lỗi: {e}")
