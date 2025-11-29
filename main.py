import pyautogui
import time
import os
import cv2        
import numpy as np 
import pytesseract 
import json 
import random 

# ==============================================================================
# 🔧 CẤU HÌNH & HỌC TẬP 
# ==============================================================================
LEARNING_FILE = 'learned_patterns.json' 
PATTERN_LENGTH = 5 
MIN_OBSERVATIONS = 2 
MIN_FUZZY_OBSERVATIONS = 5 

NGUONG_DIEM_MAU = 45      
DO_KIEN_NHAN = 8      
NGUONG_TIMER_XANH_LA = 30 
TIMER_STABILITY_THRESHOLD = 3 
BOX_WIDTH = 50 
BOX_HEIGHT = 50
TIE_COLOR_THRESHOLD = 50 

try:
    # QUAN TRỌNG: Kiểm tra đường dẫn Tesseract của bạn
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except:
    pass 

# ==============================================================================
# 🧠 PHẦN 1: HỆ THỐNG DỰ ĐOÁN
# ==============================================================================

def load_patterns():
    if os.path.exists(LEARNING_FILE):
        try:
            with open(LEARNING_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Cảnh báo: File {LEARNING_FILE} bị lỗi cấu trúc. Khởi tạo lại dữ liệu.")
            return {}
    return {}

def save_patterns(patterns):
    with open(LEARNING_FILE, 'w') as f:
        json.dump(patterns, f, indent=4)

def learn_from_history(history, learned_patterns):
    clean_history = [r for r in history if r != 'T']
    if len(clean_history) < PATTERN_LENGTH + 1:
        return 

    pattern = "".join(clean_history[-(PATTERN_LENGTH + 1):-1])
    outcome = clean_history[-1]

    if pattern not in learned_patterns:
        learned_patterns[pattern] = {'B': 0, 'P': 0} 

    if outcome in learned_patterns[pattern]:
        learned_patterns[pattern][outcome] += 1
    
    save_patterns(learned_patterns)

def simulate_and_learn_patterns(learned_patterns, num_hands=1000):
    print(f"\n--- BẮT ĐẦU GIẢ LẬP {num_hands} VÁN CHƠI ---")
    
    results = ['B'] * 45 + ['P'] * 45 + ['T'] * 10
    simulated_history = "".join(random.choices(results, k=num_hands))
    clean_history = [r for r in simulated_history if r != 'T']

    hands_learned = 0
    
    if len(clean_history) >= PATTERN_LENGTH + 1:
        for i in range(len(clean_history) - PATTERN_LENGTH):
            pattern = "".join(clean_history[i : i + PATTERN_LENGTH])
            outcome = clean_history[i + PATTERN_LENGTH]
            
            if pattern not in learned_patterns:
                learned_patterns[pattern] = {'B': 0, 'P': 0} 

            if outcome in learned_patterns[pattern]:
                learned_patterns[pattern][outcome] += 1
            
            hands_learned += 1

    save_patterns(learned_patterns)
    print(f"✅ Hoàn tất giả lập. Đã thêm {hands_learned} mẫu cầu mới vào learned_patterns.json")

def calculate_hamming_distance(s1, s2):
    if len(s1) != len(s2):
        return float('inf')
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def check_for_gãy_cầu(history):
    clean = [r for r in history if r != 'T']
    s = "".join(clean)
    n = len(clean)

    if n < 6: return None 
    if s.endswith("BBBBBB"): return "⚠️ CẢNH BÁO GÃY CẦU: BỆT RẤT DÀI (6 TAY). NÊN XEM XÉT BẺ!" 
    if s.endswith("PPPPPP"): return "⚠️ CẢNH BÁO GÃY CẦU: BỆT RẤT DÀI (6 TAY). NÊN XEM XÉT BẺ!" 
    if n < 7: return None
    last_7 = s[-7:] 
    if last_7 == "BPBPBPB" or last_7 == "PBPBPBP": return "⚠️ CẢNH BÁO GÃY CẦU: PING PONG CỰC DÀI (7 TAY). XU HƯỚNG GÃY RẤT RÕ!" 
    if last_7 == "BBPPBB P" or last_7 == "PPBBPPB": return "⚠️ CẢNH BẢO GÃY CẦU: CẦU 2-2 CỰC DÀI (7 TAY). NÊN XEM XÉT BẺ!" 
    return None

def predict_from_learned_patterns(history, learned_patterns):
    break_warning = check_for_gãy_cầu(history)
    if break_warning: return break_warning 

    clean_history = [r for r in history if r != 'T']
    if len(clean_history) < PATTERN_LENGTH:
        return phan_tich_cau_luat_cung(history)

    current_pattern = "".join(clean_history[-PATTERN_LENGTH:])
    last_in_pattern = current_pattern[-1]
    
    PREDICTIVE_CONFIDENCE = 0.55 
    FUZZY_CONFIDENCE = 0.60 

    # 1. TỰ HỌC (Exact Match)
    if current_pattern in learned_patterns:
        data = learned_patterns[current_pattern]
        total = data['B'] + data['P']
        
        if total >= MIN_OBSERVATIONS:
            prob_B = data['B'] / total
            prob_P = data['P'] / total
            
            if prob_B >= PREDICTIVE_CONFIDENCE and prob_B > prob_P: 
                if 'B' != last_in_pattern: return f"🔥 DỰ ĐOÁN GÃY CẦU (Tự học): BANKER ({round(prob_B*100)}%) 🔴"
                else: return f"🧠 Tự học: BANKER ({round(prob_B*100)}%) 🔴"
            elif prob_P >= PREDICTIVE_CONFIDENCE and prob_P > prob_B:
                if 'P' != last_in_pattern: return f"🔥 DỰ ĐOÁN GÃY CẦU (Tự học): PLAYER ({round(prob_P*100)}%) 🔵"
                else: return f"🧠 Tự học: PLAYER ({round(prob_P*100)}%) 🔵"
            else:
                if prob_B > prob_P: return f"👀 Tự học: Xu hướng NHẸ BANKER ({round(prob_B*100)}%) 🔴"
                elif prob_P > prob_B: return f"👀 Tự học: Xu hướng NHẸ PLAYER ({round(prob_P*100)}%) 🔵"
    
    # 2. TỰ HỌC PHỎNG ĐOÁN (Fuzzy Match)
    fuzzy_data = {'B': 0, 'P': 0, 'total': 0}
    for learned_pattern, data in learned_patterns.items():
        if len(learned_pattern) == PATTERN_LENGTH:
            distance = calculate_hamming_distance(current_pattern, learned_pattern)
            if distance == 1:
                fuzzy_data['B'] += data.get('B', 0)
                fuzzy_data['P'] += data.get('P', 0)
                fuzzy_data['total'] += (data.get('B', 0) + data.get('P', 0))

    if fuzzy_data['total'] >= MIN_FUZZY_OBSERVATIONS: 
        prob_B = fuzzy_data['B'] / fuzzy_data['total']
        prob_P = fuzzy_data['P'] / fuzzy_data['total']
        
        if prob_B >= FUZZY_CONFIDENCE and prob_B > prob_P:
            if 'B' != last_in_pattern: return f"✨ DỰ ĐOÁN GÃY CẦU: BANKER ({round(prob_B*100)}% - Mẫu tương tự) 🔴"
            else: return f"✨ Phỏng Đoán: BANKER ({round(prob_B*100)}% - Mẫu tương tự) 🔴"
        elif prob_P >= FUZZY_CONFIDENCE and prob_P > prob_B:
            if 'P' != last_in_pattern: return f"✨ DỰ ĐOÁN GÃY CẦU: PLAYER ({round(prob_P*100)}% - Mẫu tương tự) 🔵"
            else: return f"✨ Phỏng Đoán: PLAYER ({round(prob_P*100)}% - Mẫu tương tự) 🔵"
    
    # 3. LUẬT CỨNG (Fallback)
    return phan_tich_cau_luat_cung(history)

def phan_tich_cau_luat_cung(history):
    clean = [r for r in history if r != 'T']
    s = "".join(clean)
    if len(clean) < 3: return "⏳ Đang thu thập dữ liệu..."
    
    # CÁC LUẬT CƠ BẢN (KHÔNG CÒN LUẬT BẺ SỚM)
    
    # Luật theo Bệt (từ tay thứ 5)
    if s.endswith("BBBB"): return "🔥 Luật Cứng: ĐANG BỆT ĐỎ (4 TAY) -> ĐÁNH TIẾP BANKER 🔴"
    if s.endswith("PPPP"): return "🔥 Luật Cứng: ĐANG BỆT XANH (4 TAY) -> ĐÁNH TIẾP PLAYER 🔵"
    
    if s.endswith("PPBB"): return "🔄 Luật Cứng: ĐANG 2-2 -> ĐÁNH TIẾP PLAYER 🔵"
    if s.endswith("BPBP"): return "⚡ Luật Cứng: ĐANG 1-1 (4 TAY) -> ĐÁNH TIẾP PLAYER 🔵"
    if s.endswith("BBPBB"): return "⚖️ Luật Cứng: CẦU GÁNH 2-1-2 -> ĐÁNH PLAYER 🔵"
    if s.endswith("BBBPBB"): return "⚖️ Luật Cứng: CẦU 3-1-2 -> ĐÁNH PLAYER 🔵"
    if s.endswith("BPPBPP"): return "⚖️ Luật Cứng: CẦU 1-2-3/1-2-3 -> ĐÁNH BANKER 🔴"
    if s.endswith("BBBBPPB"): return "⚖️ Luật Cứng: CẦU 4-2-1 -> ĐÁNH PLAYER 🔵"
    if s.endswith("BPBB"): return "⚖️ Luật Cứng: CẦU NHẢY 1-2 -> ĐÁNH PLAYER 🔵"
    if s.endswith("PBPP"): return "⚖️ Luật Cứng: CẦU NHẢY 1-2 -> ĐÁNH BANKER 🔴"
    if s.endswith("BPBBP"): return "⚖️ Luật Cứng: CẦU GẤP NHẢY -> ĐÁNH BANKER 🔴"
    if s.endswith("PBPBB"): return "⚖️ Luật Cứng: CẦU GẤP NHẢY -> ĐÁNH PLAYER 🔵"
    if s.endswith("BB P"): return "🎯 Luật Phá Bệt 2: NGĂN CHẶN BỆT ĐỎ -> ĐÁNH BANKER 🔴"
    if s.endswith("PP B"): return "🎯 Luật Phá Bệt 2: NGĂN CHẶN BỆT XANH -> ĐÁNH PLAYER 🔵"
    
    return "👀 Quan sát..."

def hien_thi_lich_su(history):
    icons = {'B': '🔴', 'P': '🔵', 'T': '🟢'}
    return " ".join([icons.get(x, '?') for x in history[-15:]])

# ==============================================================================
# 📸 PHẦN 2: MẮT ĐỌC & MAIN LOOP
# ==============================================================================
def doc_so_dong_ho(region):
    try:
        screenshot = pyautogui.screenshot(region=region)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, img_processed = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        config = '--psm 7 -c tessedit_char_whitelist=0123456789'
        text = pytesseract.image_to_string(img_processed, config=config)
        val = text.strip()
        if val.isdigit(): return int(val)
        return None
    except: return None

def kiem_tra_mau_thang(pos_b, pos_p, pos_time):
    rgb_b = pyautogui.screenshot().getpixel(pos_b)
    rgb_p = pyautogui.screenshot().getpixel(pos_p)
    rgb_t = pyautogui.screenshot().getpixel(pos_time)

    score_red = rgb_b[0] - rgb_b[1]
    score_blue = rgb_p[2] - rgb_p[0]
    score_timer = rgb_t[1] - rgb_t[0]
    score_tie_color = rgb_p[1] - rgb_p[0] 

    is_banker_win = (score_red > NGUONG_DIEM_MAU) 
    is_player_win = (score_blue > NGUONG_DIEM_MAU) 
    is_timer_on = (score_timer > NGUONG_TIMER_XANH_LA)
    is_tie_signal = (score_tie_color > TIE_COLOR_THRESHOLD) 

    if is_tie_signal and not is_banker_win and not is_player_win:
        return 'T', is_timer_on, score_red, score_blue, score_timer
    if is_banker_win and not is_player_win: return 'B', is_timer_on, score_red, score_blue, score_timer
    if is_player_win and not is_banker_win: return 'P', is_timer_on, score_red, score_blue, score_timer
    return 'WAIT', is_timer_on, score_red, score_blue, score_timer

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def setup():
    clear_screen()
    print("="*60)
    print("🛠️  CÀI ĐẶT 5 BƯỚC (VỊ TRÍ MÀU & SỐ + LỊCH SỬ CẦU)")
    print("="*60)
    
    input("🔴 BƯỚC 1/5: Chỉ vào NỀN ĐỎ của ô BANKER -> Enter...")
    pos_b = pyautogui.position()
    print("✅ Đã nhớ Banker.")
    
    input("🔵 BƯỚC 2/5: Chỉ vào NỀN XANH của ô PLAYER -> Enter...")
    pos_p = pyautogui.position()
    print("✅ Đã nhớ Player.")
    
    print("-" * 60)
    input("🟢 BƯỚC 3/5: Chỉ vào VÙNG MÀU XANH của ĐỒNG HỒ -> Enter...")
    pos_time = pyautogui.position()
    print("✅ Đã nhớ Đồng Hồ (Màu).")
    
    input("🕒 BƯỚC 4/5: Chỉ vào CHÍNH GIỮA SỐ ĐỒNG HỒ (Số 15, 14...) -> Enter...")
    tx_num, ty_num = pyautogui.position()
    pos_timer_num_reg = (tx_num - BOX_WIDTH//2, ty_num - BOX_HEIGHT//2, BOX_WIDTH, BOX_HEIGHT)
    print("✅ Đã nhớ Vùng Số Đồng Hồ.")
    
    print("-" * 60)
    
    # HỎI VỀ GIẢ LẬP
    simulate = input("🤖 BẠN CÓ MUỐN GIẢ LẬP 1000 VÁN CHƠI NGẪU NHIÊN ĐỂ KHỞI TẠO KIẾN THỨC AI KHÔNG? (Y/N): ").upper()
    if simulate == 'Y':
        simulate_and_learn_patterns(load_patterns(), num_hands=1000)
    
    history_input = input("📜 BƯỚC 5/5: NHẬP MẪU CẦU CÓ SẴN (Ví dụ: B P B B P T, hoặc Enter để bỏ qua): ")
    
    initial_history = []
    if history_input:
        cleaned_input = [char.upper() for char in history_input if char.upper() in ('B', 'P', 'T')]
        initial_history.extend(cleaned_input)
        print(f"✅ Đã nhập lịch sử: {' '.join(initial_history)}")
    else:
        print("✅ Bỏ qua nhập lịch sử ban đầu.")

    print("\n🚀 BOT ĐANG CHẠY... ")
    return pos_b, pos_p, pos_time, pos_timer_num_reg, initial_history

# ==============================================================================
# CHƯƠNG TRÌNH CHÍNH
# ==============================================================================
try:
    learned_patterns = load_patterns()
    pos_b, pos_p, pos_time, pos_timer_num_reg, initial_history = setup()
    
    history = initial_history 
    last_winner = "WAIT"
    count_stable = 0
    count_timer_stable = 0 
    da_chot = False
    dang_cuoc = False
    
    b_wins = history.count('B')
    p_wins = history.count('P')
    other_results = history.count('T')

    # --- KHỞI TẠO TẤT CẢ CÁC BIẾN CHO VÒNG LẶP ---
    score_red, score_blue, score_timer = 0, 0, 0 
    doc_mau_hien_tai = "WAIT" # NEW: Khởi tạo biến này
    
    last_predicted_outcome = 'W' 
    last_final_prediction = "WAIT" 

    while True:
        winner, is_betting_time, score_red, score_blue, score_timer = kiem_tra_mau_thang(pos_b, pos_p, pos_time)
        timer_value = doc_so_dong_ho(pos_timer_num_reg)
        timer_display = str(timer_value) if timer_value is not None else "XX"

        current_prediction = predict_from_learned_patterns(history, learned_patterns)
        
        if is_betting_time:
            count_timer_stable += 1
        else:
            count_timer_stable = 0

        # TRẠNG THÁI 1: ĐANG ĐẶT CƯỢC
        if count_timer_stable >= TIMER_STABILITY_THRESHOLD:
            if not dang_cuoc:
                dang_cuoc = True
                da_chot = False
                count_stable = 0
                
                if 'BANKER' in current_prediction:
                    last_predicted_outcome = 'B'
                elif 'PLAYER' in current_prediction:
                    last_predicted_outcome = 'P'
                else:
                    last_predicted_outcome = 'W' 
                
                last_final_prediction = current_prediction
                
                # NÂNG CẤP GIAO DIỆN: Bảng Dashboard khi Đặt Cược
                os.system('cls' if os.name == 'nt' else 'clear')
                print("="*60)
                print(f"🏆 TỔNG QUAN KẾT QUẢ: Banker {b_wins} - Player {p_wins} - Hòa/Khác {other_results}")
                print("="*60)
                print(f"📊 Cầu hiện tại: {hien_thi_lich_su(history)}")
                print("-" * 60)
                print("⏳ VÁN MỚI BẮT ĐẦU! MỜI ĐẶT CƯỢC...")
                print(f"💡 DỰ ĐOÁN AI: {current_prediction}")
                print("*" * 60 + "\n")
        elif not is_betting_time:
            dang_cuoc = False

        # TRẠNG THÁI 2: ĐỌC KẾT QUẢ
        if not dang_cuoc and not da_chot:
            if winner == last_winner:
                 count_stable += 1
            else:
                 count_stable = 0
            
            last_winner = winner

            if count_stable >= DO_KIEN_NHAN:
                final_winner = winner
                if final_winner == 'WAIT':
                    continue
                
                da_chot = True
                
                win_loss_message = ""
                if last_predicted_outcome != 'W':
                    if final_winner == last_predicted_outcome:
                        win_loss_message = f"🎉 CHÚC MỪNG! ĐÃ TRÚNG CẦU ({last_predicted_outcome}) theo {last_final_prediction.split(':')[0]}!"
                    elif final_winner in ('B', 'P') and final_winner != last_predicted_outcome:
                        win_loss_message = f"😔 THẤT BẠI. Cầu ra ({final_winner}) - Dự đoán ({last_predicted_outcome})."
                    last_predicted_outcome = 'W'
                    last_final_prediction = "WAIT"
                
                history.append(final_winner)
                learn_from_history(history, learned_patterns) 
                
                if final_winner == 'B': b_wins += 1
                elif final_winner == 'P': p_wins += 1
                else: other_results += 1 

                # NÂNG CẤP GIAO DIỆN: Thông báo kết quả
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\n" + "="*60)
                if final_winner == 'B': print("🔴 KẾT QUẢ: BANKER THẮNG!")
                elif final_winner == 'P': print("🔵 KẾT QUẢ: PLAYER THẮNG!")
                else: print("🟢 KẾT QUẢ: HÒA (TIE) 🟢") 
                
                if win_loss_message:
                    print("-" * 60)
                    print(win_loss_message)
                print("=" * 60 + "\n")
        
        if da_chot and not is_betting_time:
            if winner == 'WAIT':
                da_chot = False
                count_stable = 0
                last_winner = "WAIT"
                print("🔄 Đang chờ ván mới...")

        # HIỂN THỊ TRẠNG THÁI (3 dòng cập nhật liên tục)
        win_loss_str = f"| B:{b_wins} - P:{p_wins} - H:{other_results}" 
        if dang_cuoc:
            status_update = f"🟢 ĐỒNG HỒ: {timer_display}s"
        elif da_chot:
            status_update = f"🔔 ĐÃ CHỐT: {history[-1]}"
        else:
            status_update = f"⏸️  ĐANG CHIA BÀI"
            
        doc_mau_hien_tai = winner if winner != 'WAIT' else 'WAIT' # Đảm bảo biến được định nghĩa ở đây
            
        # Sử dụng Carriage Return (\r) và di chuyển con trỏ (\033[A) để cập nhật 3 dòng dưới cùng
        print(f"\r[1] {status_update} {win_loss_str}                                       ", end="")
        print(f"\n[2] 👁️ MÀU ĐỌC: {doc_mau_hien_tai} | Ổn định KQ: {count_stable}/{DO_KIEN_NHAN} | Ổn định TG: {count_timer_stable}/{TIMER_STABILITY_THRESHOLD}      ", end="")
        print(f"\n[3] 🛠️ DEBUG: Đỏ Trội: {score_red} | Xanh Trội: {score_blue} | Timer Trội: {score_timer}      ", end="")
        
        # Di chuyển con trỏ lên 3 dòng để chuẩn bị cho lần cập nhật tiếp theo
        print("\033[A\033[A\033[A", end="") 

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nĐã dừng. Dữ liệu học tập đã được lưu vào 'learned_patterns.json'.")
except Exception as e:
    print(f"\n❌ LỖI NGHIÊM TRỌNG: {e}")
    # Đảm bảo hiển thị lỗi rõ ràng
    print(f"Chi tiết lỗi: {e}")
    print("Vui lòng kiểm tra lại đường dẫn Tesseract (dùng biến `pytesseract.pytesseract.tesseract_cmd`) hoặc cài đặt lại thư viện OCR.")
