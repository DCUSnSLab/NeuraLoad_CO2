import pandas as pd
import re
from datetime import timedelta

# 상수 정의
AFR = 14.6 #디젤 공연비
CARBON_RATIO = 0.84118
M_CO2 = 44.01
M_C = 12.01
K = (1 / AFR) * CARBON_RATIO * (M_CO2 / M_C)  # 약 0.20969

def extract_numeric(value):
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(value))
    return float(match.group()) if match else None

def calculate_co2_from_maf_with_timestamp_adjustment(csv_path):
    df = pd.read_csv(csv_path)

    # MAF 정리
    df['MAF'] = df['MAF'].apply(extract_numeric)

    # timestamp 정리
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 초 단위로 timestamp 자동 분산
    base_time = df['timestamp'].iloc[0]
    df['timestamp'] = [base_time + timedelta(seconds=i) for i in range(len(df))]

    # 시간 차이 계산
    df['delta_t'] = df['timestamp'].diff().dt.total_seconds().fillna(0)

    # CO2 계산
    df['CO2_g'] = df['MAF'] * K * df['delta_t']
    df['CO2_cumulative_g'] = df['CO2_g'].cumsum()

    return df[['timestamp', 'MAF', 'delta_t', 'CO2_g', 'CO2_cumulative_g']]

# 실행 예시
if __name__ == "__main__":
    file_path = "processed_data/obd_log_edit.csv"  # 실제 파일 경로로 수정하세요
    df_result = calculate_co2_from_maf_with_timestamp_adjustment(file_path)
    df_result.to_csv("result_data/co2_estimation_result_3.csv", index=False)

    print(df_result)
