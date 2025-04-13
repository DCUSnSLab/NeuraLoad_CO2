import pandas as pd
import re
from datetime import timedelta

# 상수 정의 (디젤 기준)
AFR = 14.6
CARBON_RATIO = 0.84118
M_CO2 = 44.01
M_C = 12.01
K = (1 / AFR) * CARBON_RATIO * (M_CO2 / M_C)  # 약 0.21104

def extract_numeric(value):
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(value))
    return float(match.group()) if match else None

def calculate_co2_from_maf_with_speed(csv_path):
    df = pd.read_csv(csv_path)

    # MAF, SPEED 정리
    df['MAF'] = df['MAF'].apply(extract_numeric)
    df['SPEED'] = df['SPEED'].apply(extract_numeric)  # km/h 기준

    # timestamp 정리
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 초 단위로 timestamp 분산
    base_time = df['timestamp'].iloc[0]
    df['timestamp'] = [base_time + timedelta(seconds=i) for i in range(len(df))]

    # 시간 차이 계산
    df['delta_t'] = df['timestamp'].diff().dt.total_seconds().fillna(0)

    # CO₂ 배출량 계산 (g)
    df['CO2_g'] = df['MAF'] * K * df['delta_t']
    df['CO2_cumulative_g'] = df['CO2_g'].cumsum()

    # 주행 거리 계산 (SPEED는 km/h → m/s → km)
    df['distance_km'] = (df['SPEED'] * 1000 / 3600) * df['delta_t'] / 1000
    df['cumulative_km'] = df['distance_km'].cumsum()

    # CO₂ 배출량 (g/km)
    df['CO2_g_per_km'] = df['CO2_cumulative_g'] / df['cumulative_km'].replace(0, float('nan'))

    return df[['timestamp', 'MAF', 'SPEED', 'delta_t',
               'CO2_g', 'CO2_cumulative_g',
               'distance_km', 'cumulative_km', 'CO2_g_per_km']]

# 실행 예시
if __name__ == "__main__":
    file_path = "processed_data/obd_log_rm_char.csv"  # 수정 필요
    df_result = calculate_co2_from_maf_with_speed(file_path)
    df_result.to_csv("result_data/co2_estimation_result_with_speed.csv", index=False)

    print(df_result)
