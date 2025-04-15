import pandas as pd
import re

# 상수 정의 (디젤 기준)
AFR = 14.6
CARBON_RATIO = 0.84118
M_CO2 = 44.01
M_C = 12.01
K = (1 / AFR) * CARBON_RATIO * (M_CO2 / M_C)  # 약 0.21104

# 숫자만 추출하는 함수
def extract_numeric(value):
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(value))
    return float(match.group()) if match else None

def calculate_co2_from_maf(csv_path):
    df = pd.read_csv(csv_path)

    # 숫자 정리
    df['MAF'] = df['MAF'].apply(extract_numeric)
    df['SPEED'] = df['SPEED'].apply(extract_numeric)

    # timestamp 처리
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['delta_t'] = df['timestamp'].diff().dt.total_seconds().fillna(0)

    # CO₂ 계산
    df['CO2_g'] = df['MAF'] * K * df['delta_t']
    df['CO2_cumulative_g'] = df['CO2_g'].cumsum()

    # 거리 계산 (km)
    df['distance_km'] = (df['SPEED'] * df['delta_t']) / 3600
    df['cumulative_km'] = df['distance_km'].cumsum()

    # 종합 계산
    total_co2 = df['CO2_cumulative_g'].iloc[-1]
    total_km = df['cumulative_km'].iloc[-1]
    total_time_sec = df['delta_t'].sum()

    g_per_km = total_co2 / total_km if total_km > 0 else None
    avg_speed_kmh = (total_km / total_time_sec) * 3600 if total_time_sec > 0 else 0

    # 시간 포맷
    minutes = int(total_time_sec // 60)
    seconds = int(total_time_sec % 60)

    # 출력
    print(f"총 주행 거리: {total_km:.3f} km")
    print(f"총 주행 시간: {int(total_time_sec)}초 ({minutes}분 {seconds}초)")
    print(f"총 CO₂ 배출량: {total_co2:.2f} g")
    print(f"평균 CO₂ 배출량: {g_per_km:.2f} g/km")
    print(f"평균 속도: {avg_speed_kmh:.2f} km/h")

    return df[['timestamp', 'MAF', 'SPEED', 'delta_t', 'CO2_g', 'CO2_cumulative_g', 'distance_km', 'cumulative_km']]

# 실행 예시
if __name__ == "__main__":
    file_path = "processed_data/obd_log_0415_1_processed.csv"  # 파일 경로 수정
    df_result = calculate_co2_from_maf(file_path)
    df_result.to_csv("result_data/co2_estimation_result_0415_1.csv", index=False)
