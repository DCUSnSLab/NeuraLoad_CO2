import obd
import time
import csv
import re
from datetime import datetime
import os

# ------------------ CO₂ 계산 상수 정의 ------------------
AFR = 14.6                 # 공기-연료비 (디젤)
CARBON_RATIO = 0.84118     # 연료 내 탄소 비율
M_CO2 = 44.01              # 이산화탄소 분자량
M_C = 12.01                # 탄소 원자량
V_molar = 22.4             # 몰당 부피 (L)
K = (1 / AFR) * CARBON_RATIO * (M_CO2 / M_C)  # CO2 계산 상수
confined_volume_L = 55   # 밀폐공간 가정 (1m³)

# ------------------ 유틸 함수 ------------------
def extract_numeric(value):
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(value))
    return float(match.group()) if match else None

# ------------------ OBD 연결 ------------------
print("🔌 OBD 연결 시도 중...")
connection = obd.OBD("COM7")

if not connection.is_connected():
    print("❌ OBD-II 연결 실패")
    exit()
print("✅ OBD-II 연결 성공")

# ------------------ 수집할 PID ------------------
commands = [obd.commands.SPEED, obd.commands.MAF]

# ------------------ CSV 초기화 ------------------
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
            row = [timestamp_str]

            # OBD 데이터 수집
            speed_resp = connection.query(obd.commands.SPEED)
            maf_resp = connection.query(obd.commands.MAF)
            speed = extract_numeric(speed_resp.value)
            maf = extract_numeric(maf_resp.value)

            # 시간 차 계산
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

            # 출력 및 기록
            row += [speed, maf, round(co2_g, 4), round(total_co2, 2), round(ppm_per_sec, 2)]
            writer.writerow(row)
            csvfile.flush()

            print(f"⏱️ {timestamp_str} | SPEED: {speed} km/h | MAF: {maf} g/s | CO₂: {co2_g:.4f} g | PPM/s: {ppm_per_sec:.2f}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 수집 중단됨")
