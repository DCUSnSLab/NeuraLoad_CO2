import obd
import time
import csv
from datetime import datetime
import os

# 포트 수동 지정 (COM5)
connection = obd.OBD("COM5")  # 포트는 첫 번째 인자로 넘깁니다

if not connection.is_connected():
    print("❌ OBD-II 연결에 실패했습니다.")
    exit()

print("✅ OBD-II 연결 성공")

# 조회할 PID 리스트
commands = [
    obd.commands.RPM,
    obd.commands.SPEED,
    obd.commands.THROTTLE_POS,
    obd.commands.ENGINE_LOAD,
    obd.commands.COOLANT_TEMP,
    obd.commands.INTAKE_TEMP,
    obd.commands.MAF,
    # obd.commands.FUEL_LEVEL
]

# 로그 파일 이름
csv_filename = "obd_log_2.csv"

# CSV 파일이 없으면 헤더 작성
write_header = not os.path.exists(csv_filename)

with open(csv_filename, mode='a', newline='') as csvfile:
    writer = csv.writer(csvfile)

    if write_header:
        header = ["timestamp"] + [cmd.name for cmd in commands]
        writer.writerow(header)

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp]

            for cmd in commands:
                response = connection.query(cmd)
                value = response.value if not response.is_null() else "N/A"
                row.append(value)

                # 콘솔에 MAF만 출력
                if cmd == obd.commands.MAF:
                    print(f"MAF: {value}")

            writer.writerow(row)
            csvfile.flush()  # 즉시 파일에 기록
            time.sleep(2)  # 2초 간격 측정
    except KeyboardInterrupt:
        print("\n프로그램 종료됨")
