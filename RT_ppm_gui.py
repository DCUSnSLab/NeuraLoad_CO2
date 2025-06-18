import obd
import time
import csv
import re
import os
from datetime import datetime
import tkinter as tk
import threading

# ------------------ CO₂ 계산 상수 정의 ------------------
AFR = 14.6
CARBON_RATIO = 0.84118
M_CO2 = 44.01
M_C = 12.01
V_molar = 22.4
K = (1 / AFR) * CARBON_RATIO * (M_CO2 / M_C)
confined_volume_L = 55

# ------------------ 세그먼트 정의 ------------------
SEGMENTS = {
    '0': ['A', 'B', 'C', 'D', 'E', 'F'],
    '1': ['B', 'C'],
    '2': ['A', 'B', 'G', 'E', 'D'],
    '3': ['A', 'B', 'C', 'D', 'G'],
    '4': ['F', 'G', 'B', 'C'],
    '5': ['A', 'F', 'G', 'C', 'D'],
    '6': ['A', 'F', 'E', 'D', 'C', 'G'],
    '7': ['A', 'B', 'C'],
    '8': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
    '9': ['A', 'B', 'C', 'D', 'F', 'G'],
    '.': []
}

# ------------------ 유틸 함수 ------------------
def extract_numeric(value):
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(value))
    return float(match.group()) if match else None

# ------------------ 세그먼트 클래스 ------------------
class SevenSegmentDigit:
    def __init__(self, canvas, x, y, size=60, on_color="red", off_color="#300000"):
        self.canvas = canvas
        self.segments = {}
        s = size
        w = s // 5
        h = s
        self.coords = {
            'A': (x + w, y, x + s - w, y + w),
            'B': (x + s - w, y + w, x + s, y + h),
            'C': (x + s - w, y + h + w, x + s, y + 2 * h),
            'D': (x + w, y + 2 * h, x + s - w, y + 2 * h + w),
            'E': (x, y + h + w, x + w, y + 2 * h),
            'F': (x, y + w, x + w, y + h),
            'G': (x + w, y + h, x + s - w, y + h + w)
        }
        for name, coord in self.coords.items():
            self.segments[name] = canvas.create_rectangle(*coord, fill=off_color, outline=off_color)
        self.on_color = on_color
        self.off_color = off_color

    def display(self, char):
        on_segments = SEGMENTS.get(char, [])
        for name in self.segments:
            color = self.on_color if name in on_segments else self.off_color
            self.canvas.itemconfig(self.segments[name], fill=color, outline=color)

# ------------------ GUI 초기화 ------------------
root = tk.Tk()
root.title("PPM 디지털 디스플레이")
canvas = tk.Canvas(root, width=400, height=200, bg="black")
canvas.pack()

digit_spacing = 120
digit_start_x = (400 - digit_spacing * 2) // 2
y_pos = 30

digits = [
    SevenSegmentDigit(canvas, digit_start_x + i * digit_spacing, y_pos) for i in range(2)
]

# 중간 소수점 (LED 점)
dot_radius = 6
dot_x = digit_start_x + digit_spacing - 10
dot_y = y_pos + 130
dot = canvas.create_oval(dot_x - dot_radius, dot_y - dot_radius, dot_x + dot_radius, dot_y + dot_radius,
                         fill="red", outline="red")

# ------------------ 실시간 업데이트 ------------------
latest_ppm_display = "00"

def update_gui():
    digits[0].display(latest_ppm_display[0])
    digits[1].display(latest_ppm_display[1])
    root.after(500, update_gui)

# ------------------ OBD 데이터 수집 ------------------
def run_obd():
    global latest_ppm_display
    print("🔌 OBD 연결 시도 중...")
    connection = obd.OBD("COM7")
    if not connection.is_connected():
        print("❌ OBD-II 연결 실패")
        return
    print("✅ OBD-II 연결 성공")

    csv_filename = "obd_ppm_0609_RT_log_3.csv"
    write_header = not os.path.exists(csv_filename)

    with open(csv_filename, mode='a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(["timestamp", "SPEED(km/h)", "MAF(g/s)", "CO2(g)", "CO2 누적(g)", "PPM/sec"])

        total_co2 = 0.0
        prev_time = None

        try:
            while True:
                timestamp = datetime.now()
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                speed_resp = connection.query(obd.commands.SPEED)
                maf_resp = connection.query(obd.commands.MAF)
                speed = extract_numeric(speed_resp.value)
                maf = extract_numeric(maf_resp.value)

                if prev_time is None or maf is None:
                    delta_t = 1
                    co2_g = 0
                    ppm_per_sec = 0
                else:
                    delta_t = (timestamp - prev_time).total_seconds()
                    co2_g = maf * K * delta_t
                    co2_mol_per_sec = (maf * K) / M_CO2
                    co2_L_per_sec = co2_mol_per_sec * V_molar
                    ppm_per_sec = (co2_L_per_sec / confined_volume_L) * 1_000_000

                prev_time = timestamp
                total_co2 += co2_g

                writer.writerow([timestamp_str, speed, maf, round(co2_g, 4), round(total_co2, 2), round(ppm_per_sec, 2)])
                csvfile.flush()

                ppm_display = round(ppm_per_sec / 10_000, 1)
                latest_ppm_display = f"{ppm_display:.1f}".replace(".", "")  # 예: "2.3" → "23"

                print(f"⏱️ {timestamp_str} | SPEED: {speed} km/h | MAF: {maf} g/s | CO₂: {co2_g:.4f} g | PPM/s: {ppm_per_sec:.2f}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 수집 중단됨")

# ------------------ 병렬 실행 ------------------
threading.Thread(target=run_obd, daemon=True).start()
root.after(0, update_gui)
root.mainloop()
