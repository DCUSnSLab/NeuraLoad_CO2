import pandas as pd
import re

# 숫자만 추출하는 함수
def extract_numeric(value):
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(value))
    return float(match.group()) if match else None

# CSV 파일 로드
csv_path = "raw_data/obd_log_0415_1.csv"  # ← 파일 경로를 실제 파일명으로 수정하세요
df = pd.read_csv(csv_path)

# 필요한 컬럼만 남기고 나머지 삭제
columns_to_keep = ['timestamp', 'RPM', 'SPEED', 'MAF']
df = df[columns_to_keep]

# RPM, SPEED, MAF에 숫자 추출 적용
for col in ['RPM', 'SPEED', 'MAF']:
    df[col] = df[col].apply(extract_numeric)

# 결과 확인
print(df.head)

# 정제된 CSV 저장 (선택)
df.to_csv("processed_data/obd_log_0415_1_processed.csv", index=False)
