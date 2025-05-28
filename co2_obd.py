import pandas as pd
import re

# 상수 정의 (디젤 기준)
AFR = 14.6
CARBON_RATIO = 0.84118
M_CO2 = 44.01
M_C = 12.01
K = (1 / AFR) * CARBON_RATIO * (M_CO2 / M_C)  # 약 0.21104

# IPCC 연료 기준 (디젤): 74.1 g CO₂ / MJ, 35.8 MJ/L
IPCC_CO2_per_L = 74.1 * 35.8  # g CO₂ / L ≈ 2654.8 g/L

# 차량 제원 CO₂ (가정): 133 g/km
SPEC_CO2_per_km = 133.0  # g/km

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

    # MAF 기반 CO₂ 계산
    df['CO2_g'] = df['MAF'] * K * df['delta_t']
    df['CO2_cumulative_g'] = df['CO2_g'].cumsum()

    # 거리 계산
    df['distance_km'] = (df['SPEED'] * df['delta_t']) / 3600
    df['cumulative_km'] = df['distance_km'].cumsum()

    # 시간, 거리, MAF 총합
    total_co2_maf = df['CO2_cumulative_g'].iloc[-1]
    total_km = df['cumulative_km'].iloc[-1]
    total_time_sec = df['delta_t'].sum()
    avg_speed_kmh = (total_km / total_time_sec) * 3600 if total_time_sec > 0 else 0

    # 연료 사용량 (L) = (MAF / AFR) * time / fuel density
    # 디젤 연료 밀도 ≈ 0.832 kg/L → g 기준으로 832
    total_maf = df['MAF'].sum() * df['delta_t'].mean()  # 단순 근사
    fuel_g = total_maf / AFR
    fuel_L = fuel_g / 832

    # IPCC 방법 CO₂ 계산
    total_co2_ipcc = fuel_L * IPCC_CO2_per_L

    # 제원 기반 CO₂ 계산
    total_co2_spec = total_km * SPEC_CO2_per_km

    # 평균 CO₂ 배출량
    g_per_km_maf = total_co2_maf / total_km if total_km > 0 else None
    g_per_km_ipcc = total_co2_ipcc / total_km if total_km > 0 else None

    # 출력
    print(f"\n🧾 주행 통계")
    print(f"총 주행 거리: {total_km:.3f} km")
    print(f"총 주행 시간: {int(total_time_sec)}초 ({int(total_time_sec//60)}분 {int(total_time_sec%60)}초)")
    print(f"평균 속도: {avg_speed_kmh:.2f} km/h")

    print(f"\n📊 CO₂ 배출량 비교")
    print(f"1. 차량 제원 기준 (133 g/km)           : {total_co2_spec:.2f} g")
    print(f"2. IPCC 연료 사용 기반 추정             : {total_co2_ipcc:.2f} g")
    print(f"   ↳ 연료 소모량 추정: {fuel_L:.3f} L")
    print(f"3. MAF 기반 추정                         : {total_co2_maf:.2f} g")

    print(f"\n📉 평균 CO₂ 배출량 비교")
    print(f"1. 제원 기준                             : 133.00 g/km")
    print(f"2. IPCC 방식                             : {g_per_km_ipcc:.2f} g/km")
    print(f"3. MAF 기반                              : {g_per_km_maf:.2f} g/km")

    return df[['timestamp', 'MAF', 'SPEED', 'delta_t', 'CO2_g', 'CO2_cumulative_g', 'distance_km', 'cumulative_km']]

# 실행
if __name__ == "__main__":
    file_path = "processed_data/obd_log_0415_1_processed.csv"  # 실제 경로로 수정
    df_result = calculate_co2_from_maf(file_path)
    df_result.to_csv("result_data/co2_estimation_result_0415_1.csv", index=False)
