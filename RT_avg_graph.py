import obd
import time
import csv
import re
import os
from datetime import datetime
import tkinter as tk
import threading
import matplotlib.pyplot as plt

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
            self.segments[name] = canvas.create_rectangle(*coord,
                                                          fill=off_color,
                                                          outline=off_color)
        self.on_color = on_color
        self.off_color = off_color

    def display(self, char):
        on_segments = SEGMENTS.get(char, [])
        for name in self.segments:
            color = self.on_color if name in on_segments else self.off_color
            self.canvas.itemconfig(self.segments[name],
                                   fill=color,
                                   outline=color)

# ------------------ GUI 초기화 ------------------
root = tk.Tk()
root.title("PPM & CO₂ 모니터")

# Timestamp 표시
time_var = tk.StringVar(value="Time: --:--:--")
time_label = tk.Label(root,
                      textvariable=time_var,
                      fg="white",
                      bg="black",
                      font=("Helvetica", 12))
time_label.pack(pady=(5, 0))

canvas = tk.Canvas(root, width=400, height=200, bg="black")
canvas.pack()

# PPM 디스플레이
digit_spacing = 120
digit_start_x = (400 - digit_spacing * 2) // 2
y_pos = 30
digits = [
    SevenSegmentDigit(canvas, digit_start_x + i * digit_spacing, y_pos)
    for i in range(2)
]
dot = canvas.create_oval(digit_start_x + digit_spacing - 10 - 6,
                         y_pos + 130 - 6,
                         digit_start_x + digit_spacing - 10 + 6,
                         y_pos + 130 + 6,
                         fill="red",
                         outline="red")

# 실시간 평균 CO₂ 표시용 라벨
avg_var = tk.StringVar(value="Avg CO₂: 0.000 g")
avg_label = tk.Label(root,
                     textvariable=avg_var,
                     fg="white",
                     bg="black",
                     font=("Helvetica", 14))
avg_label.pack(pady=5)

# ------------------ 전역 상태 변수 ------------------
latest_ppm_display = "00"
last_timestamp = None
last_avg_co2 = 0.0

co2_values = []
timestamps = []
stop_event = threading.Event()

# ------------------ GUI 업데이트 ------------------
def update_gui():
    global latest_ppm_display, last_timestamp, last_avg_co2

    # 세그먼트 숫자 업데이트
    digits[0].display(latest_ppm_display[0])
    digits[1].display(latest_ppm_display[1])

    # Timestamp 업데이트
    if last_timestamp:
        time_var.set("Time: " + last_timestamp.strftime("%Y-%m-%d %H:%M:%S"))

    # 평균 CO₂ 업데이트
    avg_var.set(f"Avg CO₂: {last_avg_co2:.3f} g")

    root.after(500, update_gui)

# ------------------ OBD 데이터 수집 ------------------
def run_obd():
    global latest_ppm_display, last_timestamp, last_avg_co2

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
            writer.writerow([
                "timestamp", "SPEED(km/h)", "MAF(g/s)",
                "CO2(g)", "CO2 누적(g)", "PPM/sec"
            ])

        total_co2 = 0.0
        prev_time = None
        count = 0

        try:
            while not stop_event.is_set():
                timestamp = datetime.now()
                speed = extract_numeric(connection.query(obd.commands.SPEED).value)
                maf_resp = connection.query(obd.commands.MAF)
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
                count += 1

                # CSV 기록
                writer.writerow([
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    speed, maf, round(co2_g, 4),
                    round(total_co2, 2), round(ppm_per_sec, 2)
                ])
                csvfile.flush()

                # PPM 디스플레이용 문자열
                ppm_display = round(ppm_per_sec / 10_000, 1)
                latest_ppm_display = f"{ppm_display:.1f}".replace(".", "")

                # 전역 타임스탬프·평균 업데이트
                last_timestamp = timestamp
                last_avg_co2 = total_co2 / count if count else 0.0

                time.sleep(1)

        except Exception as e:
            print("⚠️ OBD 수집 중 오류:", e)

# ------------------ 종료 및 그래프 출력 ------------------
def on_close():
    stop_event.set()
    time.sleep(1.1)  # 수집 루프 탈출 대기
    if co2_values:
        plt.figure()
        plt.plot(timestamps, co2_values, marker='o')
        plt.xlabel("Time")
        plt.ylabel("CO₂ per interval (g)")
        plt.title("CO₂ 출력값 추이")
        plt.tight_layout()
        plt.show()
    root.destroy()

# Bind window close and 'q' key to 종료 함수
root.protocol("WM_DELETE_WINDOW", on_close)
root.bind("<KeyPress-q>", lambda e: on_close())
root.focus_set()

# ------------------ 애플리케이션 실행 ------------------
threading.Thread(target=run_obd, daemon=True).start()
root.after(0, update_gui)
root.mainloop()
