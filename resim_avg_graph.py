import tkinter as tk
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# -------------- 상수 정의 --------------
AFR = 14.6
CARBON_RATIO = 0.84118
M_CO2 = 44.01
M_C = 12.01
V_molar = 22.4
K = (1 / AFR) * CARBON_RATIO * (M_CO2 / M_C)
confined_volume_L = 55

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

class SevenSegmentDigit:
    def __init__(self, canvas, x, y, size=60, on_color="red", off_color="#300000"):
        self.canvas = canvas
        self.segments = {}
        s, w, h = size, size // 5, size
        self.coords = {
            'A': (x + w,           y,       x + s - w,   y + w),
            'B': (x + s - w,       y + w,   x + s,       y + h),
            'C': (x + s - w,       y + h + w, x + s,     y + 2*h),
            'D': (x + w,           y + 2*h, x + s - w,   y + 2*h + w),
            'E': (x,               y + h + w, x + w,     y + 2*h),
            'F': (x,               y + w,   x + w,       y + h),
            'G': (x + w,           y + h,   x + s - w,   y + h + w)
        }
        for name, coord in self.coords.items():
            self.segments[name] = canvas.create_rectangle(*coord, fill=off_color, outline=off_color)
        self.on_color, self.off_color = on_color, off_color

    def display(self, char):
        on_segs = SEGMENTS.get(char, [])
        for name in self.segments:
            color = self.on_color if name in on_segs else self.off_color
            self.canvas.itemconfig(self.segments[name], fill=color, outline=color)

# -------------- GUI 초기화 --------------
root = tk.Tk()
root.title("PPM → % 리시뮬레이션")

# Timestamp 표시
time_var = tk.StringVar(value="Time: --:--:--")
time_label = tk.Label(root, textvariable=time_var, fg="white", bg="black", font=("Helvetica", 12))
time_label.pack(pady=(5, 0))

canvas_width = 260
canvas = tk.Canvas(root, width=canvas_width, height=200, bg="black")
canvas.pack()

# 두 자리(정수부·소수 첫째) 디지털
digit_spacing = 90
digit_start_x = (canvas_width - digit_spacing * 1.7) // 2
y_pos = 34
digits = [
    SevenSegmentDigit(canvas, digit_start_x + i * digit_spacing, y_pos)
    for i in range(2)
]

# 소수점 점
dot_radius = 6
dot_x = digit_start_x + digit_spacing - 20
dot_y = y_pos + 128
canvas.create_oval(
    dot_x - dot_radius, dot_y - dot_radius,
    dot_x + dot_radius, dot_y + dot_radius,
    fill="red", outline="red"
)

# 실시간 평균 % 표시 라벨
avg_var = tk.StringVar(value="Avg %: 0.0")
avg_label = tk.Label(root, textvariable=avg_var, fg="white", bg="black", font=("Helvetica", 14))
avg_label.pack(pady=5)

# -------------- CSV 로드 --------------
df = pd.read_csv("obd_ppm_0619_RT_log_2.csv", encoding='cp949')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# -------------- 상태 변수 --------------
index = 0
percent_values = []
timestamps = []
total_percent = 0.0
count = 0

# -------------- 업데이트 함수 --------------
def update_display():
    global index, total_percent, count

    # 데이터가 모두 끝나면 종료 및 그래프 표시
    if index >= len(df):
        on_close()
        return

    row = df.iloc[index]
    ppm = row['PPM/sec']
    ts  = row['timestamp']

    # timestamp 레이블 갱신
    time_var.set("Time: " + ts.strftime("%Y-%m-%d %H:%M:%S"))

    # ppm → % (1 % = 10000 ppm)
    percent = ppm / 10000.0
    disp = round(percent, 1)  # 소수 첫째자리

    # 세그먼트 디스플레이
    s = f"{disp:.1f}"
    digits[0].display(s[0])  # 정수부
    digits[1].display(s[2])  # 소수 첫째

    # 평균 % 계산 및 라벨 업데이트
    total_percent += percent
    count += 1
    percent_values.append(percent)
    timestamps.append(ts)
    avg_var.set(f"Avg %: {round(total_percent/count, 3)}")

    index += 1
    root.after(1000, update_display)

# -------------- 종료 시 그래프 출력 --------------
def on_close():
    if percent_values:
        plt.figure()
        plt.plot(timestamps, percent_values, marker='o')
        plt.xlabel("Time")
        plt.ylabel("% (ppm → %)")
        plt.title("리시뮬레이션 % 추이")
        plt.tight_layout()
        plt.show()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# -------------- 실행 --------------
root.after(0, update_display)
root.mainloop()
