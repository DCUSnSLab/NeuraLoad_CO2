import pandas as pd
import time

# ------------------ CO₂ 계산 상수 정의 ------------------
AFR = 14.6                 # 공기-연료비 (디젤)
CARBON_RATIO = 0.84118     # 연료 내 탄소 비율
M_CO2 = 44.01              # 이산화탄소 분자량
M_C = 12.01                # 탄소 원자량
V_molar = 22.4             # 몰당 부피 (L)
K = (1 / AFR) * CARBON_RATIO * (M_CO2 / M_C)  # CO2 계산 상수
confined_volume_L = 55     # 밀폐공간 가정 (1m³)

# ------------------ 데이터 로딩 ------------------
df = pd.read_csv('obd_ppm_0618_RT_log_3.csv', encoding='cp949')
df['timestamp'] = pd.to_datetime(df['timestamp'])

print("🔁 리시뮬레이션 시작\n")

total_co2 = 0.0
prev_time = None

for i, row in df.iterrows():
    timestamp = row['timestamp']
    speed = row['SPEED(km/h)']
    maf = row['MAF(g/s)']

    if pd.isna(maf):
        print(f"⏱️ {timestamp} | MAF 값 없음. 건너뜀")
        continue

    if prev_time is None:
        delta_t = 1
    else:
        delta_t = (timestamp - prev_time).total_seconds()
    prev_time = timestamp

    co2_g = maf * K * delta_t
    co2_mol_per_sec = (maf * K) / M_CO2
    co2_L_per_sec = co2_mol_per_sec * V_molar
    ppm_per_sec = (co2_L_per_sec / confined_volume_L) * 1_000_000
    total_co2 += co2_g

    print(f"⏱️ {timestamp} | SPEED: {speed} km/h | MAF: {maf} g/s | CO₂: {co2_g:.4f} g | 누적: {total_co2:.2f} g | PPM/s: {ppm_per_sec:.2f}")
    time.sleep(1)  # 실시간 시뮬레이션처럼 보이기 위해 지연

print("\n✅ 리시뮬레이션 완료")
