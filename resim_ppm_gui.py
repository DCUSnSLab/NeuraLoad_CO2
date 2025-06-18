import tkinter as tk
import pandas as pd
from datetime import datetime

# CO2 계산 상수
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


# GUI 설정
root = tk.Tk()
root.title("PPM 디스플레이")
canvas_width = 260
canvas = tk.Canvas(root, width=canvas_width, height=200, bg="black")
canvas.pack()

# 디지털 숫자 위치
digit_spacing = 90
digit_start_x = (canvas_width - digit_spacing * 1.7) // 2
y_pos = 34

# 디지털 숫자 2개만 생성: 일의 자리, 소수 첫째자리
digits = [
    SevenSegmentDigit(canvas, digit_start_x + i * digit_spacing, y_pos) for i in range(2)
]

# 중간 소수점 수동 생성
dot_radius = 6
dot_x = digit_start_x + digit_spacing - 20
dot_y = y_pos + 128
dot = canvas.create_oval(dot_x - dot_radius, dot_y - dot_radius, dot_x + dot_radius, dot_y + dot_radius,
                         fill="red", outline="red")

# CSV 로딩
df = pd.read_csv("obd_ppm_0618_RT_log_3.csv", encoding='cp949')
df['timestamp'] = pd.to_datetime(df['timestamp'])

index = 0
prev_time = None


def update_display():
    global index, prev_time
    if index >= len(df):
        return
    row = df.iloc[index]
    maf = row['MAF(g/s)']
    timestamp = row['timestamp']

    if pd.isna(maf):
        index += 1
        root.after(1000, update_display)
        return

    if prev_time is None:
        delta_t = 1
    else:
        delta_t = (timestamp - prev_time).total_seconds()
    prev_time = timestamp

    # PPM 계산
    co2_mol_per_sec = (maf * K) / M_CO2
    co2_L_per_sec = co2_mol_per_sec * V_molar
    ppm_per_sec = (co2_L_per_sec / confined_volume_L) * 1_000_000
    display_value = round(ppm_per_sec / 10_000, 1)  # ex: 2.2

    str_val = f"{display_value:.1f}"  # 항상 x.x 형태

    # 숫자 디스플레이
    digits[0].display(str_val[0])  # 정수부
    digits[1].display(str_val[2])  # 소수 첫째자리

    index += 1
    root.after(1000, update_display)


root.after(0, update_display)
root.mainloop()
